<script>
  import { appState } from "../stores.svelte";
  import Logo from './Logo.svelte';
  import {Activity, User, Users, ChartArea, Settings, Database, SquareTerminal, FolderOpen, Power, Plus, HouseIcon } from 'lucide-svelte';
  
  let main_menu = [
  { id: "instances", text: "Instances", icon : Database},
  { id: "analytics", text: "Analytics", icon : ChartArea},
  { id: "settings", text: "Settings", icon : Settings},
  { id: "account", text: "Account", icon : User}
  ]

  let instance_menu = [
    { id: "dashboard", text: "Dashboard", icon : Activity},
    { id: "console", text: "Console", icon : SquareTerminal},
    { id: "players", text: "Players", icon : Users},
    { id: "files", text: "Files", icon : FolderOpen},
    { id: "settings", text: "Settings", icon : Settings}
  ]


</script>

<aside class="sidebar">

  <div class="sidebar-header">
    <div class="brand-container">
      <div class = "logo">
        <Logo size={60} color="currentColor" />
      </div>
      <div class="title-text">
        <span>Observer</span>
        <span class="subtitle">SERVER // MANAGER</span>
      </div>
    </div>
  </div>

  <nav class="sidebar-nav">
    {#if appState.selected_server}
      <button class="create-button" onclick={() => {appState.go_home()}}>
      <div class = "icon">
        <HouseIcon size={20}/>
      </div>
        <p>Home</p> 
      </button>
    {:else}
      <button class="create-button">
      <div class = "icon">
        <Plus size={20}/>
      </div>
        New Instance 
      </button>
    {/if}

    {#if appState.selected_server}
        {#each instance_menu as item }
        <button class = "menu-item"  onclick={() => appState.select_section(item.id)}  class:selected={appState.selected_section === item.id}>
          <div class = "icon">
            <svelte:component this={item.icon} size={20}></svelte:component>
          </div>  
          <p>{item.text}</p>
        </button>
        {/each}    
    {:else}
        {#each main_menu as item }
        <button class = "menu-item" onclick={() => appState.select_section(item.id)} class:selected={appState.selected_section === item.id}>
          <div class = "icon">
            <svelte:component this={item.icon} size={20}></svelte:component>  
          </div>
          <p>{item.text}</p>
        </button>
        {/each}
    {/if}

  </nav>

  <div class="sidebar-footer">
    <button class="logout-button">
      <div class = "icon">
        <svelte:component this={Power} size={20}></svelte:component>
      </div>
      <p>Logout</p>
    </button>
  </div>
</aside>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@500;700;900');
  .sidebar-header{
    margin-top: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .brand-container {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .title-text{
    font-family: 'Orbitron', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    display: flex;
    flex-direction: column;
    letter-spacing: 1px;
  }

  .title-text .subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: #00ff66;
    letter-spacing: 2px;
    opacity: 0.8;
  }

  .logo {
        display: flex;
        justify-content: center;
        color: white; 
        transition: color 0.3s ease;
        width: min-content;
        height: min-content;
    }

    .logo:hover {
        color: #00ff66;
    }

  button.create-button{

    height: 60px;
    background: none;
    border: none;
    border-radius: 12px;
    padding: 10px 15px;
    position: relative;
    width: 100%;
    cursor: pointer;
    color: #112b1b;
    background-color: #00ff66f5;
    border: 1px solid #242424;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 5px;
    transition: background-color 0.3s ease, transform 0.2s ease;
  }

  button.create-button:hover{
    color: #112b1b;
    background-color: #aaffcc;
    transform: translateY(-2px);
  }

  button.logout-button{
    height: 5vh;
    background: none;
    border: none;
    border-radius: 12px;
    padding: 10px 15px;
    position: relative;
    width: 80%;
    cursor: pointer;
    color: #a3a3a3;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 5px;
    transition: background-color 0.3s ease, transform 0.2s ease;
  }

  button.logout-button:hover{
    color: #cf8080;
    background-color: #571616;
    transform: translateY(-2px);
  }

  .icon{
    position: absolute;
    left: 15px;
    display: flex;
    align-items: center; 
    top: 50%;
    transform: translateY(-50%);
  }

  button.menu-item.selected::before {
    content: "";
    position: absolute;
    left: -10px;
    top: 0;
    bottom: 0;
    width: 3px;
    background-color: #00ff66;
    border-radius: 12px;
  }

  .sidebar {
    width: 300px;
    height: 100vh;
    background-color: #141414;
    display: flex;
    flex-direction: column;
    border: 1px solid #242424;
  }

  .sidebar-footer{
    display: flex;
    justify-content: center;
  }

  button.menu-item {
    height: 60px;
    background: none;
    border: none;
    border-radius: 12px;
    padding: 10px 15px;
    position: relative;
    width: 100%;
    cursor: pointer;
    color: #a3a3a3;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 5px;
    transition: background-color 0.3s ease, transform 0.2s ease;
  }

  button.selected {
    color: #00ff66;
    background-color: #112b1b;
    display: flex;
    align-items: center;
    justify-content:center;
    margin: 5px;
    border: 1px solid #0d5529;
    border-radius: 12px;
    position: relative;
  }

  button.menu-item:not(.selected):hover {
    color: #fff;
    background-color: #333333;
    transform: translateY(-2px);
  } 
  
  .sidebar-nav {
    flex-grow: 1;
    padding: 20px;
  }
</style>