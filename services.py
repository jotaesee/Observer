import os, requests, json, hashlib
from typing import Tuple
from pathlib import Path
from abc import ABC, abstractmethod


MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

class VersionProvider:
    
        def __init__(self, provider_type: str):
            self.type = provider_type
        
        @abstractmethod
        def verify_jar(self, jarpath, hash, size):
            # aqui tendria que estar la logica del verify segun paper o segun mc normal.
            pass
        
        @abstractmethod
        def get_url(self, mc_version) -> Tuple[str, str, int]: 
            ### logica para fetchear el url
            
            pass

class JarManager:
    
    def __init__(self) -> None:
        self.versions_storage_path = Path.home() / "Server Manager" / "versions"
        Path.mkdir(self.versions_storage_path, parents= True, exist_ok= True)
    
    def is_downloaded(self, mc_version, jar_type):
        
        path = self.versions_storage_path / jar_type        
        if Path.exists(path):
            path = self.versions_storage_path / jar_type / mc_version
            if Path.is_file(path) : 
                return path
        else: Path.mkdir(path, parents=True, exist_ok=True)
        
        return False     
    
    def download_jar(self, mc_version, provider : VersionProvider, tries = 0, ):
        
        url, hash, size = provider.get_url(mc_version)
        
        print(f"[OBS] [SERVICES/downloader] Initiating download.. ")
        
        
        path = self.versions_storage_path / provider.type / mc_version
        header = requests.head(url)
        print(header)
        response = requests.get(url)
        
        with open(path, "wb") as jarfile:
            jarfile.write(response.content)
            
        if provider.verify_jar(path, hash, size):
            print(f"[OBS] [SERVICES/downloader] Minecraft: {mc_version} has been successfully downloaded from {url} in {path}")
            return path ## se verificó y se puede devolver el path del jar nuevo
        
        if tries != 3:
            os.remove(path)
            print("[OBS] [SERVICES/downloader] Download failed or corrupted. Trying again")
            self.download_jar(mc_version, provider, tries=tries+1)
        else:
            print("[OBS] [SERVICES/downloader] Retries have failed, try loading the file manually")
        return 0
    
    def get_jar(self, mc_version, jar_type):
        
        
        print(f"[OBS] [SERVICES/provider] Looking for Minecraft {mc_version}")
        path = self.is_downloaded(mc_version, jar_type)
    
        if path != False:
            print("[OBS] [SERVICES/provider] jar found, returning path to it")
            return path
        
        print("[OBS] [SERVICES/provider] Jar not found, starting downloader...")
        
        if jar_type == "OFFICIAL":
            provider = MojangProvider()
        else: provider = PaperProvider()
            
        path = self.download_jar(mc_version, provider=provider)
        
        return path
    

            
class MojangProvider(VersionProvider):
        
    def __init__(self, provider_type = "OFFICIAL"):
        
        super().__init__(provider_type="OFFICIAL")
        
    def verify_jar(self, jar_path : Path, given_hash, given_size):
        
        print("[OBS] [SERVICES/verifier] Verifying jar...")
        
        real_size = jar_path.stat().st_size
        aux = hashlib.sha1()
        
        with open(jar_path, "rb") as jarfile:
            while chunk := jarfile.read(65536):
                aux.update(chunk)
                
        calculated_hash = aux.hexdigest()
        
        print(f"[OBS] [SERVICES/verifier] Size should be {given_size} and the real size of the jar file is {real_size}")
        print(f"[OBS] [SERVICES/verifier] Hash-sha1 should be {given_hash} and the real hash-sha1 of the jar file is {calculated_hash}")
        
        if given_size != real_size or calculated_hash != given_hash:
            return False
        
        return True

    def get_url(self, mc_version):
        
        print("[OBS] [SERVICES/fetcher] Trying to get versions manifest")
        
        manifest = requests.get(MANIFEST_URL).json()
            
        for versions in manifest["versions"]:
            if versions["id"] == mc_version:
                version_url = versions["url"]
       
        print(f"[OBS] [SERVICES/fetcher] Got {mc_version} download url")    
        print(version_url)
            
        version_manifest = requests.get(version_url).json() 
            
        download_jar_url = version_manifest["downloads"]["server"]["url"]
        jar_hash = version_manifest["downloads"]["server"]["sha1"]
        jar_size = version_manifest["downloads"]["server"]["size"]
            
        return download_jar_url, jar_hash, jar_size
    

class PaperProvider(VersionProvider):
        
    def __init__(self) -> None:
            super().__init__(provider_type="PAPER")
            
    def verify_jar(self, jarpath, hash, size):
            pass
        
    def get_url(self, mc_version):
            return super().get_url(mc_version)