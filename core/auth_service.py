from werkzeug.security import check_password_hash
from models.database import User


class AuthService:
    """Service for user authentication"""
    
    @staticmethod
    def verify_user(username: str, password: str) -> User:
        """
        Verify user credentials
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            User object if credentials are valid, None otherwise
        """
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            return user
        
        return None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        """Get user by ID"""
        return User.query.get(int(user_id))
