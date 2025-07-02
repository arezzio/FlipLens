"""
User Profile routes for FlipLens application
"""

from flask import jsonify, request, g
from . import api_bp
from utils.rate_limiter import rate_limit
from utils.auth_middleware import auth_required, get_current_user
from utils.validation import validate_json_input
from models.user import User
from models.user_settings import UserSettings
from models.database import db
import logging
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

# Validation schemas
PROFILE_UPDATE_SCHEMA = {
    'type': 'object',
    'properties': {
        'first_name': {'type': 'string', 'maxLength': 50},
        'last_name': {'type': 'string', 'maxLength': 50},
        'username': {'type': 'string', 'minLength': 3, 'maxLength': 50},
        'email': {'type': 'string', 'format': 'email', 'maxLength': 120},
        'bio': {'type': 'string', 'maxLength': 500},
        'location': {'type': 'string', 'maxLength': 100},
        'website': {'type': 'string', 'maxLength': 200}
    }
}

PASSWORD_CHANGE_SCHEMA = {
    'type': 'object',
    'required': ['current_password', 'new_password'],
    'properties': {
        'current_password': {'type': 'string', 'minLength': 1},
        'new_password': {'type': 'string', 'minLength': 8, 'maxLength': 128}
    }
}

@api_bp.route('/profile', methods=['GET'])
@rate_limit('/api/profile')
@auth_required
def get_profile():
    """Get user profile information"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        logger.info(f"Getting profile for user {user.id}")
        
        # Get user settings
        settings = UserSettings.get_or_create_settings(user.id)
        
        # Build profile data
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': getattr(user, 'bio', ''),
            'location': getattr(user, 'location', ''),
            'website': getattr(user, 'website', ''),
            'profile_picture': getattr(user, 'profile_picture', None),
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_verified': getattr(user, 'is_verified', False),
            'settings': settings.to_dict() if settings else None
        }
        
        return jsonify({
            "profile": profile_data,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve profile",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/profile', methods=['PUT'])
@rate_limit('/api/profile')
@auth_required
@validate_json_input(PROFILE_UPDATE_SCHEMA)
def update_profile():
    """Update user profile information"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        data = getattr(g, 'validated_json', None)
        if not data:
            return jsonify({
                "error": "Invalid Request",
                "message": "Validated data not found",
                "status": "error",
                "code": "VALIDATION_ERROR"
            }), 400
        
        logger.info(f"Updating profile for user {user.id}")
        
        # Check if username or email is being changed and if they're already taken
        if 'username' in data and data['username'] != user.username:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({
                    "error": "Username Taken",
                    "message": "Username is already taken",
                    "status": "error",
                    "code": "USERNAME_EXISTS"
                }), 400
        
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({
                    "error": "Email Taken",
                    "message": "Email is already registered",
                    "status": "error",
                    "code": "EMAIL_EXISTS"
                }), 400
        
        # Update user fields
        updatable_fields = ['first_name', 'last_name', 'username', 'email', 'bio', 'location', 'website']
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        # Get updated settings
        settings = UserSettings.get_or_create_settings(user.id)
        
        # Build updated profile data
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': getattr(user, 'bio', ''),
            'location': getattr(user, 'location', ''),
            'website': getattr(user, 'website', ''),
            'profile_picture': getattr(user, 'profile_picture', None),
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_verified': getattr(user, 'is_verified', False),
            'settings': settings.to_dict() if settings else None
        }
        
        return jsonify({
            "profile": profile_data,
            "message": "Profile updated successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to update profile",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/profile/password', methods=['PUT'])
@rate_limit('/api/profile')
@auth_required
@validate_json_input(PASSWORD_CHANGE_SCHEMA)
def change_password():
    """Change user password"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        data = getattr(g, 'validated_json', None)
        if not data:
            return jsonify({
                "error": "Invalid Request",
                "message": "Validated data not found",
                "status": "error",
                "code": "VALIDATION_ERROR"
            }), 400
        
        logger.info(f"Changing password for user {user.id}")
        
        # Verify current password
        if not check_password_hash(user.password_hash, data['current_password']):
            return jsonify({
                "error": "Invalid Password",
                "message": "Current password is incorrect",
                "status": "error",
                "code": "INVALID_CURRENT_PASSWORD"
            }), 400
        
        # Validate new password strength
        new_password = data['new_password']
        if len(new_password) < 8:
            return jsonify({
                "error": "Weak Password",
                "message": "Password must be at least 8 characters long",
                "status": "error",
                "code": "PASSWORD_TOO_SHORT"
            }), 400
        
        # Check if new password is different from current
        if check_password_hash(user.password_hash, new_password):
            return jsonify({
                "error": "Same Password",
                "message": "New password must be different from current password",
                "status": "error",
                "code": "SAME_PASSWORD"
            }), 400
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            "message": "Password changed successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to change password",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/profile/picture', methods=['POST'])
@rate_limit('/api/profile')
@auth_required
def upload_profile_picture():
    """Upload profile picture"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # For now, return a placeholder response
        # In production, implement actual file upload logic
        return jsonify({
            "message": "Profile picture upload not yet implemented",
            "status": "info",
            "code": "NOT_IMPLEMENTED"
        }), 501
        
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to upload profile picture",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/profile/delete', methods=['DELETE'])
@rate_limit('/api/profile')
@auth_required
def delete_account():
    """Delete user account"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({
                "error": "Password Required",
                "message": "Password confirmation required for account deletion",
                "status": "error",
                "code": "PASSWORD_REQUIRED"
            }), 400
        
        # Verify password
        if not check_password_hash(user.password_hash, data['password']):
            return jsonify({
                "error": "Invalid Password",
                "message": "Password is incorrect",
                "status": "error",
                "code": "INVALID_PASSWORD"
            }), 400
        
        logger.info(f"Deleting account for user {user.id}")
        
        # In production, you might want to:
        # 1. Soft delete (mark as deleted but keep data)
        # 2. Anonymize data instead of hard delete
        # 3. Send confirmation email
        # 4. Add a grace period for account recovery
        
        # For now, we'll do a hard delete
        user_id = user.id
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"Account deleted for user {user_id}")
        
        return jsonify({
            "message": "Account deleted successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting account: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to delete account",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/profile/stats', methods=['GET'])
@rate_limit('/api/profile')
@auth_required
def get_profile_stats():
    """Get user profile statistics"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Import here to avoid circular imports
        from models.saved_item import SavedItem
        from models.portfolio_item import PortfolioItem
        from models.price_alert import PriceAlert
        from models.search_history import SearchHistory
        
        # Calculate statistics
        saved_items_count = SavedItem.query.filter_by(user_id=user.id).count()
        portfolio_items_count = PortfolioItem.query.filter_by(user_id=user.id).count()
        active_alerts_count = PriceAlert.query.filter_by(user_id=user.id, is_active=True).count()
        searches_count = SearchHistory.query.filter_by(user_id=user.id).count()
        
        # Calculate portfolio value (mock calculation)
        portfolio_items = PortfolioItem.query.filter_by(user_id=user.id).all()
        total_investment = sum(float(item.purchase_price) for item in portfolio_items)
        estimated_value = sum(float(item.current_market_price or item.purchase_price) for item in portfolio_items)
        
        stats = {
            'saved_items': saved_items_count,
            'portfolio_items': portfolio_items_count,
            'active_alerts': active_alerts_count,
            'total_searches': searches_count,
            'portfolio_value': {
                'total_investment': round(total_investment, 2),
                'estimated_value': round(estimated_value, 2),
                'profit_loss': round(estimated_value - total_investment, 2)
            },
            'member_since': user.created_at.isoformat() if user.created_at else None
        }
        
        return jsonify({
            "stats": stats,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting profile stats: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve profile statistics",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500
