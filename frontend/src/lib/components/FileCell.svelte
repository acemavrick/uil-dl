<script lang="ts">
    import { selectedItems, toggleFile } from "$lib/stores/selection";
    import { queue } from "$lib/stores/queue";
    import { commands } from "$lib/bindings";

    interface Props {
        contestId: number;
        fileType: string;
        link: string | null;
    }

    let { contestId, fileType, link }: Props = $props();

    // find this item in the queue (if any)
    let queueItem = $derived(
        $queue.find(q => q.contest_id === contestId && q.file_type === fileType)
    );

    let isSelected = $derived($selectedItems.get(contestId)?.has(fileType) ?? false);

    // queue-based status
    let status = $derived.by(() => {
        if (!link) return "unavailable" as const;
        if (!queueItem) return isSelected ? "selected" as const : "available" as const;
        return queueItem.status as "pending" | "downloading" | "complete" | "failed";
    });

    let progress = $derived.by(() => {
        if (queueItem?.status === "downloading" && queueItem.progress) {
            const { bytes, total } = queueItem.progress;
            if (total && total > 0) return Math.round((bytes / total) * 100);
        }
        return null;
    });

    function instantDownload() {
        commands.addToQueue([{ contest_id: contestId, file_type: fileType }]);
    }
</script>

{#if status === "unavailable"}
    <span class="text-text-secondary/40">—</span>
{:else if status === "downloading"}
    <span class="text-xs text-slate-blue-400 tabular-nums font-medium">
        {progress != null ? `${progress}%` : "..."}
    </span>
{:else if status === "pending"}
    <span class="text-xs text-text-secondary">pending</span>
{:else if status === "complete"}
    <span class="text-xs text-text-secondary/60">
        <svg class="w-3.5 h-3.5 inline text-text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
    </span>
{:else if status === "failed"}
    <span class="text-xs text-vermillion-400 font-medium">failed</span>
{:else}
    <!-- available or selected: show checkbox + instant download -->
    <div class="flex items-center justify-center gap-1.5">
        <button
            onclick={() => toggleFile(contestId, fileType)}
            class="w-4 h-4 rounded border flex items-center justify-center transition-colors
                {isSelected ? 'bg-gold-500 border-gold-500' : 'border-surface-border hover:border-text-secondary'}"
        >
            {#if isSelected}
                <svg class="w-3 h-3 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            {/if}
        </button>

        <!-- instant download -->
        <button
            onclick={instantDownload}
            class="p-0.5 rounded text-text-secondary hover:text-vermillion-400 transition-colors"
            title="Download {fileType.toUpperCase()}"
        >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
        </button>
    </div>
{/if}
