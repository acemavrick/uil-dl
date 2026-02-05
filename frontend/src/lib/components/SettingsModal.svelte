<script lang="ts">
    import { config } from "$lib/stores/config";
    import { cached } from "$lib/stores/cache";
    import { commands } from "$lib/bindings";
    import { APP_VERSION } from "$lib/version";

    interface Props {
        open: boolean;
        onClose: () => void;
    }

    let { open, onClose }: Props = $props();

    let rebuildingCache = $state(false);
    let cacheCount = $derived($cached.size);

    async function changeDownloadDir() {
        const { open: openDialog } = await import("@tauri-apps/plugin-dialog");
        const selected = await openDialog({ directory: true, multiple: false });
        if (selected) {
            const result = await commands.setDownloadDir(selected as string);
            if (result.status === "ok") {
                config.update((c) => ({ ...c, download_dir: selected as string }));
            }
        }
    }

    async function openDownloads() {
        await commands.openDownloadsFolder();
    }

    async function rebuildCache() {
        rebuildingCache = true;
        try {
            const result = await commands.rebuildCache();
            if (result.status === "ok") {
                cached.set(new Set(result.data));
            }
        } finally {
            rebuildingCache = false;
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Escape") onClose();
    }

    function openGitHub() {
        commands.openUrl("https://github.com/acemavrick/uil-dl");
    }
</script>

<svelte:document onkeydown={handleKeydown} />

{#if open}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={onClose}></div>

        <div class="relative bg-surface-elevated border border-surface-border rounded-xl w-[420px] shadow-2xl overflow-hidden">
            <!-- header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-surface-border">
                <h2 class="text-lg font-semibold text-text-primary">Settings</h2>
                <button onclick={onClose} class="p-1 text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-hover transition-colors" title="Close">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- content -->
            <div class="px-5 py-4 space-y-5">
                <!-- download location -->
                <div class="space-y-2">
                    <span class="text-sm font-medium text-text-primary">Download Location</span>
                    <div class="flex items-center gap-2">
                        <div class="flex-1 px-3 py-1.5 text-sm text-text-secondary bg-surface-base border border-surface-border rounded-lg truncate selectable">
                            {$config.download_dir || "Not set"}
                        </div>
                        <button onclick={openDownloads} class="p-1.5 text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-hover transition-colors" title="Open folder">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                        </button>
                    </div>
                    <button
                        onclick={changeDownloadDir}
                        class="text-xs text-slate-blue-400 hover:text-slate-blue-300 transition-colors"
                    >
                        Change location
                    </button>
                </div>

                <!-- divider -->
                <div class="border-t border-surface-border"></div>

                <!-- cache -->
                <div class="flex items-center justify-between">
                    <div>
                        <div class="text-sm text-text-primary">Cache</div>
                        <div class="text-xs text-text-secondary">{cacheCount} files cached</div>
                    </div>
                    <button
                        onclick={rebuildCache}
                        disabled={rebuildingCache}
                        class="text-xs px-3 py-1.5 rounded-lg border border-surface-border
                            text-text-secondary hover:text-text-primary hover:bg-surface-hover
                            disabled:opacity-50 transition-colors"
                    >
                        {rebuildingCache ? "Rebuilding..." : "Rebuild"}
                    </button>
                </div>
            </div>

            <!-- footer -->
            <div class="px-5 py-3 border-t border-surface-border flex items-center justify-between">
                <span class="text-xs text-text-secondary">UIL-DL v{APP_VERSION}</span>
                <button
                    onclick={openGitHub}
                    class="text-xs text-text-secondary hover:text-text-primary transition-colors"
                >
                    GitHub
                </button>
            </div>
        </div>
    </div>
{/if}
