<script lang="ts">
    import { openUrl } from "$lib/tauri";
    import { commands } from "$lib/bindings";

    let {
        contestId,
        pdfLink,
        zipLink,
        otherLink,
    }: {
        contestId: number;
        pdfLink?: string;
        zipLink?: string;
        otherLink?: string;
    } = $props();

    async function addDownload(fileType: string) {
        await commands.addToQueue([{ contest_id: contestId, file_type: fileType }]);
    }
</script>

<div class="flex items-center gap-2">
    {#if pdfLink}
        <button
            onclick={() => addDownload("pdf")}
            class="px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
            title="Download PDF"
        >
            PDF
        </button>
    {/if}
    {#if zipLink}
        <button
            onclick={() => addDownload("zip")}
            class="px-2.5 py-1 rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 text-xs font-medium hover:bg-violet-200 dark:hover:bg-violet-900/50 transition-colors"
            title="Download ZIP"
        >
            ZIP
        </button>
    {/if}
    {#if otherLink}
        <button
            onclick={() => openUrl(otherLink)}
            class="px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs font-medium hover:bg-amber-200 dark:hover:bg-amber-900/50 transition-colors"
            title="Open in browser"
        >
            Other
        </button>
    {/if}
</div>
