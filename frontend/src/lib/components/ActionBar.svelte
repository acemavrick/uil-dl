<script lang="ts">
    import { selectionSummary, selectedItems, clearSelection } from "$lib/stores/selection";
    import { queue, queueStats } from "$lib/stores/queue";
    import { commands } from "$lib/bindings";

    let hasSelection = $derived($selectionSummary.total > 0);
    let hasQueue = $derived($queue.length > 0);
    let isVisible = $derived(hasSelection || hasQueue);

    // auto-clear completed items after a short delay
    let lastCompletedCount = $state(0);
    $effect(() => {
        const completed = $queueStats.completed;
        if (completed > lastCompletedCount && $queueStats.active === 0 && $queueStats.pending === 0) {
            // everything's done, auto-clear after 3s
            const timer = setTimeout(() => commands.clearCompleted(), 3000);
            return () => clearTimeout(timer);
        }
        lastCompletedCount = completed;
    });

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

    let summaryText = $derived.by(() => {
        const { total, pdf, zip } = $selectionSummary;
        const parts: string[] = [];
        if (pdf > 0) parts.push(`${pdf} PDF`);
        if (zip > 0) parts.push(`${zip} ZIP`);
        return `${total} selected (${parts.join(", ")})`;
    });

    // queue summary
    let queueText = $derived.by(() => {
        const { active, pending, completed } = $queueStats;
        const parts: string[] = [];
        if (active > 0) parts.push(`${active} downloading`);
        if (pending > 0) parts.push(`${pending} pending`);
        if (completed > 0) parts.push(`${completed} done`);
        return parts.join(", ");
    });

    // count failed items
    let failedItems = $derived($queue.filter(q => q.status === "failed"));

    function retryAllFailed() {
        const ids = failedItems.map(q => q.id);
        if (ids.length > 0) commands.retryFailed(ids);
    }

    function clearDone() {
        commands.clearCompleted();
    }
</script>

{#if isVisible}
    <div class="flex-shrink-0 flex items-center justify-between px-5 py-2.5
        bg-surface-elevated border-t border-surface-border gap-4">

        <!-- left: selection info -->
        <div class="flex items-center gap-3 min-w-0">
            {#if hasSelection}
                <span class="text-sm text-text-primary whitespace-nowrap">{summaryText}</span>
                <button
                    onclick={clearSelection}
                    class="text-xs text-text-secondary hover:text-text-primary transition-colors whitespace-nowrap"
                >
                    Clear
                </button>
            {/if}
        </div>

        <!-- center/right: queue info + actions -->
        <div class="flex items-center gap-3">
            {#if hasQueue}
                <!-- active download indicator -->
                {#if $queueStats.active > 0}
                    <span class="w-2 h-2 rounded-full bg-slate-blue-400 animate-pulse flex-shrink-0"></span>
                {/if}

                <span class="text-xs text-text-secondary whitespace-nowrap">{queueText}</span>

                {#if failedItems.length > 0}
                    <button
                        onclick={retryAllFailed}
                        class="text-xs text-vermillion-400 hover:text-vermillion-300 transition-colors whitespace-nowrap"
                    >
                        Retry {failedItems.length} failed
                    </button>
                {/if}

                {#if $queueStats.completed > 0}
                    <button
                        onclick={clearDone}
                        class="text-xs text-text-secondary hover:text-text-primary transition-colors whitespace-nowrap"
                    >
                        Clear done
                    </button>
                {/if}
            {/if}

            {#if hasSelection}
                <button
                    onclick={downloadSelected}
                    class="px-4 py-1.5 rounded-lg text-sm font-medium
                        bg-vermillion-500 text-white hover:bg-vermillion-400
                        transition-colors whitespace-nowrap"
                >
                    Download
                </button>
            {/if}
        </div>
    </div>
{/if}
