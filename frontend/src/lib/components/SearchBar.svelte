<script lang="ts">
    import { onDestroy } from "svelte";
    import { searchQuery, searchMode, caseSensitive, type SearchMode } from "$lib/stores/search";

    let localQuery = $state("");
    let debounceTimer: ReturnType<typeof setTimeout>;

    onDestroy(() => clearTimeout(debounceTimer));

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

    function setMode(mode: SearchMode) {
        searchMode.set(mode);
    }

    function toggleCase() {
        caseSensitive.update(v => !v);
    }

    // mode button styling helper
    function modeClass(mode: SearchMode, current: SearchMode): string {
        return mode === current
            ? "bg-surface-hover text-text-primary"
            : "text-text-secondary hover:text-text-primary";
    }
</script>

<div class="flex-shrink-0 px-5 pb-3">
    <div class="flex items-center gap-2">
        <!-- search input -->
        <div class="relative flex-1">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>

            <input
                type="text"
                placeholder={$searchMode === 'regex' ? "Regex pattern..." : "Search contests..."}
                bind:value={localQuery}
                oninput={handleInput}
                class="w-full pl-9 pr-8 py-2 text-sm bg-surface-elevated border border-surface-border rounded-lg
                    text-text-primary placeholder-text-secondary
                    focus:outline-none focus:border-slate-blue-500/50 focus:ring-1 focus:ring-slate-blue-500/25
                    transition-colors"
            />

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

        <!-- mode toggles -->
        <div class="flex items-center gap-0.5 bg-surface-elevated border border-surface-border rounded-lg p-0.5">
            <button
                onclick={() => setMode('fuzzy')}
                class="px-2 py-1 text-[11px] font-medium rounded-md transition-colors {modeClass('fuzzy', $searchMode)}"
                title="Fuzzy matching"
            >
                Fuzzy
            </button>
            <button
                onclick={() => setMode('exact')}
                class="px-2 py-1 text-[11px] font-medium rounded-md transition-colors {modeClass('exact', $searchMode)}"
                title="Exact substring match"
            >
                Exact
            </button>
            <button
                onclick={() => setMode('regex')}
                class="px-2 py-1 text-[11px] font-medium rounded-md transition-colors {modeClass('regex', $searchMode)}"
                title="Regular expression"
            >
                .*
            </button>
        </div>

        <!-- case sensitivity -->
        <button
            onclick={toggleCase}
            class="px-2 py-1.5 text-[11px] font-bold rounded-lg border transition-colors
                {$caseSensitive
                    ? 'bg-surface-hover text-text-primary border-surface-border'
                    : 'text-text-secondary border-transparent hover:text-text-primary'}"
            title="Match case"
        >
            Aa
        </button>
    </div>
</div>
