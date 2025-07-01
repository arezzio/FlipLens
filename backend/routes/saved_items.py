from flask import jsonify, request
from . import api_bp
from utils.rate_limiter import rate_limit
import logging
import re
from datetime import datetime
from werkzeug.exceptions import BadRequest

# Set up logging
logger = logging.getLogger(__name__)

# Temporary in-memory storage (will be replaced with database in future tasks)
saved_items_storage = {}

@api_bp.route('/saved-items', methods=['GET'])
@rate_limit('/api/saved-items')
def get_saved_items():
    """Get user's saved items"""
    try:
        logger.info(f"GET saved items request from {request.remote_addr}")
        
        # TODO: Implement database integration
        # This will be implemented in future tasks
        
        # For now, return all items from temporary storage
        items = list(saved_items_storage.values())
        
        logger.info(f"Retrieved {len(items)} saved items")
        
        return jsonify({
            "items": items,
            "total": len(items),
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
def save_item():
    """Save an item to user's favorites"""
    try:
        logger.info(f"POST save item request from {request.remote_addr}")
        
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
        
        # Sanitize item_id
        item_id = re.sub(r'[<>"\']', '', item_id)
        
        # Check if item already exists
        if item_id in saved_items_storage:
            logger.info(f"Item {item_id} already exists, updating")
            return jsonify({
                "error": "Item Already Saved",
                "message": "Item already saved.",
                "item_id": item_id,
                "status": "error",
                "code": "ITEM_ALREADY_SAVED"
            }), 409
        
        # Create item object with timestamp
        item = {
            'id': item_id,
            'title': data['title'][:200],  # Limit title length
            'price': data['price'],
            'currency': data.get('currency', 'USD'),
            'image_url': data.get('image_url', ''),
            'item_url': data.get('item_url', ''),
            'condition': data.get('condition', 'Unknown'),
            'location': data.get('location', 'Unknown'),
            'saved_at': datetime.utcnow().isoformat(),
            'notes': data.get('notes', '')[:500]  # Limit notes length
        }
        
        # Store item
        saved_items_storage[item_id] = item
        
        logger.info(f"Item {item_id} saved successfully")
        
        return jsonify({
            "message": "Item saved successfully",
            "item": item,
            "status": "success"
        }), 201
        
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