import subprocess, threading, os, json, uuid, configparser, psutil
from collections import deque
from pathlib import Path
from services import JarManager, JavaManager, is_port_free
from exceptions import *
from mcstatus import JavaServer

default_storage_path = Path.home() / "Server Manager"

class MinecraftServerManager:

    def __init__(self) -> None:
        print("new server manager created")
        self.instances : dict[str, MinecraftInstance] = {} 
        if not default_storage_path.exists() :
            Path.mkdir(default_storage_path, parents=True, exist_ok=True) 
        self.load_servers_on_disk()
       
    pass


    def load_servers_on_disk(self):
        
        instances_dir = default_storage_path / "instances"
        
        if not instances_dir.exists() :
            Path.mkdir(instances_dir, parents=True, exist_ok=True) 
        
        iter_dir = Path.iterdir(instances_dir)
        
        for dir in iter_dir:
            if Path.exists(dir/"config.json"): 
                self.instances[dir.name] = MinecraftInstance(dir)

        print(self.instances)
    
            
    def create_server(self, ram_max, mc_version, server_type, port, java_version = "java", id = None):
        
        print("[OBS] [INFO] Creating new server folder...")
        
        if not id or id in self.instances:
            id = str(uuid.uuid4())
            while id in self.instances:
                id = str(uuid.uuid4())
        
        cwd = default_storage_path / "instances" 
        cwd = cwd / id
        Path.mkdir(cwd, parents=True)
        
        with open(cwd/"eula.txt", "w") as eula:
            eula.write("eula=true")
            
        print("[OBS] [INFO] EULA created and accepted.")
        
        config_json = {"id" : id, "ram_max": ram_max, "mc_version" : mc_version, "server_type" : server_type, "java_version" : str(java_version), "cwd":str(cwd) }
        
        with open(cwd/"config.json", "w") as config:
            json.dump(config_json, config)
        
        properties_lines = [f"port={port}\n", f"server-port={port}\n", "enable-query=true\n", f"query.port={port+1}\n"]
        
        with open(cwd/"server.properties", "w") as properties:
            properties.writelines(properties_lines)
        
        server = MinecraftInstance(cwd)
        self.instances[id] = server
        
        print("[OBS] [INFO] Server folder created, returning instance")
        return server
        
        
    def get_instace_by_id(self, id):
        if id in self.instances:
                return self.instances[id]
        else : raise InstanceNotFoundError("There's no instances with this ID")

class MinecraftInstance:
    def __init__(self, cwd : Path) -> None:
        
            
        with open(cwd/"config.json", "r") as f:
            config : dict = json.load(f)
    
        self.ram_max : str = config.get("ram_max", "-Xmx512M")
        self.java_version = config.get("java_version", "java")
        self.mc_version = config.get("mc_version", "1.15.2")
        self.server_type = config.get("server_type", "OFFICIAL")
        self.id = config["id"] 
        self.cwd = Path(cwd)
        
        self.console_entries = deque(maxlen=200)
        self.server : subprocess.Popen 
        self.process : psutil.Process
        self.status = "OFFLINE"
        self.jar_file = ""
        pass
    
    def start_server(self) :
    
        self.status = "STARTING"
        print(f"[OBS] [STATUS] Server is currently : {self.status}")
        try: 
            if self.jar_file == "" :
                provider = JarManager()
                self.jar_file = provider.get_jar(self.mc_version, self.server_type)
            
            if self.java_version == "java" :
                javaProvider = JavaManager()
                self.java_version = javaProvider.get_java(self.mc_version)
            
            properties = self.get_properties()
            port = properties.getint(configparser.UNNAMED_SECTION, "server-port")
            
            if not is_port_free(port):
                raise PortInUseError(f"Port number {port} is already being used. Try closing other instances or changing port configuration")
            
            server = subprocess.Popen(args=[self.java_version, self.ram_max, '-jar', self.jar_file, 'nogui'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.cwd)
            self.server = server 
            self.process = psutil.Process(self.server.pid)
            logger_thread = threading.Thread(target=self.logger)
            logger_thread.start()
            
            input_thread = threading.Thread(target=self.input, daemon=True)
            input_thread.start()
            
            print(f"[OBS] [STATUS] Server is now {self.status}")
        except (NetworkError, VersionNotFoundError, RetriesFailedError, ExternalApiError) as e:
            self.status = "OFFLINE"
            print(f"[OBS] [ERROR] Failed to start server: {e}")
            print(f"[OBS] [STATUS] Server state reverted to: {self.status}")
            self.server = None
            raise
        except Exception as e:
            print(f"[OBS] [ERROR] Failed to start server: {e}")
            self.status = "CRASHED"
            print(f"[OBS] [STATUS] Server is now {self.status}!")
            self.server = None
            raise

    def get_properties(self):
        properties = self.cwd/"server.properties"
        config = configparser.ConfigParser(allow_unnamed_section=True)
        with open(properties, 'r') as f:
            config.read(properties)
        return config
    
    
                    
    def get_players(self):
        try:
            properties = self.get_properties()
            query_port = properties.getint(configparser.UNNAMED_SECTION, "query.port")
            query_server = JavaServer.lookup(f"127.0.0.1:{query_port}")
            query = query_server.query()
            players = query.players.list
            player_list = []
            if players:
                for player in players:
                    player_list.append(player) 
            return player_list
        except Exception as e:
            print(e)
            return {"players" : []}
        
    def get_resource_stats(self):
        
        if not self.process: return {"cpu": 0, "ram": 0}
        try: 
            with self.process.oneshot(): 
                cpu = self.process.cpu_percent()
                ram = self.process.memory_info().rss / (1024 * 1024)
                ram = round(ram, 2)
            return {"cpu_usage": cpu, "ram_mb": ram}
        
        except psutil.NoSuchProcess: 
            return {"cpu_usage": 0, "ram_mb": 0}
        except Exception:
            return {"cpu_usage": 0, "ram_mb": 0}
                
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
        log_count = 1
        while True:
            log_line : str = server.stdout.readline()
            log_line = log_line.strip()
            if log_line == "":
                break
            if log_line:
                print(log_line)
                self.console_entries.append((log_count, log_line))
                log_count = log_count + 1
                if self.status == "STARTING" and "Done" in log_line and 'For help, type "help"' in log_line:
                        self.status = "ONLINE"
                        print(f"[OBS] [STATUS] Server is now {self.status}!")
                
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
        self.status = "CLOSING"
        print(f"[OBS] [INFO] Server state is now {self.status}...")
        self.server.stdin.write("stop\n")
        self.server.stdin.flush()
    
    def change_version(self, new_version) :######### hacer check si esta online, si esta offline cambiar y borrar, si esta online sol odescargar y "agendar"? el cambio de versoin
        self.mc_version = new_version
        os.remove(self.jar_file)