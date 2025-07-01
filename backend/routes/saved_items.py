from flask import jsonify, request, g
from . import api_bp
from utils.rate_limiter import rate_limit
from utils.auth_middleware import auth_required, get_current_user
from models.saved_item import SavedItem
from models.search_history import SearchHistory
from models.database import db
import logging
import re
from datetime import datetime
from werkzeug.exceptions import BadRequest

# Set up logging
logger = logging.getLogger(__name__)

@api_bp.route('/saved-items', methods=['GET'])
@rate_limit('/api/saved-items')
@auth_required
def get_saved_items():
    """Get user's saved items"""
    try:
        user = get_current_user()
        logger.info(f"GET saved items request from user {user.username}")

        # Get query parameters for filtering and pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 items per page
        status = request.args.get('status')  # Filter by status
        tag = request.args.get('tag')  # Filter by tag

        # Build query
        query = SavedItem.query.filter_by(user_id=user.id)

        if status:
            query = query.filter_by(status=status)

        if tag:
            query = query.filter(SavedItem.tags.contains(tag))

        # Order by creation date (newest first)
        query = query.order_by(SavedItem.created_at.desc())

        # Paginate results
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        items = [item.to_dict() for item in pagination.items]

        logger.info(f"Retrieved {len(items)} saved items for user {user.username}")

        return jsonify({
            "items": items,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "status": "success"
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving saved items: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve saved items",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/saved-items', methods=['POST'])
@rate_limit('/api/saved-items')
@auth_required
def save_item():
    """Save an item to user's favorites"""
    try:
        user = get_current_user()
        logger.info(f"POST save item request from user {user.username}")
        
        # Check Content-Type
        if not request.is_json:
            logger.warning("Request Content-Type is not application/json")
            return jsonify({
                "error": "Invalid Content-Type",
                "message": "Content-Type must be application/json",
                "status": "error",
                "code": "INVALID_CONTENT_TYPE"
            }), 415
        
        # Parse JSON body
        try:
            data = request.get_json()
        except BadRequest as e:
            logger.warning(f"Invalid JSON: {str(e)}")
            return jsonify({
                "error": "Invalid JSON",
                "message": "Request body contains invalid JSON.",
                "status": "error",
                "code": "INVALID_JSON"
            }), 400
        
        if not data:
            logger.warning("Save item request missing JSON data")
            return jsonify({
                "error": "Missing JSON body",
                "message": "Request body must be valid JSON.",
                "status": "error",
                "code": "MISSING_JSON"
            }), 400
        
        # Validate required fields
        required_fields = ['item_id', 'title', 'price']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.warning(f"Save item request missing required fields: {missing_fields}")
            return jsonify({
                "error": "Missing Required Fields",
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "status": "error",
                "code": "MISSING_FIELDS"
            }), 400
        
        item_id = data['item_id'].strip()
        
        # Validate item_id format
        if not item_id or len(item_id) > 50:
            logger.warning(f"Invalid item_id: {item_id}")
            return jsonify({
                "error": "Invalid Item ID",
                "message": "Item ID must be between 1 and 50 characters.",
                "status": "error",
                "code": "INVALID_ITEM_ID"
            }), 400
        
        # Prepare item data for database
        item_data = {
            'ebay_item_id': str(data['item_id']).strip(),
            'title': str(data['title']).strip()[:500],
            'price': float(data['price']),
            'currency': data.get('currency', 'USD'),
            'image_url': data.get('image_url', ''),
            'item_url': data.get('item_url', ''),
            'condition': data.get('condition', 'Unknown'),
            'location': data.get('location', 'Unknown'),
            'notes': data.get('notes', '')[:1000]
        }

        # Create saved item
        try:
            saved_item = SavedItem.create_saved_item(user.id, item_data)

            logger.info(f"Item {saved_item.ebay_item_id} saved successfully for user {user.username}")

            return jsonify({
                "message": "Item saved successfully",
                "item": saved_item.to_dict(),
                "status": "success"
            }), 201

        except ValueError as e:
            return jsonify({
                "error": "Item Already Saved",
                "message": str(e),
                "status": "error",
                "code": "ITEM_ALREADY_SAVED"
            }), 409
        
    except Exception as e:
        logger.error(f"Error saving item: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to save item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/saved-items/<item_id>', methods=['GET'])
@rate_limit('/api/saved-items')
def get_saved_item(item_id):
    """Get a specific saved item by ID"""
    try:
        logger.info(f"GET saved item {item_id} request from {request.remote_addr}")
        
        # Validate item_id
        if not item_id or len(item_id) > 50:
            return jsonify({
                "error": "Invalid Item ID",
                "message": "Item ID must be between 1 and 50 characters.",
                "status": "error",
                "code": "INVALID_ITEM_ID"
            }), 400
        
        # Check if item exists
        if item_id not in saved_items_storage:
            logger.warning(f"Item {item_id} not found")
            return jsonify({
                "error": "Item Not Found",
                "message": "Item not found.",
                "status": "error",
                "code": "ITEM_NOT_FOUND"
            }), 404
        
        item = saved_items_storage[item_id]
        logger.info(f"Retrieved item {item_id}")
        
        return jsonify({
            "item": item,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving item {item_id}: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/saved-items/<item_id>', methods=['PUT'])
@rate_limit('/api/saved-items')
def update_saved_item(item_id):
    """Update a saved item"""
    try:
        logger.info(f"PUT update item {item_id} request from {request.remote_addr}")
        
        # Check Content-Type
        if not request.is_json:
            logger.warning("Request Content-Type is not application/json")
            return jsonify({
                "error": "Invalid Content-Type",
                "message": "Content-Type must be application/json",
                "status": "error",
                "code": "INVALID_CONTENT_TYPE"
            }), 415
        
        # Parse JSON body
        try:
            data = request.get_json()
        except BadRequest as e:
            logger.warning(f"Invalid JSON: {str(e)}")
            return jsonify({
                "error": "Invalid JSON",
                "message": "Request body contains invalid JSON.",
                "status": "error",
                "code": "INVALID_JSON"
            }), 400
        
        if not data:
            return jsonify({
                "error": "Missing JSON body",
                "message": "Request body must be valid JSON.",
                "status": "error",
                "code": "MISSING_JSON"
            }), 400
        
        # Validate item_id
        if not item_id or len(item_id) > 50:
            return jsonify({
                "error": "Invalid Item ID",
                "message": "Item ID must be between 1 and 50 characters.",
                "status": "error",
                "code": "INVALID_ITEM_ID"
            }), 400
        
        # Check if item exists
        if item_id not in saved_items_storage:
            logger.warning(f"Item {item_id} not found for update")
            return jsonify({
                "error": "Item Not Found",
                "message": "Item not found.",
                "status": "error",
                "code": "ITEM_NOT_FOUND"
            }), 404
        
        # Update allowed fields
        item = saved_items_storage[item_id]
        allowed_fields = ['title', 'price', 'currency', 'image_url', 'item_url', 'condition', 'location', 'notes']
        
        for field in allowed_fields:
            if field in data:
                if field == 'title':
                    item[field] = data[field][:200]  # Limit title length
                elif field == 'notes':
                    item[field] = data[field][:500]  # Limit notes length
                else:
                    item[field] = data[field]
        
        # Update timestamp
        item['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Item {item_id} updated successfully")
        
        return jsonify({
            "message": "Item updated successfully",
            "item": item,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to update item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/saved-items/<item_id>', methods=['DELETE'])
@rate_limit('/api/saved-items')
def delete_saved_item(item_id):
    """Delete a saved item"""
    try:
        logger.info(f"DELETE item {item_id} request from {request.remote_addr}")
        
        # Validate item_id
        if not item_id or len(item_id) > 50:
            return jsonify({
                "error": "Invalid Item ID",
                "message": "Item ID must be between 1 and 50 characters.",
                "status": "error",
                "code": "INVALID_ITEM_ID"
            }), 400
        
        # Check if item exists
        if item_id not in saved_items_storage:
            logger.warning(f"Item {item_id} not found for deletion")
            return jsonify({
                "error": "Item Not Found",
                "message": "Item not found.",
                "status": "error",
                "code": "ITEM_NOT_FOUND"
            }), 404
        
        # Remove item
        deleted_item = saved_items_storage.pop(item_id)
        
        logger.info(f"Item {item_id} deleted successfully")
        
        return jsonify({
            "message": "Item deleted successfully",
            "deleted_item": deleted_item,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to delete item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500 