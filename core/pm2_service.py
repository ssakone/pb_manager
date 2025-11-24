import json
import subprocess
from typing import Dict, List, Optional


class PM2Service:
    """Service to interact with PM2 process manager"""
    
    @staticmethod
    def _run_command(command: List[str]) -> tuple:
        """
        Run PM2 command and return output
        
        Returns:
            Tuple of (success: bool, output: str, error: str)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            return (result.returncode == 0, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (False, '', 'Command timeout')
        except Exception as e:
            return (False, '', str(e))
    
    def start_instance(self, name: str, executable_path: str, port: int, data_dir: str) -> bool:
        """
        Start PocketBase instance with PM2 using run.sh script
        
        Args:
            name: PM2 process name
            executable_path: Path to PocketBase executable (not used directly anymore)
            port: Port to bind (not used directly anymore, handled by run.sh)
            data_dir: Path to instance directory
        
        Returns:
            True if successful
        """
        # Use run.sh script instead of direct executable
        run_script_path = f"{data_dir}/run.sh"
        
        # Check if run.sh exists (for migration purposes)
        from pathlib import Path
        if not Path(run_script_path).exists():
            raise Exception(f"run.sh script not found. This instance needs to be recreated to use the new script-based startup system.")
        
        command = [
            'pm2', 'start', run_script_path,
            '--name', name,
            '--cwd', data_dir,  # Set working directory
            '--time'  # Add timestamps to logs
        ]
        
        success, stdout, stderr = self._run_command(command)
        if not success:
            print(f"Failed to start instance: {stderr}")
        return success
    
    def stop_instance(self, pm2_name: str) -> bool:
        """Stop PM2 process"""
        success, stdout, stderr = self._run_command(['pm2', 'stop', pm2_name])
        if not success:
            print(f"Failed to stop instance: {stderr}")
        return success
    
    def restart_instance(self, pm2_name: str) -> bool:
        """Restart PM2 process"""
        success, stdout, stderr = self._run_command(['pm2', 'restart', pm2_name])
        if not success:
            print(f"Failed to restart instance: {stderr}")
        return success
    
    def delete_instance(self, pm2_name: str) -> bool:
        """Delete PM2 process"""
        success, stdout, stderr = self._run_command(['pm2', 'delete', pm2_name])
        if not success:
            print(f"Failed to delete instance: {stderr}")
        return success
    
    def get_all_status(self) -> Dict[str, Dict]:
        """
        Get status of all PM2 processes
        
        Returns:
            Dict with pm2_name as key and status info as value
        """
        success, stdout, stderr = self._run_command(['pm2', 'jlist'])
        
        if not success:
            print(f"Failed to get PM2 status: {stderr}")
            return {}
        
        try:
            processes = json.loads(stdout)
            status_map = {}
            
            for proc in processes:
                name = proc.get('name')
                pm2_env = proc.get('pm2_env', {})
                
                status_map[name] = {
                    'status': pm2_env.get('status', 'unknown'),
                    'pid': proc.get('pid'),
                    'cpu': proc.get('monit', {}).get('cpu', 0),
                    'memory': proc.get('monit', {}).get('memory', 0),
                    'uptime': pm2_env.get('pm_uptime', 0),
                    'restarts': pm2_env.get('restart_time', 0)
                }
            
            return status_map
        except json.JSONDecodeError:
            print("Failed to parse PM2 jlist output")
            return {}
    
    def get_instance_status(self, pm2_name: str) -> Optional[Dict]:
        """Get status of specific instance"""
        all_status = self.get_all_status()
        return all_status.get(pm2_name)
    
    def get_logs(self, pm2_name: str, lines: int = 100) -> str:
        """
        Get logs for specific instance
        
        Args:
            pm2_name: PM2 process name
            lines: Number of lines to retrieve
        
        Returns:
            Log output as string
        """
        success, stdout, stderr = self._run_command([
            'pm2', 'logs', pm2_name,
            '--lines', str(lines),
            '--nostream'
            # Note: --time flag is set during startup, not needed here
        ])
        
        if not success:
            return f"Failed to get logs: {stderr}"
        
        return stdout
    
    def is_running(self, pm2_name: str) -> bool:
        """Check if instance is running"""
        status = self.get_instance_status(pm2_name)
        if status:
            return status.get('status') == 'online'
        return False
