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
    import SettingsModal from "$lib/components/SettingsModal.svelte";

    let showSettings = $state(false);
</script>

<!-- app shell: fixed viewport, no page scrolling -->
<div class="h-screen flex flex-col overflow-hidden bg-surface-base">
    <AppHeader onSettingsClick={() => (showSettings = !showSettings)} />

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

    <!-- table: fills remaining space, scrolls internally -->
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

    <ActionBar />
</div>

<SettingsModal open={showSettings} onClose={() => (showSettings = false)} />
