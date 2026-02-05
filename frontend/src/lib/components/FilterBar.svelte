<script lang="ts">
    import type { Readable, Writable } from "svelte/store";
    import FilterDropdown from "./FilterDropdown.svelte";
    import FilterChip from "./FilterChip.svelte";

    interface Props {
        subjects: Readable<string[]>;
        levels: Readable<string[]>;
        years: Readable<string[]>;
        selectedSubjects: Writable<string[]>;
        selectedLevels: Writable<string[]>;
        selectedYears: Writable<string[]>;
    }

    let {
        subjects,
        levels,
        years,
        selectedSubjects,
        selectedLevels,
        selectedYears,
    }: Props = $props();

    // collect all active chips for display
    let hasFilters = $derived(
        $selectedSubjects.length > 0 ||
        $selectedLevels.length > 0 ||
        $selectedYears.length > 0
    );

    function clearAll() {
        selectedSubjects.set([]);
        selectedLevels.set([]);
        selectedYears.set([]);
    }

    function removeSubject(s: string) {
        selectedSubjects.update((v) => v.filter((x) => x !== s));
    }

    function removeLevel(l: string) {
        selectedLevels.update((v) => v.filter((x) => x !== l));
    }

    function removeYear(y: string) {
        selectedYears.update((v) => v.filter((x) => x !== y));
    }
</script>

<div class="flex-shrink-0 px-5 py-3 space-y-2.5 border-b border-surface-border">
    <!-- dropdown row -->
    <div class="flex items-center gap-2.5">
        <FilterDropdown label="Subject" options={$subjects} selected={selectedSubjects} />
        <FilterDropdown label="Level" options={$levels} selected={selectedLevels} />
        <FilterDropdown label="Year" options={$years} selected={selectedYears} />
    </div>

    <!-- active filter chips -->
    {#if hasFilters}
        <div class="flex items-center gap-1.5 flex-wrap">
            {#each $selectedSubjects as s}
                <FilterChip label={s} onRemove={() => removeSubject(s)} />
            {/each}
            {#each $selectedLevels as l}
                <FilterChip label={l} onRemove={() => removeLevel(l)} />
            {/each}
            {#each $selectedYears as y}
                <FilterChip label={y} onRemove={() => removeYear(y)} />
            {/each}

            <button
                onclick={clearAll}
                class="text-xs text-text-secondary hover:text-vermillion-400 transition-colors ml-1"
            >
                Clear all
            </button>
        </div>
    {/if}
</div>
