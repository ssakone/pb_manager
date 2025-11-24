import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from werkzeug.utils import secure_filename


class FileManagerService:
    """Service to manage files and folders for PocketBase instances"""
    
    # Files that should be protected (warnings shown)
    PROTECTED_FILES = {'pocketbase', 'run.sh', 'pb_data/data.db', 'pb_data/data.db-shm', 'pb_data/data.db-wal'}
    
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    def __init__(self, instance_path: str):
        """
        Initialize file manager for a specific instance
        
        Args:
            instance_path: Absolute path to the instance directory
        """
        self.instance_path = Path(instance_path).resolve()
        
        if not self.instance_path.exists():
            raise ValueError(f"Instance path does not exist: {instance_path}")
    
    def _validate_path(self, relative_path: str) -> Path:
        """
        Validate and resolve a path, preventing directory traversal
        
        Args:
            relative_path: Relative path within instance directory
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValueError: If path is invalid or attempts directory traversal
        """
        if not relative_path:
            return self.instance_path
        
        # Remove leading slashes and resolve
        clean_path = relative_path.lstrip('/')
        full_path = (self.instance_path / clean_path).resolve()
        
        # Ensure path is within instance directory
        try:
            full_path.relative_to(self.instance_path)
        except ValueError:
            raise ValueError("Invalid path: directory traversal detected")
        
        return full_path
    
    def _get_relative_path(self, full_path: Path) -> str:
        """Get relative path from instance root"""
        try:
            return str(full_path.relative_to(self.instance_path))
        except ValueError:
            return ""
    
    def _is_protected(self, relative_path: str) -> bool:
        """Check if a file is protected"""
        return relative_path in self.PROTECTED_FILES or any(
            relative_path.startswith(pf) for pf in self.PROTECTED_FILES
        )
    
    def list_directory(self, path: str = "") -> Dict:
        """
        List files and folders in a directory
        
        Args:
            path: Relative path within instance
            
        Returns:
            Dictionary with files and folders information
        """
        try:
            full_path = self._validate_path(path)
            
            if not full_path.exists():
                raise FileNotFoundError(f"Path does not exist: {path}")
            
            if not full_path.is_dir():
                raise ValueError(f"Path is not a directory: {path}")
            
            items = []
            
            for item in sorted(full_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                relative = self._get_relative_path(item)
                stat = item.stat()
                
                item_info = {
                    'name': item.name,
                    'path': relative,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': stat.st_size if item.is_file() else 0,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'protected': self._is_protected(relative)
                }
                
                # Add extension for files
                if item.is_file():
                    item_info['extension'] = item.suffix.lower()
                
                items.append(item_info)
            
            return {
                'success': True,
                'current_path': self._get_relative_path(full_path),
                'items': items
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_folder(self, path: str, folder_name: str) -> Dict:
        """
        Create a new folder
        
        Args:
            path: Parent directory path
            folder_name: Name of new folder
            
        Returns:
            Success/error dictionary
        """
        try:
            # Sanitize folder name
            safe_name = secure_filename(folder_name)
            if not safe_name:
                raise ValueError("Invalid folder name")
            
            parent_path = self._validate_path(path)
            new_folder = parent_path / safe_name
            
            if new_folder.exists():
                raise ValueError(f"Folder already exists: {safe_name}")
            
            new_folder.mkdir(parents=True, exist_ok=False)
            
            return {
                'success': True,
                'message': f"Folder '{safe_name}' created successfully",
                'path': self._get_relative_path(new_folder)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_item(self, path: str) -> Dict:
        """
        Delete a file or folder
        
        Args:
            path: Path to delete
            
        Returns:
            Success/error dictionary
        """
        try:
            full_path = self._validate_path(path)
            
            if not full_path.exists():
                raise FileNotFoundError(f"Path does not exist: {path}")
            
            # Prevent deletion of instance root
            if full_path == self.instance_path:
                raise ValueError("Cannot delete instance root directory")
            
            relative = self._get_relative_path(full_path)
            
            if full_path.is_dir():
                shutil.rmtree(full_path)
                item_type = "Folder"
            else:
                full_path.unlink()
                item_type = "File"
            
            return {
                'success': True,
                'message': f"{item_type} '{full_path.name}' deleted successfully",
                'was_protected': self._is_protected(relative)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def copy_item(self, source_path: str, dest_path: str) -> Dict:
        """
        Copy a file or folder
        
        Args:
            source_path: Source path
            dest_path: Destination path
            
        Returns:
            Success/error dictionary
        """
        try:
            source = self._validate_path(source_path)
            dest = self._validate_path(dest_path)
            
            if not source.exists():
                raise FileNotFoundError(f"Source does not exist: {source_path}")
            
            if dest.exists():
                raise ValueError(f"Destination already exists: {dest_path}")
            
            if source.is_dir():
                shutil.copytree(source, dest)
                item_type = "Folder"
            else:
                shutil.copy2(source, dest)
                item_type = "File"
            
            return {
                'success': True,
                'message': f"{item_type} copied successfully",
                'dest_path': self._get_relative_path(dest)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def move_item(self, source_path: str, dest_path: str) -> Dict:
        """
        Move/rename a file or folder
        
        Args:
            source_path: Source path
            dest_path: Destination path
            
        Returns:
            Success/error dictionary
        """
        try:
            source = self._validate_path(source_path)
            dest = self._validate_path(dest_path)
            
            if not source.exists():
                raise FileNotFoundError(f"Source does not exist: {source_path}")
            
            if dest.exists():
                raise ValueError(f"Destination already exists: {dest_path}")
            
            # Prevent moving instance root
            if source == self.instance_path:
                raise ValueError("Cannot move instance root directory")
            
            shutil.move(str(source), str(dest))
            
            return {
                'success': True,
                'message': f"Item moved successfully",
                'dest_path': self._get_relative_path(dest)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_file(self, path: str, filename: str, file_data, replace: bool = True) -> Dict:
        """
        Save an uploaded file
        
        Args:
            path: Directory path
            filename: Original filename
            file_data: File object from request
            replace: Whether to replace existing file
            
        Returns:
            Success/error dictionary
        """
        try:
            # Sanitize filename
            safe_name = secure_filename(filename)
            if not safe_name:
                raise ValueError("Invalid filename")
            
            # Validate file size
            file_data.seek(0, os.SEEK_END)
            file_size = file_data.tell()
            file_data.seek(0)
            
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(f"File size exceeds maximum allowed ({self.MAX_FILE_SIZE / 1024 / 1024}MB)")
            
            parent_path = self._validate_path(path)
            file_path = parent_path / safe_name
            
            if file_path.exists() and not replace:
                raise ValueError(f"File already exists: {safe_name}")
            
            # Save file
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)
            
            return {
                'success': True,
                'message': f"File '{safe_name}' uploaded successfully",
                'path': self._get_relative_path(file_path),
                'size': file_size
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_path(self, path: str) -> Path:
        """
        Get the absolute file path for downloading
        
        Args:
            path: Relative file path
            
        Returns:
            Absolute Path object
        """
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")
        
        if not full_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        return full_path
