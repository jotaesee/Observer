<script>
    import { appState } from '../stores.svelte'; 
    import { Users, Power, Settings } from 'lucide-svelte';


    let server = $props();

    let metrics = $state({
        cpu: 0,
        ram_mb: 0,
        players: 0,
        online: server.current_status === "ONLINE"
    });

    let ws = null;

    $effect(() => {
        if (metrics.online) {
            connect_websocket();
        }
        return () => {
            if (ws) ws.close();
        };
    });

    async function toggle_server() {
        if (metrics.online) {

            try {
                const res = await fetch(`http://127.0.0.1:8000/servers/${server.id}/stop/`, {method:"POST"});
                if (res.ok){
                    metrics.online = false;
                }
            } catch (error) {
                console.error("Error starting server:", error);
            }
          
        } else {
            try {
                const res = await fetch(`http://127.0.0.1:8000/servers/${server.id}/start`, {method:"POST"});
                if (res.ok){
                    metrics.online = true;
                }
            } catch (error) {
                console.error("Error starting server:", error);
            }
        
        }
        }

 

    function connect_websocket() {
        const protocol = window.location.protocol === "HTTPS" ? "wss" : "ws";
        ws = new WebSocket(`${protocol}//127.0.0.1:8000/servers/${server.id}/players`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            metrics.cpu = data.resources.cpu_usage || 0;
            metrics.ram_mb = data.resources.ram_mb || 0;
            metrics.players = data.players ? data.players.length : 0;
        };

        ws.onclose = () => {
            console.log(`Connection lost for ${server.id}`);
            metrics.online = false;
        };
    }

    function getSegments(percentage) {
        // devuelve un array de 10 booleanos para dibujar los cuadraditoss
        const activeCount = Math.round(percentage / 10);
        return Array(10).fill(false).map((_, i) => i < activeCount);
    }
</script>

<div class="card">
    <div class="card-header">
        <div class="server-info">
            <h3>{server.id}</h3>
            <span class="version">{server.server_type} {server.mc_version} </span>
        </div>
        
        <div class="status-badge" class:online={metrics.online}>
            <div class="dot"></div>
            {metrics.online ? 'ONLINE' : 'OFFLINE'}
        </div>
    </div>

    <div class="metrics-grid">
        
        <div class="metric-row">
            <span class="metric-label">CPU</span>
            <div class="bar-container">
                {#each getSegments(metrics.cpu) as active}
                    <div class="segment" class:active={active}></div>
                {/each}
            </div>
            <span class="value-label">{metrics.cpu.toFixed(1)}%</span>
        </div>

        <div class="metric-row">
            <span class="metric-label">RAM</span>
            <div class="bar-container">
                {#each getSegments((metrics.ram_mb / 4096) * 100) as active}
                    <div class="segment" class:active={active}></div>
                {/each}
            </div>
            <span class="value-label">{(metrics.ram_mb / 1024).toFixed(1)} GB</span>
        </div>

    </div>

    <div class="card-footer">
        <div class="player-count">
            <Users size={16} />
            <span>{metrics.players}</span>
        </div>

        <div class = "button-container">
            <button class="manage-button" onclick={() => appState.select_server(server.id)}>
                <Settings size={16} />
            </button>
            <button id="power_button" class="power-button" onclick={() => toggle_server()}>
                <Power size={16} />
            </button>
        </div>
    </div>
</div>

<style>
    .card {
        background-color: #111;
        border: 1px solid #242424;
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 20px;
        transition: transform 0.2s, border-color 0.2s;
    }

    .card:hover {
        border-color: #eeeeee;
    }

    .card-header {
        display: flex;
        gap: 50px;
        justify-content: space-between;
        align-items: flex-start;
    }

    .server-info h3 {
        margin: 0;
        font-family: 'Space Grotesk', sans-serif;
        color: white;
        font-size: 1.1rem;
    }

    .version {
        font-size: 0.8rem;
        color: #666;
        font-family: 'Inter', sans-serif;
    }

    .status-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.7rem;
        padding: 4px 8px;
        border-radius: 20px;
        background: #1a1a1a;
        color: #666;
        border: 1px solid #333;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    .status-badge.online {
        background: rgba(0, 255, 102, 0.1);
        color: #00ff66;
        border-color: rgba(0, 255, 102, 0.3);
    }

    .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: currentColor;
    }

    .metrics-grid {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .metric-row {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
    }


    .bar-container {
        flex-grow: 1;
        display: flex;
        gap: 2px;
        height: 8px;
    }

    .segment {
        flex: 1;
        background-color: #242424;
        border-radius: 1px;
    }

    .segment.active {
        background-color: #00ff66;
        box-shadow: 0 0 4px rgba(0, 255, 102, 0.5);
    }

    
    .metric-label { color: #fff; width: 30px; }
    .value-label { color: #fff; width: 50px; text-align: left; }
    
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: auto;
    }

    .player-count {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #888;
        font-size: 0.9rem;
    }

    .button-container{
        display: flex;
        gap: 20px;
    }
    
    .power-button {
        background: #00ff66;
        color: #000;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        font-size: 0.85rem;
        transition: all 0.2s;
    }


    .manage-button {
        background: #aaaaaa;
        color: #000;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        font-size: 0.85rem;
        transition: all 0.2s;
    }

    .manage-button:hover {
        background: #eee;
    }
</style>