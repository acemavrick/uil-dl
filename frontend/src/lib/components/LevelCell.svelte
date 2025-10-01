<script lang="ts">
    let { level, gradient }: { level: string, gradient: boolean } = $props();
    const clevel = level.toLowerCase().trim();
</script>

<!-- Gradient
    #00615c
    #0d6d44
    #497417
    #867000
    #c85a06
    #ff1f57
 -->

<div class="py-0.5 font-bold">
    {#if gradient}
        {#if clevel === 'study packet'}
            <span class="text-[#00615c]">{level}</span>
        {:else if clevel === 'invitational a'}
            <span class="text-[#0d6d44]">{level}</span>
        {:else if clevel === 'invitational b'}
            <span class="text-[#497417]">{level}</span>
        {:else if clevel === 'district'}
            <span class="text-[#867000]">{level}</span>
        {:else if clevel === 'region'}
            <span class="text-[#c85a06]">{level}</span>
        {:else if clevel === 'state'}
            <span class="text-[#ff1f57]">{level}</span>
        {:else}
            <span>{level}</span>
        {/if}
    {:else}
        <span>{level}</span>
    {/if}
</div>