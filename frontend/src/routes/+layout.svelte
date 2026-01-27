<script lang="ts">
    import "../app.css";
    import { onMount, onDestroy } from "svelte";
    import { contests, loading } from "$lib/stores/contests";
    import { cached } from "$lib/stores/cache";
    import { config } from "$lib/stores/config";
    import {
        getContests,
        getCached,
        getConfig,
        onLoadingProgress,
    } from "$lib/tauri";

    let ready = $state(false);
    let isTauri = $state(false);
    let loadingMessage = $state("Starting...");
    let unlistenFn: (() => void) | null = null;

    onMount(async () => {
        isTauri = "__TAURI_INTERNALS__" in window;

        if (!isTauri) {
            ready = true;
            return;
        }

        // disable browser context menu in tauri
        document.addEventListener("contextmenu", (e) => e.preventDefault());

        // listen for loading progress
        unlistenFn = await onLoadingProgress((progress) => {
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
        } catch (e) {
            console.error("Failed to load initial data:", e);
        }

        ready = true;
    });

    onDestroy(() => {
        if (unlistenFn) unlistenFn();
    });
</script>

<svelte:head>
    <title>UIL-DL</title>
    <meta name="description" content="UIL Academics resource downloader" />
</svelte:head>

{#if !ready}
    <div
        class="min-h-screen flex items-center justify-center bg-stone-50 dark:bg-stone-950"
    >
        <div class="text-center">
            <div
                class="animate-pulse text-lg text-stone-600 dark:text-stone-400"
            >
                {loadingMessage}
            </div>
        </div>
    </div>
{:else if !isTauri}
    <div
        class="min-h-screen flex items-center justify-center bg-stone-50 dark:bg-stone-950"
    >
        <div class="text-center p-8">
            <img 
                src="/src/lib/icons/icon.png" 
                alt="UIL-DL Icon" 
                class="w-24 h-24 mx-auto mb-6"
            />
            <h1
                class="text-3xl font-bold mb-4 text-stone-900 dark:text-stone-100"
            >
                Desktop App Required
            </h1>
            <p class="text-stone-600 dark:text-stone-400 mb-6 leading-relaxed
            text-left max-w-2xl mt-6
            ">

            It seems that you are trying to access this application through
            your own browser. If so, congratulations on finding this bug! 
            Please file a report on the repository to help me fix this 
            issue. After that, please refrain from attempting to use the 
            application this way, as it is intended to be used solely 
            as a desktop app.

            <span class="block mt-6 mb-4">
            If this message is shown to you in the official desktop app,
            please also file a report as this indicates a critical issue
            with the app.
            </span>
            
            <span class="block mt-6 mb-4">
            Reports can be filed at 
            <code class="text-emerald-600">https://github.com/acemavrick/uil-dl</code>.
            </span>

            <span class="block mt-6">
                Thanks,<br />
                <span class="italic">Shubh (acemavrick)</span>
            </span>
        </p>
    </div>
    </div>
{:else}
    <slot />
{/if}
