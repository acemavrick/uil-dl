<script lang="ts">
    import "../app.css";
    import { onMount, onDestroy, type Snippet } from "svelte";
    import { contests, loading } from "$lib/stores/contests";
    import { cached } from "$lib/stores/cache";
    import { config } from "$lib/stores/config";
    import { queue, queueStats, queuePaused } from "$lib/stores/queue";
    import { commands } from "$lib/bindings";
    import type { LoadingProgressEvent, QueueUpdateEvent } from "$lib/bindings";
    import { listen } from "@tauri-apps/api/event";

    let { children }: { children: Snippet } = $props();

    let ready = $state(false);
    let isTauri = $state(false);
    let loadingMessage = $state("Starting...");

    // event listener cleanup
    let cleanups: (() => void)[] = [];
    onDestroy(() => cleanups.forEach((fn) => fn()));

    onMount(async () => {
        isTauri = "__TAURI_INTERNALS__" in window;

        if (!isTauri) {
            ready = true;
            return;
        }

        // disable browser context menu in tauri
        document.addEventListener("contextmenu", (e) => e.preventDefault());

        // listen for loading progress
        const unlistenProgress = await listen<LoadingProgressEvent>("loading-progress", (e) => {
            const p = e.payload;
            if (p.message) loadingMessage = p.message;
            if (p.stage === "contests" && p.done) loading.update((l) => ({ ...l, contests: false }));
            if (p.stage === "cache" && p.done) loading.update((l) => ({ ...l, cache: false }));
        });

        // listen for queue updates + sync cached store
        const unlistenQueue = await listen<QueueUpdateEvent>("queue-update", (e) => {
            const p = e.payload;
            queue.set(p.queue);
            queueStats.set({ active: p.active_count, pending: p.pending_count, completed: p.completed_count });
            queuePaused.set(p.paused);

            // mark completed items in cache so they persist after queue clears
            const done = p.queue.filter((q) => q.status === "complete");
            if (done.length > 0) {
                cached.update((c) => {
                    const next = new Set(c);
                    for (const item of done) next.add(`${item.contest_id}_${item.file_type}`);
                    return next;
                });
            }
        });

        // load initial data
        try {
            const [contestResult, cachedResult, configResult, queueResult] = await Promise.all([
                commands.getContests(),
                commands.getCached(),
                commands.getConfig(),
                commands.getQueue(),
            ]);

            if (contestResult.status === "ok") contests.set(contestResult.data);
            if (cachedResult.status === "ok") cached.set(new Set(cachedResult.data));
            if (configResult.status === "ok") config.set(configResult.data);
            if (queueResult.status === "ok") queue.set(queueResult.data);
            loading.set({ contests: false, cache: false });
        } catch (e) {
            console.error("failed to load initial data:", e);
        }

        cleanups.push(unlistenProgress, unlistenQueue);
        ready = true;
    });
</script>

<svelte:head>
    <title>UIL-DL</title>
    <meta name="description" content="UIL Academics resource downloader" />
</svelte:head>

{#if !ready}
    <!-- loading screen -->
    <div class="h-screen flex items-center justify-center bg-surface-base">
        <div class="text-center space-y-4">
            <div class="w-12 h-12 mx-auto rounded-xl bg-surface-elevated border border-surface-border flex items-center justify-center">
                <svg class="w-6 h-6 text-vermillion-500 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
            </div>
            <p class="text-sm text-text-secondary animate-pulse">{loadingMessage}</p>
        </div>
    </div>
{:else if !isTauri}
    <!-- not-in-tauri message -->
    <div class="h-screen flex items-center justify-center bg-surface-base">
        <div class="text-center p-8 max-w-lg">
            <h1 class="text-2xl font-bold mb-4 text-text-primary">
                Desktop App Required
            </h1>
            <p class="text-text-secondary text-sm leading-relaxed">
                This application is intended to be used as a desktop app.
                If you're seeing this in a browser, please file a report at
                <code class="text-vermillion-400">github.com/acemavrick/uil-dl</code>.
            </p>
        </div>
    </div>
{:else}
    {@render children()}
{/if}
