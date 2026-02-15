<script>
    import { appState } from '../stores.svelte'; 
    import { onMount } from 'svelte';
    import { Users, Power, Settings} from 'lucide-svelte';


    let server = $props();

    let metrics = $state({
        cpu: 0,
        ram_mb: 0,
        players: 0,
        online: server.current_status || "OFFLINE"
    });

    let ws = null;

    onMount(() => {
    if (metrics.online === "ONLINE") {
        connect_websocket();
    }
    
    return () => {
        if (ws) {
            ws.onclose = null;
            ws.close();
        }
    };
});

    async function toggle_server() {
        if (metrics.online == "ONLINE") {

            try {
                const res = await fetch(`http://127.0.0.1:8000/servers/${server.id}/stop/`, {method:"POST"});
                if (res.ok){
                    metrics.online = "CLOSING";
                } else {
                    metrics.online == true
                }
            } catch (error) {
                console.error("Error starting server:", error);
                metrics.online == true
            }
          
        } else {
            try {
                const res = await fetch(`http://127.0.0.1:8000/servers/${server.id}/start`, {method:"POST"});
                if (res.ok){
                    metrics.online = "STARTING";
                    connect_websocket();
                }
            } catch (error) {
                console.error("Error starting server:", error);
                metrics.online = "OFFLINE"
            }
        
        }
        }

 

    function connect_websocket() {
        const protocol = window.location.protocol === "HTTPS" ? "wss:" : "ws:";
        ws = new WebSocket(`${protocol}//127.0.0.1:8000/servers/${server.id}/metrics`);

        ws.onopen = () => {
            metrics.online = "STARTING"
        }
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            metrics.online = data.status
            metrics.cpu = data.resources.cpu_usage || 0;
            metrics.ram_mb = data.resources.ram_mb || 0;
            metrics.players = data.players ? data.players.length : 0;
            if (metrics.online === "OFFLINE" || metrics.online === "CRASHED") {
                console.log(`Server reported ${metrics.online}, closing WS from frontend.`);
                ws.close(); 
            }
        };

        ws.onclose = () => {
            console.log(`Connection lost for ${server.id}`);
            metrics.cpu = 0;
            metrics.ram_mb = 0;
            metrics.players = 0;
            metrics.online = "OFFLINE";
        };

        ws.onerror = () => {
            console.log(`Connection lost for ${server.id}`);
            metrics.cpu = 0;
            metrics.ram_mb = 0;
            metrics.players = 0;
            metrics.online = "OFFLINE";
        }
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
        
        {#if metrics.online == "OFFLINE"}
            <div class="status-badge">
                <div class="dot"></div>
                {metrics.online}
            </div>
        {:else if metrics.online== "ONLINE"}
            <div class="status-badge" class:online = {true}>
                <div class="dot"></div>
                {metrics.online}
            </div>
        {:else}
            <div class="status-badge" class:loading={true}>
                <div class="dot"></div>
                {metrics.online}
            </div>
        {/if}
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
            {#if metrics.online == "OFFLINE"}
                <button id="power_button" class="power-button" onclick={() => toggle_server()}>
                    <Power size={16} />
                </button>
            {:else if metrics.online== "ONLINE"}
                <button id="power_button" class="power-button" class:on={true} onclick={() => toggle_server()}>
                    <Power size={16} />
                </button>
            {:else}
                <button id="power_button" class="power-button" class:loading={true}>
                    <Power size={16} />
                </button>
            {/if}

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
        border-color: #eeeeee9c;
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
        background: #ff00001a;
        border: 1px solid #ff16165e;
        color: #ff1616;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        transition: all 0.2s ease-in-out;
    }

    .status-badge.online {
        background: #00ff661a;
        color: #00ff66;
        border-color: #00ff664d;
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
        box-shadow: 0 0 4px #00ff6680;
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
        background: #00ff661a;
        color: #00ff66;
        border: 1px solid #00ff664d;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        font-size: 0.85rem;
        transition: all 0.2s;
    }

    .power-button:hover{
        background: #00ff66;
        color: #000;
    }

    .power-button.on:hover {
        background: #ff371d;
        color: #fff;
    }

    .power-button.on {
        color : #ff1616;
        background: #ff00001a;
        border: 1px solid #ff16165e;
        
    }

    .status-badge.loading {
        background: #ffaa001a;
        color: #ffaa00;
        border-color: #ffaa004d;
    }

    .power-button.loading {
        color: #ffaa00;
        background: #ffaa001a;
        border: 1px solid #ffaa004d;
        cursor: not-allowed;
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