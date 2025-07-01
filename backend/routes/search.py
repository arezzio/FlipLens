from flask import jsonify, request, current_app, g
from . import api_bp
from services.ebay_service import EbayService
from utils.rate_limiter import rate_limit
from utils.security import InputValidation, SecurityValidator
from utils.auth_middleware import auth_optional, get_current_user
from models.search_history import SearchHistory
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

@api_bp.route('/search', methods=['POST'])
@rate_limit('/api/search')
@auth_optional
@InputValidation.validate_search_input
def search_items():
    """Search for items using eBay Finding API with enhanced security"""
    try:
        # Get validated and sanitized data from request
        data = getattr(g, 'validated_json', None)
        if not data:
            return jsonify({
                "error": "Invalid Request",
                "message": "Validated data not found. Input validation failed.",
                "status": "error",
                "code": "VALIDATION_ERROR"
            }), 400
        query = data['query']
        limit = data['limit']
        
        logger.info(f"Processing search request: '{query}' (limit: {limit})")

        # Perform search using enhanced eBay service
        ebay_service = EbayService()
        result = ebay_service.search_items(query, limit)

        # Check for service errors
        if 'error' in result:
            logger.error(f"eBay service error: {result['error']}")
            return jsonify({
                "error": result['error'],
                "message": result.get('message', 'Service temporarily unavailable'),
                "status": "error",
                "code": "EBAY_SERVICE_ERROR"
            }), 503

        logger.info(f"Search completed successfully. Found {result.get('total', 0)} items")

        return jsonify({
            "results": result.get('results', []),
            "total": result.get('total', 0),
            "query": query,
            "limit": limit,
            "status": "success"
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error in search endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/search', methods=['GET'])
@rate_limit('/api/search')
def search_items_get():
    """Search for items using GET method (for simple queries) with validation"""
    try:
        query = request.args.get('q')
        limit = request.args.get('limit', 20)

        if not query:
            return jsonify({
                "error": "Missing Query",
                "message": "Query parameter 'q' is required.",
                "status": "error",
                "code": "MISSING_QUERY"
            }), 400

        # Validate query format
        from utils.security import SecurityValidator
        if not SecurityValidator.validate_string(query, 'query', max_length=100):
            return jsonify({
                "error": "Invalid Query Format",
                "message": "Query contains invalid characters",
                "status": "error",
                "code": "INVALID_QUERY_FORMAT"
            }), 400

        # Sanitize query
        sanitized_query = SecurityValidator.sanitize_string(query)
        
        # Validate limit
        try:
            limit = int(limit)
            if limit < 1 or limit > 100:
                return jsonify({
                    "error": "Invalid Limit",
                    "message": "Limit must be between 1 and 100.",
                    "status": "error",
                    "code": "INVALID_LIMIT"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "error": "Invalid Limit Type",
                "message": "Limit must be a valid number.",
                "status": "error",
                "code": "INVALID_LIMIT_TYPE"
            }), 400

        logger.info(f"Processing GET search request: '{sanitized_query}' (limit: {limit})")

        # Perform search
        ebay_service = EbayService()
        result = ebay_service.search_items(sanitized_query, limit)

        # Check for service errors
        if 'error' in result:
            logger.error(f"eBay service error: {result['error']}")
            return jsonify({
                "error": result['error'],
                "message": result.get('message', 'Service temporarily unavailable'),
                "status": "error",
                "code": "EBAY_SERVICE_ERROR"
            }), 503

        logger.info(f"GET search completed successfully. Found {result.get('total', 0)} items")

        return jsonify({
            "results": result.get('results', []),
            "total": result.get('total', 0),
            "query": sanitized_query,
            "limit": limit,
            "status": "success"
        }), 200

    except Exception as e:
        logger.error(f"Error in GET search endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500 