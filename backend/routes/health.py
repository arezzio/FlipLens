from flask import jsonify
from . import api_bp

@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "FlipLens Backend",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    })

@api_bp.route('/docs')
def api_documentation():
    """API documentation endpoint"""
    return jsonify({
        "api_name": "FlipLens API",
        "version": "1.0.0",
        "description": "RESTful API for FlipLens eBay product search and saved items management",
        "endpoints": {
            "health": {
                "url": "/api/health",
                "method": "GET",
                "description": "Health check endpoint",
                "response": {
                    "status": "healthy",
                    "service": "FlipLens Backend",
                    "version": "1.0.0"
                }
            },
            "search": {
                "url": "/api/search",
                "methods": ["GET", "POST"],
                "description": "Search for items using eBay Finding API",
                "parameters": {
                    "POST": {
                        "query": "string (required) - Search query",
                        "limit": "integer (optional) - Maximum results (1-100, default: 20)"
                    },
                    "GET": {
                        "q": "string (required) - Search query",
                        "limit": "integer (optional) - Maximum results (1-100, default: 20)"
                    }
                },
                "response": {
                    "results": "array - List of search results",
                    "total": "integer - Total number of results",
                    "query": "string - Original search query",
                    "limit": "integer - Results limit used",
                    "status": "string - Success/error status"
                }
            },
            "saved_items": {
                "url": "/api/saved-items",
                "methods": ["GET", "POST"],
                "description": "Manage saved items",
                "parameters": {
                    "POST": {
                        "item_id": "string (required) - eBay item ID",
                        "title": "string (required) - Item title",
                        "price": "string (required) - Item price",
                        "currency": "string (optional) - Currency code (default: USD)",
                        "image_url": "string (optional) - Item image URL",
                        "item_url": "string (optional) - eBay item URL",
                        "condition": "string (optional) - Item condition",
                        "location": "string (optional) - Item location",
                        "notes": "string (optional) - User notes"
                    }
                }
            },
            "saved_item": {
                "url": "/api/saved-items/<item_id>",
                "methods": ["GET", "PUT", "DELETE"],
                "description": "Manage individual saved items",
                "parameters": {
                    "item_id": "string (required) - eBay item ID"
                }
            }
        },
        "error_responses": {
            "400": "Bad Request - Invalid input parameters",
            "404": "Not Found - Resource not found",
            "409": "Conflict - Resource already exists",
            "500": "Internal Server Error - Server error",
            "503": "Service Unavailable - External service error"
        },
        "rate_limits": {
            "search": "100 requests per hour",
            "saved_items": "1000 requests per hour"
        }
    }) 