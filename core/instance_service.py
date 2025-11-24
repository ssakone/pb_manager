import shutil
import re
import subprocess
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from config import Config
from models.database import db
from models.instance import Instance
from core.download_service import DownloadService
from core.pm2_service import PM2Service


class InstanceService:
    """Service to manage PocketBase instances"""
    
    def __init__(self):
        self.instances_dir = Config.INSTANCES_DIR
        self.download_service = DownloadService()
        self.pm2_service = PM2Service()
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize instance name to be filesystem-safe"""
        # Replace spaces and special chars with underscore
        name = re.sub(r'[^\w\-]', '_', name)
        # Remove multiple underscores
        name = re.sub(r'_+', '_', name)
        # Convert to lowercase
        return name.lower().strip('_')
    
    def get_next_available_port(self) -> int:
        """Get next available port starting from DEFAULT_PORT_START"""
        instances = Instance.query.order_by(Instance.port.desc()).all()
        
        if not instances:
            return Config.DEFAULT_PORT_START
        
        highest_port = instances[0].port
        return max(highest_port + 1, Config.DEFAULT_PORT_START)
    
    def create_superuser(self, instance_path: Path, admin_email: str, admin_password: str) -> bool:
        """
        Create a superuser for PocketBase instance
        
        Args:
            instance_path: Path to instance directory
            admin_email: Admin email address
            admin_password: Admin password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            exe_name = self.download_service.get_executable_name()
            exe_path = instance_path / exe_name
            
            if not exe_path.exists():
                raise Exception(f"PocketBase executable not found: {exe_path}")
            
            # Run superuser upsert command
            result = subprocess.run(
                [str(exe_path), 'superuser', 'upsert', admin_email, admin_password],
                cwd=str(instance_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✓ Superuser created: {admin_email}")
                return True
            else:
                error_msg = result.stderr or result.stdout
                raise Exception(f"Failed to create superuser: {error_msg}")
        
        except subprocess.TimeoutExpired:
            raise Exception("Superuser creation timed out")
        except Exception as e:
            raise Exception(f"Failed to create superuser: {e}")
    
    def list_admins(self, instance_path: Path) -> List[Dict]:
        """
        List all admin users for a PocketBase instance
        
        Args:
            instance_path: Path to instance directory
            
        Returns:
            List of admin user dictionaries with id, email, and created date
        """
        db_path = instance_path / 'pb_data' / 'data.db'
        
        if not db_path.exists():
            return []
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query _superusers table (PocketBase internal table for admins)
            # Exclude system installer account
            cursor.execute("""
                SELECT id, email, created, updated, verified, emailVisibility
                FROM _superusers 
                WHERE email != '__pbinstaller@example.com'
                ORDER BY created DESC
            """)
            
            admins = []
            for row in cursor.fetchall():
                admins.append({
                    'id': row['id'],
                    'email': row['email'],
                    'created': row['created'],
                    'updated': row['updated'],
                    'verified': row['verified'],
                    'emailVisibility': row['emailVisibility']
                })
            
            conn.close()
            return admins
        
        except Exception as e:
            raise Exception(f"Failed to list admins: {e}")
    
    def add_admin(self, instance_path: Path, admin_email: str, admin_password: str) -> bool:
        """
        Add a new admin user (alias for create_superuser for consistency)
        
        Args:
            instance_path: Path to instance directory
            admin_email: Admin email address
            admin_password: Admin password
            
        Returns:
            True if successful
        """
        return self.create_superuser(instance_path, admin_email, admin_password)
    
    def remove_admin(self, instance_path: Path, admin_id: str) -> bool:
        """
        Remove an admin user from PocketBase instance
        
        Args:
            instance_path: Path to instance directory
            admin_id: Admin user ID to remove
            
        Returns:
            True if successful
        """
        db_path = instance_path / 'pb_data' / 'data.db'
        
        if not db_path.exists():
            raise Exception("Database not found")
        
        try:
            # Check if there's more than one admin
            admins = self.list_admins(instance_path)
            if len(admins) <= 1:
                raise Exception("Cannot delete the last admin user")
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Delete from _superusers table
            cursor.execute("DELETE FROM _superusers WHERE id = ?", (admin_id,))
            
            if cursor.rowcount == 0:
                conn.close()
                raise Exception(f"Admin not found: {admin_id}")
            
            conn.commit()
            conn.close()
            
            print(f"✓ Admin removed: {admin_id}")
            return True
        
        except Exception as e:
            raise Exception(f"Failed to remove admin: {e}")
    
    def update_version(self, instance_id: int, new_version: str) -> bool:
        """
        Update PocketBase version for an instance
        
        Args:
            instance_id: Instance ID
            new_version: New PocketBase version to install
            
        Returns:
            True if successful
        """
        instance = self.get_instance(instance_id)
        if not instance:
            raise Exception(f"Instance with ID {instance_id} not found")
        
        # Check if instance is stopped
        if self.pm2_service.is_running(instance.pm2_name):
            raise Exception("Instance must be stopped before changing version")
        
        # Setup paths
        instance_dir = Path(instance.pb_path)
        exe_name = self.download_service.get_executable_name()
        instance_exe = instance_dir / exe_name
        backup_exe = instance_dir / f"{exe_name}.backup"
        
        try:
            # Download new version
            exe_path = self.download_service.download_version(new_version)
            
            if instance_exe.exists():
                shutil.copy2(instance_exe, backup_exe)
            
            # Copy new executable
            shutil.copy2(exe_path, instance_exe)
            
            # Make executable (Unix systems)
            if self.download_service.detect_os() in ['linux', 'darwin']:
                import os
                os.chmod(instance_exe, 0o755)
            
            # Update version in database
            instance.version = new_version
            db.session.commit()
            
            # Remove backup if successful
            if backup_exe.exists():
                backup_exe.unlink()
            
            print(f"✓ Instance '{instance.name}' updated to v{new_version}")
            return True
        
        except Exception as e:
            # Restore backup if it exists
            if backup_exe.exists() and instance_exe.exists():
                shutil.copy2(backup_exe, instance_exe)
                backup_exe.unlink()
            db.session.rollback()
            raise Exception(f"Failed to update version: {e}")
    
    def update_domain(self, instance_id: int, domain: Optional[str]) -> bool:
        """
        Update domain for an instance
        
        Args:
            instance_id: Instance ID
            domain: New domain (None to remove)
            
        Returns:
            True if successful
        """
        instance = self.get_instance(instance_id)
        if not instance:
            raise Exception(f"Instance with ID {instance_id} not found")
        
        try:
            instance.domain = domain
            db.session.commit()
            
            print(f"✓ Domain for '{instance.name}' updated to: {domain or 'None'}")
            return True
        
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to update domain: {e}")
    
    def create_instance(self, name: str, version: str, port: Optional[int] = None, dev_mode: bool = False, admin_email: Optional[str] = None, admin_password: Optional[str] = None, domain: Optional[str] = None) -> Instance:
        """
        Create new PocketBase instance
        
        Args:
            name: Human-readable instance name
            version: PocketBase version
            port: Port number (auto-assigned if None)
            dev_mode: Whether to enable dev mode (verbose logging)
            admin_email: Admin email for superuser (optional)
            admin_password: Admin password for superuser (optional)
            domain: Custom domain for the instance (optional)
        
        Returns:
            Created Instance object
        """
        # Sanitize name
        sanitized_name = self.sanitize_name(name)
        
        # Check if name already exists
        if Instance.query.filter_by(name=sanitized_name).first():
            raise Exception(f"Instance with name '{sanitized_name}' already exists")
        
        # Get port
        if port is None:
            port = self.get_next_available_port()
        elif Instance.query.filter_by(port=port).first():
            raise Exception(f"Port {port} is already in use")
        
        # Download PocketBase if needed
        try:
            exe_path = self.download_service.download_version(version)
        except Exception as e:
            raise Exception(f"Failed to download PocketBase: {e}")
        
        # Create instance directory
        instance_dir = self.instances_dir / sanitized_name
        if instance_dir.exists():
            raise Exception(f"Instance directory already exists: {instance_dir}")
        
        try:
            instance_dir.mkdir(parents=True, exist_ok=True)
            
            # Create PocketBase directories
            (instance_dir / 'pb_hooks').mkdir(exist_ok=True)
            (instance_dir / 'pb_migrations').mkdir(exist_ok=True)
            (instance_dir / 'pb_data').mkdir(exist_ok=True)
            (instance_dir / 'pb_public').mkdir(exist_ok=True)
            
            # Create run.sh script
            run_script_path = instance_dir / 'run.sh'
            dev_flag = '--dev' if dev_mode else ''
            run_script_content = f'''#!/bin/bash
set -e  # Exit on any error

# PocketBase Instance Runner
# Instance: {sanitized_name}
# Version: {version}
# Port: {port}
# Dev Mode: {dev_mode}

cd "{instance_dir}"

# Check if pocketbase executable exists
if [ ! -f "./pocketbase" ]; then
    echo "Error: pocketbase executable not found in $(pwd)"
    exit 1
fi

exec "./pocketbase" serve \\
    --http "0.0.0.0:{port}" \\
    --dir "{instance_dir}/pb_data" \\
    --hooksDir "{instance_dir}/pb_hooks" \\
    --migrationsDir "{instance_dir}/pb_migrations" \\
    --publicDir "{instance_dir}/pb_public" \\
    {dev_flag}
'''
            
            with open(run_script_path, 'w') as f:
                f.write(run_script_content)
            
            # Make script executable
            import os
            os.chmod(run_script_path, 0o755)
            
            # Copy executable
            exe_name = self.download_service.get_executable_name()
            instance_exe = instance_dir / exe_name
            shutil.copy2(exe_path, instance_exe)
            
            # Make executable (Unix systems)
            if self.download_service.detect_os() in ['linux', 'darwin']:
                import os
                os.chmod(instance_exe, 0o755)
            
            # Create instance in database
            pm2_name = f"pb_{sanitized_name}"
            
            instance = Instance(
                name=sanitized_name,
                version=version,
                port=port,
                pm2_name=pm2_name,
                pb_path=str(instance_dir),
                dev_mode=dev_mode,
                domain=domain
            )
            
            db.session.add(instance)
            db.session.commit()
            
            print(f"✓ Instance '{sanitized_name}' created successfully")
            
            # Create superuser if credentials provided
            if admin_email and admin_password:
                try:
                    self.create_superuser(instance_dir, admin_email, admin_password)
                except Exception as superuser_error:
                    print(f"⚠ Warning: Failed to create superuser: {superuser_error}")
                    # Don't fail the entire instance creation if superuser creation fails
            
            return instance
        
        except Exception as e:
            # Cleanup on error
            if instance_dir.exists():
                shutil.rmtree(instance_dir)
            db.session.rollback()
            raise Exception(f"Failed to create instance: {e}")
    
    def get_all_instances(self) -> List[Instance]:
        """Get all instances"""
        return Instance.query.order_by(Instance.created_at.desc()).all()
    
    def get_instance(self, instance_id: int) -> Optional[Instance]:
        """Get instance by ID"""
        return Instance.query.get(instance_id)
    
    def get_instance_by_id(self, instance_id: int) -> Optional[Instance]:
        """Get instance by ID (alias for get_instance)"""
        return self.get_instance(instance_id)
    
    def get_instance_by_name(self, name: str) -> Optional[Instance]:
        """Get instance by name"""
        return Instance.query.filter_by(name=name).first()
    
    def update_dev_mode(self, instance_id: int, dev_mode: bool):
        """Update dev mode for an instance"""
        from models.database import db
        from models.instance import Instance
        
        instance = Instance.query.get(instance_id)
        if instance:
            instance.dev_mode = dev_mode
            db.session.commit()
    
    def regenerate_run_script(self, instance):
        """Regenerate run.sh script for an existing instance"""
        from pathlib import Path
        import os
        
        instance_dir = Path(instance.pb_path)
        run_script_path = instance_dir / 'run.sh'
        
        dev_flag = '--dev' if instance.dev_mode else ''
        run_script_content = f'''#!/bin/bash
set -e  # Exit on any error

# PocketBase Instance Runner
# Instance: {instance.name}
# Version: {instance.version}
# Port: {instance.port}
# Dev Mode: {instance.dev_mode}

cd "{instance_dir}"

# Check if pocketbase executable exists
if [ ! -f "./pocketbase" ]; then
    echo "Error: pocketbase executable not found in $(pwd)"
    exit 1
fi

exec "./pocketbase" serve \\
    --http "0.0.0.0:{instance.port}" \\
    --dir "{instance_dir}/pb_data" \\
    --hooksDir "{instance_dir}/pb_hooks" \\
    --migrationsDir "{instance_dir}/pb_migrations" \\
    --publicDir "{instance_dir}/pb_public" \\
    {dev_flag}
'''
        
        with open(run_script_path, 'w') as f:
            f.write(run_script_content)
        
        # Make script executable
        os.chmod(run_script_path, 0o755)
    
    def delete_instance(self, instance_id: int, remove_files: bool = True) -> bool:
        """
        Delete instance
        
        Args:
            instance_id: Instance ID
            remove_files: Whether to remove instance files
        
        Returns:
            True if successful
        """
        instance = self.get_instance(instance_id)
        if not instance:
            raise Exception(f"Instance with ID {instance_id} not found")
        
        try:
            # Stop and delete from PM2 if running
            if self.pm2_service.is_running(instance.pm2_name):
                self.pm2_service.stop_instance(instance.pm2_name)
            
            self.pm2_service.delete_instance(instance.pm2_name)
            
            # Remove files if requested
            if remove_files:
                instance_dir = Path(instance.pb_path)
                if instance_dir.exists():
                    shutil.rmtree(instance_dir)
                    print(f"✓ Removed instance directory: {instance_dir}")
            
            # Delete from database
            db.session.delete(instance)
            db.session.commit()
            
            print(f"✓ Instance '{instance.name}' deleted successfully")
            return True
        
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to delete instance: {e}")
    
    def get_instances_with_status(self) -> List[Dict]:
        """Get all instances with their PM2 status"""
        instances = self.get_all_instances()
        pm2_statuses = self.pm2_service.get_all_status()
        
        result = []
        for instance in instances:
            instance_data = instance.to_dict()
            pm2_status = pm2_statuses.get(instance.pm2_name, {})
            instance_data['pm2_status'] = pm2_status.get('status', 'stopped')
            instance_data['pid'] = pm2_status.get('pid')
            instance_data['cpu'] = pm2_status.get('cpu', 0)
            instance_data['memory'] = pm2_status.get('memory', 0)
            result.append(instance_data)
        
        return result
