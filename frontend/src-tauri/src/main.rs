// prevents additional console window on windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    // generate typescript bindings on build (dev only)
    #[cfg(debug_assertions)]
    {
        use tauri_specta::{collect_commands, collect_events, Builder};

        let builder = Builder::<tauri::Wry>::new()
            .commands(collect_commands![
                uil_dl_lib::commands::get_contests,
                uil_dl_lib::commands::get_cached,
                uil_dl_lib::commands::get_info_version,
                uil_dl_lib::commands::get_config,
                uil_dl_lib::commands::set_download_dir,
                uil_dl_lib::commands::set_dev_mode,
                uil_dl_lib::commands::open_file,
                uil_dl_lib::commands::open_downloads_folder,
                uil_dl_lib::commands::rebuild_cache,
                uil_dl_lib::commands::open_url,
                uil_dl_lib::commands::add_to_queue,
                uil_dl_lib::commands::remove_from_queue,
                uil_dl_lib::commands::retry_failed,
                uil_dl_lib::commands::clear_completed,
                uil_dl_lib::commands::get_queue,
            ])
            .events(collect_events![
                uil_dl_lib::bindings::LoadingProgressEvent,
                uil_dl_lib::bindings::QueueUpdateEvent,
                uil_dl_lib::bindings::ErrorEvent,
            ]);

        // generate typescript bindings with bigint support
        builder
            .export(
                specta_typescript::Typescript::default().bigint(specta_typescript::BigIntExportBehavior::Number),
                "../src/lib/bindings.ts",
            )
            .expect("failed to export typescript bindings");
    }

    uil_dl_lib::run();
}
