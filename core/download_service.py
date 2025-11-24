import os
import platform
import requests
import zipfile
import shutil
from pathlib import Path
from typing import Optional
from config import Config
from core.github_service import GitHubService


class DownloadService:
    """Service to download and manage PocketBase binaries"""
    
    def __init__(self):
        self.downloads_dir = Config.DOWNLOADS_DIR
        self.github_service = GitHubService()
    
    @staticmethod
    def detect_os() -> str:
        """Detect current operating system"""
        system = platform.system().lower()
        if system == 'linux':
            return 'linux'
        elif system == 'darwin':
            return 'darwin'
        elif system == 'windows':
            return 'windows'
        else:
            raise Exception(f"Unsupported operating system: {system}")
    
    def get_executable_name(self) -> str:
        """Get PocketBase executable name based on OS"""
        os_type = self.detect_os()
        if os_type == 'windows':
            return 'pocketbase.exe'
        return 'pocketbase'
    
    def is_downloaded(self, version: str) -> bool:
        """Check if version is already downloaded"""
        version_dir = self.downloads_dir / version
        exe_name = self.get_executable_name()
        exe_path = version_dir / exe_name
        return exe_path.exists()
    
    def download_version(self, version: str, os_type: Optional[str] = None) -> Path:
        """
        Download specific PocketBase version
        
        Args:
            version: PocketBase version to download
            os_type: Operating system (auto-detected if None)
        
        Returns:
            Path to downloaded executable
        """
        if os_type is None:
            os_type = self.detect_os()
        
        # Check if already downloaded
        version_dir = self.downloads_dir / version
        exe_name = self.get_executable_name()
        exe_path = version_dir / exe_name
        
        if exe_path.exists():
            print(f"✓ Version {version} already downloaded")
            return exe_path
        
        # Get download URL
        download_url = self.github_service.get_download_url(version, os_type)
        if not download_url:
            raise Exception(f"No download URL found for version {version} and OS {os_type}")
        
        # Create version directory
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Download file
        print(f"Downloading PocketBase v{version} for {os_type}...")
        zip_path = version_dir / 'pocketbase.zip'
        
        try:
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract ZIP
            print(f"Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(version_dir)
            
            # Remove ZIP file
            zip_path.unlink()
            
            # Make executable (Unix systems)
            if os_type in ['linux', 'darwin']:
                os.chmod(exe_path, 0o755)
            
            print(f"✓ PocketBase v{version} downloaded successfully")
            return exe_path
        
        except Exception as e:
            # Cleanup on error
            if version_dir.exists():
                shutil.rmtree(version_dir)
            raise Exception(f"Failed to download PocketBase: {e}")
    
    def get_executable_path(self, version: str) -> Optional[Path]:
        """Get path to executable for specific version"""
        version_dir = self.downloads_dir / version
        exe_name = self.get_executable_name()
        exe_path = version_dir / exe_name
        
        if exe_path.exists():
            return exe_path
        return None
