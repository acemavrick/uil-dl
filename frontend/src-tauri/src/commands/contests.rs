use crate::models::Contest;
use crate::state::AppState;
use std::sync::Arc;
use tauri::State;

#[tauri::command]
pub async fn get_contests(state: State<'_, Arc<AppState>>) -> Result<Vec<Contest>, String> {
    let contests = state.contests.read().await;
    Ok(contests.clone())
}

#[tauri::command]
pub async fn get_cached(state: State<'_, Arc<AppState>>) -> Result<Vec<String>, String> {
    let cache = state.cache.read().await;
    Ok(cache.downloaded.iter().cloned().collect())
}

#[tauri::command]
pub async fn get_info_version(state: State<'_, Arc<AppState>>) -> Result<u32, String> {
    let version = state.info_version.read().await;
    Ok(*version)
}
