from flask import Flask
from flask_login import LoginManager
from config import Config
from models.database import db, init_db, User
from core.auth_service import AuthService
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.api import api_bp


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    init_db(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @app.context_processor
    def inject_app_version():
        return {'APP_VERSION': Config.APP_VERSION}
    
    @login_manager.user_loader
    def load_user(user_id):
        return AuthService.get_user_by_id(user_id)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Force database schema creation with new dev_mode column
    with app.app_context():
        db.create_all()
        print("✅ Database schema created/updated")
    
    print("\n" + "="*50)
    print("🗄️  PocketBase Manager")
    print("="*50)
    print(f"📁 Instances directory: {Config.INSTANCES_DIR}")
    print(f"📁 Downloads directory: {Config.DOWNLOADS_DIR}")
    print(f"🔑 Admin user: {Config.ADMIN_USERNAME}")
    print("="*50)
    print(f"\n🚀 Starting server at http://{Config.HOST}:{Config.PORT}")
    print("\n")
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
