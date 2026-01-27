import { invoke } from '@tauri-apps/api/core';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { platform as getPlatformOS } from '@tauri-apps/plugin-os';

// window controls
export const startDragging = () => getCurrentWindow().startDragging();
export const minimizeWindow = () => getCurrentWindow().minimize();
export const maximizeWindow = () => getCurrentWindow().toggleMaximize();
export const closeWindow = () => getCurrentWindow().close();

// os detection (cached after first call)
let cachedPlatform: string | null = null;
export async function getPlatform(): Promise<string> {
    if (!cachedPlatform) {
        cachedPlatform = getPlatformOS();
    }
    return cachedPlatform;
}

export function isMacOS(): boolean {
    return cachedPlatform === 'macos';
}

// types matching Rust models
export interface Contest {
    id: number;
    subject: string;
    level: string;
    year: number;
    level_sort: number;
    pdf_link: string | null;
    zip_link: string | null;
    other_link: string | null;
}

export interface UserConfig {
    download_dir: string;
    dev_mode: boolean;
}

export interface LoadingProgress {
    stage: string;
    done: boolean;
    message: string | null;
    count: number | null;
}

// commands
export const openUrl = (url: string) => invoke('open_url', { url });
export const getContests = () => invoke<Contest[]>('get_contests');
export const getCached = () => invoke<string[]>('get_cached');
export const getInfoVersion = () => invoke<number>('get_info_version');
export const getConfig = () => invoke<UserConfig>('get_config');
export const setDownloadDir = (path: string) => invoke('set_download_dir', { path });
export const setDevMode = (enabled: boolean) => invoke('set_dev_mode', { enabled });
export const openFile = (id: string) => invoke('open_file', { id });
export const openDownloadsFolder = () => invoke('open_downloads_folder');
export const rebuildCache = () => invoke<number>('rebuild_cache');

// events
export const onLoadingProgress = (callback: (progress: LoadingProgress) => void): Promise<UnlistenFn> => {
    return listen<LoadingProgress>('loading-progress', (event) => callback(event.payload));
};
