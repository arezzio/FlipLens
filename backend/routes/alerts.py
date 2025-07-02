"""
Price Alerts routes for FlipLens application
"""

from flask import jsonify, request, g
from . import api_bp
from utils.rate_limiter import rate_limit
from utils.auth_middleware import auth_required, get_current_user
from utils.validation import validate_json_input
from models.price_alert import PriceAlert, AlertNotification
from models.database import db
import logging

logger = logging.getLogger(__name__)

# Validation schemas
PRICE_ALERT_SCHEMA = {
    'type': 'object',
    'required': ['item_identifier', 'alert_type'],
    'properties': {
        'item_identifier': {'type': 'string', 'minLength': 1, 'maxLength': 200},
        'platform': {'type': 'string', 'maxLength': 50},
        'condition': {'type': 'string', 'maxLength': 50},
        'alert_type': {'type': 'string', 'enum': ['price_drop', 'price_increase', 'threshold']},
        'threshold_price': {'type': 'number', 'minimum': 0},
        'percentage_change': {'type': 'number', 'minimum': 0, 'maximum': 100},
        'notification_method': {'type': 'string', 'enum': ['email', 'push', 'both']},
        'baseline_price': {'type': 'number', 'minimum': 0},
        'notes': {'type': 'string', 'maxLength': 1000}
    }
}

@api_bp.route('/alerts', methods=['GET'])
@rate_limit('/api/alerts')
@auth_required
def get_alerts():
    """Get user's price alerts"""
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
        is_active = request.args.get('is_active', type=bool)
        alert_type = request.args.get('alert_type')
        
        logger.info(f"Getting alerts for user {user.id}")
        
        # Build query
        query = PriceAlert.query.filter_by(user_id=user.id)
        
        # Apply filters
        if is_active is not None:
            query = query.filter(PriceAlert.is_active == is_active)
        
        if alert_type:
            query = query.filter(PriceAlert.alert_type == alert_type)
        
        # Order by creation date (newest first)
        query = query.order_by(PriceAlert.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        alerts = [alert.to_dict() for alert in pagination.items]
        
        # Get alert statistics
        total_alerts = PriceAlert.query.filter_by(user_id=user.id).count()
        active_alerts = PriceAlert.query.filter_by(user_id=user.id, is_active=True).count()
        triggered_alerts = PriceAlert.query.filter(
            PriceAlert.user_id == user.id,
            PriceAlert.last_triggered.isnot(None)
        ).count()
        
        alert_stats = {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'triggered_alerts': triggered_alerts,
            'inactive_alerts': total_alerts - active_alerts
        }
        
        return jsonify({
            "alerts": alerts,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            },
            "stats": alert_stats,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve alerts",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/alerts', methods=['POST'])
@rate_limit('/api/alerts')
@auth_required
@validate_json_input(PRICE_ALERT_SCHEMA)
def create_alert():
    """Create new price alert"""
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
        
        # Validate alert type specific requirements
        if data['alert_type'] == 'threshold' and 'threshold_price' not in data:
            return jsonify({
                "error": "Invalid Alert Configuration",
                "message": "threshold_price is required for threshold alerts",
                "status": "error",
                "code": "MISSING_THRESHOLD"
            }), 400
        
        if data['alert_type'] in ['price_drop', 'price_increase']:
            if 'percentage_change' not in data:
                return jsonify({
                    "error": "Invalid Alert Configuration",
                    "message": "percentage_change is required for percentage-based alerts",
                    "status": "error",
                    "code": "MISSING_PERCENTAGE"
                }), 400
            
            if 'baseline_price' not in data:
                return jsonify({
                    "error": "Invalid Alert Configuration",
                    "message": "baseline_price is required for percentage-based alerts",
                    "status": "error",
                    "code": "MISSING_BASELINE"
                }), 400
        
        logger.info(f"Creating alert for user {user.id}: {data['item_identifier']}")
        
        # Create alert
        alert = PriceAlert.create_alert(user.id, data)
        
        return jsonify({
            "alert": alert.to_dict(),
            "message": "Price alert created successfully",
            "status": "success"
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to create alert",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['GET'])
@rate_limit('/api/alerts')
@auth_required
def get_alert(alert_id):
    """Get specific alert"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get alert
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=user.id).first()
        
        if not alert:
            return jsonify({
                "error": "Alert Not Found",
                "message": "Price alert not found",
                "status": "error",
                "code": "ALERT_NOT_FOUND"
            }), 404
        
        return jsonify({
            "alert": alert.to_dict(),
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting alert: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve alert",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
@rate_limit('/api/alerts')
@auth_required
def update_alert(alert_id):
    """Update price alert"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get alert
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=user.id).first()
        
        if not alert:
            return jsonify({
                "error": "Alert Not Found",
                "message": "Price alert not found",
                "status": "error",
                "code": "ALERT_NOT_FOUND"
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Invalid Request",
                "message": "JSON data required",
                "status": "error",
                "code": "INVALID_JSON"
            }), 400
        
        logger.info(f"Updating alert {alert_id} for user {user.id}")
        
        # Update fields
        updatable_fields = [
            'platform', 'condition', 'threshold_price', 'percentage_change',
            'notification_method', 'baseline_price', 'notes', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(alert, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            "alert": alert.to_dict(),
            "message": "Alert updated successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating alert: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to update alert",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
@rate_limit('/api/alerts')
@auth_required
def delete_alert(alert_id):
    """Delete price alert"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get alert
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=user.id).first()
        
        if not alert:
            return jsonify({
                "error": "Alert Not Found",
                "message": "Price alert not found",
                "status": "error",
                "code": "ALERT_NOT_FOUND"
            }), 404
        
        logger.info(f"Deleting alert {alert_id} for user {user.id}")
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            "message": "Alert deleted successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting alert: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to delete alert",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/alerts/<int:alert_id>/toggle', methods=['POST'])
@rate_limit('/api/alerts')
@auth_required
def toggle_alert(alert_id):
    """Toggle alert active status"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "error": "Authentication Required",
                "message": "User authentication required",
                "status": "error",
                "code": "AUTH_REQUIRED"
            }), 401
        
        # Get alert
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=user.id).first()
        
        if not alert:
            return jsonify({
                "error": "Alert Not Found",
                "message": "Price alert not found",
                "status": "error",
                "code": "ALERT_NOT_FOUND"
            }), 404
        
        # Toggle active status
        alert.is_active = not alert.is_active
        db.session.commit()
        
        status_text = "activated" if alert.is_active else "deactivated"
        
        return jsonify({
            "alert": alert.to_dict(),
            "message": f"Alert {status_text} successfully",
            "status": "success"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling alert: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to toggle alert",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500
