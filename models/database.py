from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import sqlite3

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'


def migrate_database(app):
    """Run database migrations for schema changes"""
    from pathlib import Path
    
    db_path = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    
    if not db_path.exists():
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if domain column exists in instances table
        cursor.execute("PRAGMA table_info(instances)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'domain' not in columns:
            print("🔄 Adding 'domain' column to instances table...")
            cursor.execute("ALTER TABLE instances ADD COLUMN domain VARCHAR(255)")
            conn.commit()
            print("✅ Migration completed: 'domain' column added")
        
        conn.close()
    except Exception as e:
        print(f"⚠️  Migration warning: {e}")


def init_db(app):
    """Initialize database and create tables"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        migrate_database(app)
        
        # Create admin user if not exists
        from werkzeug.security import generate_password_hash
        from config import Config
        
        admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=Config.ADMIN_USERNAME,
                password=generate_password_hash(Config.ADMIN_PASSWORD)
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Admin user created: {Config.ADMIN_USERNAME}")
