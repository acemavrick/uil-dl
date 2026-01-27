<script lang="ts">
    import { type Readable } from "svelte/store";
    import { type Contest, openUrl } from "$lib/tauri";
    import LinkCell from "./LinkCell.svelte";
    import LevelCell from "./LevelCell.svelte";
    import { Menu, MenuItem, PredefinedMenuItem } from "@tauri-apps/api/menu";

    let {
        data,
        gradientColoring,
    }: { data: Readable<Contest[]>; gradientColoring: boolean } = $props();

    async function showContextMenu(e: MouseEvent, contest: Contest) {
        e.preventDefault();

        const items = [];

        if (contest.pdf_link) {
            const pdfLink = contest.pdf_link;
            items.push(
                await MenuItem.new({
                    id: "open-pdf",
                    text: "Open PDF",
                    action: () => openUrl(pdfLink),
                })
            );
        }

        if (contest.zip_link) {
            const zipLink = contest.zip_link;
            items.push(
                await MenuItem.new({
                    id: "open-zip",
                    text: "Open ZIP",
                    action: () => openUrl(zipLink),
                })
            );
        }

        // only show "Open All" if multiple links exist
        if (contest.pdf_link && contest.zip_link) {
            const pdfLink = contest.pdf_link;
            const zipLink = contest.zip_link;
            items.push(await PredefinedMenuItem.new({ item: "Separator" }));
            items.push(
                await MenuItem.new({
                    id: "open-all",
                    text: "Open All",
                    action: () => {
                        openUrl(pdfLink);
                        openUrl(zipLink);
                    },
                })
            );
        }

        // don't show menu if no links
        if (items.length === 0) return;

        const menu = await Menu.new({ items });
        await menu.popup();
    }
</script>

<div
    class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 overflow-hidden"
>
    <div
        class="flex items-center justify-end p-3 border-b border-stone-200 dark:border-stone-800"
    >
        <span class="text-sm text-stone-500 dark:text-stone-400">
            <span class="font-medium text-stone-700 dark:text-stone-200"
                >{$data.length}</span
            > contests
        </span>
    </div>
    <div class="overflow-x-auto">
        <table class="min-w-full">
            <thead>
                <tr
                    class="bg-stone-100 dark:bg-stone-800/50 border-b border-stone-200 dark:border-stone-700"
                >
                    <th
                        class="px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100"
                        >Subject</th
                    >
                    <th
                        class="px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100"
                        >Level</th
                    >
                    <th
                        class="px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100"
                        >Year</th
                    >
                    <th
                        class="px-4 py-2.5 text-left text-sm font-semibold text-stone-900 dark:text-stone-100"
                        >Links</th
                    >
                </tr>
            </thead>
            <tbody>
                {#each $data as contest (contest.id)}
                    <tr
                        class="border-b border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800/30 cursor-default"
                        oncontextmenu={(e) => showContextMenu(e, contest)}
                    >
                        <td
                            class="px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300"
                            >{contest.subject}</td
                        >
                        <td class="px-4 py-2.5 text-sm">
                            <LevelCell
                                level={contest.level}
                                gradient={gradientColoring}
                            />
                        </td>
                        <td
                            class="px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300"
                            >{contest.year}</td
                        >
                        <td class="px-4 py-2.5">
                            <LinkCell
                                contestId={contest.id}
                                pdfLink={contest.pdf_link}
                                zipLink={contest.zip_link}
                                otherLink={contest.other_link}
                            />
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
</div>
