// download queue processor with rate limiting
use crate::download::{cleanup_temp_file, download_file, DownloadOptions};
use crate::models::{DownloadProgress, QueueItem, QueueStatus, QueueUpdate};
use crate::state::{cache_id_to_filename, AppState};
use std::sync::Arc;
use std::time::Duration;
use tauri::{AppHandle, Emitter};
use tokio::time::sleep;

const MAX_CONCURRENT: usize = 4;
const START_DELAY_MS: u64 = 100;
const MAX_RETRIES: u32 = 4;
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
        // check for pending items
        let next_item = {
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
                log::warn!(
                    "download failed for {} (attempt {}/{}): {}",
                    item.id,
                    attempt + 1,
                    MAX_RETRIES + 1,
                    e
                );

                item.retries = attempt + 1;

                // cleanup temp file
                cleanup_temp_file(&dest_path).await;

                // if not last attempt, wait before retry
                if attempt < MAX_RETRIES {
                    sleep(RETRY_DELAYS[attempt as usize]).await;
                } else {
                    // max retries exceeded
                    return Err(format!("max retries exceeded: {}", e));
                }
            }
        }
    }

    Err("download failed".to_string())
}

async fn emit_queue_update(app_handle: &AppHandle, state: &Arc<AppState>) {
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
    };

    let _ = app_handle.emit("queue-update", update);
}
