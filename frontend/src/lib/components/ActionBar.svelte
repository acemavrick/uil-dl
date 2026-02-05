<script lang="ts">
    import { selectionSummary, selectedItems, clearSelection } from "$lib/stores/selection";
    import { queue, queueStats, queuePaused } from "$lib/stores/queue";
    import { contests } from "$lib/stores/contests";
    import { commands } from "$lib/bindings";

    let hasSelection = $derived($selectionSummary.total > 0);
    let hasQueue = $derived($queue.length > 0);
    let isVisible = $derived(hasSelection || hasQueue);
    let queueExpanded = $state(false);

    // contest name lookup
    let contestMap = $derived(new Map($contests.map(c => [c.id, c])));

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

    // queue summary for the collapsed bar
    let queueText = $derived.by(() => {
        const { active, pending, completed } = $queueStats;
        const parts: string[] = [];
        if (active > 0) parts.push(`${active} downloading`);
        if (pending > 0) parts.push(`${pending} pending`);
        if (completed > 0) parts.push(`${completed} done`);
        return parts.join(", ");
    });

    let failedItems = $derived($queue.filter(q => q.status === "failed"));

    function retryAllFailed() {
        const ids = failedItems.map(q => q.id);
        if (ids.length > 0) commands.retryFailed(ids);
    }

    function togglePause() {
        commands.setQueuePaused(!$queuePaused);
    }

    function removeItem(id: string) {
        commands.removeFromQueue([id]);
    }

    function retryItem(id: string) {
        commands.retryFailed([id]);
    }

    // format item label from contest data
    function itemLabel(contestId: number, fileType: string): string {
        const c = contestMap.get(contestId);
        if (!c) return `#${contestId} ${fileType.toUpperCase()}`;
        return `${c.subject} ${c.year} ${c.level} — ${fileType.toUpperCase()}`;
    }

    // progress percentage for an item
    function itemProgress(item: { progress: { bytes: number; total: number | null } | null }): number | null {
        if (!item.progress) return null;
        const { bytes, total } = item.progress;
        if (total && total > 0) return Math.round((bytes / total) * 100);
        return null;
    }
</script>

{#if isVisible}
    <div class="flex-shrink-0 bg-surface-elevated border-t border-surface-border">
        <!-- expanded queue panel -->
        {#if queueExpanded && hasQueue}
            <div class="max-h-48 overflow-y-auto border-b border-surface-border">
                <!-- queue header inside panel -->
                <div class="flex items-center justify-between px-4 py-2 sticky top-0 bg-surface-elevated/95 backdrop-blur-sm border-b border-surface-border/50">
                    <span class="text-xs font-medium text-text-secondary">Queue</span>
                    <div class="flex items-center gap-2">
                        {#if failedItems.length > 0}
                            <button
                                onclick={retryAllFailed}
                                class="text-[10px] text-vermillion-400 hover:text-vermillion-300 transition-colors"
                            >
                                Retry failed
                            </button>
                        {/if}
                        <button
                            onclick={() => commands.clearCompleted()}
                            class="text-[10px] text-text-secondary hover:text-text-primary transition-colors"
                        >
                            Clear done
                        </button>
                    </div>
                </div>

                <!-- queue items -->
                {#each $queue as item (item.id)}
                    {@const pct = itemProgress(item)}
                    <div class="flex items-center gap-2 px-4 py-1.5 text-xs hover:bg-surface-hover/50 group">
                        <!-- status indicator -->
                        <span class="w-1.5 h-1.5 rounded-full flex-shrink-0 {
                            item.status === 'downloading' ? 'bg-slate-blue-400 animate-pulse' :
                            item.status === 'pending' ? 'bg-text-secondary/40' :
                            item.status === 'complete' ? 'bg-green-500' :
                            item.status === 'failed' ? 'bg-vermillion-400' :
                            'bg-text-secondary/20'
                        }"></span>

                        <!-- name -->
                        <span class="flex-1 min-w-0 truncate {
                            item.status === 'complete' ? 'text-text-secondary/60' :
                            item.status === 'failed' ? 'text-vermillion-400' :
                            'text-text-primary'
                        }">
                            {itemLabel(item.contest_id, item.file_type)}
                        </span>

                        <!-- progress or status -->
                        <span class="text-[10px] tabular-nums text-text-secondary flex-shrink-0 w-14 text-right">
                            {#if item.status === "downloading"}
                                {pct != null ? `${pct}%` : "..."}
                            {:else if item.status === "failed"}
                                failed
                            {:else if item.status === "complete"}
                                done
                            {:else if item.status === "pending"}
                                {$queuePaused ? "paused" : "waiting"}
                            {/if}
                        </span>

                        <!-- per-item actions (visible on hover) -->
                        <div class="flex-shrink-0 w-5 opacity-0 group-hover:opacity-100 transition-opacity">
                            {#if item.status === "pending" || item.status === "failed"}
                                {#if item.status === "failed"}
                                    <button
                                        onclick={() => retryItem(item.id)}
                                        class="text-text-secondary hover:text-slate-blue-400 transition-colors"
                                        title="Retry"
                                    >
                                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                    </button>
                                {:else}
                                    <button
                                        onclick={() => removeItem(item.id)}
                                        class="text-text-secondary hover:text-vermillion-400 transition-colors"
                                        title="Remove"
                                    >
                                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                {/if}
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        {/if}

        <!-- bottom bar (always visible when isVisible) -->
        <div class="flex items-center justify-between px-5 py-2.5 gap-4">
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

            <!-- right: queue summary + actions -->
            <div class="flex items-center gap-3">
                {#if hasQueue}
                    <!-- clickable queue summary to expand/collapse -->
                    <button
                        onclick={() => queueExpanded = !queueExpanded}
                        class="flex items-center gap-2 text-xs text-text-secondary hover:text-text-primary transition-colors"
                    >
                        {#if $queueStats.active > 0}
                            <span class="w-2 h-2 rounded-full bg-slate-blue-400 animate-pulse flex-shrink-0"></span>
                        {:else if $queuePaused}
                            <span class="w-2 h-2 rounded-full bg-gold-500 flex-shrink-0"></span>
                        {/if}
                        <span class="whitespace-nowrap">{queueText}</span>
                        <svg class="w-3 h-3 transition-transform {queueExpanded ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                        </svg>
                    </button>

                    <!-- pause/resume -->
                    {#if $queueStats.active > 0 || $queueStats.pending > 0}
                        <button
                            onclick={togglePause}
                            class="text-xs transition-colors whitespace-nowrap {$queuePaused ? 'text-gold-400 hover:text-gold-300' : 'text-text-secondary hover:text-text-primary'}"
                            title={$queuePaused ? "Resume queue" : "Pause queue"}
                        >
                            {$queuePaused ? "Resume" : "Pause"}
                        </button>
                    {/if}

                    {#if failedItems.length > 0}
                        <button
                            onclick={retryAllFailed}
                            class="text-xs text-vermillion-400 hover:text-vermillion-300 transition-colors whitespace-nowrap"
                        >
                            Retry {failedItems.length} failed
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
    </div>
{/if}
