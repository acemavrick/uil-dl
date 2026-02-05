<script lang="ts">
    import type { Writable } from "svelte/store";

    interface Props {
        label: string;
        options: string[];
        selected: Writable<string[]>;
    }

    let { label, options, selected }: Props = $props();

    let open = $state(false);
    let search = $state("");
    let dropdownRef: HTMLDivElement | undefined = $state();

    let filteredOptions = $derived(
        search
            ? options.filter((o) => o.toLowerCase().includes(search.toLowerCase()))
            : options
    );

    let selectedCount = $derived($selected.length);

    function toggle(option: string) {
        selected.update((s) => {
            if (s.includes(option)) {
                return s.filter((v) => v !== option);
            }
            return [...s, option];
        });
    }

    function handleClickOutside(e: MouseEvent) {
        if (dropdownRef && !dropdownRef.contains(e.target as Node)) {
            open = false;
            search = "";
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Escape") {
            open = false;
            search = "";
        }
    }
</script>

<svelte:document onclick={handleClickOutside} onkeydown={handleKeydown} />

<div class="relative" bind:this={dropdownRef}>
    <button
        onclick={() => (open = !open)}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors
            {open
                ? 'bg-surface-hover text-text-primary'
                : 'bg-surface-elevated text-text-secondary hover:text-text-primary hover:bg-surface-hover'}
            border border-surface-border"
    >
        <span>{label}</span>
        {#if selectedCount > 0}
            <span class="ml-1 px-1.5 py-0.5 text-xs rounded-md bg-gold-500/20 text-gold-400 font-medium">
                {selectedCount}
            </span>
        {/if}
        <svg class="w-3.5 h-3.5 ml-0.5 transition-transform {open ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
    </button>

    {#if open}
        <div class="absolute top-full left-0 mt-1 w-56 bg-surface-elevated border border-surface-border rounded-lg shadow-xl z-50 overflow-hidden">
            <!-- search within dropdown -->
            <div class="p-2 border-b border-surface-border">
                <input
                    type="text"
                    placeholder="Search..."
                    bind:value={search}
                    class="w-full px-2.5 py-1.5 text-sm bg-surface-base border border-surface-border rounded-md
                        text-text-primary placeholder-text-secondary
                        focus:outline-none focus:border-slate-blue-500/50 focus:ring-1 focus:ring-slate-blue-500/25"
                />
            </div>

            <!-- options list -->
            <div class="max-h-48 overflow-y-auto p-1">
                {#each filteredOptions as option}
                    <button
                        onclick={() => toggle(option)}
                        class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-sm text-left
                            hover:bg-surface-hover transition-colors"
                    >
                        <!-- checkbox indicator -->
                        <div class="w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center transition-colors
                            {$selected.includes(option)
                                ? 'bg-gold-500 border-gold-500'
                                : 'border-surface-border'}"
                        >
                            {#if $selected.includes(option)}
                                <svg class="w-3 h-3 text-surface-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            {/if}
                        </div>
                        <span class="text-text-primary truncate">{option}</span>
                    </button>
                {/each}

                {#if filteredOptions.length === 0}
                    <p class="px-2.5 py-2 text-xs text-text-secondary">No matches</p>
                {/if}
            </div>
        </div>
    {/if}
</div>
