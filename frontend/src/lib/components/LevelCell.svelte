<script lang="ts">
    let { level, gradient }: { level: string, gradient: boolean } = $props();
    const clevel = level.toLowerCase().trim();
</script>

<div class="px-4 py-2 space-x-2">
    <!-- link-style coloring for level -->
    <!-- because this is a scale, we can just pick a color and then go up the scale -->
    <!-- for light mode, we go darker in tailwind colors -->
    <!-- for dark mode, we go the other way -->
    {#if gradient}
        {#if clevel === 'study packet'}
            <span class="text-teal-900">Study Packet</span>
        {:else if clevel === 'invitational a'}
            <span class="text-teal-400">Invitational A</span>
        {:else if clevel === 'invitational b'}
            <span class="text-teal-500">Invitational B</span>
        {:else if clevel === 'district'}
            <span class="text-teal-600">District</span>
        {:else if clevel === 'region'}
            <span class="text-teal-700">Region</span>
        {:else if clevel === 'state'}
            <span class="text-teal-950">State</span>
        {:else}
            <span>{level}</span>
        {/if}
    {:else}
        <span>{level}</span>
    {/if}
</div>