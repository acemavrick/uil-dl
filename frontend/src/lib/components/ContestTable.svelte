<script lang="ts">
    import { type Readable } from "svelte/store";
    import LinkCell from "$lib/components/LinkCell.svelte";
    import LevelCell from "$lib/components/LevelCell.svelte";

    type Contest = { id: number, subject: string, level: string, year: number, level_sort: number, pdf_link: string|null, zip_link: string|null, other_link: string|null };
    let { data, gradient_coloring }: { data: Readable<Contest[]>, gradient_coloring: boolean } = $props();
</script>

<div class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm overflow-hidden">
    <!-- count display -->
    <div class="flex items-center justify-end gap-3 p-3 sm:p-4 border-b border-stone-200 dark:border-stone-800">
        <div class="text-xs sm:text-sm text-stone-500 dark:text-stone-400 whitespace-nowrap">
            Showing <span class="font-medium text-stone-700 dark:text-stone-200">{$data.length}</span> contests
        </div>
    </div>
    <div class="overflow-x-auto">
        <table class="min-w-full">
            <thead>
                <tr class="bg-stone-100 dark:bg-stone-800/50 border-b border-stone-200 dark:border-stone-700">
                    <th class="px-3 sm:px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100">Subject</th>
                    <th class="px-3 sm:px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100">Level</th>
                    <th class="px-3 sm:px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100">Year</th>
                    <th class="px-3 sm:px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100">Links</th>
                </tr>
            </thead>
            <tbody>
                {#each $data as contest (contest.id)}
                    <tr class="border-b border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800/30 transition-colors">
                        <td class="px-3 sm:px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300">{contest.subject}</td>
                        <td class="px-3 sm:px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300">
                            <LevelCell level={contest.level} gradient={gradient_coloring} />
                        </td>
                        <td class="px-3 sm:px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300">{contest.year}</td>
                        <td class="px-3 sm:px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300">
                            <LinkCell pdf_link={contest.pdf_link} zip_link={contest.zip_link} other_link={contest.other_link} />
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
</div>
