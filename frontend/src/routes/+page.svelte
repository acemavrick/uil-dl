<script lang="ts">
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
    import AppHeader from "$lib/components/AppHeader.svelte";
    import FilterBar from "$lib/components/FilterBar.svelte";
    import SearchBar from "$lib/components/SearchBar.svelte";
    import ContestTable from "$lib/components/ContestTable.svelte";
    import ActionBar from "$lib/components/ActionBar.svelte";

    let showSettings = $state(false);
</script>

<!-- app shell: fixed viewport, no page scrolling -->
<div class="h-screen flex flex-col overflow-hidden bg-surface-base">
    <AppHeader onSettingsClick={() => (showSettings = !showSettings)} />

    <!-- filter bar + search -->
    {#if !$loading.contests}
        <FilterBar
            {subjects}
            {levels}
            {years}
            {selectedSubjects}
            {selectedLevels}
            {selectedYears}
        />
        <SearchBar />
    {/if}

    <!-- table area: fills remaining space, scrolls internally -->
    <div class="flex-1 min-h-0 overflow-y-auto">
        {#if $loading.contests}
            <div class="p-8">
                <div class="animate-pulse space-y-3">
                    {#each Array(8) as _}
                        <div class="h-8 bg-surface-elevated rounded"></div>
                    {/each}
                </div>
            </div>
        {:else}
            <ContestTable data={filteredContests} />
        {/if}
    </div>

    <!-- action bar: visible when items are selected -->
    <ActionBar />
</div>

<!-- queue panel placeholder (task 9) -->

<!-- settings modal placeholder (task 10) -->
{#if showSettings}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={() => (showSettings = false)}></div>
        <div class="relative bg-surface-elevated border border-surface-border rounded-xl p-6 w-96 shadow-2xl">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-text-primary">Settings</h2>
                <button onclick={() => (showSettings = false)} class="text-text-secondary hover:text-text-primary" title="Close">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            <p class="text-sm text-text-secondary">Settings modal coming soon.</p>
        </div>
    </div>
{/if}
