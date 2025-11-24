import requests
import time
from typing import List, Dict, Optional
from config import Config


class GitHubService:
    """Service to interact with GitHub API for PocketBase releases"""
    
    def __init__(self):
        self.api_url = Config.GITHUB_API_URL
        self.cache_duration = Config.GITHUB_CACHE_DURATION
        self._cache = None
        self._cache_time = 0
    
    def get_releases(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get PocketBase releases from GitHub API
        Returns list of releases with version and download URLs
        """
        # Check cache
        if not force_refresh and self._cache and (time.time() - self._cache_time) < self.cache_duration:
            return self._cache
        
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            releases_data = response.json()
            
            releases = []
            for release in releases_data:
                if release.get('draft') or release.get('prerelease'):
                    continue
                
                version = release.get('tag_name', '').lstrip('v')
                if not version:
                    continue
                
                assets = {}
                for asset in release.get('assets', []):
                    name = asset.get('name', '').lower()
                    download_url = asset.get('browser_download_url')
                    
                    if 'linux_amd64' in name or 'linux_arm64' in name:
                        assets['linux'] = download_url
                    elif 'darwin_amd64' in name or 'darwin_arm64' in name:
                        assets['darwin'] = download_url
                    elif 'windows_amd64' in name:
                        assets['windows'] = download_url
                
                if assets:
                    releases.append({
                        'version': version,
                        'name': release.get('name', version),
                        'published_at': release.get('published_at'),
                        'assets': assets
                    })
            
            # Update cache
            self._cache = releases
            self._cache_time = time.time()
            
            return releases
        
        except Exception as e:
            print(f"Error fetching releases: {e}")
            # Return cached data if available
            if self._cache:
                return self._cache
            return []
    
    def get_download_url(self, version: str, os_type: str) -> Optional[str]:
        """
        Get download URL for specific version and OS
        
        Args:
            version: PocketBase version (e.g., '0.34.0')
            os_type: Operating system ('linux', 'darwin', 'windows')
        
        Returns:
            Download URL or None if not found
        """
        releases = self.get_releases()
        
        for release in releases:
            if release['version'] == version:
                return release['assets'].get(os_type)
        
        return None
