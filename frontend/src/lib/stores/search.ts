import { writable } from 'svelte/store';

export const searchQuery = writable<string>('');
export const fuzzyEnabled = writable<boolean>(true);
