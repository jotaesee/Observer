from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from collections import deque
from schemas import *
import manager, configparser
from exceptions import *
import asyncio
from services import get_available_versions
## this is just barebones, WIP.


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # La dirección de tu frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permitir GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)

serverManager = manager.MinecraftServerManager()


@app.websocket("/servers/{server_id}/metrics")
async def online_players(websocket : WebSocket, server_id : str):
    await websocket.accept()
    
    try:
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e: 
        await websocket.close(1000, "Server Instance not found.")
        return
    if not instance.server or instance.status == "OFFLINE" or instance.status == "CRASHED":
        await websocket.close(1000, "Server Instance not running.")
        return
    
    
    while True:
        try:
            
            if instance.status == "OFFLINE" or instance.status == "CRASHED": 
                await websocket.close(1000, "server shutdown, closing connection.")
                break
            
            players = await run_in_threadpool(instance.get_players)
            resources = await run_in_threadpool(instance.get_resource_stats)
            uptime_seconds = await run_in_threadpool(instance.get_uptime)
            await websocket.send_json({"players": players, "resources" : resources, "status" : instance.status, "uptime_seconds" : uptime_seconds},)
            
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
                await websocket.close(1011, f"something broke the websocket : {e}")
            except:
                pass
            break
        
@app.websocket("/servers/{server_id}/console")
async def real_time_console(websocket : WebSocket, server_id):
    await websocket.accept()
        
    try:
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e: 
        await websocket.close(1000, "Server Instance not found.")
        return
    if not instance.server or instance.status == "OFFLINE":
        await websocket.close(1000, "Server Instance not online.")
        return
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
                    
                        
            if instance.status in ["OFFLINE", "CRASHED"] : 
                await websocket.close(1000, "server shutdown, closing connection.")
                break

        except WebSocketDisconnect:
            print(f"Client disconnected from server {server_id}")
            break
        except Exception as e:
            print(f"something broke the websocket : {e}")
            try:
                await websocket.close(1011, f"something broke the websocket : {e}")
            except:
                pass
            break     
               
@app.get("/versions") 
async def get_versions():
    return get_available_versions()

@app.get("/servers")
async def get_instances():
    all_instances = [instance.to_dict() for instance in serverManager.instances.values()]
    return all_instances

@app.get("/servers/{server_id}/status")
async def get_server_status(server_id):
    server_instance = serverManager.get_instace_by_id(server_id)    
    return server_instance.status

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

@app.post("/servers/{server_id}/stop")
async def stopServer(server_id : str):
    try:
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e: 
        raise HTTPException(404, "Server Instance not found")
    
    if instance.status == "OFFLINE" or instance.status == "CLOSING":
        print(instance.status)
        raise HTTPException(400, "Server Instance is already offline.")
    
    try: 
        instance.stop()
    except Exception as e : 
        raise HTTPException(500, f"{e}")
    
    return {"msg":f"Server Instance with id : {server_id} is now offline!"}

@app.post("/servers/create")
def create_server(request: CreateServerRequest):
    try: 
        request_dict = request.model_dump()
        new_server = serverManager.create_server(**request_dict)
    except Exception as e:
        raise HTTPException(500, f"{e}")
    return {"msg": f"New server instance for version {request.mc_version} {request.server_type} has been created.", "id": new_server.id}
    

@app.get("/servers/{server_id}/properties")
def get_properties_by_id(server_id):
    try:
        instance = serverManager.get_instace_by_id(server_id)
        config = instance.get_properties()
        print(dict(config[configparser.UNNAMED_SECTION]))
        return dict(config[configparser.UNNAMED_SECTION])
    except InstanceNotFoundError as e: 
        raise HTTPException(404, e)
    
@app.put("/servers/{server_id}/properties")
def update_properties(server_id, new_config : dict):
    try: 
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e : 
        raise HTTPException(404, e)
    
    current_config = instance.get_properties()
    current_config[configparser.UNNAMED_SECTION].update(new_config)

    path = instance.cwd / "server.properties"
    with open(path, "w") as properties_file : 
        current_config.write(properties_file)
    
    return {"msg" : "properties updated"}


@app.get("/servers/{server_id}/icon")
def get_server_icon(server_id) : 
    try: 
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e : 
        raise HTTPException(404, e)
    
    icon = instance.get_icon()
    if icon != None : return FileResponse(icon)
    else: raise HTTPException(404, "No icon available.")

@app.post("/servers/{server_id}/icon")
async def upload_icon(server_id, icon : UploadFile = File(...)) : 
    try: 
        instance = serverManager.get_instace_by_id(server_id)
    except InstanceNotFoundError as e : 
        raise HTTPException(404, e)
    
    if not icon.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image.")
    
    content = await icon.read()
    path = instance.cwd / "server-icon.png"
    with open(path, "wb") as image : 
        image.write(content)
    return {"msg": "Icon uploaded."}

