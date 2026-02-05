<script lang="ts">
    import type { Readable, Writable } from "svelte/store";
    import FilterDropdown from "./FilterDropdown.svelte";
    import FilterChip from "./FilterChip.svelte";
    import { downloadFilter, type DownloadFilter } from "$lib/stores/contests";

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

    const dlFilterOptions: { value: DownloadFilter; label: string }[] = [
        { value: "any", label: "Any status" },
        { value: "all", label: "Fully downloaded" },
        { value: "some", label: "Any downloaded" },
        { value: "pdf", label: "PDF downloaded" },
        { value: "zip", label: "ZIP downloaded" },
        { value: "none", label: "Not downloaded" },
    ];

    // collect all active chips for display
    let hasFilters = $derived(
        $selectedSubjects.length > 0 ||
        $selectedLevels.length > 0 ||
        $selectedYears.length > 0 ||
        $downloadFilter !== "any"
    );

    function clearAll() {
        selectedSubjects.set([]);
        selectedLevels.set([]);
        selectedYears.set([]);
        downloadFilter.set("any");
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

        <!-- download status: simple select, not multi-select -->
        <select
            bind:value={$downloadFilter}
            class="text-xs px-2.5 py-1.5 rounded-lg bg-surface-elevated border border-surface-border
                text-text-secondary hover:text-text-primary transition-colors cursor-pointer
                focus:outline-none focus:border-slate-blue-500/50"
        >
            {#each dlFilterOptions as opt}
                <option value={opt.value}>{opt.label}</option>
            {/each}
        </select>
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
            {#if $downloadFilter !== "any"}
                <FilterChip
                    label={dlFilterOptions.find(o => o.value === $downloadFilter)?.label ?? ""}
                    onRemove={() => downloadFilter.set("any")}
                />
            {/if}

            <button
                onclick={clearAll}
                class="text-xs text-text-secondary hover:text-vermillion-400 transition-colors ml-1"
            >
                Clear all
            </button>
        </div>
    {/if}
</div>
