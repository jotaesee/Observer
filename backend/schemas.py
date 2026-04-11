from pydantic import BaseModel, FilePath, DirectoryPath
from typing import Optional

class CreateServerRequest(BaseModel):
    
    ram_max : str = "-Xmx512M"
    mc_version : str = "1.15.2"
    server_type : str = "OFFICIAL"
    port : int = 25565
    java_version : str = "java"
    id : str
    
class ServerCommand(BaseModel):
    cmd : str