<script lang="ts">
    let { level, gradient = true }: { level: string; gradient?: boolean } = $props();

    // warm-tinted colors that read well on dark surfaces
    const levelColors: Record<string, string> = {
        'study packet': 'text-[#4fd1c5]',
        'invitational a': 'text-[#68d391]',
        'invitational b': 'text-[#a3d977]',
        'district': 'text-[#d4a04a]',
        'region': 'text-[#e8816d]',
        'state': 'text-[#f687b3]',
    };

    let colorClass = $derived(
        gradient ? (levelColors[level.toLowerCase().trim()] ?? 'text-text-primary') : 'text-text-primary'
    );
</script>

<span class="text-sm font-medium {colorClass}">{level}</span>
