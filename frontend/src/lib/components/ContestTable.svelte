<script lang="ts">
    import { onMount } from "svelte";
    import { on } from "svelte/events";

    /**
      "id": 2,
      "subject": "Accounting",
      "level": "District",
      "year": 2019,
      "level_sort": 3,
      "pdf_link": "https://www.uiltexas.org/files/academics/Accounting_StudyPacket_D_19.pdf",
      "zip_link": null,
      "other_link": null
    */


    let contests: {id: number, subject: string, level: string, year: number, level_sort: number, pdf_link: string|null, zip_link: string|null, other_link: string|null}[] = [];

    function fetchContests() {
        fetch("/api/contests")
            .then(response => response.json())
            .then(data => {
                contests = data.contests;
                // sort by subject, then by year desc, then level_sort
                contests.sort((a, b) => {
                    if (a.subject < b.subject) return -1;
                    if (a.subject > b.subject) return 1;
                    if (a.year > b.year) return -1;
                    if (a.year < b.year) return 1;
                    if (a.level_sort < b.level_sort) return -1;
                    if (a.level_sort > b.level_sort) return 1;
                    return 0;
                });
            });
    }

    onMount(() => {
        fetchContests();
    });
</script>

<table class="min-w-full bg-white shadow-md rounded-lg overflow-scroll">
    <thead>
        <tr class="bg-gray-200">
            <th class="px-4 py-2 text-left">Subject</th>
            <th class="px-4 py-2 text-left">Level</th>
            <th class="px-4 py-2 text-left">Year</th>
            <th class="px-4 py-2 text-left">Links</th>
        </tr>
    </thead>
    <tbody>
        {#each contests as contest}
            <tr class="border-b hover:bg-gray-100">
                <td class="px-4 py-2">{contest.subject}</td>
                <td class="px-4 py-2">{contest.level}</td>
                <td class="px-4 py-2">{contest.year}</td>
                <td class="px-4 py-2 space-x-2">
                    {#if contest.pdf_link}
                        <a href={contest.pdf_link} target="_blank" class="text-blue-600 hover:underline">PDF</a>
                    {/if}
                    {#if contest.zip_link}
                        <a href={contest.zip_link} target="_blank" class="text-blue-600 hover:underline">ZIP</a>
                    {/if}
                    {#if contest.other_link}
                        <a href={contest.other_link} target="_blank" class="text-blue-600 hover:underline">Other</a>
                    {/if}
                </td>
            </tr>
        {/each}
    </tbody>
</table>