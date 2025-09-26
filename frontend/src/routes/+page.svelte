<script lang="ts">
    import { onMount } from "svelte";
    import ContestTable from "$lib/components/ContestTable.svelte";

    let health = $state<string>("initialized");

    function fetchHealth() {
        health = "fetching...";
        fetch("/api/health")
            .then(response => {
                if (response.ok) {
                    health = "OK";
                } else {
                    health = response.status + " " + response.statusText;
                }
            })
    }

    onMount(() => {
        fetchHealth();
    });
</script>

<svelte:head>
    <title>UIL-DL 2.0 Beta 1</title>
</svelte:head>

<div class="flex flex-col items-center min-w-full bg-gray-50 text-gray-800 pt-10">
	<h1 class="text-4xl font-light mb-4 text-gray-900">UIL-DL 2.0 Beta 1</h1>
	<p class="text-lg text-gray-600">
		Backend Health Status: 
		<span class="font-medium {health === 'OK' ? 'text-green-600' : health === 'fetching...' ? 'text-blue-600' : 'text-red-600'}">
			{health}
		</span>
        <button class="ml-4 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition" onclick={fetchHealth}>
            Refresh Status
        </button>
	</p>

    <ContestTable />
</div>
