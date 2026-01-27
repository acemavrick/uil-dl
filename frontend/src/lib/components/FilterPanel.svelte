<script lang="ts">
    import { type Writable, type Readable } from "svelte/store";
    import MultiSelect from "./MultiSelect.svelte";

    let {
        subjects,
        levels,
        years,
        selectedSubjects,
        selectedLevels,
        selectedYears,
    }: {
        subjects: Readable<string[]>;
        levels: Readable<string[]>;
        years: Readable<string[]>;
        selectedSubjects: Writable<string[]>;
        selectedLevels: Writable<string[]>;
        selectedYears: Writable<string[]>;
    } = $props();
</script>

<div
    class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 p-4 sm:p-6"
>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
            <label
                class="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5"
                >Subject</label
            >
            <MultiSelect
                options={$subjects}
                selected={selectedSubjects}
                placeholder="All subjects..."
            />
        </div>
        <div>
            <label
                class="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5"
                >Level</label
            >
            <MultiSelect
                options={$levels}
                selected={selectedLevels}
                placeholder="All levels..."
            />
        </div>
        <div>
            <label
                class="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5"
                >Year</label
            >
            <MultiSelect
                options={$years}
                selected={selectedYears}
                placeholder="All years..."
            />
        </div>
    </div>
</div>
