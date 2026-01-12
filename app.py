from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from schemas import *
import manager
from exceptions import *
import asyncio
## this is just barebones, WIP.


app = FastAPI()
serverManager = manager.MinecraftServerManager()


@app.websocket("/servers/{server_id}/players")
async def online_players(websocket : WebSocket, server_id : str):
    await websocket.accept()
    
    try:
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e: 
        await websocket.close(404, "Server Instance not found.")
    if not instance.server or instance.status != "ONLINE":
        await websocket.close(404, "Server Instance not online.")
    
    last_status = None
    
    while True:
        try:
            players = await run_in_threadpool(instance.get_players)
            if last_status != players:
                last_status = players
                await websocket.send_json(players)
            await asyncio.sleep(5.0)
        except Exception as e:
            print(f"something broke the websocket : {e}")
            break

@app.get("/servers")
async def get_instances():
    all_instances = [instance.to_dict() for instance in serverManager.instances.values()]
    return all_instances

@app.get("/online_servers")
async def get_online_instances():
    all_online_instances  = [instance.to_dict() for instance in serverManager.instances.values() if instance.status == "ONLINE"]
    return all_online_instances    

@app.get("/")
async def root():
    return RedirectResponse("/docs")

@app.post("/servers/{server_id}/run")
async def run_command(cmd : ServerCommand, server_id):
    try:
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e: 
        raise HTTPException(404, "Server Instance not found")
    
    if instance.status != "ONLINE": raise HTTPException(400, "Couldn't run command. Server is OFFLINE. ")
    
    instance.run_cmd(cmd.cmd)
    return {"msg": "Command sent", "command":f"{cmd.cmd}"}


@app.post("/servers/{server_id}/start")
async def startServer(server_id : str):
    try:
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e: 
        raise HTTPException(404, "Server Instance not found")
    
    if instance.status == "ONLINE" or instance.status == "STARTING":
        raise HTTPException(400, "Server Instance is already running.")
    
    try: instance.start_server()
    except Exception as e : 
        raise HTTPException(500, f"{e}")
    
    return {"msg":f"Server Instance with id : {server_id} is now running!"}

@app.post("/servers/create")
def create_server(request: CreateServerRequest):
    try: new_server = serverManager.create_server(ram_max=request.ram_max, mc_version=request.mc_version, server_type=request.server_type, java_version = str(request.java_version) )
    except Exception as e:
        raise HTTPException(500, f"{e}")
    return {"msg": f"New server instance for version {request.mc_version} {request.server_type} has been created.", "id": new_server.id}
    