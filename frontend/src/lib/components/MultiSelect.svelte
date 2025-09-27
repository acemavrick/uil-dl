<script lang="ts">
    import { type Writable } from 'svelte/store';
    
    let { 
        options,
        selected,
        placeholder = 'Select...' 
    }: { 
        options: string[],
        selected: Writable<string[]>,
        placeholder?: string 
    } = $props();

    let isOpen = $state(false);

    function toggleOption(option: string) {
        const currentSelected = $selected;
        if (currentSelected.includes(option)) {
            $selected = currentSelected.filter(item => item !== option);
        } else {
            $selected = [...currentSelected, option];
        }
    }

    function clearAll() {
        $selected = [];
    }
</script>

<div class="relative mt-1">
    <button 
        type="button"
        class="w-full rounded border border-gray-300 px-2 py-1 text-sm text-left bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        onclick={() => isOpen = !isOpen}
    >
        {$selected.length ? `${$selected.length} selected` : placeholder}
        <span class="float-right">▼</span>
    </button>

    {#if isOpen}
        <div class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded shadow-lg max-h-60 overflow-auto">
            {#if $selected.length > 0}
                <button 
                    type="button"
                    class="w-full px-2 py-1 text-sm text-left hover:bg-gray-100 border-b"
                    onclick={clearAll}
                >
                    Clear selection
                </button>
            {/if}
            {#each options as option}
                <label class="flex items-center w-full px-2 py-1 hover:bg-gray-100 cursor-pointer">
                    <input 
                        type="checkbox" 
                        checked={$selected.includes(option)}
                        onchange={() => toggleOption(option)}
                        class="mr-2"
                    />
                    <span class="text-sm">{option}</span>
                </label>
            {/each}
        </div>
    {/if}
</div>
