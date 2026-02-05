// network state commands
use crate::state::AppState;
use std::sync::Arc;
use tauri::State;

#[derive(Debug, Clone, serde::Serialize, specta::Type)]
pub struct NetworkStatus {
    pub online: bool,
    pub last_error: Option<String>,
}

#[tauri::command]
#[specta::specta]
pub async fn get_network_status(state: State<'_, Arc<AppState>>) -> Result<NetworkStatus, String> {
    let network = state.network_state.read().await;
    Ok(NetworkStatus {
        online: network.online,
        last_error: network.last_error.clone(),
    })
}

#[tauri::command]
#[specta::specta]
pub async fn check_connectivity(state: State<'_, Arc<AppState>>) -> Result<bool, String> {
    let online = crate::network::check_network_connectivity().await;

    let mut network = state.network_state.write().await;
    if online {
        network.mark_online();
    } else {
        network.mark_offline("unable to reach server".to_string());
    }

    Ok(online)
}
