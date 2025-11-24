import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database
    BASE_DIR = Path(__file__).parent
    STORAGE_DIR = BASE_DIR / 'storage'
    STORAGE_DIR.mkdir(exist_ok=True)
    
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'storage/instances.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR / DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PocketBase Instances
    INSTANCES_DIR = Path(os.path.expanduser(os.getenv('INSTANCES_DIR', '~/pocketbase-instances')))
    INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Downloads cache
    DOWNLOADS_DIR = INSTANCES_DIR / '.downloads'
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    
    # Admin credentials
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Port configuration
    DEFAULT_PORT_START = int(os.getenv('DEFAULT_PORT_START', '7200'))
    
    # GitHub API
    GITHUB_API_URL = os.getenv('GITHUB_API_URL', 'https://api.github.com/repos/pocketbase/pocketbase/releases')
    GITHUB_CACHE_DURATION = int(os.getenv('GITHUB_CACHE_DURATION', '3600'))
