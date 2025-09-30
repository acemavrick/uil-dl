<script lang="ts">
    import { writable, derived, type Writable, type Readable } from "svelte/store";
    import ContestTable from "$lib/components/ContestTable.svelte";
    import FilterPanel from "$lib/components/FilterPanel.svelte";
    import icon from "$lib/assets/icon.svg";

    type Contest = { id: number, subject: string, level: string, year: number, level_sort: number, pdf_link: string|null, zip_link: string|null, other_link: string|null };

    let { data }: { data: any } = $props();
    let gradient_coloring = $state(true);
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

<div class="flex flex-col items-center min-w-full bg-stone-100 text-gray-800 pt-10 px-4 bg-fixed">
    <h1 class="text-4xl font-semibold mb-4 text-gray-900">
        <a href="/" target="_blank" title="Go to homepage">
            <img src={icon} alt="UIL-DL Online Logo" class="inline w-15 h-15 mb-2 mr-2" />
        </a>
        UIL-DL <span class="text-emerald-600 font-normal">Online</span>
    </h1>

    <FilterPanel 
        allContests={allContests}
        selectedSubjects={selectedSubjects}
        selectedLevels={selectedLevels}
        selectedYears={selectedYears}
    />

    <ContestTable data={filteredContests} gradient_coloring={gradient_coloring} />
</div>
