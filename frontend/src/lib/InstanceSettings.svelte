<script>
  import { appState } from '../stores.svelte';
  import { API_BASE } from './config';
  import { Save, RotateCw, Upload, Image as ImageIcon } from 'lucide-svelte';

  let { serverId } = $props();

  const DEFAULTS = {
    'server-port': '25565',
    'motd': 'A Minecraft Server',
    'max-players': '20',
    'online-mode': 'true',
    'pvp': 'true',
    'gamemode': 'survival',
    'difficulty': 'easy',
    'force-gamemode': 'false',
    'hardcore': 'false',
    'level-name': 'world',
    'level-seed': '',
    'level-type': 'DEFAULT',
    'generate-structures': 'true',
    'allow-nether': 'true',
    'spawn-npcs': 'true',
    'spawn-animals': 'true',
    'spawn-monsters': 'true',
    'spawn-protection': '16',
    'max-build-height': '256',
    'white-list': 'false',
    'enable-command-block': 'false',
    'op-permission-level': '4',
    'player-idle-timeout': '0',
    'enable-rcon': 'false',
    'rcon.port': '25575',
    'rcon.password': '',
    'enable-query': 'true',
    'query.port': '25566',
    'server-ip': '',
    'allow-flight': 'false',
    'announce-player-achievements': 'true',
    'snooper-enabled': 'true',
    'view-distance': '10',
    'network-compression-threshold': '256',
    'max-world-size': '29999984',
    'max-tick-time': '60000',
    'enable-jmx-monitoring': 'false',
    'sync-chunk-writes': 'true',
    'entity-broadcast-range-percentage': '100',
    'function-permission-level': '2',
    'prevent-proxy-connections': 'false',
    'rate-limit': '0',
    'broadcast-rcon-to-ops': 'true',
    'broadcast-console-to-ops': 'true',
    'require-resource-pack': 'false',
    'resource-pack': '',
    'resource-pack-sha1': '',
    'enforce-whitelist': 'false',
    'enforce-secure-profile': 'true',
    'initial-disabled-packs': '',
    'initial-enabled-packs': 'vanilla',
  };

  const GAMEMODE_NAMES = { '0': 'survival', 'survival': 'survival', '1': 'creative', 'creative': 'creative', '2': 'adventure', 'adventure': 'adventure', '3': 'spectator', 'spectator': 'spectator' };
  const GAMEMODE_VALUES = { 'survival': '0', 'creative': '1', 'adventure': '2', 'spectator': '3' };
  const DIFFICULTY_NAMES = { '0': 'peaceful', 'peaceful': 'peaceful', '1': 'easy', 'easy': 'easy', '2': 'normal', 'normal': 'normal', '3': 'hard', 'hard': 'hard' };
  const DIFFICULTY_VALUES = { 'peaceful': '0', 'easy': '1', 'normal': '2', 'hard': '3' };
  const BOOL_KEYS = [
    'online-mode', 'pvp', 'force-gamemode', 'hardcore',
    'white-list', 'enable-command-block', 'enable-rcon', 'enable-query',
    'allow-nether', 'allow-flight', 'generate-structures',
    'spawn-npcs', 'spawn-animals', 'spawn-monsters', 'announce-player-achievements',
    'snooper-enabled', 'enable-jmx-monitoring', 'sync-chunk-writes',
    'prevent-proxy-connections', 'broadcast-rcon-to-ops', 'require-resource-pack',
    'enforce-whitelist', 'enforce-secure-profile', 'broadcast-console-to-ops'
  ];
  const GAMEMODE_OPTIONS = ['survival', 'creative', 'adventure', 'spectator'];
  const DIFFICULTY_OPTIONS = ['peaceful', 'easy', 'normal', 'hard'];
  const LEVEL_TYPE_OPTIONS = ['DEFAULT', 'FLAT', 'LARGEBIOMES', 'AMPLIFIED', 'BUFFET', 'CUSTOMIZED'];
  const PERM_LEVEL_OPTIONS = [
    { value: '1', label: '1 — Bypass spawn protection' },
    { value: '2', label: '2 — Use command blocks' },
    { value: '3', label: '3 — Use /ban, /kick, /op' },
    { value: '4', label: '4 — Use /stop, all commands' },
  ];

  let server = $state({ id: '' });
  let props = $state({ ...DEFAULTS });
  let loading = $state(true);
  let saving = $state(false);
  let showPopup = $state(false);
  let changed = $state(false);

  let iconUrl = $state(null);
  let iconUploading = $state(false);
  let iconError = $state('');
  let iconInput;

  function markChanged() {
    changed = true;
  }

  function norm(val) {
    if (val === true || val === 'true') return 'true';
    return 'false';
  }

  function toDisplay(key, val) {
    if (val === undefined || val === null) return DEFAULTS[key];
    if (BOOL_KEYS.includes(key)) return norm(val);
    if (key === 'gamemode') return GAMEMODE_NAMES[val] || val;
    if (key === 'difficulty') return DIFFICULTY_NAMES[val] || val;
    return String(val);
  }

  function toSave(key, val) {
    if (BOOL_KEYS.includes(key)) return norm(val);
    if (key === 'gamemode') return GAMEMODE_VALUES[val] || val;
    if (key === 'difficulty') return DIFFICULTY_VALUES[val] || val;
    return String(val);
  }

  async function loadData() {
    loading = true;
    try {
      const res = await fetch(`${API_BASE}/servers`);
      if (res.ok) {
        const all = await res.json();
        server = all.find(s => s.id === serverId) || { id: serverId };
      }
      await fetchProps();
      await fetchIcon();
    } catch (e) {
      console.error('Failed to load server', e);
    } finally {
      loading = false;
    }
  }

  async function fetchProps() {
    try {
      const res = await fetch(`${API_BASE}/servers/${serverId}/properties`);
      if (res.ok) {
        const data = await res.json();
        const merged = {};
        for (const key of Object.keys(DEFAULTS)) {
          merged[key] = toDisplay(key, data[key]);
        }
        for (const key of Object.keys(data)) {
          if (!(key in DEFAULTS)) {
            merged[key] = data[key];
          }
        }
        props = merged;
      }
    } catch (e) {
      console.error('Failed to load properties', e);
    }
  }

  async function fetchIcon() {
    try {
      const res = await fetch(`${API_BASE}/servers/${serverId}/icon`);
      if (res.ok) {
        const blob = await res.blob();
        iconUrl = URL.createObjectURL(blob);
      } else {
        iconUrl = null;
      }
    } catch (e) {
      iconUrl = null;
    }
  }

  async function saveChanges() {
    saving = true;
    try {
      const payload = {};
      for (const key of Object.keys(props)) {
        payload[key] = toSave(key, props[key]);
      }
      const res = await fetch(`${API_BASE}/servers/${serverId}/properties`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        showPopup = true;
        if (server.current_status === 'ONLINE') {
          appState.restartRequired = true;
        }
        changed = false;
        await fetchProps();
      }
    } catch (e) {
      console.error('Failed to save', e);
    } finally {
      saving = false;
    }
  }

  function toggle(key) {
    props[key] = props[key] === 'true' ? 'false' : 'true';
    markChanged();
  }

  function triggerIconUpload() {
    iconInput?.click();
  }

  async function handleIconUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    iconError = '';
    if (!file.type.startsWith('image/')) {
      iconError = 'File must be an image';
      return;
    }
    iconUploading = true;
    try {
      const fd = new FormData();
      fd.append('icon', file);
      const res = await fetch(`${API_BASE}/servers/${serverId}/icon`, {
        method: 'POST',
        body: fd,
      });
      if (res.ok) {
        await fetchIcon();
      } else {
        iconError = 'Upload failed';
      }
    } catch (e) {
      iconError = 'Upload failed';
    } finally {
      iconUploading = false;
      e.target.value = '';
    }
  }

  $effect(() => {
    if (serverId) {
      loadData();
    } else {
      loading = false;
    }

    return () => {
      if (iconUrl) URL.revokeObjectURL(iconUrl);
    };
  });
</script>

<div class="settings-page">
  {#if loading}
    <div class="loading-indicator">Loading settings...</div>
  {/if}

  <div class="page-header">
    <div class="header-left">
      <div class="icon-area">
        {#if iconUrl}
          <img src={iconUrl} alt="Server icon" class="server-icon" />
        {:else}
          <div class="icon-placeholder">
            <ImageIcon size={24} />
          </div>
        {/if}
        <div class="icon-actions">
          <button class="icon-btn" onclick={triggerIconUpload} disabled={iconUploading} title="Upload icon">
            <Upload size={14} />
          </button>
        </div>
        <input type="file" accept="image/png,.png" bind:this={iconInput} onchange={handleIconUpload} class="icon-input" />
      </div>
      <div class="header-info">
        <h2>Server Settings</h2>
        <span class="server-name">{server.id || serverId}</span>
      </div>
    </div>
    <div class="header-status">
      {#if iconUploading}
        <span class="icon-status uploading">Uploading...</span>
      {/if}
      {#if iconError}
        <span class="icon-status error">{iconError}</span>
      {/if}
    </div>
  </div>

  <div class="sections-grid">
    <div class="card">
      <div class="section-title">General</div>
      <div class="settings-grid">
        <div class="field full-width">
          <label>MOTD</label>
          <input type="text" bind:value={props.motd} oninput={markChanged} placeholder="A Minecraft Server" />
        </div>

        <div class="field">
          <label>Server Port</label>
          <input type="number" bind:value={props['server-port']} oninput={markChanged} min="1" max="65535" />
        </div>

        <div class="field">
          <label>Max Players</label>
          <input type="number" bind:value={props['max-players']} oninput={markChanged} min="1" max="100" />
        </div>

        <div class="field">
          <label>Gamemode</label>
          <select bind:value={props.gamemode} onchange={markChanged}>
            {#each GAMEMODE_OPTIONS as g}
              <option value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>
            {/each}
          </select>
        </div>

        <div class="field">
          <label>Difficulty</label>
          <select bind:value={props.difficulty} onchange={markChanged}>
            {#each DIFFICULTY_OPTIONS as d}
              <option value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
            {/each}
          </select>
        </div>

        <div class="field toggle-field">
          <label>Online Mode</label>
          <button class="toggle" class:on={props['online-mode'] === 'true'} onclick={() => toggle('online-mode')} aria-label="Toggle Online Mode">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>PVP</label>
          <button class="toggle" class:on={props.pvp === 'true'} onclick={() => toggle('pvp')} aria-label="Toggle PVP">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Force Gamemode</label>
          <button class="toggle" class:on={props['force-gamemode'] === 'true'} onclick={() => toggle('force-gamemode')} aria-label="Toggle Force Gamemode">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Hardcore</label>
          <button class="toggle" class:on={props.hardcore === 'true'} onclick={() => toggle('hardcore')} aria-label="Toggle Hardcore">
            <div class="toggle-knob"></div>
          </button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">World</div>
      <div class="settings-grid">
        <div class="field">
          <label>Level Name</label>
          <input type="text" bind:value={props['level-name']} oninput={markChanged} placeholder="world" />
        </div>

        <div class="field">
          <label>Level Seed</label>
          <input type="text" bind:value={props['level-seed']} oninput={markChanged} placeholder="(random)" />
        </div>

        <div class="field">
          <label>Level Type</label>
          <select bind:value={props['level-type']} onchange={markChanged}>
            {#each LEVEL_TYPE_OPTIONS as t}
              <option value={t}>{t}</option>
            {/each}
          </select>
        </div>

        <div class="field toggle-field">
          <label>Generate Structures</label>
          <button class="toggle" class:on={props['generate-structures'] === 'true'} onclick={() => toggle('generate-structures')} aria-label="Toggle Generate Structures">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Allow Nether</label>
          <button class="toggle" class:on={props['allow-nether'] === 'true'} onclick={() => toggle('allow-nether')} aria-label="Toggle Allow Nether">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field">
          <label>Spawn Protection</label>
          <input type="number" bind:value={props['spawn-protection']} oninput={markChanged} min="0" max="100" />
        </div>

        <div class="field">
          <label>Max Build Height</label>
          <input type="number" bind:value={props['max-build-height']} oninput={markChanged} min="64" max="320" />
        </div>

        <div class="field toggle-field">
          <label>Spawn NPCs</label>
          <button class="toggle" class:on={props['spawn-npcs'] === 'true'} onclick={() => toggle('spawn-npcs')} aria-label="Toggle Spawn NPCs">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Spawn Animals</label>
          <button class="toggle" class:on={props['spawn-animals'] === 'true'} onclick={() => toggle('spawn-animals')} aria-label="Toggle Spawn Animals">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Spawn Monsters</label>
          <button class="toggle" class:on={props['spawn-monsters'] === 'true'} onclick={() => toggle('spawn-monsters')} aria-label="Toggle Spawn Monsters">
            <div class="toggle-knob"></div>
          </button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">Server</div>
      <div class="settings-grid">
        <div class="field toggle-field">
          <label>White-list</label>
          <button class="toggle" class:on={props['white-list'] === 'true'} onclick={() => toggle('white-list')} aria-label="Toggle White-list">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Command Blocks</label>
          <button class="toggle" class:on={props['enable-command-block'] === 'true'} onclick={() => toggle('enable-command-block')} aria-label="Toggle Command Blocks">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field">
          <label>Op Permission Level</label>
          <select bind:value={props['op-permission-level']} onchange={markChanged}>
            {#each PERM_LEVEL_OPTIONS as opt}
              <option value={opt.value}>{opt.label}</option>
            {/each}
          </select>
        </div>

        <div class="field">
          <label>Player Idle Timeout</label>
          <input type="number" bind:value={props['player-idle-timeout']} oninput={markChanged} min="0" placeholder="0 = no limit" />
        </div>

        <div class="field toggle-field">
          <label>Enable RCON</label>
          <button class="toggle" class:on={props['enable-rcon'] === 'true'} onclick={() => toggle('enable-rcon')} aria-label="Toggle RCON">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field">
          <label>RCON Port</label>
          <input type="number" bind:value={props['rcon.port']} oninput={markChanged} min="1" max="65535" />
        </div>

        <div class="field">
          <label>RCON Password</label>
          <input type="text" bind:value={props['rcon.password']} oninput={markChanged} placeholder="(empty)" />
        </div>

        <div class="field toggle-field">
          <label>Enable Query</label>
          <button class="toggle" class:on={props['enable-query'] === 'true'} onclick={() => toggle('enable-query')} aria-label="Toggle Query">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field">
          <label>Query Port</label>
          <input type="number" bind:value={props['query.port']} oninput={markChanged} min="1" max="65535" />
        </div>

        <div class="field">
          <label>Server IP</label>
          <input type="text" bind:value={props['server-ip']} oninput={markChanged} placeholder="(bind to all)" />
        </div>

        <div class="field toggle-field">
          <label>Allow Flight</label>
          <button class="toggle" class:on={props['allow-flight'] === 'true'} onclick={() => toggle('allow-flight')} aria-label="Toggle Allow Flight">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Snooper Enabled</label>
          <button class="toggle" class:on={props['snooper-enabled'] === 'true'} onclick={() => toggle('snooper-enabled')} aria-label="Toggle Snooper">
            <div class="toggle-knob"></div>
          </button>
        </div>

        <div class="field toggle-field">
          <label>Announce Achievements</label>
          <button class="toggle" class:on={props['announce-player-achievements'] === 'true'} onclick={() => toggle('announce-player-achievements')} aria-label="Toggle Announce Achievements">
            <div class="toggle-knob"></div>
          </button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">Performance</div>
      <div class="settings-grid">
        <div class="field">
          <label>View Distance</label>
          <input type="number" bind:value={props['view-distance']} oninput={markChanged} min="2" max="32" />
        </div>

        <div class="field">
          <label>Network Compression</label>
          <input type="number" bind:value={props['network-compression-threshold']} oninput={markChanged} min="-1" placeholder="-1 = disable" />
        </div>

        <div class="field">
          <label>Max World Size</label>
          <input type="number" bind:value={props['max-world-size']} oninput={markChanged} min="1" max="29999984" />
        </div>

        <div class="field">
          <label>Max Tick Time</label>
          <input type="number" bind:value={props['max-tick-time']} oninput={markChanged} min="0" placeholder="-1 = no watchdog" />
        </div>

        <div class="field">
          <label>Entity Broadcast Range</label>
          <input type="number" bind:value={props['entity-broadcast-range-percentage']} oninput={markChanged} min="10" max="1000" />
        </div>
      </div>
    </div>
  </div>

  <div class="save-row">
    <button class="save-btn" onclick={saveChanges} disabled={!changed || saving}>
      <Save size={16} />
      <span>{saving ? 'Saving...' : 'Save Changes'}</span>
    </button>
    <span class="unsaved-hint">{changed ? '* Unsaved changes' : ''}</span>
  </div>

  {#if showPopup}
    <div class="popup-overlay" role="button" tabindex="-1" onclick={() => showPopup = false}>
      <div class="popup" onclick={(e) => e.stopPropagation()}>
        <div class="popup-icon">
          <RotateCw size={24} />
        </div>
        <h3>Changes Saved</h3>
        {#if server.current_status === 'ONLINE'}
          <p>
            Some settings require a server restart to take effect.<br />
            The server will <strong>not</strong> restart automatically.
          </p>
        {:else}
          <p>All changes have been applied.</p>
        {/if}
        <button class="popup-btn" onclick={() => showPopup = false}>OK</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .loading-indicator {
    color: #888;
    font-size: 0.8rem;
    font-family: 'Inter', sans-serif;
    padding: 8px 0;
  }

  .settings-page {
    display: flex;
    flex-direction: column;
    gap: 16px;
    width: 100%;
    height: 100%;
  }

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .header-info h2 {
    margin: 0;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    color: white;
  }

  .header-info .server-name {
    font-size: 0.85rem;
    color: #666;
    font-family: 'Inter', sans-serif;
  }

  .header-status {
    display: flex;
    align-items: center;
  }

  .icon-status {
    font-size: 0.75rem;
    font-family: 'Inter', sans-serif;
  }

  .icon-status.uploading {
    color: #ffaa00;
  }

  .icon-status.error {
    color: #ff371d;
  }

  .icon-area {
    display: flex;
    align-items: center;
    gap: 8px;
    position: relative;
  }

  .icon-input {
    display: none;
  }

  .server-icon {
    width: 64px;
    height: 64px;
    border-radius: 8px;
    object-fit: cover;
    border: 2px solid #242424;
  }

  .icon-placeholder {
    width: 64px;
    height: 64px;
    border-radius: 8px;
    border: 2px dashed #333;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #555;
    background: #0a0a0a;
  }

  .icon-actions {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .icon-btn {
    background: #242424;
    border: 1px solid #333;
    color: #aaa;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .icon-btn:hover:not(:disabled) {
    background: #333;
    color: #00ff66;
    border-color: #0d5529;
  }

  .icon-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .sections-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 16px;
    flex: 1;
    min-height: 0;
  }

  .card {
    background-color: #111;
    border: 1px solid #242424;
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }

  .section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #00ff66;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #242424;
    flex-shrink: 0;
  }

  .settings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    flex: 1;
    align-content: start;
  }

  .full-width {
    grid-column: span 2;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .field label {
    font-size: 0.65rem;
    color: #888;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .field input[type="text"],
  .field input[type="number"],
  .field select {
    width: 100%;
    background: #0a0a0a;
    border: 1px solid #333;
    color: #eee;
    padding: 6px 8px;
    font-size: 0.8rem;
    border-radius: 5px;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
    font-family: 'Inter', sans-serif;
  }

  .field input:focus,
  .field select:focus {
    border-color: #00ff66;
  }

  .field select {
    cursor: pointer;
  }

  .toggle-field {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 2px 0;
  }

  .toggle {
    width: 40px;
    height: 22px;
    border-radius: 11px;
    border: none;
    background: #242424;
    cursor: pointer;
    position: relative;
    transition: background 0.2s;
    padding: 0;
    flex-shrink: 0;
  }

  .toggle.on {
    background: #00ff66;
  }

  .toggle-knob {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #555;
    position: absolute;
    top: 3px;
    left: 3px;
    transition: all 0.2s;
  }

  .toggle.on .toggle-knob {
    background: #000;
    left: 21px;
  }

  .save-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 8px 0 4px;
  }

  .save-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #00ff66;
    color: #000;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
  }

  .save-btn:hover:not(:disabled) {
    background: #00cc52;
  }

  .save-btn:disabled {
    background: #242424;
    color: #555;
    cursor: not-allowed;
  }

  .unsaved-hint {
    font-size: 0.75rem;
    color: #ffaa00;
    font-family: 'JetBrains Mono', monospace;
  }

  .popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    z-index: 9999;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .popup {
    background: #0a0a0a;
    border: 1px solid #242424;
    border-radius: 12px;
    padding: 32px;
    width: 400px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  }

  .popup-icon {
    color: #ffaa00;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffaa001a;
    border-radius: 50%;
  }

  .popup h3 {
    margin: 0;
    font-family: 'Space Grotesk', sans-serif;
    color: white;
    font-size: 1.1rem;
  }

  .popup p {
    margin: 0;
    color: #888;
    font-size: 0.85rem;
    line-height: 1.6;
    font-family: 'Inter', sans-serif;
  }

  .popup-btn {
    background: #00ff66;
    color: #000;
    border: none;
    padding: 10px 32px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background 0.2s;
    margin-top: 8px;
  }

  .popup-btn:hover {
    background: #00cc52;
  }
</style>
