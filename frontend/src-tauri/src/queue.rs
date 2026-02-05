// download queue processor with rate limiting
use crate::download::{cleanup_temp_file, download_file, DownloadOptions};
use crate::models::{DownloadProgress, QueueItem, QueueStatus, QueueUpdate};
use crate::state::{cache_id_to_filename, AppState};
use std::sync::Arc;
use std::time::Duration;
use tauri::{AppHandle, Emitter};
use tokio::time::sleep;

const MAX_CONCURRENT: usize = 4;
const START_DELAY_MS: u64 = 150;
const MAX_RETRIES: u32 = 4;
const RATE_LIMIT_BACKOFF_SECS: u64 = 60;
const RETRY_DELAYS: [Duration; 4] = [
    Duration::from_secs(1),
    Duration::from_secs(3),
    Duration::from_secs(10),
    Duration::from_secs(30),
];

/// start queue processor in background
pub fn start_queue_processor(app_handle: AppHandle, state: Arc<AppState>) {
    tauri::async_runtime::spawn(async move {
        queue_processor_loop(app_handle, state).await;
    });
}

async fn queue_processor_loop(app_handle: AppHandle, state: Arc<AppState>) {
    let semaphore = Arc::new(tokio::sync::Semaphore::new(MAX_CONCURRENT));

    loop {
        // skip picking up new items when paused
        let next_item = if state.is_queue_paused() {
            None
        } else {
            let mut queue = state.queue.write().await;
            queue.iter_mut().find_map(|item| {
                if item.status == QueueStatus::Pending {
                    item.status = QueueStatus::Downloading;
                    Some(item.clone())
                } else {
                    None
                }
            })
        };

        if let Some(item) = next_item {
            // rate limiting: delay between starting new downloads
            sleep(Duration::from_millis(START_DELAY_MS)).await;

            let app = app_handle.clone();
            let state_clone = state.clone();
            let sem = semaphore.clone();

            // spawn download task
            tauri::async_runtime::spawn(async move {
                // acquire semaphore permit (blocks if max concurrent reached)
                let _permit = sem.acquire().await.unwrap();

                process_download_item(app, state_clone, item).await;
            });
        } else {
            // no pending items, sleep before checking again
            sleep(Duration::from_millis(500)).await;
        }
    }
}

async fn process_download_item(app_handle: AppHandle, state: Arc<AppState>, mut item: QueueItem) {
    let result = download_with_retry(&app_handle, &state, &mut item).await;

    // update final status
    {
        let mut queue = state.queue.write().await;
        if let Some(q_item) = queue.iter_mut().find(|q| q.id == item.id) {
            match result {
                Ok(bytes) => {
                    q_item.status = QueueStatus::Complete;
                    q_item.progress = Some(DownloadProgress {
                        bytes,
                        total: Some(bytes),
                    });
                    q_item.error = None;

                    // add to cache
                    let mut cache = state.cache.write().await;
                    cache.mark_downloaded(&item.id);
                }
                Err(e) => {
                    q_item.status = QueueStatus::Failed;
                    q_item.error = Some(e);
                }
            }
        }
    }

    // emit queue update
    emit_queue_update(&app_handle, &state).await;
}

async fn download_with_retry(
    app_handle: &AppHandle,
    state: &Arc<AppState>,
    item: &mut QueueItem,
) -> Result<u64, String> {
    use crate::network::is_network_error;
    // get contest and URL
    let (url, dest_path) = {
        let contests = state.contests.read().await;
        let contest = contests
            .iter()
            .find(|c| c.id == item.contest_id)
            .ok_or_else(|| "contest not found".to_string())?;

        let url = match item.file_type.as_str() {
            "pdf" => contest
                .pdf_link
                .clone()
                .ok_or_else(|| "no pdf link".to_string())?,
            "zip" => contest
                .zip_link
                .clone()
                .ok_or_else(|| "no zip link".to_string())?,
            _ => return Err("unsupported file type".to_string()),
        };

        let config = state.config.read().await;
        let filename = cache_id_to_filename(contest, &item.file_type);
        let dest_path = std::path::Path::new(&config.download_dir).join(filename);

        (url, dest_path)
    };

    // retry loop
    for attempt in 0..=MAX_RETRIES {
        let app_clone = app_handle.clone();
        let state_clone = state.clone();
        let item_id = item.id.clone();

        let result = download_file(
            DownloadOptions {
                url: url.clone(),
                dest_path: dest_path.clone(),
                expected_size: None,
            },
            move |bytes, total| {
                // update progress in queue
                let app = app_clone.clone();
                let state = state_clone.clone();
                let id = item_id.clone();

                tauri::async_runtime::spawn(async move {
                    let mut queue = state.queue.write().await;
                    if let Some(item) = queue.iter_mut().find(|q| q.id == id) {
                        item.progress = Some(DownloadProgress { bytes, total });
                    }
                    drop(queue);

                    // emit progress update (throttled to ~2 per second)
                    emit_queue_update(&app, &state).await;
                });
            },
        )
        .await;

        match result {
            Ok(bytes) => return Ok(bytes),
            Err(e) => {
                let error_str = e.to_string();
                let is_rate_limited = matches!(e, crate::download::DownloadError::RateLimited(_));

                log::warn!(
                    "download failed for {} (attempt {}/{}): {}",
                    item.id,
                    attempt + 1,
                    MAX_RETRIES + 1,
                    error_str
                );

                item.retries = attempt + 1;

                // update item error message in queue so frontend can show it
                {
                    let mut queue = state.queue.write().await;
                    if let Some(q_item) = queue.iter_mut().find(|q| q.id == item.id) {
                        if is_rate_limited {
                            q_item.error = Some("rate limited — waiting".to_string());
                        } else {
                            q_item.error = Some(error_str.clone());
                        }
                    }
                }
                emit_queue_update(app_handle, state).await;

                if is_network_error(&error_str) {
                    let mut network = state.network_state.write().await;
                    network.mark_offline(error_str.clone());
                }

                cleanup_temp_file(&dest_path).await;

                if attempt < MAX_RETRIES {
                    if is_rate_limited {
                        // rate limited: use retry-after header or default backoff
                        let wait = if let crate::download::DownloadError::RateLimited(Some(secs)) = &e {
                            Duration::from_secs(*secs)
                        } else {
                            Duration::from_secs(RATE_LIMIT_BACKOFF_SECS)
                        };
                        log::info!("rate limited, waiting {}s before retry", wait.as_secs());
                        sleep(wait).await;
                    } else {
                        sleep(RETRY_DELAYS[attempt as usize]).await;
                    }
                } else {
                    return Err(format!("max retries exceeded: {}", error_str));
                }
            }
        }
    }

    Err("download failed".to_string())
}

pub async fn emit_queue_update(app_handle: &AppHandle, state: &Arc<AppState>) {
    let queue = state.queue.read().await;
    let queue_vec = queue.clone();

    let active_count = queue_vec
        .iter()
        .filter(|item| item.status == QueueStatus::Downloading)
        .count();
    let pending_count = queue_vec
        .iter()
        .filter(|item| item.status == QueueStatus::Pending)
        .count();
    let completed_count = queue_vec
        .iter()
        .filter(|item| item.status == QueueStatus::Complete)
        .count();

    let update = QueueUpdate {
        queue: queue_vec,
        active_count,
        pending_count,
        completed_count,
        paused: state.is_queue_paused(),
    };

    let _ = app_handle.emit("queue-update", update);
}
