use crate::models::UserConfig;
use crate::state::AppState;
use std::sync::Arc;
use tauri::State;

#[tauri::command]
pub async fn get_config(state: State<'_, Arc<AppState>>) -> Result<UserConfig, String> {
    let config = state.config.read().await;
    Ok(config.clone())
}

#[tauri::command]
pub async fn set_download_dir(state: State<'_, Arc<AppState>>, path: String) -> Result<(), String> {
    let mut config = state.config.write().await;
    config.download_dir = path;
    // TODO: persist to config file
    Ok(())
}

#[tauri::command]
pub async fn set_dev_mode(state: State<'_, Arc<AppState>>, enabled: bool) -> Result<(), String> {
    let mut config = state.config.write().await;
    config.dev_mode = enabled;
    Ok(())
}
