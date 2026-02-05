<script lang="ts">
    import { selectionSummary, selectedItems, clearSelection } from "$lib/stores/selection";
    import { contests } from "$lib/stores/contests";
    import { commands } from "$lib/bindings";

    let isVisible = $derived($selectionSummary.total > 0);

    function downloadSelected() {
        const items: { contest_id: number; file_type: string }[] = [];
        for (const [contestId, types] of $selectedItems.entries()) {
            for (const fileType of types) {
                items.push({ contest_id: contestId, file_type: fileType });
            }
        }
        if (items.length > 0) {
            commands.addToQueue(items);
            clearSelection();
        }
    }

    // build a summary string like "3 selected (2 PDF, 1 ZIP)"
    let summaryText = $derived.by(() => {
        const { total, pdf, zip } = $selectionSummary;
        const parts: string[] = [];
        if (pdf > 0) parts.push(`${pdf} PDF`);
        if (zip > 0) parts.push(`${zip} ZIP`);
        return `${total} selected (${parts.join(", ")})`;
    });
</script>

{#if isVisible}
    <div class="flex-shrink-0 flex items-center justify-between px-5 py-2.5
        bg-surface-elevated border-t border-surface-border">
        <div class="flex items-center gap-3">
            <span class="text-sm text-text-primary">
                {summaryText}
            </span>
            <button
                onclick={clearSelection}
                class="text-xs text-text-secondary hover:text-text-primary transition-colors"
            >
                Clear
            </button>
        </div>

        <button
            onclick={downloadSelected}
            class="px-4 py-1.5 rounded-lg text-sm font-medium
                bg-vermillion-500 text-white hover:bg-vermillion-400
                transition-colors"
        >
            Download
        </button>
    </div>
{/if}
