<script lang="ts">
    import type { Readable } from "svelte/store";
    import type { Contest } from "$lib/tauri";
    import { selectedItems, toggleRow, selectAll, selectAllColumn } from "$lib/stores/selection";
    import FileCell from "./FileCell.svelte";
    import LevelCell from "./LevelCell.svelte";

    interface Props {
        data: Readable<Contest[]>;
    }

    let { data }: Props = $props();

    // sorting
    type SortKey = "subject" | "level" | "year";
    type SortDir = "asc" | "desc";
    let sortKey: SortKey = $state("year");
    let sortDir: SortDir = $state("desc");

    const levelOrder: Record<string, number> = {
        "Study Packet": 0,
        "Invitational A": 1,
        "Invitational B": 2,
        "District": 3,
        "Region": 4,
        "State": 5,
    };

    function toggleSort(key: SortKey) {
        if (sortKey === key) {
            sortDir = sortDir === "asc" ? "desc" : "asc";
        } else {
            sortKey = key;
            sortDir = key === "year" ? "desc" : "asc";
        }
    }

    let sortedData = $derived.by(() => {
        const items = [...$data];
        const dir = sortDir === "asc" ? 1 : -1;

        items.sort((a, b) => {
            if (sortKey === "subject") return dir * a.subject.localeCompare(b.subject);
            if (sortKey === "level") return dir * ((levelOrder[a.level] ?? 99) - (levelOrder[b.level] ?? 99));
            if (sortKey === "year") return dir * (a.year - b.year);
            return 0;
        });
        return items;
    });

    // master checkbox state
    let masterState = $derived.by(() => {
        const items = $data;
        if (items.length === 0) return "none" as const;
        const sel = $selectedItems;
        let allSelected = true;
        let someSelected = false;
        for (const c of items) {
            const types = sel.get(c.id);
            const hasPdf = c.pdf_link != null;
            const hasZip = c.zip_link != null;
            if (!hasPdf && !hasZip) continue;
            const pdfOk = !hasPdf || types?.has("pdf");
            const zipOk = !hasZip || types?.has("zip");
            if (pdfOk && zipOk) someSelected = true;
            else allSelected = false;
        }
        if (allSelected && someSelected) return "all" as const;
        if (someSelected) return "some" as const;
        return "none" as const;
    });

    // column checkbox states
    function columnState(fileType: string) {
        const items = $data.filter(c => fileType === "pdf" ? c.pdf_link : c.zip_link);
        if (items.length === 0) return "none" as const;
        const sel = $selectedItems;
        const selectedCount = items.filter(c => sel.get(c.id)?.has(fileType)).length;
        if (selectedCount === items.length) return "all" as const;
        if (selectedCount > 0) return "some" as const;
        return "none" as const;
    }

    let pdfColState = $derived(columnState("pdf"));
    let zipColState = $derived(columnState("zip"));

    // row checkbox state
    function rowState(contest: Contest) {
        const types = $selectedItems.get(contest.id);
        if (!types || types.size === 0) return "none" as const;
        const available: string[] = [];
        if (contest.pdf_link) available.push("pdf");
        if (contest.zip_link) available.push("zip");
        if (available.length === 0) return "none" as const;
        const allSelected = available.every(t => types.has(t));
        if (allSelected) return "all" as const;
        return "some" as const;
    }
</script>

{#if sortedData.length === 0}
    <div class="flex-1 flex items-center justify-center">
        <p class="text-sm text-text-secondary">No contests match your filters.</p>
    </div>
{:else}
    <table class="w-full text-sm">
        <thead class="sticky top-0 z-10 bg-surface-elevated border-b border-surface-border">
            <tr>
                <!-- master checkbox -->
                <th class="w-10 px-3 py-2.5 text-left">
                    <button
                        onclick={() => selectAll($data)}
                        class="w-4 h-4 rounded border flex items-center justify-center transition-colors
                            {masterState === 'all' ? 'bg-gold-500 border-gold-500' : masterState === 'some' ? 'bg-gold-500/50 border-gold-500' : 'border-surface-border hover:border-text-secondary'}"
                    >
                        {#if masterState === "all"}
                            <svg class="w-3 h-3 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                        {:else if masterState === "some"}
                            <svg class="w-3 h-3 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
                            </svg>
                        {/if}
                    </button>
                </th>

                <!-- sortable columns -->
                <th class="px-3 py-2.5 text-left">
                    <button onclick={() => toggleSort("subject")} class="flex items-center gap-1 text-text-secondary hover:text-text-primary transition-colors font-medium">
                        Subject
                        {#if sortKey === "subject"}
                            <span class="text-xs">{sortDir === "asc" ? "▲" : "▼"}</span>
                        {/if}
                    </button>
                </th>
                <th class="w-32 px-3 py-2.5 text-left">
                    <button onclick={() => toggleSort("level")} class="flex items-center gap-1 text-text-secondary hover:text-text-primary transition-colors font-medium">
                        Level
                        {#if sortKey === "level"}
                            <span class="text-xs">{sortDir === "asc" ? "▲" : "▼"}</span>
                        {/if}
                    </button>
                </th>
                <th class="w-20 px-3 py-2.5 text-left">
                    <button onclick={() => toggleSort("year")} class="flex items-center gap-1 text-text-secondary hover:text-text-primary transition-colors font-medium">
                        Year
                        {#if sortKey === "year"}
                            <span class="text-xs">{sortDir === "asc" ? "▲" : "▼"}</span>
                        {/if}
                    </button>
                </th>

                <!-- file column headers with select-all -->
                <th class="w-20 px-3 py-2.5 text-center">
                    <div class="flex flex-col items-center gap-1">
                        <span class="text-text-secondary font-medium text-xs">PDF</span>
                        <button
                            onclick={() => selectAllColumn("pdf", $data.filter(c => c.pdf_link).map(c => c.id))}
                            class="w-3.5 h-3.5 rounded border flex items-center justify-center transition-colors
                                {pdfColState === 'all' ? 'bg-gold-500 border-gold-500' : pdfColState === 'some' ? 'bg-gold-500/50 border-gold-500' : 'border-surface-border hover:border-text-secondary'}"
                        >
                            {#if pdfColState === "all"}
                                <svg class="w-2.5 h-2.5 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            {:else if pdfColState === "some"}
                                <svg class="w-2.5 h-2.5 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
                                </svg>
                            {/if}
                        </button>
                    </div>
                </th>
                <th class="w-20 px-3 py-2.5 text-center">
                    <div class="flex flex-col items-center gap-1">
                        <span class="text-text-secondary font-medium text-xs">ZIP</span>
                        <button
                            onclick={() => selectAllColumn("zip", $data.filter(c => c.zip_link).map(c => c.id))}
                            class="w-3.5 h-3.5 rounded border flex items-center justify-center transition-colors
                                {zipColState === 'all' ? 'bg-gold-500 border-gold-500' : zipColState === 'some' ? 'bg-gold-500/50 border-gold-500' : 'border-surface-border hover:border-text-secondary'}"
                        >
                            {#if zipColState === "all"}
                                <svg class="w-2.5 h-2.5 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            {:else if zipColState === "some"}
                                <svg class="w-2.5 h-2.5 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
                                </svg>
                            {/if}
                        </button>
                    </div>
                </th>
            </tr>
        </thead>

        <tbody>
            {#each sortedData as contest (contest.id)}
                {@const rState = rowState(contest)}
                {@const isSelected = rState !== "none"}
                <tr class="border-b border-surface-border/50 transition-colors
                    {isSelected ? 'bg-gold-500/[0.06]' : 'hover:bg-surface-elevated/60'}">
                    <!-- row checkbox -->
                    <td class="px-3 py-2">
                        <button
                            onclick={() => toggleRow(contest.id, [
                                ...(contest.pdf_link ? ["pdf"] : []),
                                ...(contest.zip_link ? ["zip"] : []),
                            ])}
                            class="w-4 h-4 rounded border flex items-center justify-center transition-colors
                                {rState === 'all' ? 'bg-gold-500 border-gold-500' : rState === 'some' ? 'bg-gold-500/50 border-gold-500' : 'border-surface-border hover:border-text-secondary'}"
                        >
                            {#if rState === "all"}
                                <svg class="w-3 h-3 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            {:else if rState === "some"}
                                <svg class="w-3 h-3 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
                                </svg>
                            {/if}
                        </button>
                    </td>

                    <td class="px-3 py-2 text-text-primary">{contest.subject}</td>
                    <td class="px-3 py-2">
                        <LevelCell level={contest.level} gradient={true} />
                    </td>
                    <td class="px-3 py-2 text-text-secondary tabular-nums">{contest.year}</td>
                    <td class="px-3 py-2 text-center">
                        <FileCell contestId={contest.id} fileType="pdf" link={contest.pdf_link} />
                    </td>
                    <td class="px-3 py-2 text-center">
                        <FileCell contestId={contest.id} fileType="zip" link={contest.zip_link} />
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>
{/if}
