from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required
from core.github_service import GitHubService
from core.instance_service import InstanceService
from core.pm2_service import PM2Service
from core.file_manager_service import FileManagerService

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/versions', methods=['GET'])
@login_required
def get_versions():
    """Get available PocketBase versions"""
    try:
        github_service = GitHubService()
        releases = github_service.get_releases()
        
        # Return only necessary info
        versions = [{
            'version': r['version'],
            'name': r['name'],
            'published_at': r['published_at']
        } for r in releases[:20]]  # Latest 20 versions
        
        return jsonify({'success': True, 'versions': versions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances', methods=['GET', 'POST'])
@login_required
def instances():
    """Get all instances or create new instance"""
    instance_service = InstanceService()
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name')
            version = data.get('version')
            port = data.get('port')
            dev_mode = data.get('dev_mode', False)  # Default to False if not provided
            admin_email = data.get('admin_email')
            admin_password = data.get('admin_password')
            domain = data.get('domain')
            
            if not name or not version:
                return jsonify({'success': False, 'error': 'Name and version are required'}), 400
            
            # Convert port to int if provided
            if port:
                try:
                    port = int(port)
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid port number'}), 400
            
            instance = instance_service.create_instance(
                name, version, port, dev_mode, admin_email, admin_password, domain
            )
            return jsonify({'success': True, 'instance': instance.to_dict()}), 201
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    else:  # GET
        try:
            instances = instance_service.get_instances_with_status()
            return jsonify({'success': True, 'instances': instances})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>', methods=['GET', 'DELETE'])
@login_required
def instance_detail(instance_id):
    """Get or delete specific instance"""
    instance_service = InstanceService()
    
    if request.method == 'DELETE':
        try:
            instance_service.delete_instance(instance_id)
            return jsonify({'success': True, 'message': 'Instance deleted successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    else:  # GET
        try:
            instance = instance_service.get_instance(instance_id)
            if not instance:
                return jsonify({'success': False, 'error': 'Instance not found'}), 404
            
            return jsonify({'success': True, 'instance': instance.to_dict()})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/start', methods=['POST'])
@login_required
def start_instance(instance_id):
    """Start PocketBase instance"""
    try:
        instance_service = InstanceService()
        pm2_service = PM2Service()
        
        instance = instance_service.get_instance(instance_id)
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        # Get executable path
        from pathlib import Path
        exe_name = instance_service.download_service.get_executable_name()
        exe_path = Path(instance.pb_path) / exe_name
        
        if not exe_path.exists():
            return jsonify({'success': False, 'error': 'Executable not found'}), 404
        
        # Start with PM2
        success = pm2_service.start_instance(
            instance.pm2_name,
            str(exe_path),
            instance.port,
            instance.pb_path
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Instance started successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start instance'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/stop', methods=['POST'])
@login_required
def stop_instance(instance_id):
    """Stop PocketBase instance"""
    try:
        instance_service = InstanceService()
        pm2_service = PM2Service()
        
        instance = instance_service.get_instance(instance_id)
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        success = pm2_service.stop_instance(instance.pm2_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Instance stopped successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to stop instance'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/restart', methods=['POST'])
@login_required
def restart_instance(instance_id):
    """Restart PocketBase instance"""
    try:
        instance_service = InstanceService()
        pm2_service = PM2Service()
        
        instance = instance_service.get_instance(instance_id)
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        success = pm2_service.restart_instance(instance.pm2_name)
        
        if success:
            return jsonify({'success': True, 'message': 'Instance restarted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to restart instance'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/dev', methods=['POST'])
@login_required
def toggle_dev_mode(instance_id):
    """Toggle dev mode for an instance"""
    try:
        instance_service = InstanceService()
        pm2_service = PM2Service()
        
        instance = instance_service.get_instance_by_id(instance_id)
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        # Toggle dev mode
        new_dev_mode = not instance.dev_mode
        
        # Update instance in database
        instance_service.update_dev_mode(instance_id, new_dev_mode)
        
        # Regenerate run.sh script
        instance_service.regenerate_run_script(instance)
        
        # Restart instance if it was running
        was_running = pm2_service.is_running(instance.pm2_name)
        if was_running:
            pm2_service.restart_instance(instance.pm2_name)
        
        return jsonify({
            'success': True,
            'dev_mode': new_dev_mode,
            'message': f"Dev mode {'enabled' if new_dev_mode else 'disabled'} successfully"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/logs', methods=['GET'])
@login_required
def get_logs(instance_id):
    """Get instance logs"""
    try:
        instance_service = InstanceService()
        pm2_service = PM2Service()
        
        instance = instance_service.get_instance(instance_id)
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        lines = request.args.get('lines', 100, type=int)
        logs = pm2_service.get_logs(instance.pm2_name, lines)
        
        return jsonify({'success': True, 'logs': logs})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/status', methods=['GET'])
@login_required
def get_status(instance_id):
    """Get instance status"""
    try:
        instance_service = InstanceService()
        pm2_service = PM2Service()
        
        instance = instance_service.get_instance(instance_id)
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        status = pm2_service.get_instance_status(instance.pm2_name)
        
        return jsonify({
            'success': True,
            'status': status if status else {'status': 'stopped'}
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/version', methods=['POST'])
@login_required
def update_version(instance_id):
    """Update PocketBase version for an instance"""
    try:
        instance_service = InstanceService()
        
        data = request.get_json()
        new_version = data.get('version', '')
        
        if not new_version:
            return jsonify({'success': False, 'error': 'Version required'}), 400
        
        instance_service.update_version(instance_id, new_version)
        
        return jsonify({'success': True, 'message': f'Instance updated to v{new_version}'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/domain', methods=['POST'])
@login_required
def update_domain(instance_id):
    """Update domain for an instance"""
    try:
        instance_service = InstanceService()
        
        data = request.get_json()
        domain = data.get('domain', None)
        
        # Empty string should be converted to None
        if domain == '':
            domain = None
        
        instance_service.update_domain(instance_id, domain)
        
        return jsonify({'success': True, 'message': 'Domain updated successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# File Manager Routes

@api_bp.route('/instances/<int:instance_id>/files', methods=['GET'])
@login_required
def list_files(instance_id):
    """List files and folders in instance directory"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        path = request.args.get('path', '')
        file_manager = FileManagerService(instance.pb_path)
        
        result = file_manager.list_directory(path)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/files/upload', methods=['POST'])
@login_required
def upload_files(instance_id):
    """Upload files to instance directory"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        path = request.form.get('path', '')
        replace = request.form.get('replace', 'true').lower() == 'true'
        
        files = request.files.getlist('files')
        file_manager = FileManagerService(instance.pb_path)
        
        results = []
        for file in files:
            if file.filename:
                result = file_manager.save_file(path, file.filename, file, replace)
                results.append(result)
        
        # Check if all uploads succeeded
        all_success = all(r['success'] for r in results)
        
        return jsonify({
            'success': all_success,
            'results': results,
            'message': f"Uploaded {len(results)} file(s)"
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/files/download', methods=['GET'])
@login_required
def download_file(instance_id):
    """Download a file from instance directory"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        path = request.args.get('path', '')
        if not path:
            return jsonify({'success': False, 'error': 'Path required'}), 400
        
        file_manager = FileManagerService(instance.pb_path)
        file_path = file_manager.get_file_path(path)
        
        return send_file(file_path, as_attachment=True, download_name=file_path.name)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_bp.route('/instances/<int:instance_id>/files/mkdir', methods=['POST'])
@login_required
def create_folder(instance_id):
    """Create a new folder"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        data = request.get_json()
        path = data.get('path', '')
        folder_name = data.get('name', '')
        
        if not folder_name:
            return jsonify({'success': False, 'error': 'Folder name required'}), 400
        
        file_manager = FileManagerService(instance.pb_path)
        result = file_manager.create_folder(path, folder_name)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/files/delete', methods=['POST'])
@login_required
def delete_item(instance_id):
    """Delete a file or folder"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        data = request.get_json()
        path = data.get('path', '')
        
        if not path:
            return jsonify({'success': False, 'error': 'Path required'}), 400
        
        file_manager = FileManagerService(instance.pb_path)
        result = file_manager.delete_item(path)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/files/copy', methods=['POST'])
@login_required
def copy_item(instance_id):
    """Copy a file or folder"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        data = request.get_json()
        source = data.get('source', '')
        dest = data.get('dest', '')
        
        if not source or not dest:
            return jsonify({'success': False, 'error': 'Source and destination required'}), 400
        
        file_manager = FileManagerService(instance.pb_path)
        result = file_manager.copy_item(source, dest)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/files/move', methods=['POST'])
@login_required
def move_item(instance_id):
    """Move/rename a file or folder"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        data = request.get_json()
        source = data.get('source', '')
        dest = data.get('dest', '')
        
        if not source or not dest:
            return jsonify({'success': False, 'error': 'Source and destination required'}), 400
        
        file_manager = FileManagerService(instance.pb_path)
        result = file_manager.move_item(source, dest)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Admin Management Routes

@api_bp.route('/instances/<int:instance_id>/admins', methods=['GET'])
@login_required
def list_instance_admins(instance_id):
    """List all admin users for an instance"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        from pathlib import Path
        admins = instance_service.list_admins(Path(instance.pb_path))
        
        return jsonify({'success': True, 'admins': admins})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/admins', methods=['POST'])
@login_required
def add_instance_admin(instance_id):
    """Add a new admin user to an instance"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        from pathlib import Path
        instance_service.add_admin(Path(instance.pb_path), email, password)
        
        return jsonify({'success': True, 'message': f'Admin user {email} added successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/instances/<int:instance_id>/admins/<admin_id>', methods=['DELETE'])
@login_required
def delete_instance_admin(instance_id, admin_id):
    """Remove an admin user from an instance"""
    try:
        instance_service = InstanceService()
        instance = instance_service.get_instance(instance_id)
        
        if not instance:
            return jsonify({'success': False, 'error': 'Instance not found'}), 404
        
        from pathlib import Path
        instance_service.remove_admin(Path(instance.pb_path), admin_id)
        
        return jsonify({'success': True, 'message': 'Admin user removed successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
