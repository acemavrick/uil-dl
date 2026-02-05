<script lang="ts">
    import "../app.css";
    import { onMount } from "svelte";
    import { contests, loading } from "$lib/stores/contests";
    import { cached } from "$lib/stores/cache";
    import { config } from "$lib/stores/config";
    import { queue, queueStats } from "$lib/stores/queue";
    import {
        getContests,
        getCached,
        getConfig,
        onLoadingProgress,
    } from "$lib/tauri";
    import { commands } from "$lib/bindings";
    import { listen } from "@tauri-apps/api/event";

    let ready = $state(false);
    let isTauri = $state(false);
    let loadingMessage = $state("Starting...");

    onMount(async () => {
        isTauri = "__TAURI_INTERNALS__" in window;

        if (!isTauri) {
            ready = true;
            return;
        }

        // disable browser context menu in tauri
        document.addEventListener("contextmenu", (e) => e.preventDefault());

        // listen for loading progress
        await onLoadingProgress((progress) => {
            if (progress.message) {
                loadingMessage = progress.message;
            }
            if (progress.stage === "contests" && progress.done) {
                loading.update((l) => ({ ...l, contests: false }));
            }
            if (progress.stage === "cache" && progress.done) {
                loading.update((l) => ({ ...l, cache: false }));
            }
        });

        // listen for queue updates
        await listen<{
            queue: any[];
            active_count: number;
            pending_count: number;
            completed_count: number;
        }>("queue-update", (event) => {
            queue.set(event.payload.queue);
            queueStats.set({
                active: event.payload.active_count,
                pending: event.payload.pending_count,
                completed: event.payload.completed_count,
            });
        });

        // load initial data once backend is ready
        try {
            const [contestData, cachedData, configData] = await Promise.all([
                getContests(),
                getCached(),
                getConfig(),
            ]);

            contests.set(contestData);
            cached.set(new Set(cachedData));
            config.set(configData);
            loading.set({ contests: false, cache: false });

            // load initial queue state
            const queueResult = await commands.getQueue();
            if (queueResult.status === "ok") {
                queue.set(queueResult.data);
            }
        } catch (e) {
            console.error("Failed to load initial data:", e);
        }

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
    <slot />
{/if}
