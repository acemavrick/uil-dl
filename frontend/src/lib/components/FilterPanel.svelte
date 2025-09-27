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

<div class="p-4 bg-white shadow-md rounded-lg mb-4 w-full">
    <h2 class="text-lg font-semibold mb-2">Filters</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
            <label for="subject-filter" class="block text-sm font-medium text-gray-700">Subject</label>
            <MultiSelect options={$uniqueSubjects} selected={selectedSubjects} placeholder="Select subjects..." />
        </div>
        <div>
            <label for="level-filter" class="block text-sm font-medium text-gray-700">Level</label>
            <MultiSelect options={$uniqueLevels} selected={selectedLevels} placeholder="Select levels..." />
        </div>
        <div>
            <label for="year-filter" class="block text-sm font-medium text-gray-700">Year</label>
            <MultiSelect options={$uniqueYears} selected={selectedYears} placeholder="Select years..." />
        </div>
    </div>
</div>
