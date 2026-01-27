import { writable } from 'svelte/store';
import type { UserConfig } from '$lib/tauri';

export const config = writable<UserConfig>({
    download_dir: '',
    dev_mode: false
});
