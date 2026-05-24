<script>
  import { onMount } from 'svelte';
  import { appState } from '../stores.svelte';
  import { API_BASE } from './config';
  import { Settings, Server, Shield, Users as UsersIcon } from 'lucide-svelte';

  let { serverId } = $props();

  const GAMEMODE_NAMES = { '0': 'Survival', 'survival': 'Survival', '1': 'Creative', 'creative': 'Creative', '2': 'Adventure', 'adventure': 'Adventure', '3': 'Spectator', 'spectator': 'Spectator' };
  const DIFFICULTY_NAMES = { '0': 'Peaceful', 'peaceful': 'Peaceful', '1': 'Easy', 'easy': 'Easy', '2': 'Normal', 'normal': 'Normal', '3': 'Hard', 'hard': 'Hard' };

  let motd = $state('--');
  let gamemode = $state('--');
  let difficulty = $state('--');
  let maxPlayers = $state('--');
  let loading = $state(true);

  onMount(() => {
    fetchProperties();
  });

  async function fetchProperties() {
    try {
      const res = await fetch(`${API_BASE}/servers/${serverId}/properties`);
      if (res.ok) {
        const data = await res.json();
        motd = data.motd || '--';
        gamemode = GAMEMODE_NAMES[data.gamemode] || data.gamemode || '--';
        difficulty = DIFFICULTY_NAMES[data.difficulty] || data.difficulty || '--';
        maxPlayers = data['max-players'] || '--';
      }
    } catch (e) {
      console.error('Failed to fetch server properties', e);
    } finally {
      loading = false;
    }
  }

  function goToSettings() {
    appState.selected_section = "settings";
  }
</script>

<div class="card" onclick={goToSettings} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && goToSettings()}>
  <div class="card-title">
    <Settings size={16} />
    <span>Server Properties</span>
  </div>

  {#if loading}
    <div class="loading">Loading...</div>
  {:else}
    <div class="props-list">
      <div class="prop-row">
        <Server size={14} />
        <span class="prop-label">MOTD</span>
        <span class="prop-value motd">{motd}</span>
      </div>
      <div class="prop-row">
        <Shield size={14} />
        <span class="prop-label">Gamemode</span>
        <span class="prop-value">{gamemode}</span>
      </div>
      <div class="prop-row">
        <Shield size={14} />
        <span class="prop-label">Difficulty</span>
        <span class="prop-value">{difficulty}</span>
      </div>
      <div class="prop-row">
        <UsersIcon size={14} />
        <span class="prop-label">Max Players</span>
        <span class="prop-value">{maxPlayers}</span>
      </div>
    </div>
    <button class="configure-btn" onclick={(e) => { e.stopPropagation(); goToSettings(); }}>
      Configure &rarr;
    </button>
  {/if}
</div>

<style>
  .card {
    background-color: #111;
    border: 1px solid #242424;
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: border-color 0.2s;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .card:hover {
    border-color: #00ff664d;
  }

  .card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: #888;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .loading {
    color: #555;
    font-size: 0.8rem;
    font-style: italic;
    text-align: center;
    padding: 12px 0;
    font-family: 'Inter', sans-serif;
  }

  .props-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .prop-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    color: #888;
  }

  .prop-label {
    color: #666;
    width: 80px;
    flex-shrink: 0;
  }

  .prop-value {
    color: #ddd;
    font-weight: 500;
  }

  .motd {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .configure-btn {
    width: 100%;
    background: transparent;
    border: 1px solid #333;
    color: #00ff66;
    padding: 8px 16px;
    border-radius: 6px;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: 4px;
  }

  .configure-btn:hover {
    background: #112b1b;
    border-color: #0d5529;
  }
</style>
