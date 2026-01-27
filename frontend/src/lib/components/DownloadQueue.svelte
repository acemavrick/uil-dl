<script lang="ts">
    import { queue, queueStats } from "$lib/stores/queue";
    import { commands } from "$lib/bindings";

    let expanded = $state(true);

    function formatBytes(bytes: number): string {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i)) + " " + sizes[i];
    }

    function getStatusColor(status: string): string {
        switch (status) {
            case "pending":
                return "text-stone-500 dark:text-stone-400";
            case "downloading":
                return "text-blue-600 dark:text-blue-400";
            case "complete":
                return "text-emerald-600 dark:text-emerald-400";
            case "failed":
                return "text-red-600 dark:text-red-400";
            default:
                return "text-stone-500";
        }
    }

    async function removeItem(id: string) {
        await commands.removeFromQueue([id]);
    }

    async function retryItem(id: string) {
        await commands.retryFailed([id]);
    }

    async function clearCompleted() {
        await commands.clearCompleted();
    }
</script>

{#if $queue.length > 0}
    <div
        class="fixed bottom-4 right-4 w-96 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl shadow-lg overflow-hidden"
    >
        <!-- header -->
        <button
            onclick={() => (expanded = !expanded)}
            class="w-full px-4 py-3 flex items-center justify-between hover:bg-stone-50 dark:hover:bg-stone-800/50"
        >
            <div class="flex items-center gap-2">
                <svg
                    class="h-5 w-5 {expanded
                        ? 'rotate-180'
                        : ''} transition-transform"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                    />
                </svg>
                <span class="font-semibold">Downloads</span>
                <span
                    class="text-xs px-2 py-0.5 rounded-full bg-stone-100 dark:bg-stone-800"
                >
                    {$queue.length}
                </span>
            </div>
            <div class="flex items-center gap-2 text-xs text-stone-500">
                {#if $queueStats.active > 0}
                    <span class="flex items-center gap-1">
                        <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                        {$queueStats.active} active
                    </span>
                {/if}
                {#if $queueStats.pending > 0}
                    <span>{$queueStats.pending} pending</span>
                {/if}
            </div>
        </button>

        {#if expanded}
            <!-- queue items -->
            <div class="max-h-96 overflow-y-auto">
                {#each $queue as item (item.id)}
                    <div
                        class="px-4 py-3 border-t border-stone-200 dark:border-stone-800"
                    >
                        <div class="flex items-start justify-between gap-2 mb-2">
                            <div class="flex-1 min-w-0">
                                <div
                                    class="text-sm font-medium truncate text-stone-900 dark:text-stone-100"
                                >
                                    {item.file_type.toUpperCase()} #{item.contest_id}
                                </div>
                                <div
                                    class="text-xs {getStatusColor(
                                        item.status
                                    )} capitalize"
                                >
                                    {item.status}
                                    {#if item.retries > 0}
                                        (retry {item.retries}/4)
                                    {/if}
                                </div>
                            </div>
                            <div class="flex items-center gap-1">
                                {#if item.status === "failed"}
                                    <button
                                        onclick={() => retryItem(item.id)}
                                        class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-800"
                                        title="Retry"
                                    >
                                        <svg
                                            class="h-4 w-4"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                        >
                                            <path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                stroke-width="2"
                                                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                                            />
                                        </svg>
                                    </button>
                                {/if}
                                {#if item.status === "pending" || item.status === "failed"}
                                    <button
                                        onclick={() => removeItem(item.id)}
                                        class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-800"
                                        title="Remove"
                                    >
                                        <svg
                                            class="h-4 w-4"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                        >
                                            <path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                stroke-width="2"
                                                d="M6 18L18 6M6 6l12 12"
                                            />
                                        </svg>
                                    </button>
                                {/if}
                            </div>
                        </div>

                        <!-- progress bar for downloading -->
                        {#if item.status === "downloading" && item.progress}
                            <div class="space-y-1">
                                <div
                                    class="w-full bg-stone-200 dark:bg-stone-700 rounded-full h-1.5"
                                >
                                    <div
                                        class="bg-blue-600 h-1.5 rounded-full transition-all"
                                        style="width: {item.progress.total
                                            ? (item.progress.bytes /
                                                  item.progress.total) *
                                              100
                                            : 0}%"
                                    ></div>
                                </div>
                                <div
                                    class="text-xs text-stone-500 dark:text-stone-400"
                                >
                                    {formatBytes(item.progress.bytes)}
                                    {#if item.progress.total}
                                        / {formatBytes(item.progress.total)}
                                    {/if}
                                </div>
                            </div>
                        {/if}

                        <!-- error message -->
                        {#if item.status === "failed" && item.error}
                            <div
                                class="mt-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/10 px-2 py-1 rounded"
                            >
                                {item.error}
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>

            <!-- footer actions -->
            {#if $queueStats.completed > 0}
                <div
                    class="px-4 py-2 border-t border-stone-200 dark:border-stone-800 flex justify-end"
                >
                    <button
                        onclick={clearCompleted}
                        class="text-xs px-3 py-1 rounded bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 text-stone-700 dark:text-stone-300"
                    >
                        Clear completed ({$queueStats.completed})
                    </button>
                </div>
            {/if}
        {/if}
    </div>
{/if}
