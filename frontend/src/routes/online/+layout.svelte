<script lang="ts">
	import '../../app.css';
	import fav512 from '$lib/assets/icon-512.png';
	
	let { children } = $props();
</script>

<svelte:head>
	<!-- theme and app metadata (changed from homepage) -->
	<meta name="theme-color" content="#3b82f6" />
	<meta name="msapplication-TileColor" content="#3b82f6" />
	<meta name="apple-mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-status-bar-style" content="default" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<meta name="description" content="UIL-DL - Your app description here" />
	<meta name="author" content="Your Name" />
	
	<!-- open graph -->
	<meta property="og:type" content="website" />
	<meta property="og:title" content="UIL-DL" />
	<meta property="og:description" content="Your app description here" />
	<meta property="og:image" content={fav512} />
	<title>UIL-DL Online</title>
</svelte:head>

{@render children?.()}
