import { writable } from 'svelte/store';
import type { UserConfig } from '$lib/bindings';

export const config = writable<UserConfig>({
    download_dir: '',
    dev_mode: false
});
