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
	<meta name="theme-color" content="#059669" />
	<meta name="msapplication-TileColor" content="#059669" />
	<meta name="apple-mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<meta name="description" content="UIL-DL - Browse and filter the complete UIL Academics catalog. Click any link to access contest packets instantly." />
	<meta name="author" content="acemavrick" />
	<meta name="keywords" content="UIL, UIL Academics, contest packets, UIL materials, Texas UIL, academic competitions, uildl" />
	
	<!-- open graph -->
	<meta property="og:type" content="website" />
	<meta property="og:title" content="UIL-DL - Browse UIL Contest Packets" />
	<meta property="og:description" content="Browse and filter the complete UIL Academics catalog. Access contest packets instantly." />
	<meta property="og:image" content={fav512} />
	
	<!-- twitter card -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="UIL-DL - Browse UIL Contest Packets" />
	<meta name="twitter:description" content="Browse and filter UIL Academics materials instantly." />
	<meta name="twitter:image" content={fav512} />

	<title>UIL-DL</title>
</svelte:head>

{@render children?.()}
