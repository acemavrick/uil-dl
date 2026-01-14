<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/icon.svg';
	import fav16 from '$lib/assets/icon-16.png';
	import fav32 from '$lib/assets/icon-32.png';
	import fav48 from '$lib/assets/icon-48.png';
	import fav192 from '$lib/assets/icon-192.png';
	import fav512 from '$lib/assets/icon-512.png';
	
	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="icon" sizes="16x16" href={fav16} />
	<link rel="icon" sizes="32x32" href={fav32} />
	<link rel="icon" sizes="48x48" href={fav48} />
	<link rel="icon" sizes="192x192" href={fav192} />
	<link rel="icon" sizes="512x512" href={fav512} />

	<!-- theme and app metadata -->
	<meta name="theme-color" content="#0ea5e9" />
	<meta name="msapplication-TileColor" content="#0ea5e9" />
	<meta name="apple-mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<meta name="description" content="UIL-DL streamlines finding, filtering, and downloading UIL Academics contest packets with batch downloads, smart caching, and a responsive UI. Available as a desktop app or online browser version." />
	<meta name="author" content="acemavrick" />
	<meta name="keywords" content="UIL, UIL Academics, contest packets, download, batch download, UIL materials, Texas UIL, academic competitions, uildl, uildl app, uildl desktop, uildl online" />
	
	<!-- open graph -->
	<meta property="og:type" content="website" />
	<meta property="og:title" content="UIL-DL - Download UIL Academics Materials in Seconds" />
	<meta property="og:description" content="Stop hunting for contest packets. Filter by subject, level, and year – then download everything at once. Available as desktop app or online." />
	<meta property="og:image" content={fav512} />
	<meta property="og:url" content="https://uildl.app" />
	
	<!-- twitter card -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="UIL-DL - Download UIL Academics Materials in Seconds" />
	<meta name="twitter:description" content="Streamline finding, filtering, and downloading UIL contest packets with batch downloads and smart caching." />
	<meta name="twitter:image" content={fav512} />

	<title>UIL-DL</title>
</svelte:head>

{@render children?.()}
