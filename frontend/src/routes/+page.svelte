<script lang="ts">
    import { onMount } from "svelte";

    let health = $state<string>("initialized");

    function fetchHealth() {
        health = "fetching...";
        fetch("/health")
            .then(response => {
                if (response.ok) {
                    health = "OK";
                } else {
                    health = "Not OK";
                }
            })
    }

    onMount(() => {
        fetchHealth();
    });

    // fetch health every 3 seconds
    setInterval(() => {
        fetchHealth();
    }, 3000);
</script>


<div class="flex flex-col items-center justify-center min-h-screen bg-gray-50 text-gray-800">
	<h1 class="text-4xl font-light mb-4 text-gray-900">UIL-DL 2.0 Beta 1</h1>
	<p class="text-lg text-gray-600">
		Backend Health Status: 
		<span class="font-medium {health === 'OK' ? 'text-green-600' : health === 'fetching...' ? 'text-blue-600' : 'text-red-600'}">
			{health}
		</span>
	</p>
</div>
