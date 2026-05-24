<script>
  import { onMount, onDestroy } from 'svelte';
  import { WS_BASE, API_BASE } from './config';

  let { serverId } = $props();

  let logs = $state([]);
  let command = $state('');
  let connected = $state(false);
  let reconnecting = $state(false);
  let autoScroll = $state(true);
  let retryCount = $state(0);
  let maxLogs = 500;
  let commandHistory = $state([]);
  let historyIndex = $state(-1);
  let terminalEl = $state(null);
  let inputEl = $state(null);
  let ws = null;
  let reconnectTimer = null;
  let inputId = 0;

  const STATUS_COLORS = {
    connected: '#00ff66',
    reconnecting: '#ffaa00',
    disconnected: '#ff371d'
  };

  function parseMinecraftText(text) {
    const ansiMap = {
      '0': 'color: #000000', '1': 'color: #0000aa', '2': 'color: #00aa00',
      '3': 'color: #00aaaa', '4': 'color: #aa0000', '5': 'color: #aa00aa',
      '6': 'color: #ffaa00', '7': 'color: #aaaaaa', '8': 'color: #555555',
      '9': 'color: #5555ff', 'a': 'color: #55ff55', 'b': 'color: #55ffff',
      'c': 'color: #ff5555', 'd': 'color: #ff55ff', 'e': 'color: #ffff55',
      'f': 'color: #ffffff',
      'l': 'font-weight: bold', 'm': 'text-decoration: line-through',
      'n': 'text-decoration: underline', 'o': 'font-style: italic',
      'r': 'color: inherit; font-weight: normal; font-style: normal; text-decoration: none'
    };
    let openSpans = 0;
    let result = text.replace(/§([0-9a-fklmnor])/gi, (_, code) => {
      const style = ansiMap[code.toLowerCase()];
      if (!style) return '';
      const span = `<span style="${style}">`;
      openSpans++;
      return span;
    });
    result += '</span>'.repeat(openSpans);
    return result;
  }

  function formatTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour12: false });
  }

  function connect() {
    if (ws) {
      ws.onclose = null;
      ws.close();
    }

    ws = new WebSocket(`${WS_BASE}/servers/${serverId}/console`);

    ws.onopen = () => {
      connected = true;
      reconnecting = false;
      logs = [];
      inputId = 0;
      addLog('--- Console connected ---');
    };

    ws.onmessage = (event) => {
      retryCount = 0;
      addLog(event.data);
    };

    ws.onclose = () => {
      connected = false;
      if (!reconnecting) {
        addLog('--- Connection lost ---');
      }
      attemptReconnect();
    };

    ws.onerror = () => {
      if (!reconnecting) {
        addLog('--- Connection error ---');
      }
    };
  }

  function addLog(text) {
    inputId++;
    const entry = { id: inputId, text, html: parseMinecraftText(text), time: formatTime() };
    logs = [...logs, entry];
    if (logs.length > maxLogs) {
      logs = logs.slice(-maxLogs);
    }
  }

  function attemptReconnect() {
    if (reconnectTimer) return;
    reconnecting = true;
    retryCount++;

    let delay;
    if (retryCount <= 3) {
      delay = 2000 * Math.pow(2, retryCount - 1);
      addLog(`--- Reconnecting in ${delay / 1000}s (${retryCount}/3) ---`);
    } else {
      delay = 60000;
      addLog(`--- Retrying every 60s ---`);
    }

    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, delay);
  }

  async function sendCommand() {
    const trimmed = command.trim();
    if (!trimmed) return;

    addLog(`§e> §f${trimmed}`);
    commandHistory = [...commandHistory, trimmed];
    historyIndex = -1;

    try {
      const res = await fetch(`${API_BASE}/servers/${serverId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: trimmed })
      });
      if (!res.ok) {
        const err = await res.json();
        addLog(`§cCommand failed: ${err.detail || res.statusText}`);
      }
    } catch (e) {
      addLog(`§cNetwork error: ${e.message}`);
    }

    command = '';
  }

  function onKeydown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendCommand();
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length === 0) return;
      if (historyIndex === -1) {
        historyIndex = commandHistory.length - 1;
      } else if (historyIndex > 0) {
        historyIndex--;
      }
      command = commandHistory[historyIndex];
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex === -1) return;
      if (historyIndex < commandHistory.length - 1) {
        historyIndex++;
        command = commandHistory[historyIndex];
      } else {
        historyIndex = -1;
        command = '';
      }
      return;
    }
    historyIndex = -1;
  }

  function clearLogs() {
    logs = [];
    inputId = 0;
  }

  function scrollToBottom() {
    if (!autoScroll || !terminalEl) return;
    requestAnimationFrame(() => {
      terminalEl.scrollTop = terminalEl.scrollHeight;
    });
  }

  function handleScroll() {
    if (!terminalEl) return;
    const threshold = 50;
    const atBottom = terminalEl.scrollHeight - terminalEl.scrollTop - terminalEl.clientHeight < threshold;
    if (!atBottom && autoScroll) {
      autoScroll = false;
    }
  }

  $effect(() => {
    if (logs.length > 0) {
      scrollToBottom();
    }
  });

  $effect(() => {
    if (connected && inputEl) {
      inputEl.focus();
    }
  });

  onMount(() => {
    connect();
  });

  onDestroy(() => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
  });
</script>

<div class="console-wrapper">
  <div class="console-header">
    <div class="connection-status">
      <span
        class="status-dot"
        style="background-color: {connected ? STATUS_COLORS.connected : reconnecting ? STATUS_COLORS.reconnecting : STATUS_COLORS.disconnected}"
      ></span>
      <span class="status-text">
        {connected ? 'Connected' : reconnecting ? 'Reconnecting...' : 'Disconnected'}
      </span>
    </div>
    <div class="console-actions">
      <span class="log-count">{logs.length} lines</span>
      <button
        class="action-btn"
        class:active={autoScroll}
        onclick={() => { autoScroll = !autoScroll; if (autoScroll) scrollToBottom(); }}
        title="Toggle auto-scroll"
      >
        Auto-scroll
      </button>
      <button class="action-btn" onclick={clearLogs} title="Clear console">Clear</button>
    </div>
  </div>

  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="terminal"
    bind:this={terminalEl}
    onscroll={handleScroll}
    onclick={() => inputEl?.focus()}
  >
    {#if logs.length === 0}
      <div class="terminal-empty">Waiting for logs...</div>
    {/if}
    {#each logs as log (log.id)}
      <div class="log-line">
        <span class="log-time">[{log.time}]</span>
        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
        <span class="log-text" onclick={(e) => e.stopPropagation()}>{@html log.html}</span>
      </div>
    {/each}
  </div>

  <form class="input-bar" onsubmit={(e) => { e.preventDefault(); sendCommand(); }}>
    <span class="prompt">&gt;</span>
    <input
      bind:this={inputEl}
      type="text"
      bind:value={command}
      onkeydown={onKeydown}
      placeholder="Type a command..."
      disabled={!connected}
      autocomplete="off"
      spellcheck="false"
    />
    <button class="send-btn" type="submit" disabled={!connected || !command.trim()}>
      Send
    </button>
  </form>
</div>

<style>
  .console-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #0a0a0a;
    border: 1px solid #242424;
    border-radius: 8px;
    overflow: hidden;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  }

  .console-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 16px;
    background-color: #111;
    border-bottom: 1px solid #242424;
    flex-shrink: 0;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    color: #888;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    transition: background-color 0.3s ease;
  }

  .status-text {
    font-size: 0.75rem;
    color: #888;
  }

  .console-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .log-count {
    font-size: 0.7rem;
    color: #555;
  }

  .action-btn {
    background: transparent;
    border: 1px solid #333;
    color: #888;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.2s;
  }

  .action-btn:hover {
    background: #1a1a1a;
    color: #fff;
    border-color: #555;
  }

  .action-btn.active {
    background: #112b1b;
    color: #00ff66;
    border-color: #0d5529;
  }

  .terminal {
    flex-grow: 1;
    overflow-y: auto;
    padding: 12px 16px;
    background-color: #050505;
    cursor: text;
  }

  .terminal::-webkit-scrollbar {
    width: 6px;
  }

  .terminal::-webkit-scrollbar-track {
    background: #0a0a0a;
  }

  .terminal::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 3px;
  }

  .terminal::-webkit-scrollbar-thumb:hover {
    background: #555;
  }

  .terminal-empty {
    color: #444;
    font-size: 0.85rem;
    text-align: center;
    padding: 40px 0;
    font-style: italic;
  }

  .log-line {
    display: flex;
    gap: 8px;
    line-height: 1.6;
    font-size: 0.8rem;
    word-break: break-all;
  }

  .log-time {
    color: #555;
    flex-shrink: 0;
    user-select: none;
  }

  .log-text {
    color: #ccc;
  }

  .log-text :global(span) {
    white-space: pre-wrap;
  }

  .input-bar {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 8px 16px;
    background-color: #111;
    border-top: 1px solid #242424;
    flex-shrink: 0;
  }

  .prompt {
    color: #00ff66;
    font-size: 0.85rem;
    margin-right: 8px;
    user-select: none;
    font-weight: bold;
  }

  .input-bar input {
    flex-grow: 1;
    background: transparent;
    border: none;
    color: #eee;
    font-family: inherit;
    font-size: 0.85rem;
    outline: none;
    padding: 6px 0;
  }

  .input-bar input::placeholder {
    color: #444;
  }

  .input-bar input:disabled {
    color: #555;
  }

  .send-btn {
    background: #00ff66;
    color: #000;
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 0.75rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
    margin-left: 8px;
  }

  .send-btn:hover:not(:disabled) {
    background: #00cc52;
  }

  .send-btn:disabled {
    background: #242424;
    color: #555;
    cursor: not-allowed;
  }
</style>
