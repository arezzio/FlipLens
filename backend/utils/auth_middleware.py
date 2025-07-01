"""
Authentication middleware for FlipLens application
"""

from functools import wraps
from flask import request, jsonify, g
from models.user import User
import logging

logger = logging.getLogger(__name__)

def auth_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    "error": "Missing Token",
                    "message": "Authorization token is required",
                    "status": "error",
                    "code": "MISSING_TOKEN"
                }), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify token and get user
            user = User.verify_jwt_token(token)
            
            if not user:
                return jsonify({
                    "error": "Invalid Token",
                    "message": "Invalid or expired token",
                    "status": "error",
                    "code": "INVALID_TOKEN"
                }), 401
            
            if not user.is_active:
                return jsonify({
                    "error": "Account Disabled",
                    "message": "Your account has been disabled",
                    "status": "error",
                    "code": "ACCOUNT_DISABLED"
                }), 403
            
            # Store user in Flask's g object for use in the route
            g.current_user = user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Authentication Error",
                "message": "Failed to authenticate request",
                "status": "error",
                "code": "AUTHENTICATION_ERROR"
            }), 500
    
    return decorated_function

def auth_optional(f):
    """Decorator to optionally authenticate routes (user can be None)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Verify token and get user
                user = User.verify_jwt_token(token)
                
                if user and user.is_active:
                    g.current_user = user
                else:
                    g.current_user = None
            else:
                g.current_user = None
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Optional authentication error: {str(e)}", exc_info=True)
            # For optional auth, we don't fail the request
            g.current_user = None
            return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get the current authenticated user from Flask's g object"""
    return getattr(g, 'current_user', None)

def require_verified_user(f):
    """Decorator to require verified user account"""
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user.is_verified:
            return jsonify({
                "error": "Account Not Verified",
                "message": "Please verify your email address to access this feature",
                "status": "error",
                "code": "ACCOUNT_NOT_VERIFIED"
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges (for future use)"""
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        # For now, we'll use a simple check - in the future, add admin role
        if not hasattr(user, 'is_admin') or not user.is_admin:
            return jsonify({
                "error": "Admin Required",
                "message": "Admin privileges required to access this resource",
                "status": "error",
                "code": "ADMIN_REQUIRED"
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
