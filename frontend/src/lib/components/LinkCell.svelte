<script lang="ts">
    // lightweight cell renderer for link trio
    let { pdf_link, zip_link, other_link }: { pdf_link: string | null, zip_link: string | null, other_link: string | null } = $props();
</script>

<div class="px-4 py-2 space-x-2">
    {#if pdf_link}
        <a href={pdf_link} target="_blank" class="text-blue-600 hover:underline">PDF</a>
    {/if}
    {#if zip_link}
        <a href={zip_link} target="_blank" class="text-blue-600 hover:underline">ZIP</a>
    {/if}
    {#if other_link}
        <a href={other_link} target="_blank" class="text-blue-600 hover:underline">Other</a>
    {/if}
    {#if !pdf_link && !zip_link && !other_link}
        <span class="text-gray-400">—</span>
    {/if}
</div>

