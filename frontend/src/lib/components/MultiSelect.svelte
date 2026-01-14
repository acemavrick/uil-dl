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

<div class="relative">
    <button 
        type="button"
        class="w-full rounded-lg border border-stone-300 dark:border-stone-700 px-3 py-2 text-sm text-left bg-white dark:bg-stone-900 text-stone-900 dark:text-stone-100 hover:border-emerald-500 dark:hover:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400 focus:border-transparent transition-colors"
        onclick={() => isOpen = !isOpen}
    >
        <span class="block truncate">
            {$selected.length ? `${$selected.length} selected` : placeholder}
        </span>
        <span class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-stone-400 dark:text-stone-500">
            {isOpen ? '▲' : '▼'}
        </span>
    </button>

    {#if isOpen}
        <div class="absolute z-20 w-full mt-1 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-700 rounded-lg shadow-lg max-h-60 overflow-auto">
            {#if $selected.length > 0}
                <button 
                    type="button"
                    class="w-full px-3 py-2 text-sm text-left text-emerald-600 dark:text-emerald-400 hover:bg-stone-50 dark:hover:bg-stone-800 border-b border-stone-200 dark:border-stone-700 font-medium transition-colors"
                    onclick={clearAll}
                >
                    Clear selection
                </button>
            {/if}
            {#each options as option}
                <label class="flex items-center w-full px-3 py-2 hover:bg-stone-50 dark:hover:bg-stone-800 cursor-pointer transition-colors">
                    <input 
                        type="checkbox" 
                        checked={$selected.includes(option)}
                        onchange={() => toggleOption(option)}
                        class="mr-2 rounded border-stone-300 dark:border-stone-600 text-emerald-600 dark:text-emerald-500 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                    />
                    <span class="text-sm text-stone-700 dark:text-stone-300">{option}</span>
                </label>
            {/each}
        </div>
    {/if}
</div>