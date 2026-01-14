<script lang="ts">
    // lightweight cell renderer for link trio
    let { pdf_link, zip_link, other_link }: { pdf_link: string | null, zip_link: string | null, other_link: string | null } = $props();
</script>

<div class="py-0.5 flex flex-wrap gap-2">
    {#if pdf_link}
        <a 
            href={pdf_link} 
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 text-xs font-medium transition-colors"
        >
            PDF
        </a>
    {/if}
    {#if zip_link}
        <a 
            href={zip_link} 
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/50 text-xs font-medium transition-colors"
        >
            ZIP
        </a>
    {/if}
    {#if other_link}
        <a 
            href={other_link} 
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-900/50 text-xs font-medium transition-colors"
        >
            Other
        </a>
    {/if}
    {#if !pdf_link && !zip_link && !other_link}
        <span class="text-stone-400 dark:text-stone-500 text-xs">No files</span>
    {/if}
</div>