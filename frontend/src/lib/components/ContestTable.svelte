<script lang="ts">
    import { type Readable } from "svelte/store";
    import { createTable, Render, Subscribe, createRender } from "svelte-headless-table";
    import { addSortBy } from "svelte-headless-table/plugins";
    import LinkCell from "$lib/components/LinkCell.svelte";
    import LevelCell from "$lib/components/LevelCell.svelte";

    type Contest = { id: number, subject: string, level: string, year: number, level_sort: number, pdf_link: string|null, zip_link: string|null, other_link: string|null };
    let { data, gradient_coloring }: { data: Readable<Contest[]>, gradient_coloring: boolean } = $props();

    // table
    const table = createTable(data, {
        addSortBy: addSortBy({ initialSortKeys: [{ id: 'subject', order: 'asc' }] }),
    });

    const columns = table.createColumns([
        table.column({
            header: "Subject",
            accessor: "subject",
            cell: (cell) => cell.value as unknown as string,
            plugins: {
                addSortBy: {},
            },
        }),
        table.column({
            header: "Level",
            accessor: "level",
            cell: (cell) => createRender(
                LevelCell as unknown as new (...args: any[]) => import('svelte').SvelteComponent,
                {
                    level: cell.value as unknown as string,
                    gradient: gradient_coloring
                }
            ),
            plugins: {
                addSortBy: {},
            },
        }),
        table.column({
            header: "Year",
            accessor: "year",
            cell: (cell) => String(cell.value as unknown as number),
            plugins: {
                addSortBy: {},
            },
        }),
        table.display({
            id: "links",
            header: "Links",
            cell: (cell) => createRender(
                LinkCell as unknown as new (...args: any[]) => import('svelte').SvelteComponent,
                {
                    pdf_link: cell.row.isData() ? (cell.row.original as Contest).pdf_link : null,
                    zip_link: cell.row.isData() ? (cell.row.original as Contest).zip_link : null,
                    other_link: cell.row.isData() ? (cell.row.original as Contest).other_link : null,
                }
            ),
        }),
    ]);

    const { headerRows, rows, tableAttrs, tableBodyAttrs, tableHeadAttrs } = table.createViewModel(columns);
</script>

<div class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
        <table class="min-w-full" {...$tableAttrs}>
            <thead {...$tableHeadAttrs}>
                {#each $headerRows as headerRow (headerRow.id)}
                    <Subscribe rowAttrs={headerRow.attrs()} let:rowAttrs>
                        <tr class="bg-stone-100 dark:bg-stone-800/50 border-b border-stone-200 dark:border-stone-700" {...rowAttrs}>
                            {#each headerRow.cells as cell (cell.id)}
                                <Subscribe attrs={cell.attrs()} props={cell.props()} let:attrs let:props>
                                    <th class="px-3 sm:px-4 py-2.5 text-left align-top whitespace-nowrap" {...attrs}>
                                        <button
                                            type="button"
                                            class="flex items-center gap-2 w-full text-left text-sm font-semibold text-stone-900 dark:text-stone-100 {props.addSortBy ? 'cursor-pointer hover:text-emerald-600 dark:hover:text-emerald-400' : 'cursor-default'} transition-colors"
                                            onclick={props.addSortBy?.toggle}
                                            disabled={!props.addSortBy}
                                        >
                                            <Render of={cell.render()} />
                                            {#if props.addSortBy?.order === 'asc'}
                                                <span class="text-emerald-600 dark:text-emerald-400 text-xs">▲</span>
                                            {:else if props.addSortBy?.order === 'desc'}
                                                <span class="text-emerald-600 dark:text-emerald-400 text-xs">▼</span>
                                            {/if}
                                        </button>
                                    </th>
                                </Subscribe>
                            {/each}
                        </tr>
                    </Subscribe>
                {/each}
            </thead>
            <tbody {...$tableBodyAttrs}>
                {#each $rows as row (row.id)}
                    <Subscribe rowAttrs={row.attrs()} let:rowAttrs>
                        <tr class="border-b border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800/30 transition-colors" {...rowAttrs}>
                            {#each row.cells as cell (cell.id)}
                                <Subscribe attrs={cell.attrs()} let:attrs>
                                    <td class="px-3 sm:px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300" {...attrs}>
                                        <Render of={cell.render()} />
                                    </td>
                                </Subscribe>
                            {/each}
                        </tr>
                    </Subscribe>
                {/each}
            </tbody>
        </table>
    </div>
</div>