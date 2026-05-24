<script>
  import { onMount } from "svelte";
  import ServerCard from "./ServerCard.svelte";
  import { API_BASE } from "./config";
  import { appState } from '../stores.svelte';

  let instances = $state();
  let waiting_fetch = $state(true);

  onMount(()=>{
    get_servers()
  })

  $effect(() => {
    appState.refreshCounter;
    get_servers();
  });

  async function get_servers() {
    try {
      const res = await fetch(`${API_BASE}/servers`, {method:"GET"});
      instances = await res.json()
    } catch (error) {
     console.error("fetch just failed", error.message);   
    }
    finally {
      waiting_fetch = false;
    }
  }

</script>

{#if waiting_fetch == false}
    <div class="card-grid">
    {#each instances as server (server.id) }
        <ServerCard {...server}/>
    {/each}
  </div>
{:else}
  <p> waiting for fetch...</p>
{/if}

<style>

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    grid-template-rows: repeat(auto-fill, minmax(220px, 1fr));
    margin-top: 3vh;
    margin-left: 2vw;
    margin-right: 2vw;
    grid-column-gap: 20px;
    grid-row-gap: 20px; 
}

</style>
