<script lang="ts">
    let { level, gradient }: { level: string, gradient: boolean } = $props();
    const clevel = level.toLowerCase().trim();
</script>

<div class="py-0.5">
    {#if gradient}
        {#if clevel === 'study packet'}
            <span class="text-teal-200 dark:text-teal-900">{level}</span>
        {:else if clevel === 'invitational a'}
            <span class="text-teal-400 dark:text-teal-600">{level}</span>
        {:else if clevel === 'invitational b'}
            <span class="text-teal-500">{level}</span>
        {:else if clevel === 'district'}
            <span class="text-teal-600 dark:text-teal-400">{level}</span>
        {:else if clevel === 'region'}
            <span class="text-teal-700 dark:text-teal-300">{level}</span>
        {:else if clevel === 'state'}
            <span class="text-teal-900 dark:text-teal-200">{level}</span>
        {:else}
            <span>{level}</span>
        {/if}
    {:else}
        <span>{level}</span>
    {/if}
</div>