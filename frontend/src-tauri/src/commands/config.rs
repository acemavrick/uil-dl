use crate::models::UserConfig;
use crate::state::AppState;
use std::sync::Arc;
use tauri::State;

#[tauri::command]
#[specta::specta]
pub async fn get_config(state: State<'_, Arc<AppState>>) -> Result<UserConfig, String> {
    let config = state.config.read().await;
    Ok(config.clone())
}

#[tauri::command]
#[specta::specta]
pub async fn set_download_dir(
    state: State<'_, Arc<AppState>>,
    path: String,
) -> Result<(), String> {
    let path_buf = std::path::PathBuf::from(&path);

    // validate path
    if !path_buf.exists() {
        std::fs::create_dir_all(&path_buf)
            .map_err(|e| format!("Failed to create directory: {}", e))?;
    }

    let mut config = state.config.write().await;
    config.download_dir = path;

    // rebuild cache for new directory
    let contests = state.contests.read().await;
    let mut cache = state.cache.write().await;
    cache.downloads_dir = path_buf;
    cache.rebuild(&contests);

    Ok(())
}

#[tauri::command]
#[specta::specta]
pub async fn set_dev_mode(state: State<'_, Arc<AppState>>, enabled: bool) -> Result<(), String> {
    let mut config = state.config.write().await;
    config.dev_mode = enabled;
    Ok(())
}
