"""
User model for FlipLens application
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app
import secrets
import logging

from .database import db

logger = logging.getLogger(__name__)

class User(db.Model):
    """User model with authentication and profile management"""
    
    __tablename__ = 'users'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile fields
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Security fields
    email_verification_token = db.Column(db.String(255), nullable=True)
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    saved_items = db.relationship('SavedItem', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, email, username, password, first_name=None, last_name=None):
        self.email = email.lower().strip()
        self.username = username.strip()
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.email_verification_token = self.generate_verification_token()
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        """Generate email verification token"""
        return secrets.token_urlsafe(32)
    
    def generate_password_reset_token(self):
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verify password reset token"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if datetime.utcnow() > self.password_reset_expires:
            return False
        
        return self.password_reset_token == token
    
    def generate_jwt_token(self, expires_in=3600):
        """Generate JWT token for authentication"""
        try:
            payload = {
                'user_id': self.id,
                'username': self.username,
                'email': self.email,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(
                payload,
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            
            return token
        except Exception as e:
            logger.error(f"Failed to generate JWT token for user {self.id}: {str(e)}")
            return None
    
    @staticmethod
    def verify_jwt_token(token):
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return None
            
            return user
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to verify JWT token: {str(e)}")
            return None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data.update({
                'email_verification_token': self.email_verification_token,
                'password_reset_token': self.password_reset_token,
                'password_reset_expires': self.password_reset_expires.isoformat() if self.password_reset_expires else None,
            })
        
        return data
    
    @classmethod
    def create_user(cls, email, username, password, first_name=None, last_name=None):
        """Create a new user with validation"""
        try:
            # Check if user already exists
            if cls.query.filter_by(email=email.lower()).first():
                raise ValueError("Email already registered")
            
            if cls.query.filter_by(username=username).first():
                raise ValueError("Username already taken")
            
            # Create new user
            user = cls(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user created: {user.username} ({user.email})")
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    def delete_user(self):
        """Delete user and all associated data"""
        try:
            db.session.delete(self)
            db.session.commit()
            logger.info(f"User deleted: {self.username}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete user {self.username}: {str(e)}")
            raise
