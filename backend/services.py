import os, requests, json, hashlib, platform, shutil, stat
from typing import Tuple
from pathlib import Path
from exceptions import *
import socket
from abc import abstractmethod

DEFAULT_STORAGE_PATH = Path.home() / "Server Manager"
MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
PAPER_BASE_URL = "https://api.papermc.io/v2/projects/paper"
BELL_JAVA_MANIFEST_URL = "https://api.bell-sw.com/v1/liberica/releases"

def get_available_versions():
    available_versions = {"OFFICIAL":[],"PAPER":[]}
    if check_internet_connection() :
        res = requests.get(MANIFEST_URL)
        if res.ok:
            data = res.json()
            for version in data["versions"] :
                if version["type"] == "release":
                    available_versions["OFFICIAL"].append(version["id"])
        res = requests.get(PAPER_BASE_URL)
        if res.ok:
            data = res.json()
            for version in data["versions"]:
                available_versions["PAPER"].append(version)
        
        available_versions["PAPER"].reverse()
        return available_versions
    else:
        versions_dir = DEFAULT_STORAGE_PATH / "versions"
        if not versions_dir.exists() :
            return available_versions
        
        official_versions_path = versions_dir/"OFFICIAL"
        
        if official_versions_path.exists() :
            iter_official_versions = Path.iterdir(official_versions_path)
            for version in iter_official_versions:
                available_versions["OFFICIAL"].append(version.name)
        
        paper_versions_path = versions_dir/"PAPER"
        
        if paper_versions_path.exists() :
            iter_paper_versions = Path.iterdir(official_versions_path)
            for version in iter_paper_versions:
                available_versions["PAPER"].append(version.name)
        
        available_versions["OFFICIAL"].reverse()
        available_versions["PAPER"].reverse()
                        
        return available_versions

def check_internet_connection(url='http://www.google.com/', timeout=5):
    try:
        requests.head(url, timeout=timeout)
        return True
    except (Exception) as e:
        print(e)
        return False


def is_port_free(port : int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1) 
        return s.connect_ex(('127.0.0.1', port)) != 0

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

        path : Path = self.versions_storage_path / provider.type / mc_version
        
        try:
            with requests.get(url, timeout=30, stream=True) as response : 
                response.raise_for_status()
            
                with open(path, "wb") as jarfile:
                    for chunk in response.iter_content(8192):
                        jarfile.write(chunk)
                    
            if provider.verify_jar(path, hash, size):
                print(f"[OBS] [SERVICES/downloader] Minecraft: {mc_version} has been successfully downloaded from {url} in {path}")
                return path ## se verificó y se puede devolver el path del jar nuevo
        except (requests.RequestException, DownloadCorruptedError) as e:
            
            if path.exists(): 
                os.remove(path)
            
            if tries < 3:
                print("[OBS] [SERVICES/downloader] Download failed or corrupted. Trying again")
                self.download_jar(mc_version, provider, tries=tries+1)
            else:
                print("[OBS] [SERVICES/downloader] Retries have failed, try loading the file manually")
                raise RetriesFailedError("All 3 attempts for downloading the jar have failed.") 
    
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
            raise DownloadCorruptedError("Download is corrupted.")
        
        return True

    def get_url(self, mc_version):
        try:
            print("[OBS] [SERVICES/fetcher] Trying to get versions manifest")
            
            manifest = requests.get(MANIFEST_URL, timeout=10)
            manifest.raise_for_status()
            manifest = manifest.json()
                
            for versions in manifest["versions"]:
                if versions["id"] == mc_version:
                    version_url = versions["url"]
        
            print(f"[OBS] [SERVICES/fetcher] Got {mc_version} download url")    
            print(version_url)
                
            version_manifest = requests.get(version_url, timeout=10) 
            version_manifest.raise_for_status()
            version_manifest = version_manifest.json()
            
            if mc_version in ["1.0", "1.1","1.2" ,"1.2.1","1.2.2","1.2.3","1.2.4"]:
                download_jar_url = version_manifest["downloads"]["client"]["url"]
                jar_hash = version_manifest["downloads"]["client"]["sha1"]
                jar_size = version_manifest["downloads"]["client"]["size"]
            else:
                download_jar_url = version_manifest["downloads"]["server"]["url"]
                jar_hash = version_manifest["downloads"]["server"]["sha1"]
                jar_size = version_manifest["downloads"]["server"]["size"]
                
            return download_jar_url, jar_hash, jar_size
        
        except requests.exceptions.Timeout:
            raise NetworkError("Mojang's download site timed out.")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection Error. Maybe no internet?")
        except requests.exceptions.HTTPError as e:
            print(f"Error HTTP: {e}")
            raise ExternalApiError(f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Unkown Error: {e}")

class PaperProvider(VersionProvider):
        
    def __init__(self) -> None:
            super().__init__(provider_type="PAPER")
            
    def verify_jar(self, jar_path, given_hash, given_size):
        
        print("[OBS] [SERVICES/verifier] Verifying jar...")
    
        aux = hashlib.sha256()
        
        with open(jar_path, "rb") as jarfile:
            while chunk := jarfile.read(65536):
                aux.update(chunk)
                
        calculated_hash = aux.hexdigest()
        
        print(f"[OBS] [SERVICES/verifier] Hash-sha256 should be {given_hash} and the real hash-sha256 of the jar file is {calculated_hash}")
        
        if calculated_hash != given_hash:
            print(f"[OBS] [SERVICES/verifier] Hashes don't match.")
            raise DownloadCorruptedError("Download is corrupted.")
        
        print(f"[OBS] [SERVICES/verifier] Hashes match.")
        return True
        
    def get_url(self, mc_version):
        try:
            versions_response = requests.get(PAPER_BASE_URL,timeout=10)
            versions_response.raise_for_status()
            versions_response = versions_response.json()
            
            valid_versions = versions_response["versions"]
                
            if mc_version not in valid_versions:
                raise VersionNotFoundError("Paper Version Not Found")
                
            builds_response =  requests.get(f"{PAPER_BASE_URL}/versions/{mc_version}", timeout=10)
            builds_response.raise_for_status()
            builds_response = builds_response.json()
            
            latest_build = builds_response["builds"][-1]
                
            info_response = requests.get(f"{PAPER_BASE_URL}/versions/{mc_version}/builds/{latest_build}", timeout=10)
            info_response.raise_for_status()
            info_response = info_response.json()
                
            jar_name = info_response["downloads"]["application"]["name"]
            sha256 = info_response["downloads"]["application"]["sha256"]
            download_url = f"{PAPER_BASE_URL}/versions/{mc_version}/builds/{latest_build}/downloads/{jar_name}"
                
            return download_url, sha256, None 
        except requests.exceptions.Timeout:
            raise NetworkError("PaperMC site timed out.")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection Error. Maybe no internet?")
        except requests.exceptions.HTTPError as e:
            print(f"Error HTTP: {e}")
            raise ExternalApiError(f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Unkown Error: {e}")
    
class JavaManager():
    
    def __init__(self) -> None:
        self.java_storage_path = Path.home() / "Server Manager" / "runtimes"
        
        self.system = platform.system().lower()
        if self.system not in ["windows", "linux"]:
            raise SystemNotCompatible("Operative system is not compatible with automatic java download")
        
        self.architecture = platform.machine().lower()
        if self.architecture in ["amd64", "x86_64"] :
            self.architecture = "x86"
        elif self.architecture in ["aarch64", "arm64"] : 
            self.architecture = "arm"
        else : raise ArchNotSupported("Architecture not supported for automatic java download.")
        
        self.java_exec = "java.exe" if self.system == "windows" else "java"
        pass
    
    def get_java(self, mc_version):
        
        print(f"[OBS] [SERVICES/JarManager] Looking for java for {mc_version} and current system specs... ")
        path = self.is_java_downloaded(mc_version)
        if path:
            print(f"[OBS] [SERVICES/JarManager] Java for {mc_version} has been found! Returning path to it... ")
            return path
        
        print(f"[OBS] [SERVICES/JarManager] Java has not been found. Need to download.")
        path = self.download_java(mc_version)
        return path
    
        
    def is_java_downloaded(self, mc_version):
    
        path = self.java_storage_path / "versions_cache.json"
        if not path.exists() :
            self.java_storage_path.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as new_cache:
                template = {"versions":{}}
                json.dump(template, new_cache)      
        
        with open(path, "r") as versions_file :
            cache : dict = json.load(versions_file)
            
        java_version = cache["versions"].get(mc_version)
            
        if java_version == None :
            java_version = self.which_java(mc_version)
            cache["versions"][mc_version] = java_version
            with open(path, "w") as versions_file:
                json.dump(cache, versions_file)

        java_folder_path = self.java_storage_path /f"{java_version}_{self.system}_{self.architecture}"
        java_exec_paths = list(java_folder_path.rglob(self.java_exec))
        if java_exec_paths :
            return java_exec_paths[0]
    
        return False
     
    
    def which_java(self, mc_version) :
        try:
            print("[OBS] [SERVICES/fetcher] Trying to get versions manifest to determine Java version.")
            
            manifest = requests.get(MANIFEST_URL, timeout=10)
            manifest.raise_for_status()
            manifest = manifest.json()
                
            for versions in manifest["versions"]:
                if versions["id"] == mc_version:
                    version_url = versions["url"]
        
            print(f"[OBS] [SERVICES/fetcher] Got {mc_version} url, looking for corresponding java version...")    
            print(version_url)
                
            version_manifest = requests.get(version_url, timeout=10) 
            version_manifest.raise_for_status()
            version_manifest = version_manifest.json()
            
            java_version = version_manifest["javaVersion"]["majorVersion"]
            print(f"[OBS] [SERVICES/fetcher] Java version for Minecraft : {mc_version}, should be : {java_version}") 
            return java_version        
        except requests.exceptions.Timeout:
            raise NetworkError("Mojang's download site timed out.")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection Error. Maybe no internet?")
        except requests.exceptions.HTTPError as e:
            print(f"Error HTTP: {e}")
            raise ExternalApiError(f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Unkown Error: {e}")
        
    def download_java(self, mc_version, tries=0) :
        
        print("estamos intentando descargar")
        with open(Path(self.java_storage_path / "versions_cache.json"), "r") as versions_file :
            cache : dict = json.load(versions_file)
        
        java_version = cache["versions"].get(mc_version)
        print(java_version)
        url, given_hash, given_size = self.get_url(java_version)
        package_type = "tar.gz" if self.system == "linux" else "zip"

        package_filename = f"{java_version}_{self.system}_{self.architecture}.{package_type}"  
        package_path = self.java_storage_path / package_filename 
        
        try:
            print(f"[OBS] [SERVICES/downloader] Initiating Java download.. ")
            res = requests.get(url,stream=True)
            if res.ok:        
                
                with open(package_path, 'wb') as zipfile:
                    for chunk in res.iter_content(chunk_size=512*1024):
                        zipfile.write(chunk)            
                
            if self.verify_zipfile(package_path, given_hash, given_size):
                
                extract_folder = self.java_storage_path / f"{java_version}_{self.system}_{self.architecture}"
                print(f"[OBS] [SERVICES/downloader] Java {java_version} .{package_type} has been successfully downloaded at {extract_folder}! ")
                return self.extract_java(package_path, extract_folder, java_version)
            
            else: raise DownloadCorruptedError()
    
        except (requests.RequestException, DownloadCorruptedError) as e:
        
            if package_path.exists(): 
                package_path.unlink()

            if tries < 3:
                print("[OBS] [SERVICES/downloader] Java Download failed or corrupted. Trying again")
                self.download_java(mc_version, tries=tries+1)
            else:
                print("[OBS] [SERVICES/downloader] Retries have failed, try loading the file manually")
                raise RetriesFailedError("All 3 attempts for downloading Java have failed.") 

    def get_url(self, java_version) :
        package_type = "tar.gz" if self.system == "linux" else "zip"
        available_versions_url = f"{BELL_JAVA_MANIFEST_URL}/?version-feature={java_version}&os={self.system}&arch={self.architecture}&bitness=64&bundle-type=jre&package-type={package_type}"
        print(available_versions_url)
        try:
            res = requests.get(available_versions_url)
            if res.ok :
                download_url = res.json()[0].get("downloadUrl")
                file_size = res.json()[0].get("size")
                hash_sha1 = res.json()[0].get("sha1")
                
            return download_url, hash_sha1, file_size 
            
        except requests.exceptions.Timeout:
            raise NetworkError("Bellsoft's download site timed out.")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection Error. Maybe no internet?")
        except requests.exceptions.HTTPError as e:
            print(f"Error HTTP: {e}")
            raise ExternalApiError(f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Unkown Error: {e}")
        
    def verify_zipfile(self, java_path : Path, given_hash, given_size):
        
        print("[OBS] [SERVICES/verifier] Verifying Java package...")
        
        real_size = java_path.stat().st_size
        aux = hashlib.sha1()
        
        with open(java_path, "rb") as jarfile:
            while chunk := jarfile.read(65536):
                aux.update(chunk)
                
        calculated_hash = aux.hexdigest()
        
        print(f"[OBS] [SERVICES/verifier] Size should be {given_size} and the real size of the Java .zip file is {real_size}")
        print(f"[OBS] [SERVICES/verifier] Hash-sha1 should be {given_hash} and the real hash-sha1 of the Java .zip file is {calculated_hash}")
        
        if given_size != real_size or calculated_hash != given_hash:
            raise DownloadCorruptedError("Download is corrupted.")
        
        return True
    
    
    def extract_java(self, package_path: Path, extract_folder: Path, java_version):
        
        print(f"[OBS] [SERVICES/extractor] Now extracting {package_path.name}...")
        package_type = "gztar" if self.system == "linux" else "zip"
        shutil.unpack_archive(package_path, extract_folder, package_type)
        package_path.unlink()
        
        java_exec_paths = list(extract_folder.rglob(self.java_exec))
        if not java_exec_paths:
            raise Exception("No java executable found inside extracted file.")
            
        final_java_path = java_exec_paths[0]
        
        if self.system == "linux":
            st = os.stat(final_java_path)
            os.chmod(final_java_path, st.st_mode | stat.S_IEXEC)
            
        print(f"[OBS] [SERVICES/extractor] Java ready at {final_java_path}")
        return final_java_path