import subprocess, threading, os, json
from pathlib import Path
import uuid
from services import JarManager, is_port_free
from exceptions import *
from mcstatus import JavaServer

default_storage_path = Path.home() / "Server Manager"

class MinecraftServerManager:

    def __init__(self) -> None:
        print("new server manager created")
        self.instances : dict[str, MinecraftInstance] = {} 
        self.load_servers_on_disk()
       
    pass


    def load_servers_on_disk(self):
        
        dirs = Path.iterdir(default_storage_path)
        
        for dir in dirs:
            if Path.exists(dir/"config.json"): 
                self.instances[dir.name] = MinecraftInstance(dir)

        print(self.instances)
    
            
    def create_server(self, ram_max = "-Xmx512M", mc_version = "1.16.22", server_type = "PAPER", java_version = "C:\\Program Files\\BellSoft\\LibericaJDK-14\\bin\\java.exe", cwd=default_storage_path):
        
        print("[OBS] [INFO] Creating new server folder...")
        
        new_pid = str(uuid.uuid4())
        while new_pid in self.instances:
            new_pid = str(uuid.uuid4())
            
        cwd = cwd / new_pid
        Path.mkdir(cwd, parents=True)
        
        eulastring = "eula=true"
        
        with open(cwd/"eula.txt", "w") as eula:
            eula.write(eulastring)
            
        print("[OBS] [INFO] EULA created and accepted.")
        
        config_json = {"id" : new_pid, "ram_max": ram_max, "mc_version" : mc_version, "server_type" : server_type, "java_version" : java_version, "cwd":str(cwd) }
        
        with open(cwd/"config.json", "w") as config:
            json.dump(config_json, config)
        
        
        server = MinecraftInstance(cwd)
        self.instances[new_pid] = server
        
        print("[OBS] [INFO] Server folder created, returning instance")
        return server
        
        
    def get_instace_by_id(self, id):
        if id in self.instances:
                return self.instances[id]
        else : raise InstanceNotFoundError("There's no instances with this ID")

class MinecraftInstance:
    def __init__(self, cwd : Path) -> None:
            
        with open(cwd/"config.json", "r") as f:
            config = json.load(f)
    
        self.ram_max : str = config["ram_max"]
        self.java_version = config["java_version"]
        self.mc_version = config["mc_version"]
        self.server_type = config["server_type"]
        self.id = config["id"] 
        self.cwd = config["cwd"]
        
        self.server : subprocess.Popen
        self.status = "OFFLINE"
        self.status_checker : JavaServer
        self.jar_file = ""
        pass
    
    def start_server(self) :
    
        self.status = "STARTING"
        print(f"[OBS] [STATUS] Server is currently : {self.status}")
        try: 
            if self.jar_file == "" :
                provider = JarManager()
                self.jar_file = provider.get_jar(self.mc_version, self.server_type)
            
            port = self.get_port()
            if not is_port_free(port):
                raise PortInUseError(f"Port number {port} is already being used. Try closing other instances or changing port configuration")
            
            self.status_checker = JavaServer.lookup(f"127.0.0.1:{port}")
            server = subprocess.Popen(args=[self.java_version, self.ram_max, '-jar', self.jar_file, 'nogui'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.cwd)
            self.server = server 
            logger_thread = threading.Thread(target=self.logger)
            logger_thread.start()
            
            input_thread = threading.Thread(target=self.input, daemon=True)
            input_thread.start()
            
            self.status = "ONLINE"
            print(f"[OBS] [STATUS] Server is now {self.status}")
        except (NetworkError, VersionNotFoundError, RetriesFailedError, ExternalApiError) as e:
            self.status = "OFFLINE"
            print(f"[OBS] [ERROR] Failed to start server: {e}")
            print(f"[OBS] [STATUS] Server state reverted to: {self.status}")
            self.server = None
        except Exception as e:
            print(f"[OBS] [ERROR] Failed to start server: {e}")
            self.status = "CRASHED"
            print(f"[OBS] [STATUS] Server is now {self.status}!")
            self.server = None

    def get_port(self):
        return 25565
    
    
    def online_check(self):
        server = self.server
        if self.status == "ONLINE" and server:
            code = server.poll()
            if code is not None:
                if code == 0:
                    print("[OBS] [STATUS] Server has been shutdown successfully while running in background.")
                    self.status = "OFFLINE"
                else: 
                    print("[OBS] [STATUS] Server has crashed while running in background.")
                    self.status = "CRASHED"
                print(f"[OBS] [STATUS] Server is now {self.status}!")
                self.server = None
                    
    def get_players(self):
        try:
            status = self.status_checker.status()
            players = status.players.sample
            player_list = []
            
            if players != None:
                for player in players:
                    player_list.append(player.name) 
            
            return {"players":player_list}
        except Exception as e:
            return {"players" : []}
                
    def to_dict(self):
        server_info = {
            "id" : self.id,
            "ram_max": self.ram_max,
            "java_version" : self.java_version,
            "mc_version" : self.mc_version,
            "server_type" : self.server_type,
            "cwd" : str(self.cwd),
            "current_status": self.status,
            "jar_file" : self.jar_file
        }
        return server_info
        
    def logger(self) : 
        server = self.server
        print("----------------- STARTING LOGGER THREAD --------------")
        while self.status != "OFFLINE":
            log_line : str = server.stdout.readline()
            log_line = log_line.strip()
            if log_line == "":
                break
            print(log_line)
        code = server.wait()
        print(f"[OBS] [INFO] Server has stopped with return code : {code}")
        if code != 0:
            self.status = "CRASHED"
            print(f"[OBS] [STATUS] Server is now {self.status}")
        else : 
            self.status = "OFFLINE"
            print(f"[OBS] [STATUS] Server is now {self.status}")
        self.server = None
    
    def input(self) : 
        server = self.server
        print("----------------- INPUT BY DEBUG CONSOLE IS NOW RUNNING --------------")
        
        while self.status != "OFFLINE":
            input_str = input()
            self.run_cmd(input_str)
            
            
    def run_cmd(self, cmd : str) :
        server = self.server
        if not cmd.endswith("\n"):
            cmd = cmd + "\n"
        server.stdin.write(cmd)
        server.stdin.flush()
        
    def stop(self):
        print("[OBS] [INFO] Shutting down server...")
        self.server.stdin.write("stop")
        self.server.stdin.flush()
        self.status = "OFFLINE"
        print(f"[OBS] [STATUS] Server is now {self.status}")
    
    def change_version(self, new_version) :######### hacer check si esta online, si esta offline cambiar y borrar, si esta online sol odescargar y "agendar"? el cambio de versoin
        self.mc_version = new_version
        os.remove(self.jar_file)