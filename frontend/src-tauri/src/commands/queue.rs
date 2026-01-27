// queue management commands
use crate::models::{QueueItem, QueueRequest, QueueStatus};
use crate::state::AppState;
use std::sync::Arc;
use tauri::State;

#[tauri::command]
#[specta::specta]
pub async fn add_to_queue(
    state: State<'_, Arc<AppState>>,
    items: Vec<QueueRequest>,
) -> Result<(), String> {
    let mut queue = state.queue.write().await;
    let cache = state.cache.read().await;

    for req in items {
        let id = format!("{}_{}", req.contest_id, req.file_type);

        // skip if already in queue
        if queue.iter().any(|item| item.id == id) {
            continue;
        }

        // skip if already cached
        if cache.is_cached(&id) {
            continue;
        }

        // add to queue
        let item = QueueItem {
            id,
            contest_id: req.contest_id,
            file_type: req.file_type,
            status: QueueStatus::Pending,
            progress: None,
            error: None,
            retries: 0,
        };

        queue.push(item);
    }

    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn remove_from_queue(
    state: State<'_, Arc<AppState>>,
    ids: Vec<String>,
) -> Result<(), String> {
    let mut queue = state.queue.write().await;

    // only remove pending or failed items
    queue.retain(|item| {
        if ids.contains(&item.id) {
            !matches!(item.status, QueueStatus::Pending | QueueStatus::Failed)
        } else {
            true
        }
    });

    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn retry_failed(
    state: State<'_, Arc<AppState>>,
    ids: Vec<String>,
) -> Result<(), String> {
    let mut queue = state.queue.write().await;

    for item in queue.iter_mut() {
        if ids.contains(&item.id) && item.status == QueueStatus::Failed {
            item.status = QueueStatus::Pending;
            item.retries = 0;
            item.error = None;
            item.progress = None;
        }
    }

    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn clear_completed(state: State<'_, Arc<AppState>>) -> Result<(), String> {
    let mut queue = state.queue.write().await;
    queue.retain(|item| item.status != QueueStatus::Complete);
    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn get_queue(state: State<'_, Arc<AppState>>) -> Result<Vec<QueueItem>, String> {
    let queue = state.queue.read().await;
    Ok(queue.clone())
}
