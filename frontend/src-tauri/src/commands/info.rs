// info.json refresh command
use crate::info::parse_info;
use crate::models::RawInfo;
use crate::network::check_network_connectivity;
use crate::state::AppState;
use std::sync::Arc;
use tauri::State;

const INFO_JSON_URL: &str = "https://raw.githubusercontent.com/acemavrick/uil-dl/dev/frontend/src-tauri/baked/info.json";

#[derive(Debug, Clone, serde::Serialize, specta::Type)]
pub struct RefreshResult {
    pub updated: bool,
    pub version: u32,
    pub message: String,
}

#[tauri::command]
#[specta::specta]
pub async fn refresh_info(state: State<'_, Arc<AppState>>) -> Result<RefreshResult, String> {
    // check network connectivity first
    if !check_network_connectivity().await {
        return Err("no network connection available".to_string());
    }

    // fetch latest info.json
    let response = reqwest::get(INFO_JSON_URL)
        .await
        .map_err(|e| format!("failed to fetch info.json: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("http error: {}", response.status()));
    }

    let text = response
        .text()
        .await
        .map_err(|e| format!("failed to read response: {}", e))?;

    let raw_info: RawInfo = serde_json::from_str(&text)
        .map_err(|e| format!("failed to parse info.json: {}", e))?;

    let new_version = raw_info.version;

    // check current version
    let current_version = {
        let version = state.info_version.read().await;
        *version
    };

    if new_version <= current_version {
        return Ok(RefreshResult {
            updated: false,
            version: current_version,
            message: "already up to date".to_string(),
        });
    }

    // parse contests
    let contests = parse_info(raw_info);

    // update state
    {
        let mut c = state.contests.write().await;
        *c = contests.clone();
    }
    {
        let mut v = state.info_version.write().await;
        *v = new_version;
    }

    // rebuild cache with new contests
    {
        let mut cache = state.cache.write().await;
        cache.rebuild(&contests);
    }

    log::info!("refreshed info.json: {} -> {}", current_version, new_version);

    Ok(RefreshResult {
        updated: true,
        version: new_version,
        message: format!("updated to version {}", new_version),
    })
}

#[tauri::command]
#[specta::specta]
pub async fn check_for_updates(state: State<'_, Arc<AppState>>) -> Result<bool, String> {
    // check network connectivity first
    if !check_network_connectivity().await {
        return Ok(false);
    }

    // fetch latest info.json to check version only
    let response = reqwest::get(INFO_JSON_URL)
        .await
        .map_err(|e| format!("failed to fetch info.json: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("http error: {}", response.status()));
    }

    let text = response
        .text()
        .await
        .map_err(|e| format!("failed to read response: {}", e))?;

    let raw_info: RawInfo = serde_json::from_str(&text)
        .map_err(|e| format!("failed to parse info.json: {}", e))?;

    let current_version = {
        let version = state.info_version.read().await;
        *version
    };

    Ok(raw_info.version > current_version)
}
