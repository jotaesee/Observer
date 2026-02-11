<script>
  import { onMount } from "svelte";
  import Sidebar from "./lib/sidebar.svelte";

  let servers = $state([]);

  onMount(async () => {
    const res = await fetch("http://127.0.0.1:8000/servers");
    const data = await res.json();
    servers = data
  });
</script>

<div class="app-layout">

<Sidebar />

<main class = "main-content">
</main>

</div>

<style>

.app-layout{
  display:flex;
  background-color: #0d0d0d;
  width: 100vw;
  height: 100vh;
}

</style>