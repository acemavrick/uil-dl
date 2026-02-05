import { writable } from 'svelte/store';

export type SearchMode = 'fuzzy' | 'exact' | 'regex';

export const searchQuery = writable<string>('');
export const searchMode = writable<SearchMode>('fuzzy');
export const caseSensitive = writable<boolean>(false);
