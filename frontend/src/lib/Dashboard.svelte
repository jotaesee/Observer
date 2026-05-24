<script>
  import { onMount, onDestroy } from 'svelte';
  import { WS_BASE, API_BASE } from './config';
  import { appState } from '../stores.svelte';
  import ServerProperties from './ServerProperties.svelte';
  import {
    Users, Power, RotateCw, Play, Square,
    Cpu, HardDrive, Clock, Terminal, Activity, X
  } from 'lucide-svelte';

  let { serverId } = $props();

  let server = $state(null);
  let loading = $state(true);

  let status = $state('OFFLINE');
  let cpu = $state(0);
  let ramMb = $state(0);
  let players = $state([]);
  let uptimeSeconds = $state(0);
  let maxRamMb = $state(4096);

  let logs = $state([]);
  let command = $state('');
  let logId = 0;
  let wsMetrics = null;
  let wsConsole = null;

  let dispUptime = $state(0);

  let formattedUptime = $derived(formatUptime(dispUptime));
  let playerCount = $derived(players.length);

  onMount(async () => {
    await fetchServerData();
    if (status === 'ONLINE') {
      connectMetrics();
      connectConsole();
    }
    return () => cleanup();
  });

  async function fetchServerData() {
    try {
      const res = await fetch(`${API_BASE}/servers`);
      const all = await res.json();
      const found = all.find(s => s.id === serverId);
      if (found) {
        server = found;
        status = found.current_status;
        maxRamMb = parseRamMax(found.ram_max);
      }
    } catch (e) {
      console.error('Failed to fetch server data', e);
    } finally {
      loading = false;
    }
  }

  function parseRamMax(ramMax) {
    const match = ramMax.match(/-Xmx(\d+)([MG])/);
    if (!match) return 4096;
    const val = parseInt(match[1]);
    return match[2] === 'G' ? val * 1024 : val;
  }

  function formatUptime(s) {
    if (s <= 0) return '--';
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = Math.floor(s % 60);
    if (h > 0) return `${h}h ${m}m ${sec}s`;
    if (m > 0) return `${m}m ${sec}s`;
    return `${sec}s`;
  }

  function connectMetrics() {
    if (wsMetrics) { wsMetrics.onclose = null; wsMetrics.close(); }
    wsMetrics = new WebSocket(`${WS_BASE}/servers/${serverId}/metrics`);

    wsMetrics.onmessage = (event) => {
      const data = JSON.parse(event.data);
      status = data.status;
      cpu = data.resources.cpu_usage || 0;
      ramMb = data.resources.ram_mb || 0;
      players = data.players || [];
      uptimeSeconds = data.uptime_seconds || 0;
      dispUptime = uptimeSeconds;
      if (data.status === 'OFFLINE' || data.status === 'CRASHED') {
        wsMetrics.close();
      }
    };

    wsMetrics.onclose = () => {
      if (status === 'ONLINE' || status === 'STARTING') {
        setTimeout(connectMetrics, 3000);
      }
    };
  }

  function connectConsole() {
    if (wsConsole) { wsConsole.onclose = null; wsConsole.close(); }
    wsConsole = new WebSocket(`${WS_BASE}/servers/${serverId}/console`);

    wsConsole.onmessage = (event) => {
      logId++;
      logs = [...logs, { id: logId, text: event.data }];
      if (logs.length > 50) logs = logs.slice(-50);
    };

    wsConsole.onclose = () => {
      if (status === 'ONLINE' || status === 'STARTING') {
        setTimeout(connectConsole, 3000);
      }
    };
  }

  $effect(() => {
    if (status !== 'ONLINE') return;
    const id = setInterval(() => { dispUptime++; }, 1000);
    return () => clearInterval(id);
  });

  async function startServer() {
    try {
      await fetch(`${API_BASE}/servers/${serverId}/start`, { method: 'POST' });
      status = 'STARTING';
      setTimeout(() => {
        connectMetrics();
        connectConsole();
      }, 2000);
    } catch (e) {
      console.error('Failed to start server', e);
    }
  }

  async function stopServer() {
    try {
      await fetch(`${API_BASE}/servers/${serverId}/stop`, { method: 'POST' });
      status = 'CLOSING';
    } catch (e) {
      console.error('Failed to stop server', e);
    }
  }

  async function restartServer() {
    try {
      await fetch(`${API_BASE}/servers/${serverId}/stop`, { method: 'POST' });
      status = 'CLOSING';

      const check = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/servers/${serverId}/status`);
          const s = await res.text();
          if (JSON.parse(s) === 'OFFLINE') {
            clearInterval(check);
            status = 'OFFLINE';
            await fetch(`${API_BASE}/servers/${serverId}/start`, { method: 'POST' });
            status = 'STARTING';
            setTimeout(() => {
              connectMetrics();
              connectConsole();
            }, 2000);
          }
        } catch (e) { /* ignore */ }
      }, 1000);

      setTimeout(() => clearInterval(check), 30000);
    } catch (e) {
      console.error('Failed to restart server', e);
    }
  }

  async function sendCommand() {
    const trimmed = command.trim();
    if (!trimmed) return;
    command = '';
    try {
      await fetch(`${API_BASE}/servers/${serverId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: trimmed })
      });
    } catch (e) {
      console.error('Command failed', e);
    }
  }

  function cleanup() {
    if (wsMetrics) { wsMetrics.onclose = null; wsMetrics.close(); }
    if (wsConsole) { wsConsole.onclose = null; wsConsole.close(); }
  }

  function getSegments(percentage) {
    const active = Math.round(Math.min(percentage, 100) / 10);
    return Array(10).fill(false).map((_, i) => i < active);
  }

  function statusClass(s) {
    if (s === 'ONLINE') return 'online';
    if (s === 'STARTING' || s === 'CLOSING') return 'loading';
    return 'offline';
  }

  function canPower(s) {
    return s === 'OFFLINE' || s === 'ONLINE';
  }
</script>

{#if loading}
  <div class="loading-state">Loading server data...</div>
{:else if !server}
  <div class="loading-state">Server not found</div>
{:else}
  <div class="dashboard">
    <!-- HEADER -->
    <div class="card header-card">
      <div class="header-left">
        <h2 class="server-name">{server.id}</h2>
        <span class="server-version">{server.server_type} {server.mc_version}</span>
      </div>
      <div class="header-right">
        <div class="status-badge" class:online={status === 'ONLINE'} class:loading={status === 'STARTING' || status === 'CLOSING'}>
          <div class="dot"></div>
          {status}
        </div>
        <div class="power-group">
          {#if status === 'OFFLINE'}
            <button class="power-btn start" onclick={startServer} title="Start">
              <Play size={16} />
            </button>
          {:else if status === 'ONLINE'}
            <button class="power-btn restart" onclick={restartServer} title="Restart">
              <RotateCw size={16} />
            </button>
            <button class="power-btn stop" onclick={stopServer} title="Stop">
              <Square size={16} />
            </button>
          {:else}
            <button class="power-btn disabled" disabled>
              <Activity size={16} />
            </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- RESTART BANNER -->
    {#if appState.restartRequired}
      <div class="restart-banner">
        <RotateCw size={14} />
        <span>Pending changes — Restart server to apply</span>
        <button class="banner-close" onclick={() => appState.dismissRestartNotice()}>
          <X size={14} />
        </button>
      </div>
    {/if}

    <!-- BENTO GRID -->
    <div class="bento-grid">
      <!-- RESOURCES -->
      <div class="card bento-card resources-card">
        <div class="card-title">
          <Cpu size={16} />
          <span>Resources</span>
        </div>
        <div class="metrics-list">
          <div class="metric-item">
            <div class="metric-header">
              <span class="metric-label">CPU</span>
              <span class="metric-value">{cpu.toFixed(1)}%</span>
            </div>
            <div class="bar-container">
              {#each getSegments(cpu) as active}
                <div class="segment" class:active={active}></div>
              {/each}
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-header">
              <span class="metric-label">RAM</span>
              <span class="metric-value">{(ramMb / 1024).toFixed(1)} GB</span>
            </div>
            <div class="bar-container">
              {#each getSegments((ramMb / maxRamMb) * 100) as active}
                <div class="segment" class:active={active}></div>
              {/each}
            </div>
            <span class="metric-sub">of {(maxRamMb / 1024).toFixed(0)} GB</span>
          </div>
          <div class="uptime-row">
            <Clock size={14} />
            <span class="uptime-label">Uptime</span>
            <span class="uptime-value">{formattedUptime}</span>
          </div>
        </div>
      </div>

      <!-- PLAYERS -->
      <div class="card bento-card players-card">
        <div class="card-title">
          <Users size={16} />
          <span>Players</span>
          {#if status === 'ONLINE'}
            <span class="count-badge">{playerCount}</span>
          {/if}
        </div>
        <div class="players-list">
          {#if status !== 'ONLINE'}
            <div class="empty-state">Server is offline</div>
          {:else if playerCount === 0}
            <div class="empty-state">No players online</div>
          {:else}
            {#each players as player}
              <div class="player-entry">
                <div class="player-dot"></div>
                <span class="player-name">{player}</span>
              </div>
            {/each}
          {/if}
        </div>
      </div>

      <!-- SERVER PROPERTIES -->
      <div class="card bento-card props-card">
        <ServerProperties {serverId} />
      </div>

      <!-- QUICK ACTIONS -->
      <div class="card bento-card actions-card">
        <div class="card-title">
          <Activity size={16} />
          <span>Quick Actions</span>
        </div>
        <div class="actions-row">
          <button class="action-btn primary" onclick={startServer} disabled={status !== 'OFFLINE'}>
            <Play size={16} />
            <span>Start</span>
          </button>
          <button class="action-btn warning" onclick={restartServer} disabled={status !== 'ONLINE'}>
            <RotateCw size={16} />
            <span>Restart</span>
          </button>
          <button class="action-btn danger" onclick={stopServer} disabled={status !== 'ONLINE'}>
            <Square size={16} />
            <span>Stop</span>
          </button>
        </div>
      </div>

      <!-- CONSOLE -->
      <div class="card bento-card console-card">
        <div class="card-title">
          <Terminal size={16} />
          <span>Console</span>
          <span class="log-count">{logs.length} lines</span>
        </div>
        <div class="console-output">
          {#if logs.length === 0}
            <div class="empty-state">Waiting for console output...</div>
          {:else}
            {#each logs as log (log.id)}
              <div class="console-line">{log.text}</div>
            {/each}
          {/if}
        </div>
        <form class="console-input" onsubmit={(e) => { e.preventDefault(); sendCommand(); }}>
          <span class="prompt">&gt;</span>
          <input
            type="text"
            bind:value={command}
            placeholder="Send a command..."
            disabled={status !== 'ONLINE'}
            autocomplete="off"
            spellcheck="false"
          />
          <button class="send-btn" type="submit" disabled={status !== 'ONLINE' || !command.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  </div>
{/if}

<style>
  .loading-state {
    color: #666;
    text-align: center;
    padding: 60px 0;
    font-family: 'Inter', sans-serif;
  }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 16px;
    width: 100%;
    height: 100%;
  }

  .card {
    background-color: #111;
    border: 1px solid #242424;
    border-radius: 12px;
    padding: 20px;
    transition: border-color 0.2s;
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
    margin-bottom: 16px;
  }

  /* HEADER */
  .header-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .server-name {
    margin: 0;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    color: white;
  }

  .server-version {
    font-size: 0.8rem;
    color: #666;
    font-family: 'Inter', sans-serif;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .status-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    padding: 4px 10px;
    border-radius: 20px;
    background: #ff00001a;
    border: 1px solid #ff16165e;
    color: #ff1616;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }

  .status-badge.online {
    background: #00ff661a;
    color: #00ff66;
    border-color: #00ff664d;
  }

  .status-badge.loading {
    background: #ffaa001a;
    color: #ffaa00;
    border-color: #ffaa004d;
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: currentColor;
  }

  .power-group {
    display: flex;
    gap: 8px;
  }

  .power-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 8px;
    border: 1px solid #333;
    background: transparent;
    cursor: pointer;
    transition: all 0.2s;
  }

  .power-btn.start { color: #00ff66; border-color: #00ff664d; }
  .power-btn.start:hover { background: #00ff66; color: #000; }

  .power-btn.restart { color: #ffaa00; border-color: #ffaa004d; }
  .power-btn.restart:hover { background: #ffaa00; color: #000; }

  .power-btn.stop { color: #ff371d; border-color: #ff371d5e; }
  .power-btn.stop:hover { background: #ff371d; color: #fff; }

  .power-btn.disabled { color: #555; border-color: #242424; cursor: not-allowed; }

  /* RESTART BANNER */
  .restart-banner {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    background: #ffaa001a;
    border: 1px solid #ffaa004d;
    border-radius: 8px;
    color: #ffaa00;
    font-size: 0.8rem;
    font-family: 'Inter', sans-serif;
  }

  .banner-close {
    margin-left: auto;
    background: transparent;
    border: none;
    color: #ffaa00;
    cursor: pointer;
    padding: 2px;
    opacity: 0.6;
    transition: opacity 0.2s;
  }

  .banner-close:hover {
    opacity: 1;
  }

  /* BENTO GRID */
  .bento-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    grid-template-rows: auto 1fr;
    gap: 16px;
    flex-grow: 1;
    min-height: 0;
  }

  .resources-card { grid-column: 1; grid-row: 1; }
  .players-card { grid-column: 2; grid-row: 1; }
  .props-card { grid-column: 3; grid-row: 1; }
  .props-card :global(.card) { border: none; padding: 0; background: transparent; }
  .actions-card { display: none; }
  .console-card { grid-column: 1 / -1; grid-row: 2; min-height: 0; }

  /* RESOURCES */
  .metrics-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .metric-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #aaa;
  }

  .metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #fff;
    font-weight: 600;
  }

  .metric-sub {
    font-size: 0.65rem;
    color: #555;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 2px;
  }

  .bar-container {
    display: flex;
    gap: 3px;
    height: 10px;
  }

  .segment {
    flex: 1;
    background-color: #242424;
    border-radius: 2px;
    transition: background-color 0.3s;
  }

  .segment.active {
    background-color: #00ff66;
    box-shadow: 0 0 4px #00ff6680;
  }

  .uptime-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-top: 8px;
    border-top: 1px solid #242424;
    color: #888;
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
  }

  .uptime-label {
    color: #888;
  }

  .uptime-value {
    color: #fff;
    font-weight: 600;
  }

  /* PLAYERS */
  .players-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 160px;
    overflow-y: auto;
  }

  .players-list::-webkit-scrollbar { width: 4px; }
  .players-list::-webkit-scrollbar-track { background: transparent; }
  .players-list::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }

  .count-badge {
    background: #112b1b;
    color: #00ff66;
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #0d5529;
    margin-left: auto;
  }

  .empty-state {
    color: #555;
    font-size: 0.8rem;
    font-style: italic;
    padding: 12px 0;
    text-align: center;
  }

  .player-entry {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 6px;
    background: #0a0a0a;
    border: 1px solid #1a1a1a;
  }

  .player-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #00ff66;
    flex-shrink: 0;
  }

  .player-name {
    font-size: 0.8rem;
    color: #ddd;
    font-family: 'JetBrains Mono', monospace;
  }

  /* QUICK ACTIONS */
  .actions-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    border: 1px solid #333;
    background: transparent;
    color: #aaa;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
    flex: 1;
    justify-content: center;
  }

  .action-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .action-btn.primary { border-color: #00ff664d; color: #00ff66; }
  .action-btn.primary:hover:not(:disabled) { background: #00ff66; color: #000; }

  .action-btn.warning { border-color: #ffaa004d; color: #ffaa00; }
  .action-btn.warning:hover:not(:disabled) { background: #ffaa00; color: #000; }

  .action-btn.danger { border-color: #ff371d5e; color: #ff371d; }
  .action-btn.danger:hover:not(:disabled) { background: #ff371d; color: #fff; }

  /* CONSOLE */
  .console-card {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .console-card .card-title {
    flex-shrink: 0;
  }

  .console-output {
    background: #050505;
    border: 1px solid #1a1a1a;
    border-radius: 8px;
    padding: 12px;
    flex-grow: 1;
    overflow-y: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    line-height: 1.5;
    min-height: 0;
  }

  .console-output::-webkit-scrollbar { width: 4px; }
  .console-output::-webkit-scrollbar-track { background: transparent; }
  .console-output::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }

  .console-line {
    color: #bbb;
    word-break: break-all;
    padding: 1px 0;
  }

  .log-count {
    font-size: 0.65rem;
    color: #555;
    margin-left: auto;
    text-transform: none;
    letter-spacing: 0;
  }

  .console-input {
    display: flex;
    align-items: center;
    gap: 0;
    margin-top: 12px;
    padding: 6px 12px;
    background: #0a0a0a;
    border: 1px solid #242424;
    border-radius: 8px;
  }

  .prompt {
    color: #00ff66;
    font-size: 0.85rem;
    font-weight: bold;
    margin-right: 8px;
    user-select: none;
  }

  .console-input input {
    flex-grow: 1;
    background: transparent;
    border: none;
    color: #eee;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    outline: none;
    padding: 6px 0;
  }

  .console-input input::placeholder { color: #444; }
  .console-input input:disabled { color: #555; }

  .send-btn {
    background: #00ff66;
    color: #000;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
  }

  .send-btn:hover:not(:disabled) { background: #00cc52; }
  .send-btn:disabled { background: #242424; color: #555; cursor: not-allowed; }
</style>
