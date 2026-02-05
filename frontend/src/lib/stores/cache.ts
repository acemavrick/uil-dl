import { writable } from 'svelte/store';

// set of cached file IDs: "42_pdf", "42_zip", etc.
export const cached = writable<Set<string>>(new Set());
