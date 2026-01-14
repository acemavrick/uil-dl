<script lang="ts">
    import { writable, derived, type Writable, type Readable } from "svelte/store";
    import ContestTable from "$lib/components/ContestTable.svelte";
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import icon from "$lib/assets/icon.svg";
    import { APP_VERSION } from "$lib/version";

    type Contest = { id: number, subject: string, level: string, year: number, level_sort: number, pdf_link: string|null, zip_link: string|null, other_link: string|null };

    let { data }: { data: any } = $props();
    
    let gradient_coloring = $state(true);
    let showHelp = $state(true);
    
    const allContests: Writable<Contest[]> = writable([]);
    const selectedSubjects: Writable<string[]> = writable([]);
    const selectedLevels: Writable<string[]> = writable([]);
    const selectedYears: Writable<string[]> = writable([]);

    const filteredContests = derived(
        [allContests, selectedSubjects, selectedLevels, selectedYears],
        ([$allContests, $selectedSubjects, $selectedLevels, $selectedYears]) => {
            if ($selectedSubjects.length === 0 && $selectedLevels.length === 0 && $selectedYears.length === 0) {
                return $allContests;
            }
            return $allContests.filter(c => {
                const subjectMatch = $selectedSubjects.length === 0 || $selectedSubjects.includes(c.subject);
                const levelMatch = $selectedLevels.length === 0 || $selectedLevels.includes(c.level);
                const yearMatch = $selectedYears.length === 0 || $selectedYears.includes(String(c.year));
                return subjectMatch && levelMatch && yearMatch;
            });
        }
    );

    function sortAndSet(items: Contest[]) {
        items.sort((a, b) => {
            if (a.subject < b.subject) return -1;
            if (a.subject > b.subject) return 1;
            if (a.year > b.year) return -1;
            if (a.year < b.year) return 1;
            if (a.level_sort < b.level_sort) return -1;
            if (a.level_sort > b.level_sort) return 1;
            return 0;
        });
        allContests.set(items);
    }

    // seed store from prerendered data
    const info = data?.info ?? { contests: [] };
    sortAndSet(info.contests ?? []);
</script>

<div class="min-h-screen bg-stone-50 dark:bg-stone-950 text-stone-900 dark:text-stone-100 transition-colors duration-200">
    <!-- header -->
    <header class="sticky top-0 z-50 bg-white/80 dark:bg-stone-900/80 backdrop-blur border-b border-stone-200 dark:border-stone-800">
        <nav class="mx-auto max-w-7xl px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
            <!-- logo -->
            <div class="flex items-center gap-3">
                <img src={icon} alt="UIL-DL" class="h-8 w-8 rounded-lg" />
                <div class="flex items-baseline gap-2">
                    <h1 class="text-xl font-bold text-stone-900 dark:text-stone-100">UIL-DL</h1>
                </div>
            </div>

            <!-- actions -->
            <div class="flex items-center gap-2 sm:gap-3">
                <!-- help toggle -->
                <button
                    onclick={() => showHelp = !showHelp}
                    title="Toggle help and legend"
                    class="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
                >
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span class="hidden sm:inline">Help</span>
                </button>

                <!-- github -->
                <a
                    href="https://github.com/acemavrick/uil-dl"
                    title="View source on GitHub"
                    class="inline-flex items-center gap-1.5 rounded-lg bg-stone-100 dark:bg-stone-800 px-3 py-1.5 text-sm font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-200 dark:hover:bg-stone-700 transition-colors"
                >
                    <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                    <span class="hidden sm:inline">GitHub</span>
                </a>
            </div>
        </nav>
    </header>

    <!-- main content -->
    <main class="mx-auto max-w-7xl px-4 sm:px-6 py-6 space-y-6">
        <!-- help panel (collapsible) -->
        {#if showHelp}
            <div class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 p-6 shadow-sm">
                <div class="flex items-start justify-between mb-4">
                    <h2 class="text-lg font-semibold text-stone-900 dark:text-stone-100">About & Guide</h2>
                    <button
                        onclick={() => showHelp = false}
                        aria-label="Close help panel"
                        class="text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 transition-colors"
                    >
                        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div class="grid gap-6 md:grid-cols-2">
                    <!-- about -->
                    <div class="space-y-3">
                        <h3 class="text-sm font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">About</h3>
                        <p class="text-sm text-stone-600 dark:text-stone-400 leading-relaxed">
                            UIL-DL v{APP_VERSION} lets you browse and filter the complete UIL Academics catalog. Click any link to open resources directly.
                        </p>
                        <div class="flex flex-wrap gap-2 text-xs">
                            <a href="https://github.com/acemavrick/uil-dl" class="text-emerald-600 dark:text-emerald-400 hover:underline">View source →</a>
                            <a href="https://github.com/acemavrick/uil-dl/blob/standalone/README.md" class="text-emerald-600 dark:text-emerald-400 hover:underline">Documentation →</a>
                        </div>
                    </div>

                    <!-- level legend -->
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <h3 class="text-sm font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">Level Colors</h3>
                            <button
                                onclick={() => gradient_coloring = !gradient_coloring}
                                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 dark:bg-emerald-500 text-white hover:bg-emerald-500 dark:hover:bg-emerald-400 transition-colors"
                            >
                                {gradient_coloring ? '✓ Enabled' : 'Disabled'}
                            </button>
                        </div>
                        {#if gradient_coloring}
                            <div class="grid grid-cols-2 gap-2 text-sm">
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-[#00d692] dark:bg-[#00615c]"></span>
                                    <span class="text-stone-600 dark:text-stone-400">Study Packet</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-[#76c859] dark:bg-[#0d6d44]"></span>
                                    <span class="text-stone-600 dark:text-stone-400">Invitational A</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-[#adb431] dark:bg-[#497417]"></span>
                                    <span class="text-stone-600 dark:text-stone-400">Invitational B</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-[#d89a2f] dark:bg-[#867000]"></span>
                                    <span class="text-stone-600 dark:text-stone-400">District</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-[#f57c4f] dark:bg-[#c85a06]"></span>
                                    <span class="text-stone-600 dark:text-stone-400">Region</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-[#ff61AC] dark:bg-[#ff1f57]"></span>
                                    <span class="text-stone-600 dark:text-stone-400">State</span>
                                </div>
                            </div>
                        {:else}
                            <p class="text-xs text-stone-500 dark:text-stone-400">Color coding disabled. All levels display in default text.</p>
                        {/if}
                    </div>

                    <!-- link legend -->
                    <div class="space-y-3">
                        <h3 class="text-sm font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">Link Types</h3>
                        <div class="flex flex-wrap gap-2">
                            <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium">
                                PDF
                            </span>
                            <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 text-xs font-medium">
                                ZIP
                            </span>
                            <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs font-medium">
                                Other
                            </span>
                        </div>
                        <p class="text-xs text-stone-500 dark:text-stone-400">Click any link to open the resource in a new tab.</p>
                    </div>
                </div>
            </div>
        {/if}

        <!-- filters -->
        <div class="space-y-4">
            <FilterPanel 
                allContests={allContests}
                selectedSubjects={selectedSubjects}
                selectedLevels={selectedLevels}
                selectedYears={selectedYears}
            />
            
            <!-- filter explanation -->
            <div class="rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 px-4 py-3">
                <p class="text-sm text-emerald-800 dark:text-emerald-200/90">
                    <strong class="font-semibold">Tip:</strong> Select multiple options in each filter to narrow results. Filters combine to show only contests matching all selected criteria.
                </p>
            </div>
        </div>

        <!-- table -->
        <ContestTable data={filteredContests} gradient_coloring={gradient_coloring} />
    </main>

    <!-- footer -->
    <footer class="border-t border-stone-200 dark:border-stone-800 mt-12">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 py-6">
            <div class="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-stone-500 dark:text-stone-400">
                <div class="flex items-center gap-2">
                    <span>UIL-DL v{APP_VERSION}</span>
                    <span>•</span>
                    <a href="https://github.com/acemavrick/uil-dl" class="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Open Source</a>
                </div>
                <div class="flex flex-wrap items-center justify-center gap-4">
                    <a href="https://github.com/acemavrick/uil-dl/releases" class="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Releases</a>
                    <a href="https://discord.gg/a6DdBaebPk" class="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Discord</a>
                </div>
            </div>
        </div>
    </footer>
</div>
