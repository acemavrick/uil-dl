// user config persistence
use crate::models::UserConfig;
use std::path::PathBuf;

const CONFIG_FILENAME: &str = "config.json";

/// get config file path in app data directory
fn get_config_path() -> Result<PathBuf, String> {
    let app_data = dirs::data_dir()
        .ok_or_else(|| "failed to get app data directory".to_string())?;
    let config_dir = app_data.join("dev.randeria.uildl");

    // ensure directory exists
    std::fs::create_dir_all(&config_dir)
        .map_err(|e| format!("failed to create config directory: {}", e))?;

    Ok(config_dir.join(CONFIG_FILENAME))
}

/// load config from disk, or return default if not found
pub fn load_config() -> UserConfig {
    let config_path = match get_config_path() {
        Ok(p) => p,
        Err(e) => {
            log::warn!("failed to get config path: {}, using defaults", e);
            return UserConfig::default();
        }
    };

    if !config_path.exists() {
        log::info!("config file not found, using defaults");
        return UserConfig::default();
    }

    match std::fs::read_to_string(&config_path) {
        Ok(contents) => match serde_json::from_str::<UserConfig>(&contents) {
            Ok(config) => {
                log::info!("loaded config from {:?}", config_path);
                config
            }
            Err(e) => {
                log::error!("failed to parse config file: {}, using defaults", e);
                UserConfig::default()
            }
        },
        Err(e) => {
            log::error!("failed to read config file: {}, using defaults", e);
            UserConfig::default()
        }
    }
}

/// save config to disk
pub fn save_config(config: &UserConfig) -> Result<(), String> {
    let config_path = get_config_path()?;

    let json = serde_json::to_string_pretty(config)
        .map_err(|e| format!("failed to serialize config: {}", e))?;

    std::fs::write(&config_path, json)
        .map_err(|e| format!("failed to write config file: {}", e))?;

    log::info!("saved config to {:?}", config_path);
    Ok(())
}
