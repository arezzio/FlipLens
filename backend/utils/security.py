"""
Security utilities for the FlipLens backend
Provides input validation, sanitization, and security headers
"""

import re
import logging
import hashlib
import secrets
from flask import request, jsonify, current_app
from functools import wraps
from typing import Dict, Any, Optional, List
import html
import urllib.parse

logger = logging.getLogger(__name__)

class ApiKeySecurity:
    """API key security utilities"""
    
    @staticmethod
    def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
        """Mask an API key for secure logging"""
        if not api_key or len(api_key) < visible_chars:
            return "***"
        
        return f"{api_key[:visible_chars]}{'*' * (len(api_key) - visible_chars)}"
    
    @staticmethod
    def validate_api_key_strength(api_key: str) -> tuple[bool, str]:
        """Validate API key strength"""
        if not api_key:
            return False, "API key is empty"
        
        if len(api_key) < 10:
            return False, "API key is too short (minimum 10 characters)"
        
        if len(api_key) > 200:
            return False, "API key is too long (maximum 200 characters)"
        
        # Check for common weak patterns
        if api_key.lower() in ['test', 'demo', 'sample', 'example']:
            return False, "API key appears to be a test/demo key"
        
        # Check for repeated characters
        if len(set(api_key)) < len(api_key) * 0.3:
            return False, "API key has too many repeated characters"
        
        return True, "API key strength is acceptable"
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

class SecurityValidator:
    """Input validation and sanitization utilities"""
    
    # Regex patterns for validation
    PATTERNS = {
        'query': r'^[a-zA-Z0-9\s\-_.,!?()]+$',  # Alphanumeric, spaces, basic punctuation
        'item_id': r'^[0-9]+$',  # Numeric only
        'price': r'^[0-9]+(\.[0-9]{1,2})?$',  # Decimal number with up to 2 decimal places
        'url': r'^https?://[^\s/$.?#].[^\s]*$',  # Basic URL validation
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email validation
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'safe_text': r'^[a-zA-Z0-9\s\-_.,!?()]+$',
        'api_key': r'^[A-Za-z0-9\-_\.]+$'  # API key format
    }
    
    @classmethod
    def validate_string(cls, value: str, pattern: str, max_length: int = 100) -> bool:
        """Validate a string against a pattern and length limit"""
        if not isinstance(value, str):
            return False
        
        if len(value) > max_length:
            return False
        
        if not re.match(cls.PATTERNS.get(pattern, cls.PATTERNS['safe_text']), value):
            return False
        
        return True
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string to prevent XSS and injection attacks"""
        if not isinstance(value, str):
            return ""
        
        # HTML escape
        value = html.escape(value)
        
        # Remove potentially dangerous characters
        value = re.sub(r'[<>"\']', '', value)
        
        # URL decode to prevent double encoding attacks
        try:
            value = urllib.parse.unquote(value)
        except:
            pass
        
        return value.strip()
    
    @classmethod
    def validate_json_structure(cls, data: Dict[str, Any], required_fields: List[str], optional_fields: Optional[Dict[str, Any]] = None) -> tuple[bool, str]:
        """Validate JSON structure and required fields"""
        if not isinstance(data, dict):
            return False, "Data must be a JSON object"
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Check optional fields with type validation
        if optional_fields:
            for field, expected_type in optional_fields.items():
                if field in data and not isinstance(data[field], expected_type):
                    return False, f"Invalid type for field {field}: expected {expected_type.__name__}"
        
        return True, ""
    
    @classmethod
    def validate_api_key_format(cls, api_key: str) -> bool:
        """Validate API key format"""
        return cls.validate_string(api_key, 'api_key', max_length=200)

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        # Prevent XSS attacks
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' http://localhost:5000 https://localhost:5000; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Remove server information
        if 'Server' in response.headers:
            del response.headers['Server']
        
        return response

class InputValidation:
    """Input validation decorators"""
    
    @staticmethod
    def validate_search_input(f):
        """Validate search endpoint input"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check Content-Type
                if not request.is_json:
                    logger.warning(f"Invalid Content-Type from {request.remote_addr}")
                    return jsonify({
                        "error": "Invalid Content-Type",
                        "message": "Content-Type must be application/json",
                        "status": "error",
                        "code": "INVALID_CONTENT_TYPE"
                    }), 415
                
                # Parse JSON
                try:
                    data = request.get_json()
                except Exception as e:
                    logger.warning(f"Invalid JSON from {request.remote_addr}: {str(e)}")
                    return jsonify({
                        "error": "Invalid JSON",
                        "message": "Request body contains invalid JSON",
                        "status": "error",
                        "code": "INVALID_JSON"
                    }), 400
                
                if not data:
                    logger.warning(f"Missing JSON body from {request.remote_addr}")
                    return jsonify({
                        "error": "Missing JSON Body",
                        "message": "Request body must be valid JSON",
                        "status": "error",
                        "code": "MISSING_JSON"
                    }), 400
                
                # Validate required fields
                required_fields = ['query']
                is_valid, error_msg = SecurityValidator.validate_json_structure(
                    data, required_fields, {'limit': int}
                )
                
                if not is_valid:
                    logger.warning(f"Invalid JSON structure from {request.remote_addr}: {error_msg}")
                    return jsonify({
                        "error": "Invalid Request Structure",
                        "message": error_msg,
                        "status": "error",
                        "code": "INVALID_STRUCTURE"
                    }), 400
                
                # Validate and sanitize query
                query = data['query'].strip()
                if not query:
                    logger.warning(f"Empty query from {request.remote_addr}")
                    return jsonify({
                        "error": "Empty Query",
                        "message": "Query cannot be empty",
                        "status": "error",
                        "code": "EMPTY_QUERY"
                    }), 400
                
                if not SecurityValidator.validate_string(query, 'query', max_length=100):
                    logger.warning(f"Invalid query format from {request.remote_addr}: {query}")
                    return jsonify({
                        "error": "Invalid Query Format",
                        "message": "Query contains invalid characters",
                        "status": "error",
                        "code": "INVALID_QUERY_FORMAT"
                    }), 400
                
                # Sanitize query
                sanitized_query = SecurityValidator.sanitize_string(query)
                data['query'] = sanitized_query
                
                # Validate limit
                limit = data.get('limit', 20)
                try:
                    limit = int(limit)
                    if limit < 1 or limit > 100:
                        logger.warning(f"Invalid limit from {request.remote_addr}: {limit}")
                        return jsonify({
                            "error": "Invalid Limit",
                            "message": "Limit must be between 1 and 100",
                            "status": "error",
                            "code": "INVALID_LIMIT"
                        }), 400
                    data['limit'] = limit
                except (ValueError, TypeError):
                    logger.warning(f"Invalid limit type from {request.remote_addr}: {type(limit)}")
                    return jsonify({
                        "error": "Invalid Limit Type",
                        "message": "Limit must be a valid number",
                        "status": "error",
                        "code": "INVALID_LIMIT_TYPE"
                    }), 400
                
                # Replace request data with sanitized version
                from flask import g
                g.validated_json = data
                
                logger.info(f"Validated search request from {request.remote_addr}: '{sanitized_query}' (limit: {limit})")
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Validation error: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Validation Error",
                    "message": "An error occurred during input validation",
                    "status": "error",
                    "code": "VALIDATION_ERROR"
                }), 500
        
        return decorated_function
    
    @staticmethod
    def validate_saved_item_input(f):
        """Validate saved item endpoint input"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check Content-Type
                if not request.is_json:
                    return jsonify({
                        "error": "Invalid Content-Type",
                        "message": "Content-Type must be application/json",
                        "status": "error",
                        "code": "INVALID_CONTENT_TYPE"
                    }), 415
                
                # Parse JSON
                try:
                    data = request.get_json()
                except Exception as e:
                    logger.warning(f"Invalid JSON from {request.remote_addr}: {str(e)}")
                    return jsonify({
                        "error": "Invalid JSON",
                        "message": "Request body contains invalid JSON",
                        "status": "error",
                        "code": "INVALID_JSON"
                    }), 400
                
                if not data:
                    return jsonify({
                        "error": "Missing JSON Body",
                        "message": "Request body must be valid JSON",
                        "status": "error",
                        "code": "MISSING_JSON"
                    }), 400
                
                # Validate required fields
                required_fields = ['item_id', 'title', 'price']
                optional_fields = {
                    'currency': str,
                    'image_url': str,
                    'item_url': str,
                    'condition': str,
                    'location': str,
                    'notes': str
                }
                
                is_valid, error_msg = SecurityValidator.validate_json_structure(
                    data, required_fields, optional_fields
                )
                
                if not is_valid:
                    logger.warning(f"Invalid JSON structure from {request.remote_addr}: {error_msg}")
                    return jsonify({
                        "error": "Invalid Request Structure",
                        "message": error_msg,
                        "status": "error",
                        "code": "INVALID_STRUCTURE"
                    }), 400
                
                # Validate and sanitize fields
                for field in ['title', 'condition', 'location', 'notes']:
                    if field in data:
                        if not SecurityValidator.validate_string(data[field], 'safe_text', max_length=500):
                            return jsonify({
                                "error": f"Invalid {field}",
                                "message": f"{field} contains invalid characters",
                                "status": "error",
                                "code": f"INVALID_{field.upper()}"
                            }), 400
                        data[field] = SecurityValidator.sanitize_string(data[field])
                
                # Validate URLs
                for url_field in ['image_url', 'item_url']:
                    if url_field in data and data[url_field]:
                        if not SecurityValidator.validate_string(data[url_field], 'url', max_length=500):
                            return jsonify({
                                "error": f"Invalid {url_field}",
                                "message": f"{url_field} must be a valid URL",
                                "status": "error",
                                "code": f"INVALID_{url_field.upper()}"
                            }), 400
                
                # Validate price
                if not SecurityValidator.validate_string(data['price'], 'price', max_length=20):
                    return jsonify({
                        "error": "Invalid Price",
                        "message": "Price must be a valid number",
                        "status": "error",
                        "code": "INVALID_PRICE"
                    }), 400
                
                # Replace request data with sanitized version
                from flask import g
                g.validated_json = data
                
                logger.info(f"Validated saved item request from {request.remote_addr}")
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Validation error: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Validation Error",
                    "message": "An error occurred during input validation",
                    "status": "error",
                    "code": "VALIDATION_ERROR"
                }), 500
        
        return decorated_function

def register_security_middleware(app):
    """Register security middleware with Flask app"""
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        return SecurityHeaders.add_security_headers(response)
    
    # Enhanced request logging and security monitoring
    @app.before_request
    def log_request():
        # Log request details for security monitoring
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        method = request.method
        path = request.path
        
        # Check for suspicious patterns
        suspicious_patterns = [
            '/admin', '/wp-admin', '/phpmyadmin', '/config',
            'union select', 'drop table', 'insert into',
            '<script', 'javascript:', 'data:text/html'
        ]
        
        request_data = f"{method} {path}"
        is_suspicious = any(pattern in request_data.lower() for pattern in suspicious_patterns)
        
        if is_suspicious:
            logger.warning(f"Suspicious request detected from {client_ip}: {request_data}")
            logger.warning(f"User-Agent: {user_agent}")
        
        # Log all requests in development
        if current_app.config.get('FLASK_ENV') == 'development':
            logger.info(f"Request: {method} {path} from {client_ip}")
    
    # Error handling with security considerations
    @app.errorhandler(404)
    def not_found(error):
        # Don't expose internal paths in 404 responses
        return {"error": "Not Found", "status": "error"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        # Don't expose internal error details in production
        if current_app.config.get('FLASK_ENV') == 'production':
            logger.error(f"Internal server error: {str(error)}", exc_info=True)
            return {"error": "Internal Server Error", "status": "error"}, 500
        else:
            return {"error": "Internal Server Error", "message": str(error), "status": "error"}, 500
    
    # Validate API configuration on startup
    try:
        from config.settings import Config
        config_summary = Config.get_secure_config_summary()
        logger.info(f"Security configuration loaded: {config_summary}")
        
        # Validate API keys if configured
        if config_summary['api_keys_configured']['EBAY_API_KEY']:
            ebay_key = Config.get_api_key('EBAY_API_KEY')
            if ebay_key:
                is_strong, strength_msg = ApiKeySecurity.validate_api_key_strength(ebay_key)
                if not is_strong:
                    logger.warning(f"eBay API key strength issue: {strength_msg}")
                else:
                    logger.info("eBay API key strength validation passed")
        
        # Validate SECRET_KEY in production
        if Config.is_production():
            secret_key = Config.get_api_key('SECRET_KEY')
            if secret_key:
                is_strong, strength_msg = ApiKeySecurity.validate_api_key_strength(secret_key)
                if not is_strong:
                    logger.warning(f"SECRET_KEY strength issue: {strength_msg}")
                else:
                    logger.info("SECRET_KEY strength validation passed")
    
    except Exception as e:
        logger.error(f"Error during security configuration validation: {str(e)}")
    
    logger.info("Enhanced security middleware registered successfully") 