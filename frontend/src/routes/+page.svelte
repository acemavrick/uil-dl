<script lang="ts">
    import icon from "$lib/assets/icon.svg";
    import app_lm_home from "$lib/assets/light_mode_homepage.png";
    import { APP_VERSION, ONLINE_VERSION } from "$lib/version";

    const app_version = APP_VERSION;
    const online_version = ONLINE_VERSION;
</script>

<!-- main page -->
<div class="min-h-screen bg-slate-950 text-slate-100">
    <!-- top navigation -->
    <header class="sticky top-0 z-50 backdrop-blur supports-[backdrop-filter]:bg-slate-950/80 border-b border-slate-800/50">
        <nav class="mx-auto max-w-7xl px-4 sm:px-6 py-4 flex items-center justify-between">
            <a href="/" class="flex items-center gap-2 font-semibold text-lg group">
                <img src={icon} alt="UIL-DL" class="h-9 w-9 rounded-lg group-hover:scale-105 transition-transform">
                <span class="text-slate-100">UIL-DL</span>
            </a>
            <div class="flex items-center gap-2 sm:gap-3">
                <a 
                    href="/online" 
                    title="Launch UIL-DL Online in your browser"
                    class="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 sm:px-4 sm:py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 hover:bg-emerald-500 hover:shadow-emerald-500/40 transition-all duration-200"
                >
                    <span class="hidden sm:inline">Online</span>
                    <span class="sm:hidden">▶ Online</span>
                </a>
               <a 
                    href="https://discord.gg/a6DdBaebPk" 
                    title="Join the UIL-DL community on Discord"
                    class="hidden md:inline-flex items-center gap-1.5 rounded-lg bg-slate-800 px-3 py-2 text-sm font-semibold text-white ring-1 ring-inset ring-slate-700 hover:bg-slate-700 transition-colors"
                >
                    Discord
                </a>
                <a 
                    href="https://github.com/acemavrick/uil-dl/blob/standalone/README.md" 
                    title="Read the full documentation"
                    class="hidden lg:inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white ring-1 ring-inset ring-slate-800 hover:bg-slate-800 transition-colors"
                >
                    Docs
                </a>
                <a 
                    href="https://github.com/acemavrick/uil-dl/releases" 
                    title="Download the desktop app"
                    class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 sm:px-4 sm:py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/25 hover:bg-sky-500 hover:shadow-sky-500/40 transition-all duration-200"
                >
                    <span class="hidden sm:inline">Download</span>
                    <span class="sm:hidden">⬇</span>
                </a>
            </div>
        </nav>
    </header>

    <!-- hero -->
    <section class="relative overflow-hidden">
        <!-- background effects -->
        <div class="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950"></div>
        <div aria-hidden="true" class="pointer-events-none absolute -top-40 left-1/2 h-[32rem] w-[32rem] -translate-x-1/2 rounded-full bg-emerald-500/20 blur-3xl"></div>
        <div aria-hidden="true" class="pointer-events-none absolute -bottom-32 -right-32 h-[28rem] w-[28rem] rounded-full bg-fuchsia-500/10 blur-3xl"></div>
        
        <div class="relative mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28 lg:py-32">
            <div class="text-center">
                <!-- version badges -->
                <div class="flex items-center justify-center gap-2 mb-6">
                    <span class="inline-flex items-center rounded-full bg-sky-900/60 px-3 py-1 text-xs font-medium text-sky-100 ring-1 ring-inset ring-sky-700/50 backdrop-blur">
                        Desktop {app_version}
                    </span>
                    <span class="inline-flex items-center rounded-full bg-emerald-900/60 px-3 py-1 text-xs font-medium text-emerald-100 ring-1 ring-inset ring-emerald-700/50 backdrop-blur">
                        Online {online_version}
                    </span>
                    </div>

                <!-- headline -->
                <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight max-w-4xl mx-auto">
                    UIL Academics materials,
                    <span class="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">instantly accessible</span>
                </h1>

                <!-- subhead -->
                <p class="mt-6 text-lg sm:text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
                    Stop hunting for contest packets. Filter by subject, level, and year – then download everything at once. Choose the browser app or install the desktop version.
                </p>

                <!-- cta buttons -->
                <div class="mt-10 flex flex-wrap items-center justify-center gap-4">
                    <a 
                        href="/online" 
                        title="Launch UIL-DL Online — no installation required"
                        class="group inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3.5 text-base font-semibold text-white shadow-xl shadow-emerald-500/30 hover:bg-emerald-500 hover:shadow-emerald-500/50 transition-all duration-200 hover:scale-105"
                    >
                        <span>Launch Online</span>
                        <svg class="h-5 w-5 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                    </a>
                    <a 
                        href="https://github.com/acemavrick/uil-dl/releases" 
                        title="Download the desktop app for offline use"
                        class="group inline-flex items-center gap-2 rounded-xl bg-sky-600 px-6 py-3.5 text-base font-semibold text-white shadow-lg shadow-sky-500/30 hover:bg-sky-500 hover:shadow-sky-500/50 transition-all duration-200 hover:scale-105"
                    >
                        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        <span>Get Desktop App</span>
                    </a>
                </div>

                <!-- secondary links -->
                <div class="mt-6 flex flex-wrap items-center justify-center gap-6 text-sm">
                    <a href="https://discord.gg/a6DdBaebPk" class="text-slate-400 hover:text-emerald-400 transition-colors font-medium">
                        Join Discord →
                    </a>
                    <a href="https://github.com/acemavrick/uil-dl/blob/standalone/README.md" class="text-slate-400 hover:text-emerald-400 transition-colors font-medium">
                        Read docs →
                    </a>
                    <a href="https://github.com/acemavrick/uil-dl" class="text-slate-400 hover:text-emerald-400 transition-colors font-medium">
                        View source →
                    </a>
                </div>
            </div>
        </div>
    </section>

    <!-- app preview -->
    <section class="relative mx-auto max-w-7xl px-4 sm:px-6 pb-20 sm:pb-28">
        <div class="rounded-3xl bg-gradient-to-br from-slate-900/90 to-slate-900/50 ring-1 ring-slate-800/70 p-2 sm:p-4 shadow-2xl shadow-slate-900/50 backdrop-blur">
            <img src={app_lm_home} alt="UIL-DL desktop app interface" class="w-full rounded-2xl shadow-2xl ring-1 ring-white/10">
        </div>
    </section>

    <!-- feature grid -->
    <section class="relative mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
        <div class="text-center mb-16">
            <h2 class="text-3xl sm:text-4xl font-bold tracking-tight">Built for efficiency</h2>
            <p class="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
                No more repetitive downloads or scattered files. UIL-DL keeps everything organized and cached.
            </p>
        </div>

        <div class="grid gap-8 md:grid-cols-3">
            <!-- feature 1 -->
            <div class="relative group">
                <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 blur-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative rounded-2xl bg-slate-900/50 ring-1 ring-slate-800 p-8 hover:ring-slate-700 transition-all">
                    <div class="inline-flex items-center justify-center rounded-xl bg-emerald-500/10 p-3 ring-1 ring-emerald-500/20">
                        <svg class="h-6 w-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                        </svg>
                    </div>
                    <h3 class="mt-6 text-xl font-semibold">Instant filtering</h3>
                    <p class="mt-3 text-slate-400 leading-relaxed">
                        Sort by subject, level, and year with one click. Column headers toggle between ascending and descending order.
                    </p>
                </div>
            </div>

            <!-- feature 2 -->
            <div class="relative group">
                <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 blur-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative rounded-2xl bg-slate-900/50 ring-1 ring-slate-800 p-8 hover:ring-slate-700 transition-all">
                    <div class="inline-flex items-center justify-center rounded-xl bg-violet-500/10 p-3 ring-1 ring-violet-500/20">
                        <svg class="h-6 w-6 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                    </div>
                    <h3 class="mt-6 text-xl font-semibold">Batch downloads</h3>
                    <p class="mt-3 text-slate-400 leading-relaxed">
                        Select multiple contests and download all PDFs or data files at once. The app handles concurrency automatically.
                    </p>
                </div>
            </div>

            <!-- feature 3 -->
            <div class="relative group">
                <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-orange-500/10 to-red-500/10 blur-xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative rounded-2xl bg-slate-900/50 ring-1 ring-slate-800 p-8 hover:ring-slate-700 transition-all">
                    <div class="inline-flex items-center justify-center rounded-xl bg-orange-500/10 p-3 ring-1 ring-orange-500/20">
                        <svg class="h-6 w-6 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                        </svg>
                    </div>
                    <h3 class="mt-6 text-xl font-semibold">Smart caching</h3>
                    <p class="mt-3 text-slate-400 leading-relaxed">
                        Files you've grabbed before load instantly from cache. Repeat downloads are zero‑bandwidth and lightning fast.
                    </p>
                </div>
            </div>
        </div>
    </section>

    <!-- how it works -->
    <section class="relative mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
        <div class="rounded-3xl bg-gradient-to-br from-slate-900 to-slate-950 ring-1 ring-slate-800 p-8 sm:p-12 lg:p-16">
            <h2 class="text-3xl sm:text-4xl font-bold tracking-tight mb-12">How it works</h2>
            
            <div class="grid gap-8 lg:grid-cols-3">
                <div class="flex gap-4">
                    <div class="flex-shrink-0">
                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 ring-1 ring-emerald-500/20">
                            <span class="text-lg font-bold text-emerald-400">1</span>
                        </div>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold mb-2">Refresh the catalog</h3>
                        <p class="text-slate-400 leading-relaxed">
                            Click Refresh Info to pull the latest UIL materials index. The catalog updates automatically when new contests are added.
                        </p>
                    </div>
                </div>

                <div class="flex gap-4">
                    <div class="flex-shrink-0">
                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 ring-1 ring-violet-500/20">
                            <span class="text-lg font-bold text-violet-400">2</span>
                        </div>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold mb-2">Pick what you need</h3>
                        <p class="text-slate-400 leading-relaxed">
                            Use filters or sort columns to find contests. Select rows and click Download Selected to start the batch.
                        </p>
                    </div>
                </div>

                <div class="flex gap-4">
                    <div class="flex-shrink-0">
                        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/10 ring-1 ring-orange-500/20">
                            <span class="text-lg font-bold text-orange-400">3</span>
                        </div>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold mb-2">Cache & organize</h3>
                        <p class="text-slate-400 leading-relaxed">
                            Files are saved with clean names. A local manifest tracks downloads – refresh or reset without losing files.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- two apps callout -->
    <section class="relative mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
        <div class="text-center mb-12">
            <h2 class="text-3xl sm:text-4xl font-bold tracking-tight">Choose your flavor</h2>
            <p class="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
                Both apps share the same catalog and similar features, though only the desktop app offers downloads. Pick whichever fits your workflow.
            </p>
        </div>

        <div class="grid gap-6 lg:grid-cols-2">
            <!-- online app -->
            <div class="relative group">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative rounded-3xl bg-slate-900/50 ring-1 ring-slate-800 p-10 hover:ring-emerald-500/50 transition-all">
                    <div class="flex items-start justify-between mb-6">
                        <div>
                            <h3 class="text-2xl font-bold text-emerald-400">UIL-DL Online</h3>
                            <p class="mt-1 text-sm text-slate-400">Version {online_version}</p>
                        </div>
                        <span class="inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300 ring-1 ring-emerald-500/20">
                            No install
                        </span>
                    </div>
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-start gap-3 text-slate-300">
                            <svg class="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Launch instantly from any browser</span>
                        </li>
                        <li class="flex items-start gap-3 text-slate-300">
                            <svg class="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Browse and filter the full catalog</span>
                        </li>
                        <li class="flex items-start gap-3 text-slate-300">
                            <svg class="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Direct links to all resources</span>
                        </li>
            </ul>
                    <a 
                        href="/online" 
                        title="Launch UIL-DL Online"
                        class="inline-flex items-center justify-center w-full gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-base font-semibold text-white shadow-lg hover:bg-emerald-500 transition-all"
                    >
                        Launch Online
                    </a>
                </div>
            </div>

            <!-- desktop app -->
            <div class="relative group">
                <div class="absolute inset-0 rounded-3xl bg-gradient-to-br from-sky-500/20 to-blue-500/20 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative rounded-3xl bg-slate-900/50 ring-1 ring-slate-800 p-10 hover:ring-sky-500/50 transition-all">
                    <div class="flex items-start justify-between mb-6">
                        <div>
                            <h3 class="text-2xl font-bold text-sky-400">Desktop App</h3>
                            <p class="mt-1 text-sm text-slate-400">Version {app_version}</p>
                        </div>
                        <span class="inline-flex items-center rounded-full bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-300 ring-1 ring-sky-500/20">
                            Full-featured
                        </span>
                    </div>
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-start gap-3 text-slate-300">
                            <svg class="h-5 w-5 text-sky-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Batch download to local folders</span>
                        </li>
                        <li class="flex items-start gap-3 text-slate-300">
                            <svg class="h-5 w-5 text-sky-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Smart caching for offline access</span>
                        </li>
                        <li class="flex items-start gap-3 text-slate-300">
                            <svg class="h-5 w-5 text-sky-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Organized filenames for workflows</span>
                        </li>
                    </ul>
                    <a 
                        href="https://github.com/acemavrick/uil-dl/releases" 
                        title="Download the desktop app"
                        class="inline-flex items-center justify-center w-full gap-2 rounded-xl bg-sky-600 px-4 py-3 text-base font-semibold text-white shadow-lg hover:bg-sky-500 transition-all"
                    >
                        Get Desktop App
                    </a>
                </div>
            </div>
        </div>
    </section>

    <!-- privacy note -->
    <section class="relative mx-auto max-w-7xl px-4 sm:px-6 py-12">
        <div class="rounded-2xl bg-slate-900/50 ring-1 ring-slate-800 p-8 text-center">
            <h3 class="text-lg font-semibold mb-3">Privacy first</h3>
            <p class="text-slate-400 max-w-2xl mx-auto">
                Only anonymous, functional events are measured to improve the app. Delete the <code class="text-emerald-400">ga4_csnt</code> token from your app data directory to opt out at any time.
            </p>
        </div>
    </section>

    <!-- contact & resources -->
    <section class="relative mx-auto max-w-7xl px-4 sm:px-6 py-20 sm:py-28">
        <div class="text-center mb-12">
            <h2 class="text-3xl sm:text-4xl font-bold tracking-tight">Questions? Feedback?</h2>
            <p class="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
                Open an issue, join the Discord, or reach out directly.
            </p>
        </div>

        <div class="flex flex-wrap justify-center gap-4">
            <a 
                href="https://github.com/acemavrick/uil-dl/issues" 
                title="Report bugs or request features on GitHub"
                class="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-6 py-3 text-base font-semibold text-white ring-1 ring-inset ring-slate-700 hover:bg-slate-700 transition-all"
            >
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                <span>GitHub Issues</span>
            </a>
            <a 
                href="https://discord.gg/a6DdBaebPk" 
                title="Chat with the community on Discord"
                class="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-6 py-3 text-base font-semibold text-white ring-1 ring-inset ring-slate-700 hover:bg-slate-700 transition-all"
            >
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0 a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                </svg>
                <span>Discord</span>
            </a>
            <a 
                href="https://github.com/acemavrick" 
                title="Contact the developer"
                class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-6 py-3 text-base font-semibold text-white ring-1 ring-inset ring-slate-800 hover:bg-slate-800 transition-all"
            >
                <span>Contact</span>
            </a>
        </div>
    </section>

    <!-- footer -->
    <footer class="border-t border-slate-800/50">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 py-12">
            <div class="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                <div class="flex items-center gap-3">
                    <img src={icon} alt="UIL-DL" class="h-8 w-8 rounded-lg opacity-80">
                    <div>
                        <p class="text-sm font-semibold text-slate-300">UIL-DL</p>
                        <p class="text-xs text-slate-500">Open source • MIT License</p>
                    </div>
                </div>
                <div class="flex flex-wrap gap-6 text-sm">
                    <a href="https://github.com/acemavrick/uil-dl" class="text-slate-400 hover:text-emerald-400 transition-colors">
                        GitHub
                    </a>
                    <a href="https://github.com/acemavrick/uil-dl/blob/standalone/README.md" class="text-slate-400 hover:text-emerald-400 transition-colors">
                        Documentation
                    </a>
                    <a href="https://discord.gg/a6DdBaebPk" class="text-slate-400 hover:text-emerald-400 transition-colors">
                        Discord
                    </a>
                    <a href="https://github.com/acemavrick" class="text-slate-400 hover:text-emerald-400 transition-colors">
                        © 2025 acemavrick
                    </a>
                </div>
            </div>
        </div>
    </footer>
</div>