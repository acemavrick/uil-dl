pub mod bindings;
pub mod commands;
mod download;
mod info;
pub mod models;
mod queue;
mod state;

use models::{LoadingProgress, RawInfo};
use state::{AppState, CacheIndex};
use std::path::PathBuf;
use std::sync::Arc;
use queue::start_queue_processor;
use tauri::{Emitter, Manager, RunEvent,
    utils::config::WebviewUrl,
    webview::WebviewWindowBuilder,
};

const BAKED_INFO: &str = include_str!("../baked/info.json");

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_os::init())
        .plugin(
            tauri_plugin_log::Builder::default()
                .level(log::LevelFilter::Info)
                .build(),
        )
        .manage(Arc::new(AppState::new()))
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // hide window instead of closing
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .setup(|app| {
            let _window = WebviewWindowBuilder::new(
                app,
                "main",
                WebviewUrl::default() // use devURL in dev, frontendDist in prod
            )
            .title_bar_style(tauri::TitleBarStyle::Overlay)
            .title("")
            .inner_size(1000.0, 700.0)
            .min_inner_size(600.0, 400.0)
            .resizable(true)
            .background_color(tauri::window::Color(0, 0, 0, 255))
            .on_navigation(|url| {
                // allow tauri/asset protocols and localhost ONLY
                let allowed = matches!(url.scheme(), "tauri" | "asset")
                || url.host_str() == Some("localhost")
                || url.host_str() == Some("127.0.0.1");
                
                // for debug, REMOVE IN PRODUCTION
                if !allowed {
                    log::warn!("Blocked navigation to {}", url);
                }
                
                allowed
            })
            .build()?;
            
            let handle = app.handle().clone();
            let state = app.state::<Arc<AppState>>().inner().clone();

            // start queue processor
            start_queue_processor(handle.clone(), state.clone());

            // async initialization
            tauri::async_runtime::spawn(async move {
                initialize_app(handle, state).await;
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_contests,
            commands::get_cached,
            commands::get_info_version,
            commands::get_config,
            commands::set_download_dir,
            commands::set_dev_mode,
            commands::open_file,
            commands::open_downloads_folder,
            commands::rebuild_cache,
            commands::open_url,
            commands::add_to_queue,
            commands::remove_from_queue,
            commands::retry_failed,
            commands::clear_completed,
            commands::get_queue,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::Reopen { has_visible_windows, .. } = event {
                if !has_visible_windows {
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
            }
        });
}

async fn initialize_app(handle: tauri::AppHandle, state: Arc<AppState>) {
    // stage 1: load config
    let _ = handle.emit(
        "loading-progress",
        LoadingProgress {
            stage: "config".to_string(),
            done: false,
            message: Some("Loading configuration...".to_string()),
            count: None,
        },
    );

    let config = models::UserConfig::default();
    let downloads_dir = PathBuf::from(&config.download_dir);

    // ensure downloads directory exists
    if !downloads_dir.exists() {
        let _ = std::fs::create_dir_all(&downloads_dir);
    }

    {
        let mut cfg = state.config.write().await;
        *cfg = config;
    }

    let _ = handle.emit(
        "loading-progress",
        LoadingProgress {
            stage: "config".to_string(),
            done: true,
            message: None,
            count: None,
        },
    );

    // stage 2: parse contests from baked info.json
    let _ = handle.emit(
        "loading-progress",
        LoadingProgress {
            stage: "contests".to_string(),
            done: false,
            message: Some("Parsing contest data...".to_string()),
            count: None,
        },
    );

    let contests = match serde_json::from_str::<RawInfo>(BAKED_INFO) {
        Ok(raw) => {
            let version = raw.version;
            let parsed = info::parse_info(raw);
            {
                let mut v = state.info_version.write().await;
                *v = version;
            }
            parsed
        }
        Err(e) => {
            log::error!("Failed to parse baked info.json: {}", e);
            Vec::new()
        }
    };

    let contest_count = contests.len() as u32;
    {
        let mut c = state.contests.write().await;
        *c = contests.clone();
    }

    let _ = handle.emit(
        "loading-progress",
        LoadingProgress {
            stage: "contests".to_string(),
            done: true,
            message: None,
            count: Some(contest_count),
        },
    );

    // stage 3: scan cache
    let _ = handle.emit(
        "loading-progress",
        LoadingProgress {
            stage: "cache".to_string(),
            done: false,
            message: Some("Scanning downloaded files...".to_string()),
            count: None,
        },
    );

    let mut cache = CacheIndex::new(downloads_dir);
    cache.rebuild(&contests);
    let cache_count = cache.count() as u32;

    {
        let mut c = state.cache.write().await;
        *c = cache;
    }

    let _ = handle.emit(
        "loading-progress",
        LoadingProgress {
            stage: "cache".to_string(),
            done: true,
            message: None,
            count: Some(cache_count),
        },
    );

    log::info!(
        "Initialized: {} contests, {} cached files",
        contest_count,
        cache_count
    );
}
