from flask import Blueprint, render_template
from flask_login import login_required
from core.instance_service import InstanceService
from core.github_service import GitHubService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    instance_service = InstanceService()
    github_service = GitHubService()
    
    # Get instances with status
    instances = instance_service.get_instances_with_status()
    
    # Get available versions
    releases = github_service.get_releases()
    versions = [r['version'] for r in releases[:10]]  # Latest 10 versions
    
    return render_template('dashboard.html', instances=instances, versions=versions)
