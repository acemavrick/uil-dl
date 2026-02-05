<script lang="ts">
    interface Props {
        label: string;
        onRemove: () => void;
    }

    let { label, onRemove }: Props = $props();
</script>

<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium
    bg-gold-500/10 text-gold-400 border border-gold-500/20">
    <span>{label}</span>
    <button
        onclick={onRemove}
        class="hover:text-gold-300 transition-colors"
        title="Remove filter"
    >
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
    </button>
</span>
