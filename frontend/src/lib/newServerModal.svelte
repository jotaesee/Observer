<script>
  import { appState } from "../stores.svelte";
  import { X, Server, Network, FolderCode } from "lucide-svelte";
  import { onMount } from "svelte";
  import { API_BASE } from "./config";

  let form = $state({
    id: "",
    server_type: "OFFICIAL",
    mc_version: "",
    java_path: "",
    port: 25565,
    ram_gb: 4,
  });

  let serverTypes = ["OFFICIAL", "PAPER"];
  let mcVersions = $state({});

  onMount(() => {
    getVersions();
  });

  async function getVersions() {
    const res = await fetch(`${API_BASE}/versions`, {
      method: "GET",
    });

    if (res.ok) {
      const data = await res.json();
      mcVersions = data;
    }
  }

  async function handleCreate() {
    const requestBody = {
      id: form.id,
      server_type: form.server_type,
      mc_version: form.mc_version,
      port: form.port,
      ram_max: `-Xmx${form.ram_gb}G`,
      java_version: form.java_path.trim() === "" ? "java" : form.java_path,
    };

    console.log("creating instance for:", requestBody);

    const res = await fetch(`${API_BASE}/servers/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (res.ok) {
      console.log("instance created successfully");
      appState.triggerRefresh();
    }

    appState.toggle_Modal();
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={() => appState.toggle_Modal()}>
  <div class="modal-container" onclick={(e) => e.stopPropagation()}>
    <div class="modal-header">
      <div>
        <h2>New Instance Wizard</h2>
        <p>Configure your new Minecraft server deployment</p>
      </div>
      <button class="close-btn" onclick={() => appState.toggle_Modal()}>
        <X size={20} />
      </button>
    </div>

    <hr class="divider" />

    <div class="modal-body form-grid">
      <div class="input-group full-width">
        <div class="label-row">
          <!-- svelte-ignore a11y_label_has_associated_control -->
          <label>Instance Name</label>
          <span class="char-counter">{form.id.length}/25</span>
        </div>
        <div class="input-wrapper">
          <Server size={18} class="input-icon" />
          <input
            type="text"
            bind:value={form.id}
            placeholder="e.g. My Survival World"
            maxlength="25"
          />
        </div>
      </div>

      <div class="input-group">
        <!-- svelte-ignore a11y_label_has_associated_control -->
        <label>Server Type</label>
        <select bind:value={form.server_type}>
          {#each serverTypes as type}
            <option value={type}>{type}</option>
          {/each}
        </select>
      </div>

      <div class="input-group">
        <!-- svelte-ignore a11y_label_has_associated_control -->
        <label>Version</label>
        <select bind:value={form.mc_version}>
          {#if form.server_type === "OFFICIAL"}
            {#each mcVersions["OFFICIAL"] as version}
              <option value={version}>{version}</option>
            {/each}
          {:else}
            {#each mcVersions["PAPER"] as version}
              <option value={version}>{version}</option>
            {/each}
          {/if}
        </select>
      </div>

      <div class="input-group">
        <!-- svelte-ignore a11y_label_has_associated_control -->
        <label>Custom Java Path (Optional)</label>
        <div class="input-wrapper">
          <FolderCode size={18} class="input-icon" />
          <input
            type="text"
            bind:value={form.java_path}
            placeholder="Auto-managed"
          />
        </div>
      </div>

      <div class="input-group">
        <!-- svelte-ignore a11y_label_has_associated_control -->
        <label>Server Port</label>
        <div class="input-wrapper">
          <Network size={18} class="input-icon" />
          <input type="number" bind:value={form.port} />
        </div>
      </div>

      <div class="input-group full-width ram-slider-group">
        <div class="ram-header">
          <!-- svelte-ignore a11y_label_has_associated_control -->
          <label>Max RAM Usage</label>
          <span class="ram-badge">{form.ram_gb} GB</span>
        </div>
        <input
          type="range"
          min="1"
          max="16"
          step="1"
          bind:value={form.ram_gb}
          class="ram-slider"
        />
        <div class="ram-labels">
          <span>1GB</span>
          <span>8GB</span>
          <span>16GB</span>
        </div>
      </div>
    </div>

    <hr class="divider" />

    <div class="modal-footer">
      <button class="btn-cancel" onclick={() => appState.toggle_Modal()}
        >Cancel</button
      >
      <button class="btn-create" onclick={handleCreate}
        >Create Server &rarr;</button
      >
    </div>
  </div>
</div>

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    z-index: 9999;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .modal-container {
    background-color: #0a0a0a;
    border: 1px solid #242424;
    border-radius: 12px;
    width: 600px;
    display: flex;
    flex-direction: column;
    font-family: "Inter", sans-serif;
    color: white;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    padding: 24px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .modal-header h2 {
    margin: 0 0 8px 0;
    font-size: 1.25rem;
    font-family: "Space Grotesk", sans-serif;
  }

  .modal-header p {
    margin: 0;
    color: #888;
    font-size: 0.85rem;
  }

  .close-btn {
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    transition: color 0.2s;
  }

  .close-btn:hover {
    color: #fff;
  }

  .divider {
    border: none;
    border-top: 1px solid #242424;
    margin: 0;
  }

  .modal-body {
    padding: 24px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  .full-width {
    grid-column: span 2;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .input-group label {
    font-size: 0.8rem;
    color: #aaa;
  }

  .label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .char-counter {
    font-size: 0.7rem;
    color: #666;
    font-family: monospace;
  }

  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  :global(.input-icon) {
    position: absolute;
    left: 12px;
    color: #666;
  }

  input[type="text"],
  input[type="number"],
  select {
    width: 100%;
    background-color: #111;
    border: 1px solid #333;
    color: white;
    padding: 10px 12px 10px 38px;
    font-size: 0.9rem;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
  }

  select {
    padding-left: 12px;
    appearance: auto;
  }

  input:focus,
  select:focus {
    border-color: #00ff66;
  }

  .ram-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .ram-badge {
    background: rgba(0, 255, 102, 0.1);
    color: #00ff66;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: bold;
    border: 1px solid rgba(0, 255, 102, 0.3);
  }

  .ram-slider {
    width: 100%;
    accent-color: #00ff66;
    cursor: pointer;
  }

  .ram-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.65rem;
    color: #666;
  }

  .modal-footer {
    padding: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .btn-cancel {
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    font-size: 0.9rem;
    transition: color 0.2s;
  }

  .btn-cancel:hover {
    color: #fff;
  }

  .btn-create {
    background-color: #00ff66;
    color: #000;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
    font-size: 0.9rem;
    transition:
      transform 0.1s,
      background-color 0.2s;
  }

  .btn-create:hover {
    background-color: #00cc52;
    transform: translateY(-1px);
  }
</style>
