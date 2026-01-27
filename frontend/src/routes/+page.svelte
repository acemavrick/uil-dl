<script lang="ts">
    import { onMount } from "svelte";
    import {
        filteredContests,
        selectedSubjects,
        selectedLevels,
        selectedYears,
        subjects,
        levels,
        years,
        loading,
    } from "$lib/stores/contests";
    import ContestTable from "$lib/components/ContestTable.svelte";
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import icon from "$lib/icons/icon.png";
    import { APP_VERSION } from "$lib/version";
    import { startDragging, getPlatform } from "$lib/tauri";

    let gradientColoring = $state(true);
    let showHelp = $state(false);
    let isMacOS = $state(false);

    onMount(async () => {
        const platform = await getPlatform();
        isMacOS = platform === "macos";
    });

    function handleHeaderMouseDown(e: MouseEvent) {
        // only start drag on left click and not on interactive elements
        const target = e.target as HTMLElement;
        const isInteractive = target.closest("button, a, input, select");
        if (e.buttons === 1 && !isInteractive) {
            startDragging();
        }
    }
</script>

<div
    class="min-h-screen bg-stone-50 dark:bg-stone-950 text-stone-900 dark:text-stone-100"
>
    <!-- header (draggable titlebar region) -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <header
        onmousedown={handleHeaderMouseDown}
        class="sticky top-0 z-50 bg-white/80 dark:bg-stone-900/80 backdrop-blur border-b border-stone-200 dark:border-stone-800 cursor-default"
    >
        <nav
            class="mx-auto max-w-7xl py-3 flex items-center justify-between gap-4"
            style:padding-left={isMacOS ? "80px" : "16px"}
            style:padding-right={isMacOS ? "16px" : "16px"}
        >
            <div class="flex items-center gap-3">
                <img src={icon} alt="UIL-DL" class="h-8 w-8 rounded-lg" />
                <h1 class="text-xl font-bold">UIL-DL</h1>
                <span class="text-xs text-stone-500 dark:text-stone-400"
                    >v{APP_VERSION}</span
                >
            </div>

            <div class="flex items-center gap-2">
                <button
                    onclick={() => (showHelp = !showHelp)}
                    class="p-2 rounded-lg text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800"
                    title="Help"
                >
                    <svg
                        class="h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                </button>
                <a
                    href="https://github.com/acemavrick/uil-dl"
                    target="_blank"
                    rel="noopener"
                    class="p-2 rounded-lg text-stone-600 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800"
                    title="GitHub"
                >
                    <svg
                        class="h-5 w-5"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
                        />
                    </svg>
                </a>
            </div>
        </nav>
    </header>

    <main class="mx-auto max-w-7xl px-4 py-6 space-y-6">
        <!-- help panel -->
        {#if showHelp}
            <div
                class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 p-6"
            >
                <div class="flex items-start justify-between mb-4">
                    <h2 class="text-lg font-semibold">Guide</h2>
                    <button
                        onclick={() => (showHelp = false)}
                        class="text-stone-400 hover:text-stone-600 dark:hover:text-stone-300"
                    >
                        <svg
                            class="h-5 w-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </button>
                </div>

                <div class="grid gap-6 md:grid-cols-2">
                    <div class="space-y-3">
                        <h3
                            class="text-sm font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide"
                        >
                            Level Colors
                        </h3>
                        <div class="flex items-center gap-2 mb-2">
                            <button
                                onclick={() =>
                                    (gradientColoring = !gradientColoring)}
                                class="text-xs px-2 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-500"
                            >
                                {gradientColoring ? "Enabled" : "Disabled"}
                            </button>
                        </div>
                        {#if gradientColoring}
                            <div class="grid grid-cols-2 gap-2 text-sm">
                                <div class="flex items-center gap-2">
                                    <span
                                        class="w-3 h-3 rounded-full bg-[#00d692] dark:bg-[#00615c]"
                                    ></span> Study Packet
                                </div>
                                <div class="flex items-center gap-2">
                                    <span
                                        class="w-3 h-3 rounded-full bg-[#76c859] dark:bg-[#0d6d44]"
                                    ></span> Invitational A
                                </div>
                                <div class="flex items-center gap-2">
                                    <span
                                        class="w-3 h-3 rounded-full bg-[#adb431] dark:bg-[#497417]"
                                    ></span> Invitational B
                                </div>
                                <div class="flex items-center gap-2">
                                    <span
                                        class="w-3 h-3 rounded-full bg-[#d89a2f] dark:bg-[#867000]"
                                    ></span> District
                                </div>
                                <div class="flex items-center gap-2">
                                    <span
                                        class="w-3 h-3 rounded-full bg-[#f57c4f] dark:bg-[#c85a06]"
                                    ></span> Region
                                </div>
                                <div class="flex items-center gap-2">
                                    <span
                                        class="w-3 h-3 rounded-full bg-[#ff61AC] dark:bg-[#ff1f57]"
                                    ></span> State
                                </div>
                            </div>
                        {/if}
                    </div>

                    <div class="space-y-3">
                        <h3
                            class="text-sm font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide"
                        >
                            Link Types
                        </h3>
                        <div class="flex flex-wrap gap-2">
                            <span
                                class="px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium"
                                >PDF</span
                            >
                            <span
                                class="px-2.5 py-1 rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 text-xs font-medium"
                                >ZIP</span
                            >
                            <span
                                class="px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs font-medium"
                                >Other</span
                            >
                        </div>
                        <p class="text-xs text-stone-500">
                            Click to open in your default app or browser.
                        </p>
                    </div>
                </div>
            </div>
        {/if}

        <!-- filters -->
        {#if !$loading.contests}
            <FilterPanel
                {subjects}
                {levels}
                {years}
                {selectedSubjects}
                {selectedLevels}
                {selectedYears}
            />
        {/if}

        <!-- table -->
        {#if $loading.contests}
            <div
                class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 p-8"
            >
                <div class="animate-pulse space-y-4">
                    <div
                        class="h-4 bg-stone-200 dark:bg-stone-700 rounded w-1/4"
                    ></div>
                    <div
                        class="h-4 bg-stone-200 dark:bg-stone-700 rounded w-1/2"
                    ></div>
                    <div
                        class="h-4 bg-stone-200 dark:bg-stone-700 rounded w-1/3"
                    ></div>
                </div>
            </div>
        {:else}
            <ContestTable data={filteredContests} {gradientColoring} />
        {/if}
    </main>

    <footer class="border-t border-stone-200 dark:border-stone-800 mt-12">
        <div
            class="mx-auto max-w-7xl px-4 py-6 text-sm text-stone-500 dark:text-stone-400 text-center"
        >
            UIL-DL v{APP_VERSION} ·
            <a
                href="https://github.com/acemavrick/uil-dl"
                class="hover:text-emerald-600">Open Source</a
            >
        </div>
    </footer>
</div>
