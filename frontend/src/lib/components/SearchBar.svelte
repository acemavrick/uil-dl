<script lang="ts">
    import { searchQuery } from "$lib/stores/search";

    let localQuery = $state("");
    let debounceTimer: ReturnType<typeof setTimeout>;

    function handleInput() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchQuery.set(localQuery);
        }, 200);
    }

    function clear() {
        localQuery = "";
        searchQuery.set("");
    }
</script>

<div class="flex-shrink-0 px-5 pb-3">
    <div class="relative">
        <!-- search icon -->
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>

        <input
            type="text"
            placeholder="Search contests..."
            bind:value={localQuery}
            oninput={handleInput}
            class="w-full pl-9 pr-8 py-2 text-sm bg-surface-elevated border border-surface-border rounded-lg
                text-text-primary placeholder-text-secondary
                focus:outline-none focus:border-slate-blue-500/50 focus:ring-1 focus:ring-slate-blue-500/25
                transition-colors"
        />

        <!-- clear button -->
        {#if localQuery}
            <button
                onclick={clear}
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors"
                title="Clear search"
            >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        {/if}
    </div>
</div>
