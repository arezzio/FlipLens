"""
Authentication routes for FlipLens application
"""

from flask import jsonify, request, current_app
from . import api_bp
from utils.rate_limiter import rate_limit
from utils.security import SecurityValidator, InputValidation
from models.user import User
from models.database import db
import logging
import re
from email_validator import validate_email, EmailNotValidError
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is strong"

@api_bp.route('/auth/register', methods=['POST'])
@rate_limit('/api/auth/register', per_minute=5)  # Stricter rate limit for registration
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid Request",
                "message": "Request body must be JSON",
                "status": "error",
                "code": "INVALID_JSON"
            }), 400
        
        # Validate required fields
        required_fields = ['email', 'username', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": "Missing Fields",
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "status": "error",
                "code": "MISSING_FIELDS"
            }), 400
        
        email = data['email'].strip().lower()
        username = data['username'].strip()
        password = data['password']
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Validate email format
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({
                "error": "Invalid Email",
                "message": "Please provide a valid email address",
                "status": "error",
                "code": "INVALID_EMAIL"
            }), 400
        
        # Validate username
        if not SecurityValidator.validate_string(username, 'alphanumeric', max_length=30):
            return jsonify({
                "error": "Invalid Username",
                "message": "Username must be 1-30 characters and contain only letters and numbers",
                "status": "error",
                "code": "INVALID_USERNAME"
            }), 400
        
        # Validate password strength
        is_strong, password_message = validate_password_strength(password)
        if not is_strong:
            return jsonify({
                "error": "Weak Password",
                "message": password_message,
                "status": "error",
                "code": "WEAK_PASSWORD"
            }), 400
        
        # Validate optional name fields
        if first_name and not SecurityValidator.validate_string(first_name, 'safe_text', max_length=50):
            return jsonify({
                "error": "Invalid First Name",
                "message": "First name contains invalid characters",
                "status": "error",
                "code": "INVALID_FIRST_NAME"
            }), 400
        
        if last_name and not SecurityValidator.validate_string(last_name, 'safe_text', max_length=50):
            return jsonify({
                "error": "Invalid Last Name",
                "message": "Last name contains invalid characters",
                "status": "error",
                "code": "INVALID_LAST_NAME"
            }), 400
        
        # Create user
        try:
            user = User.create_user(
                email=email,
                username=username,
                password=password,
                first_name=first_name or None,
                last_name=last_name or None
            )
            
            # Generate JWT token
            token = user.generate_jwt_token(expires_in=86400)  # 24 hours
            
            if not token:
                return jsonify({
                    "error": "Token Generation Failed",
                    "message": "Failed to generate authentication token",
                    "status": "error",
                    "code": "TOKEN_GENERATION_FAILED"
                }), 500
            
            logger.info(f"User registered successfully: {user.username} ({user.email})")
            
            return jsonify({
                "message": "User registered successfully",
                "user": user.to_dict(),
                "token": token,
                "status": "success"
            }), 201
            
        except ValueError as e:
            return jsonify({
                "error": "Registration Failed",
                "message": str(e),
                "status": "error",
                "code": "REGISTRATION_FAILED"
            }), 409
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Registration failed due to server error",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/auth/login', methods=['POST'])
@rate_limit('/api/auth/login', per_minute=10)  # Rate limit for login attempts
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid Request",
                "message": "Request body must be JSON",
                "status": "error",
                "code": "INVALID_JSON"
            }), 400
        
        # Validate required fields
        email_or_username = data.get('email') or data.get('username')
        password = data.get('password')
        
        if not email_or_username or not password:
            return jsonify({
                "error": "Missing Credentials",
                "message": "Email/username and password are required",
                "status": "error",
                "code": "MISSING_CREDENTIALS"
            }), 400
        
        # Find user by email or username
        user = None
        if '@' in email_or_username:
            # It's an email
            user = User.query.filter_by(email=email_or_username.lower().strip()).first()
        else:
            # It's a username
            user = User.query.filter_by(username=email_or_username.strip()).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                "error": "Invalid Credentials",
                "message": "Invalid email/username or password",
                "status": "error",
                "code": "INVALID_CREDENTIALS"
            }), 401
        
        if not user.is_active:
            return jsonify({
                "error": "Account Disabled",
                "message": "Your account has been disabled",
                "status": "error",
                "code": "ACCOUNT_DISABLED"
            }), 403
        
        # Generate JWT token
        token = user.generate_jwt_token(expires_in=86400)  # 24 hours
        
        if not token:
            return jsonify({
                "error": "Token Generation Failed",
                "message": "Failed to generate authentication token",
                "status": "error",
                "code": "TOKEN_GENERATION_FAILED"
            }), 500
        
        # Update last login
        user.update_last_login()
        
        logger.info(f"User logged in successfully: {user.username}")
        
        return jsonify({
            "message": "Login successful",
            "user": user.to_dict(),
            "token": token,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Login failed due to server error",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/auth/me', methods=['GET'])
@rate_limit('/api/auth/me')
def get_current_user():
    """Get current user information"""
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
        
        return jsonify({
            "user": user.to_dict(),
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to get user information",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/auth/logout', methods=['POST'])
@rate_limit('/api/auth/logout')
def logout():
    """User logout endpoint (client-side token removal)"""
    try:
        # In a JWT-based system, logout is primarily handled client-side
        # by removing the token. We can log the logout event here.
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user = User.verify_jwt_token(token)
            
            if user:
                logger.info(f"User logged out: {user.username}")
        
        return jsonify({
            "message": "Logout successful",
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Logout failed due to server error",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500
