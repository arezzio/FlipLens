"""
Input validation utilities for FlipLens application
"""

from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)

def validate_json_input(schema):
    """
    Decorator to validate JSON input against a schema
    This is a simplified validation - in production you might want to use jsonschema
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check if request has JSON data
                if not request.is_json:
                    return jsonify({
                        "error": "Invalid Content Type",
                        "message": "Request must contain JSON data",
                        "status": "error",
                        "code": "INVALID_CONTENT_TYPE"
                    }), 400
                
                data = request.get_json()
                if not data:
                    return jsonify({
                        "error": "Invalid JSON",
                        "message": "Request body must contain valid JSON",
                        "status": "error",
                        "code": "INVALID_JSON"
                    }), 400
                
                # Basic validation - check required fields
                if 'required' in schema:
                    for field in schema['required']:
                        if field not in data:
                            return jsonify({
                                "error": "Missing Required Field",
                                "message": f"Field '{field}' is required",
                                "status": "error",
                                "code": "MISSING_FIELD"
                            }), 400
                
                # Store validated data in g for use in the route
                g.validated_json = data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Validation error: {str(e)}")
                return jsonify({
                    "error": "Validation Error",
                    "message": "Failed to validate input data",
                    "status": "error",
                    "code": "VALIDATION_ERROR"
                }), 400
        
        return decorated_function
    return decorator

def validate_query_params(required_params=None, optional_params=None):
    """
    Decorator to validate query parameters
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if required_params:
                    for param in required_params:
                        if param not in request.args:
                            return jsonify({
                                "error": "Missing Query Parameter",
                                "message": f"Query parameter '{param}' is required",
                                "status": "error",
                                "code": "MISSING_PARAM"
                            }), 400
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Query parameter validation error: {str(e)}")
                return jsonify({
                    "error": "Parameter Validation Error",
                    "message": "Failed to validate query parameters",
                    "status": "error",
                    "code": "PARAM_VALIDATION_ERROR"
                }), 400
        
        return decorated_function
    return decorator

def validate_email(email):
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """Basic password strength validation"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def sanitize_string(value, max_length=None):
    """Basic string sanitization"""
    if not isinstance(value, str):
        return str(value)
    
    # Remove leading/trailing whitespace
    value = value.strip()
    
    # Limit length if specified
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value

def validate_pagination_params(page=None, per_page=None, max_per_page=100):
    """Validate pagination parameters"""
    try:
        if page is not None:
            page = int(page)
            if page < 1:
                page = 1
        else:
            page = 1
        
        if per_page is not None:
            per_page = int(per_page)
            if per_page < 1:
                per_page = 20
            elif per_page > max_per_page:
                per_page = max_per_page
        else:
            per_page = 20
        
        return page, per_page
        
    except (ValueError, TypeError):
        return 1, 20
