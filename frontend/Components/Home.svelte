<script lang="ts">
  var status = 'loading...';

  function fetchStatus() {
    status = 'loading...';
    fetch('/api/health')
      .then(res => res.json())
      .then(data => status = data.status)
      .catch(err => status = 'could not reach /api/health; error: ' + err.message + '; ' + err.toString())
  }

  fetchStatus();
  setInterval(fetchStatus, 1000);
</script>

<div class="bg-gray-100 text-blue p-4 rounded-lg shadow-md">
  <h1>UIL-DL</h1>
  <p>Backend status: {status}</p>
</div>



