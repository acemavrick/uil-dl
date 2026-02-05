// queue management commands
use crate::models::{QueueItem, QueueRequest, QueueStatus};
use crate::queue::emit_queue_update;
use crate::state::AppState;
use std::sync::Arc;
use tauri::{AppHandle, State};

#[tauri::command]
#[specta::specta]
pub async fn add_to_queue(
    app_handle: AppHandle,
    state: State<'_, Arc<AppState>>,
    items: Vec<QueueRequest>,
) -> Result<(), String> {
    {
        let mut queue = state.queue.write().await;
        let cache = state.cache.read().await;

        for req in items {
            let id = format!("{}_{}", req.contest_id, req.file_type);

            // skip if already in queue or cached
            if queue.iter().any(|item| item.id == id) || cache.is_cached(&id) {
                continue;
            }

            queue.push(QueueItem {
                id,
                contest_id: req.contest_id,
                file_type: req.file_type,
                status: QueueStatus::Pending,
                progress: None,
                error: None,
                retries: 0,
            });
        }
    }
    emit_queue_update(&app_handle, &state).await;
    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn remove_from_queue(
    app_handle: AppHandle,
    state: State<'_, Arc<AppState>>,
    ids: Vec<String>,
) -> Result<(), String> {
    {
        let mut queue = state.queue.write().await;
        queue.retain(|item| {
            if ids.contains(&item.id) {
                !matches!(item.status, QueueStatus::Pending | QueueStatus::Failed)
            } else {
                true
            }
        });
    }
    emit_queue_update(&app_handle, &state).await;
    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn retry_failed(
    app_handle: AppHandle,
    state: State<'_, Arc<AppState>>,
    ids: Vec<String>,
) -> Result<(), String> {
    {
        let mut queue = state.queue.write().await;
        for item in queue.iter_mut() {
            if ids.contains(&item.id) && item.status == QueueStatus::Failed {
                item.status = QueueStatus::Pending;
                item.retries = 0;
                item.error = None;
                item.progress = None;
            }
        }
    }
    emit_queue_update(&app_handle, &state).await;
    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn clear_completed(
    app_handle: AppHandle,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    {
        let mut queue = state.queue.write().await;
        queue.retain(|item| item.status != QueueStatus::Complete);
    }
    emit_queue_update(&app_handle, &state).await;
    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn get_queue(state: State<'_, Arc<AppState>>) -> Result<Vec<QueueItem>, String> {
    let queue = state.queue.read().await;
    Ok(queue.clone())
}

#[tauri::command]
#[specta::specta]
pub async fn set_queue_paused(
    app_handle: AppHandle,
    state: State<'_, Arc<AppState>>,
    paused: bool,
) -> Result<(), String> {
    state.set_queue_paused(paused);
    emit_queue_update(&app_handle, &state).await;
    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn get_queue_paused(state: State<'_, Arc<AppState>>) -> Result<bool, String> {
    Ok(state.is_queue_paused())
}
