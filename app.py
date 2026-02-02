from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from collections import deque
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
    
    
    while True:
        try:
            
            if instance.status != "ONLINE" : 
                await websocket.close(200, "server shutdown, closing connection.")
                break
            
            players = await run_in_threadpool(instance.get_players)
            resources = await run_in_threadpool(instance.get_resource_stats)
            await websocket.send_json({"players": players, "resources" : resources},)
            
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            except asyncio.TimeoutError:
                pass
                
        except WebSocketDisconnect:
            print(f"Client disconnected from server {server_id}")
            break
        except Exception as e:
            print(f"something broke the websocket : {e}")
            try:
                await websocket.close(400, f"something broke the websocket : {e}")
            except:
                pass
            break
        
@app.websocket("/servers/{server_id}/console")
async def real_time_console(websocket : WebSocket, server_id):
    await websocket.accept()
        
    try:
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e: 
        await websocket.close(404, "Server Instance not found.")
        
    if not instance.server or instance.status != "ONLINE" or instance.status != "STARTING":
        await websocket.close(404, "Server Instance not online.")
    
    log_number_read = 0
    
    while True:
        try: 
            data = instance.console_entries.copy()
            
            if not data or data[-1][0] <= log_number_read:
               await asyncio.sleep(0.1)
            else:
                new_logs = []
                for log_id, log_text in data : 
                    if log_id > log_number_read :
                        log_number_read = log_id
                        new_logs.append(log_text)

                for log in new_logs: 
                    await websocket.send_text(log)
                    
                        
            if instance.status != "ONLINE" : 
                await websocket.close(200, "server shutdown, closing connection.")
                break

        except WebSocketDisconnect:
            print(f"Client disconnected from server {server_id}")
            break
        except Exception as e:
            print(f"something broke the websocket : {e}")
            try:
                await websocket.close(400, f"something broke the websocket : {e}")
            except:
                pass
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
    except PortInUseError : 
        raise HTTPException(403, "The server cannot be setup on this port, it is already being used. Try changing server.properties or stop other server")
    except Exception as e : 
        raise HTTPException(500, f"{e}")
    
    return {"msg":f"Server Instance with id : {server_id} is now running!"}

@app.post("/servers/create")
def create_server(request: CreateServerRequest):
    try: 
        request_dict = request.model_dump()
        new_server = serverManager.create_server(**request_dict)
    except Exception as e:
        raise HTTPException(500, f"{e}")
    return {"msg": f"New server instance for version {request.mc_version} {request.server_type} has been created.", "id": new_server.id}
    