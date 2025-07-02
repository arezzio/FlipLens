"""
Portfolio routes for FlipLens application
"""

from flask import jsonify, request, g
from . import api_bp
from utils.rate_limiter import rate_limit
from utils.auth_middleware import auth_required, get_current_user
from utils.validation import validate_json_input
from models.portfolio_item import PortfolioItem
from models.database import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Validation schemas
PORTFOLIO_ITEM_SCHEMA = {
    'type': 'object',
    'required': ['item_name', 'purchase_price', 'purchase_date', 'condition'],
    'properties': {
        'item_name': {'type': 'string', 'minLength': 1, 'maxLength': 500},
        'brand': {'type': 'string', 'maxLength': 100},
        'model': {'type': 'string', 'maxLength': 200},
        'size': {'type': 'string', 'maxLength': 50},
        'color': {'type': 'string', 'maxLength': 100},
        'condition': {'type': 'string', 'enum': ['new', 'excellent', 'very good', 'good', 'fair', 'poor']},
        'category': {'type': 'string', 'maxLength': 100},
        'purchase_price': {'type': 'number', 'minimum': 0},
        'purchase_date': {'type': 'string'},
        'purchase_platform': {'type': 'string', 'maxLength': 100},
        'purchase_location': {'type': 'string', 'maxLength': 200},
        'notes': {'type': 'string', 'maxLength': 1000},
        'tags': {'type': 'string', 'maxLength': 500}
    }
}

@api_bp.route('/portfolio', methods=['GET'])
@rate_limit('/api/portfolio')
@auth_required
def get_portfolio():
    """Get user's portfolio items"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')  # owned, listed, sold
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        logger.info(f"Getting portfolio for user {user.id} (page: {page}, per_page: {per_page})")
        
        # Build query
        query = PortfolioItem.query.filter_by(user_id=user.id)
        
        # Apply status filter
        if status:
            query = query.filter(PortfolioItem.status == status)
        
        # Apply sorting
        sort_column = getattr(PortfolioItem, sort_by, PortfolioItem.created_at)
        if sort_order.lower() == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        items = [item.to_dict() for item in pagination.items]
        
        # Calculate portfolio summary
        total_items = PortfolioItem.query.filter_by(user_id=user.id).count()
        owned_items = PortfolioItem.query.filter_by(user_id=user.id, status='owned').count()
        listed_items = PortfolioItem.query.filter_by(user_id=user.id, status='listed').count()
        sold_items = PortfolioItem.query.filter_by(user_id=user.id, status='sold').count()
        
        # Calculate total investment and current value
        all_items = PortfolioItem.query.filter_by(user_id=user.id).all()
        total_investment = sum(float(item.purchase_price) for item in all_items)
        current_value = 0
        total_profit_loss = 0
        
        for item in all_items:
            if item.status == 'sold' and item.sale_price:
                current_value += float(item.sale_price)
                total_profit_loss += float(item.sale_price) - float(item.purchase_price)
            elif item.current_market_price:
                current_value += float(item.current_market_price)
                total_profit_loss += float(item.current_market_price) - float(item.purchase_price)
            else:
                current_value += float(item.purchase_price)  # Use purchase price as fallback
        
        portfolio_summary = {
            'total_items': total_items,
            'owned_items': owned_items,
            'listed_items': listed_items,
            'sold_items': sold_items,
            'total_investment': round(total_investment, 2),
            'current_value': round(current_value, 2),
            'total_profit_loss': round(total_profit_loss, 2),
            'profit_percentage': round((total_profit_loss / total_investment * 100), 2) if total_investment > 0 else 0
        }
        
        return jsonify({
            "items": items,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            },
            "summary": portfolio_summary,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve portfolio",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/portfolio', methods=['POST'])
@rate_limit('/api/portfolio')
@auth_required
@validate_json_input(PORTFOLIO_ITEM_SCHEMA)
def add_portfolio_item():
    """Add new item to portfolio"""
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
        
        logger.info(f"Adding portfolio item for user {user.id}: {data['item_name']}")
        
        # Create portfolio item
        portfolio_item = PortfolioItem.create_portfolio_item(user.id, data)
        
        return jsonify({
            "item": portfolio_item.to_dict(),
            "message": "Portfolio item added successfully",
            "status": "success"
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding portfolio item: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to add portfolio item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/portfolio/<int:item_id>', methods=['GET'])
@rate_limit('/api/portfolio')
@auth_required
def get_portfolio_item(item_id):
    """Get specific portfolio item"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get portfolio item
        item = PortfolioItem.query.filter_by(id=item_id, user_id=user.id).first()
        
        if not item:
            return jsonify({
                "error": "Item Not Found",
                "message": "Portfolio item not found",
                "status": "error",
                "code": "ITEM_NOT_FOUND"
            }), 404
        
        return jsonify({
            "item": item.to_dict(),
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting portfolio item: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve portfolio item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/portfolio/<int:item_id>', methods=['PUT'])
@rate_limit('/api/portfolio')
@auth_required
def update_portfolio_item(item_id):
    """Update portfolio item"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get portfolio item
        item = PortfolioItem.query.filter_by(id=item_id, user_id=user.id).first()
        
        if not item:
            return jsonify({
                "error": "Item Not Found",
                "message": "Portfolio item not found",
                "status": "error",
                "code": "ITEM_NOT_FOUND"
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Invalid Request",
                "message": "JSON data required",
                "status": "error",
                "code": "INVALID_JSON"
            }), 400
        
        logger.info(f"Updating portfolio item {item_id} for user {user.id}")
        
        # Update fields
        updatable_fields = [
            'item_name', 'brand', 'model', 'size', 'color', 'condition', 'category',
            'purchase_price', 'purchase_date', 'purchase_platform', 'purchase_location',
            'current_market_price', 'listing_price', 'listing_platform', 'notes', 'tags'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'purchase_date' and data[field]:
                    setattr(item, field, datetime.fromisoformat(data[field].replace('Z', '+00:00')))
                else:
                    setattr(item, field, data[field])
        
        # Update market price if provided
        if 'current_market_price' in data:
            item.update_market_price(data['current_market_price'])
        
        # Handle status changes
        if 'status' in data:
            if data['status'] == 'listed' and 'listing_price' in data:
                item.mark_as_listed(data['listing_price'], data.get('listing_platform'))
            elif data['status'] == 'sold' and 'sale_price' in data:
                item.mark_as_sold(data['sale_price'], data.get('sale_platform'))
            else:
                item.status = data['status']
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "item": item.to_dict(),
            "message": "Portfolio item updated successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating portfolio item: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to update portfolio item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/portfolio/<int:item_id>', methods=['DELETE'])
@rate_limit('/api/portfolio')
@auth_required
def delete_portfolio_item(item_id):
    """Delete portfolio item"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get portfolio item
        item = PortfolioItem.query.filter_by(id=item_id, user_id=user.id).first()
        
        if not item:
            return jsonify({
                "error": "Item Not Found",
                "message": "Portfolio item not found",
                "status": "error",
                "code": "ITEM_NOT_FOUND"
            }), 404
        
        logger.info(f"Deleting portfolio item {item_id} for user {user.id}")
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            "message": "Portfolio item deleted successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting portfolio item: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to delete portfolio item",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500
