from pydantic import BaseModel, FilePath, DirectoryPath
from typing import Optional

class CreateServerRequest(BaseModel):
    
    ram_max : str
    mc_version : str
    server_type : str = "OFFICIAL"
    java_version : FilePath
    
class ServerCommand(BaseModel):
    cmd : str