<script>
  import { onMount } from "svelte";
  import Sidebar from "./lib/sidebar.svelte";
  import { appState } from "./stores.svelte";
  import ServerList from "./lib/ServerList.svelte";
  import NewServerModal from "./lib/newServerModal.svelte";

  let servers = $state([]);

  onMount(async () => {
    const res = await fetch("http://127.0.0.1:8000/servers");
    const data = await res.json();
    servers = data;
  });
</script>

<div class="app-layout">
  <Sidebar />

  {#if appState.isNewInstanceModalOpen}
    <NewServerModal />
  {/if}

  <main class="main-content">
    {#if !appState.selected_server}
      {#if appState.selected_section == "instances"}
        <ServerList />
      {:else if appState.selected_section == "analytics"}
        <p>analytics</p>
      {:else if appState.selected_section == "settings"}
        <p>settings</p>
      {:else if appState.selected_section == "account"}
        <p>account</p>
      {/if}
    {:else if appState.selected_section == "dashboard"}
      <p>dashboard</p>
    {:else if appState.selected_section == "console"}
      <p>analytics</p>
    {:else if appState.selected_section == "players"}
      <p>players</p>
    {:else if appState.selected_section == "files"}
      <p>files</p>
    {:else if appState.selected_section == "settings"}
      <p>settings</p>
    {/if}
  </main>
</div>

<style>
  .app-layout {
    display: flex;
    background-color: #0d0d0d;
    width: 100vw;
    height: 100vh;
  }

  .main-content {
    flex-grow: 1;
    overflow-y: auto;
    height: 100vh;
    padding: 20px;
  }
</style>
