use crate::state::{cache_id_to_filename, AppState};
use std::sync::Arc;
use tauri::State;

#[tauri::command]
pub async fn open_file(state: State<'_, Arc<AppState>>, id: String) -> Result<(), String> {
    let parts: Vec<&str> = id.split('_').collect();
    if parts.len() != 2 {
        return Err("Invalid file ID format".to_string());
    }

    let contest_id: u32 = parts[0].parse().map_err(|_| "Invalid contest ID")?;
    let file_type = parts[1];

    let contests = state.contests.read().await;
    let contest = contests
        .iter()
        .find(|c| c.id == contest_id)
        .ok_or("Contest not found")?;

    let config = state.config.read().await;
    let filename = cache_id_to_filename(contest, file_type);
    let path = std::path::Path::new(&config.download_dir).join(&filename);

    if !path.exists() {
        // file was deleted externally, update cache
        drop(config);
        drop(contests);
        let mut cache = state.cache.write().await;
        cache.mark_removed(&id);
        return Err("File not found - it may have been deleted".to_string());
    }

    opener::open(&path).map_err(|e| format!("Failed to open file: {}", e))
}

#[tauri::command]
pub async fn open_downloads_folder(state: State<'_, Arc<AppState>>) -> Result<(), String> {
    let config = state.config.read().await;
    let path = std::path::Path::new(&config.download_dir);

    // create if doesn't exist
    if !path.exists() {
        std::fs::create_dir_all(path).map_err(|e| format!("Failed to create directory: {}", e))?;
    }

    opener::open(path).map_err(|e| format!("Failed to open folder: {}", e))
}

#[tauri::command]
pub async fn rebuild_cache(state: State<'_, Arc<AppState>>) -> Result<usize, String> {
    let contests = state.contests.read().await;
    let mut cache = state.cache.write().await;
    cache.rebuild(&contests);
    Ok(cache.count())
}

#[tauri::command]
pub fn open_url(url: String) -> Result<(), String> {
    opener::open_browser(&url).map_err(|e| format!("Failed to open URL: {}", e))
}
