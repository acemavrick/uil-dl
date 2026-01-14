<script lang="ts">
    import { type Writable, type Readable } from 'svelte/store';
    import { derived } from 'svelte/store';
    import MultiSelect from './MultiSelect.svelte';

    type Contest = { id: number, subject: string, level: string, year: number, level_sort: number, pdf_link: string|null, zip_link: string|null, other_link: string|null };

    let {
        allContests,
        selectedSubjects,
        selectedLevels,
        selectedYears,
    }: {
        allContests: Readable<Contest[]>,
        selectedSubjects: Writable<string[]>,
        selectedLevels: Writable<string[]>,
        selectedYears: Writable<string[]>,
    } = $props();

    const uniqueSubjects = derived(allContests, ($contests) => [...new Set($contests.map(c => c.subject))].sort());
    const uniqueLevels = derived(allContests, ($contests) => [...new Set($contests.map(c => c.level))].sort());
    const uniqueYears = derived(allContests, ($contests) => [...new Set($contests.map(c => String(c.year)))].sort((a,b) => Number(b) - Number(a)));

</script>

<div class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 p-4 sm:p-6 shadow-sm">
    <h2 class="text-base font-semibold text-stone-900 dark:text-stone-100 mb-4">Filter Contests</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
            <label for="subject-filter" class="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5">Subject</label>
            <MultiSelect options={$uniqueSubjects} selected={selectedSubjects} placeholder="All subjects..." />
        </div>
        <div>
            <label for="level-filter" class="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5">Level</label>
            <MultiSelect options={$uniqueLevels} selected={selectedLevels} placeholder="All levels..." />
        </div>
        <div>
            <label for="year-filter" class="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5">Year</label>
            <MultiSelect options={$uniqueYears} selected={selectedYears} placeholder="All years..." />
        </div>
    </div>
</div>