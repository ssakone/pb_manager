from datetime import datetime
from models.database import db


class Instance(db.Model):
    """PocketBase instance model"""
    __tablename__ = 'instances'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    version = db.Column(db.String(20), nullable=False)
    port = db.Column(db.Integer, unique=True, nullable=False)
    pm2_name = db.Column(db.String(150), unique=True, nullable=False)
    pb_path = db.Column(db.String(500), nullable=False)
    dev_mode = db.Column(db.Boolean, default=False, nullable=False)
    domain = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Instance {self.name} v{self.version}>'
    
    def to_dict(self):
        """Convert instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'port': self.port,
            'pm2_name': self.pm2_name,
            'pb_path': self.pb_path,
            'dev_mode': self.dev_mode,
            'domain': self.domain,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
