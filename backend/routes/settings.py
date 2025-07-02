"""
User Settings routes for FlipLens application
"""

from flask import jsonify, request, g
from . import api_bp
from utils.rate_limiter import rate_limit
from utils.auth_middleware import auth_required, get_current_user
from utils.validation import validate_json_input
from models.user_settings import UserSettings
from models.database import db
import logging

logger = logging.getLogger(__name__)

# Validation schema for settings update
SETTINGS_UPDATE_SCHEMA = {
    'type': 'object',
    'properties': {
        'notifications': {
            'type': 'object',
            'properties': {
                'email_notifications': {'type': 'boolean'},
                'push_notifications': {'type': 'boolean'},
                'price_alert_notifications': {'type': 'boolean'},
                'market_update_notifications': {'type': 'boolean'},
                'newsletter_notifications': {'type': 'boolean'}
            }
        },
        'app_preferences': {
            'type': 'object',
            'properties': {
                'dark_mode': {'type': 'boolean'},
                'currency': {'type': 'string', 'enum': ['USD', 'EUR', 'GBP', 'CAD', 'AUD']},
                'language': {'type': 'string', 'enum': ['en', 'es', 'fr', 'de', 'it']},
                'timezone': {'type': 'string', 'maxLength': 50}
            }
        },
        'display_preferences': {
            'type': 'object',
            'properties': {
                'items_per_page': {'type': 'integer', 'minimum': 10, 'maximum': 100},
                'default_sort_order': {'type': 'string'},
                'show_profit_percentage': {'type': 'boolean'},
                'show_fliplens_rating': {'type': 'boolean'}
            }
        },
        'privacy_settings': {
            'type': 'object',
            'properties': {
                'profile_visibility': {'type': 'string', 'enum': ['private', 'public']},
                'share_analytics': {'type': 'boolean'}
            }
        },
        'platform_integrations': {
            'type': 'object',
            'properties': {
                'ebay': {
                    'type': 'object',
                    'properties': {
                        'connected': {'type': 'boolean'},
                        'username': {'type': 'string', 'maxLength': 100}
                    }
                },
                'poshmark': {
                    'type': 'object',
                    'properties': {
                        'connected': {'type': 'boolean'},
                        'username': {'type': 'string', 'maxLength': 100}
                    }
                },
                'mercari': {
                    'type': 'object',
                    'properties': {
                        'connected': {'type': 'boolean'},
                        'username': {'type': 'string', 'maxLength': 100}
                    }
                }
            }
        },
        'advanced_settings': {
            'type': 'object',
            'properties': {
                'auto_update_market_prices': {'type': 'boolean'},
                'price_update_frequency': {'type': 'string', 'enum': ['hourly', 'daily', 'weekly']},
                'enable_experimental_features': {'type': 'boolean'}
            }
        }
    }
}

@api_bp.route('/settings', methods=['GET'])
@rate_limit('/api/settings')
@auth_required
def get_settings():
    """Get user settings"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        logger.info(f"Getting settings for user {user.id}")
        
        # Get or create user settings
        settings = UserSettings.get_or_create_settings(user.id)
        
        return jsonify({
            "settings": settings.to_dict(),
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve settings",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/settings', methods=['PUT'])
@rate_limit('/api/settings')
@auth_required
@validate_json_input(SETTINGS_UPDATE_SCHEMA)
def update_settings():
    """Update user settings"""
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
        
        logger.info(f"Updating settings for user {user.id}")
        
        # Get or create user settings
        settings = UserSettings.get_or_create_settings(user.id)
        
        # Update settings
        success = settings.update_settings(data)
        
        if not success:
            return jsonify({
                "error": "Update Failed",
                "message": "Failed to update settings",
                "status": "error",
                "code": "UPDATE_FAILED"
            }), 500
        
        return jsonify({
            "settings": settings.to_dict(),
            "message": "Settings updated successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to update settings",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/settings/reset', methods=['POST'])
@rate_limit('/api/settings')
@auth_required
def reset_settings():
    """Reset user settings to defaults"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        logger.info(f"Resetting settings to defaults for user {user.id}")
        
        # Reset settings to defaults
        settings = UserSettings.reset_to_defaults(user.id)
        
        if not settings:
            return jsonify({
                "error": "Reset Failed",
                "message": "Failed to reset settings",
                "status": "error",
                "code": "RESET_FAILED"
            }), 500
        
        return jsonify({
            "settings": settings.to_dict(),
            "message": "Settings reset to defaults successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to reset settings",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/settings/currencies', methods=['GET'])
@rate_limit('/api/settings')
def get_supported_currencies():
    """Get list of supported currencies"""
    try:
        currencies = [
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "EUR", "name": "Euro", "symbol": "€"},
            {"code": "GBP", "name": "British Pound", "symbol": "£"},
            {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$"},
            {"code": "AUD", "name": "Australian Dollar", "symbol": "A$"},
        ]
        
        return jsonify({
            "currencies": currencies,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting currencies: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve currencies",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/settings/languages', methods=['GET'])
@rate_limit('/api/settings')
def get_supported_languages():
    """Get list of supported languages"""
    try:
        languages = [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "es", "name": "Spanish", "native_name": "Español"},
            {"code": "fr", "name": "French", "native_name": "Français"},
            {"code": "de", "name": "German", "native_name": "Deutsch"},
            {"code": "it", "name": "Italian", "native_name": "Italiano"},
        ]
        
        return jsonify({
            "languages": languages,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting languages: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve languages",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/settings/timezones', methods=['GET'])
@rate_limit('/api/settings')
def get_supported_timezones():
    """Get list of supported timezones"""
    try:
        # Common timezones - in production, you might want to use pytz for a complete list
        timezones = [
            {"value": "UTC", "label": "UTC (Coordinated Universal Time)"},
            {"value": "America/New_York", "label": "Eastern Time (US & Canada)"},
            {"value": "America/Chicago", "label": "Central Time (US & Canada)"},
            {"value": "America/Denver", "label": "Mountain Time (US & Canada)"},
            {"value": "America/Los_Angeles", "label": "Pacific Time (US & Canada)"},
            {"value": "Europe/London", "label": "London"},
            {"value": "Europe/Paris", "label": "Paris"},
            {"value": "Europe/Berlin", "label": "Berlin"},
            {"value": "Asia/Tokyo", "label": "Tokyo"},
            {"value": "Asia/Shanghai", "label": "Shanghai"},
            {"value": "Australia/Sydney", "label": "Sydney"},
        ]
        
        return jsonify({
            "timezones": timezones,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting timezones: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve timezones",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/settings/export', methods=['GET'])
@rate_limit('/api/settings')
@auth_required
def export_settings():
    """Export user settings as JSON"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        logger.info(f"Exporting settings for user {user.id}")
        
        # Get user settings
        settings = UserSettings.get_or_create_settings(user.id)
        
        export_data = {
            "export_date": "2024-01-01T00:00:00Z",  # Use current timestamp in production
            "user_id": user.id,
            "username": user.username,
            "settings": settings.to_dict()
        }
        
        return jsonify({
            "export": export_data,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error exporting settings: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to export settings",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500
