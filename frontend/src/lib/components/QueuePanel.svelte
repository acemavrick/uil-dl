<script lang="ts">
    import { queue, queueStats } from "$lib/stores/queue";
    import { commands } from "$lib/bindings";

    let expanded = $state(false);

    let totalItems = $derived($queue.length);
    let activeCount = $derived($queueStats.active + $queueStats.pending);

    function formatBytes(bytes: number): string {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i)) + " " + sizes[i];
    }

    function statusIcon(status: string): string {
        switch (status) {
            case "pending": return "⏳";
            case "downloading": return "↓";
            case "complete": return "✓";
            case "failed": return "✕";
            default: return "·";
        }
    }

    async function clearCompleted() {
        await commands.clearCompleted();
    }

    async function retryItem(id: string) {
        await commands.retryFailed([id]);
    }

    async function removeItem(id: string) {
        await commands.removeFromQueue([id]);
    }
</script>

{#if totalItems > 0}
    <!-- pill trigger -->
    <div class="fixed bottom-4 right-4 z-40">
        {#if !expanded}
            <button
                onclick={() => (expanded = true)}
                class="flex items-center gap-2 px-3 py-1.5 rounded-full
                    bg-surface-elevated border border-surface-border
                    shadow-lg hover:bg-surface-hover transition-colors"
            >
                {#if activeCount > 0}
                    <span class="w-2 h-2 rounded-full bg-slate-blue-400 animate-pulse"></span>
                {/if}
                <span class="text-xs text-text-primary font-medium">
                    {activeCount > 0 ? `${activeCount} downloading` : `${totalItems} in queue`}
                </span>
            </button>
        {:else}
            <!-- expanded panel -->
            <div class="w-80 bg-surface-elevated border border-surface-border rounded-xl shadow-2xl overflow-hidden">
                <!-- header -->
                <div class="flex items-center justify-between px-4 py-2.5 border-b border-surface-border">
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-medium text-text-primary">Queue</span>
                        <span class="text-xs text-text-secondary">{totalItems}</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                        {#if $queueStats.completed > 0}
                            <button
                                onclick={clearCompleted}
                                class="text-xs text-text-secondary hover:text-text-primary transition-colors"
                            >
                                Clear done
                            </button>
                        {/if}
                        <button
                            onclick={() => (expanded = false)}
                            class="p-1 text-text-secondary hover:text-text-primary transition-colors"
                            title="Collapse"
                        >
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- items -->
                <div class="max-h-72 overflow-y-auto">
                    {#each $queue as item (item.id)}
                        <div class="flex items-center gap-3 px-4 py-2 border-b border-surface-border/50
                            {item.status === 'failed' ? 'bg-vermillion-500/[0.05]' : ''}">
                            <!-- status indicator -->
                            <span class="text-xs w-4 text-center flex-shrink-0
                                {item.status === 'downloading' ? 'text-slate-blue-400' :
                                 item.status === 'complete' ? 'text-text-secondary/50' :
                                 item.status === 'failed' ? 'text-vermillion-400' :
                                 'text-text-secondary'}">
                                {statusIcon(item.status)}
                            </span>

                            <!-- item info -->
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-1.5">
                                    <span class="text-xs font-medium text-text-primary truncate">
                                        {item.file_type.toUpperCase()} #{item.contest_id}
                                    </span>
                                    {#if item.retries > 0}
                                        <span class="text-[10px] text-text-secondary">×{item.retries}</span>
                                    {/if}
                                </div>

                                <!-- progress bar -->
                                {#if item.status === "downloading" && item.progress}
                                    <div class="mt-1 flex items-center gap-2">
                                        <div class="flex-1 h-1 bg-surface-border rounded-full overflow-hidden">
                                            <div
                                                class="h-full bg-slate-blue-400 rounded-full transition-all"
                                                style="width: {item.progress.total ? (item.progress.bytes / item.progress.total) * 100 : 0}%"
                                            ></div>
                                        </div>
                                        <span class="text-[10px] text-text-secondary tabular-nums">
                                            {item.progress.total ? formatBytes(item.progress.bytes) : "..."}
                                        </span>
                                    </div>
                                {/if}

                                <!-- error message -->
                                {#if item.status === "failed" && item.error}
                                    <p class="text-[10px] text-vermillion-400 mt-0.5 truncate">{item.error}</p>
                                {/if}
                            </div>

                            <!-- actions -->
                            <div class="flex items-center gap-0.5 flex-shrink-0">
                                {#if item.status === "failed"}
                                    <button onclick={() => retryItem(item.id)} class="p-1 text-text-secondary hover:text-text-primary rounded transition-colors" title="Retry">
                                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                    </button>
                                {/if}
                                {#if item.status === "pending" || item.status === "failed"}
                                    <button onclick={() => removeItem(item.id)} class="p-1 text-text-secondary hover:text-vermillion-400 rounded transition-colors" title="Remove">
                                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
    </div>
{/if}
