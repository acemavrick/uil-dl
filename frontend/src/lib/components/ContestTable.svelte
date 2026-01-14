<script lang="ts">
    import { type Readable, type Writable, writable, derived } from "svelte/store";
    import { createTable, Render, Subscribe, createRender } from "svelte-headless-table";
    import { addSortBy, addTableFilter, addHiddenColumns } from "svelte-headless-table/plugins";
    import LinkCell from "$lib/components/LinkCell.svelte";
    import LevelCell from "$lib/components/LevelCell.svelte";

    type Contest = { id: number, subject: string, level: string, year: number, level_sort: number, pdf_link: string|null, zip_link: string|null, other_link: string|null };
    let { data, gradient_coloring }: { data: Readable<Contest[]>, gradient_coloring: boolean } = $props();

    // table with global filter
    // fuzzy match: all tokens must be subsequences of the candidate string
    function isSubsequence(token: string, target: string) {
        // simple, fast fuzzy: chars of token appear in order in target
        let i = 0;
        for (let j = 0; j < target.length && i < token.length; j++) {
            if (target.charCodeAt(j) === token.charCodeAt(i)) i++;
        }
        return i === token.length;
    }

    const fuzzyContains = ({ value, filterValue }: { value: string, filterValue: string }) => {
        const q = (filterValue ?? '').trim().toLowerCase();
        if (q === '') return true;
        const tokens = q.split(/\s+/g);
        const target = (value ?? '').toLowerCase();
        return tokens.every((t) => isSubsequence(t, target));
    };

    const table = createTable(data, {
        addSortBy: addSortBy({ initialSortKeys: [{ id: 'subject', order: 'asc' }] }),
        addTableFilter: addTableFilter({ fn: fuzzyContains, includeHiddenColumns: true }),
        addHiddenColumns: addHiddenColumns({ initialHiddenColumnIds: ['searchIndex'] }),
    });

    const columns = table.createColumns([
        // hidden composite index for cross-column fuzzy search
        table.column<string, string>({
            id: 'searchIndex',
            header: 'Search',
            accessor: (row) => `${(row as Contest).subject} ${(row as Contest).level} ${(row as Contest).year}`,
            cell: (cell) => cell.value as unknown as string,
            plugins: {
                addTableFilter: {},
            },
        }),
        table.column({
            header: "Subject",
            accessor: "subject",
            cell: (cell) => cell.value as unknown as string,
            plugins: {
                addSortBy: {},
                addTableFilter: {},
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
                addTableFilter: {},
            },
        }),
        table.column({
            header: "Year",
            accessor: "year",
            cell: (cell) => String(cell.value as unknown as number),
            plugins: {
                addSortBy: {},
                addTableFilter: {
                    getFilterValue: (v: number) => String(v),
                },
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
            plugins: {
                addTableFilter: { exclude: true },
            },
        }),
    ]);

    const { headerRows, rows, tableAttrs, tableBodyAttrs, tableHeadAttrs, pluginStates } = table.createViewModel(columns);

    // expose plugin state for UI
    const filterValue = pluginStates.addTableFilter.filterValue as Writable<string>;
    const filteredCount = derived(rows, ($rows) => $rows.filter((r) => r.isData()).length);
    const totalCount = derived(data, ($data) => $data.length);
</script>

<div class="rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm overflow-hidden">
    <!-- search toolbar -->
    <div class="flex items-center justify-between gap-3 p-3 sm:p-4 border-b border-stone-200 dark:border-stone-800">
        <div class="relative flex-1 max-w-lg">
            <svg class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 104.5 4.5a7.5 7.5 0 0012.15 12.15z" />
            </svg>
            <input
                aria-label="Search contests"
                placeholder="Search by subject, level, or year"
                class="w-full rounded-lg border border-stone-300 dark:border-stone-700 bg-white dark:bg-stone-800 pl-9 pr-9 py-2 text-sm text-stone-800 dark:text-stone-100 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                value={$filterValue}
                oninput={(e) => filterValue.set((e.target as HTMLInputElement).value)}
            />
            {#if $filterValue}
                <button
                    type="button"
                    title="Clear search"
                    aria-label="Clear search"
                    class="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300"
                    onclick={() => filterValue.set("")}
                >
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            {/if}
        </div>
        <div class="text-xs sm:text-sm text-stone-500 dark:text-stone-400 whitespace-nowrap">
            Showing <span class="font-medium text-stone-700 dark:text-stone-200">{$filteredCount}</span> of {$totalCount}
        </div>
    </div>
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
                                <Subscribe attrs={cell.attrs()} props={cell.props()} let:attrs let:props>
                                    <td class="px-3 sm:px-4 py-2.5 text-sm text-stone-700 dark:text-stone-300 {props.addTableFilter?.matches ? 'bg-emerald-50/50 dark:bg-emerald-900/20' : ''}" {...attrs}>
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