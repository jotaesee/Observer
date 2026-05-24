<script>
  import Sidebar from "./lib/sidebar.svelte";
  import { appState } from "./stores.svelte";
  import ServerList from "./lib/ServerList.svelte";
  import NewServerModal from "./lib/newServerModal.svelte";
  import Console from "./lib/Console.svelte";
  import Dashboard from "./lib/Dashboard.svelte";
  import InstanceSettings from "./lib/InstanceSettings.svelte";
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
    {:else}
      {#if appState.selected_section == "dashboard"}
        <Dashboard serverId={appState.selected_server} />
      {:else if appState.selected_section == "console"}
        <Console serverId={appState.selected_server} />
      {:else if appState.selected_section == "players"}
        <p>players</p>
      {:else if appState.selected_section == "files"}
        <p>files</p>
      {:else if appState.selected_section == "settings"}
        <InstanceSettings serverId={appState.selected_server} />
      {/if}
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
