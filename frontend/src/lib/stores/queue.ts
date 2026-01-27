// download queue store
import { writable } from 'svelte/store';
import type { QueueItem } from '$lib/bindings';

export const queue = writable<QueueItem[]>([]);
export const queueStats = writable({
    active: 0,
    pending: 0,
    completed: 0
});
