<script lang="ts">
	import '../../app.css';
	import fav512 from '$lib/assets/icon-512.png';
	
	let { children } = $props();
</script>

<svelte:head>
	<!-- theme and app metadata -->
	<meta name="theme-color" content="#059669" />
	<meta name="msapplication-TileColor" content="#059669" />
	<meta name="apple-mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<meta name="description" content="UIL-DL Online - Browse and filter the complete UIL Academics catalog in your browser. Click any link to access contest packets instantly, no installation required." />
	<meta name="author" content="acemavrick" />
	<meta name="keywords" content="UIL, UIL Academics, contest packets, online, browser, UIL materials, Texas UIL, academic competitions, no download, uildl, uildl app, uildl desktop, uildl online" />
	
	<!-- open graph -->
	<meta property="og:type" content="website" />
	<meta property="og:title" content="UIL-DL Online - Browse UIL Contest Packets" />
	<meta property="og:description" content="Browse and filter the complete UIL Academics catalog in your browser. Access contest packets instantly with no installation required." />
	<meta property="og:image" content={fav512} />
	<meta property="og:url" content="https://uildl.app/online" />
	
	<!-- twitter card -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="UIL-DL Online - Browse UIL Contest Packets" />
	<meta name="twitter:description" content="Browse and filter UIL Academics materials instantly in your browser. No installation required." />
	<meta name="twitter:image" content={fav512} />
	
	<title>UIL-DL Online</title>
</svelte:head>

{@render children?.()}
