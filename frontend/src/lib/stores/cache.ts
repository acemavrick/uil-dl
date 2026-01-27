import { writable, derived } from 'svelte/store';

// set of cached file IDs: "42_pdf", "42_zip", etc.
export const cached = writable<Set<string>>(new Set());

// helper to check if a specific file is cached
export const isCached = (contestId: number, fileType: string): boolean => {
    let result = false;
    cached.subscribe(c => { result = c.has(`${contestId}_${fileType}`); })();
    return result;
};

// reactive check for use in components
export const createCacheCheck = (contestId: number, fileType: string) => {
    return derived(cached, ($cached) => $cached.has(`${contestId}_${fileType}`));
};
