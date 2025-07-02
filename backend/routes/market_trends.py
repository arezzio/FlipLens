"""
Market Trends routes for FlipLens application
"""

from flask import jsonify, request, g
from . import api_bp
from utils.rate_limiter import rate_limit
from utils.auth_middleware import auth_optional, get_current_user
from models.market_trend import MarketTrend
from models.database import db
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@api_bp.route('/market-trends/<item_identifier>', methods=['GET'])
@rate_limit('/api/market-trends')
@auth_optional
def get_market_trends(item_identifier):
    """Get market price trends for an item"""
    try:
        # Get query parameters
        platform = request.args.get('platform')
        condition = request.args.get('condition')
        days_back = request.args.get('days_back', 30, type=int)
        
        # Validate days_back
        if days_back < 1 or days_back > 365:
            return jsonify({
                "error": "Invalid Time Range",
                "message": "days_back must be between 1 and 365",
                "status": "error",
                "code": "INVALID_TIME_RANGE"
            }), 400
        
        logger.info(f"Getting market trends for {item_identifier} (platform: {platform}, condition: {condition}, days: {days_back})")
        
        # Get price trends
        trends = MarketTrend.get_price_trends(
            item_identifier=item_identifier,
            platform=platform,
            condition=condition,
            days_back=days_back
        )
        
        # Get market summary
        summary = MarketTrend.get_market_summary(
            item_identifier=item_identifier,
            platform=platform,
            condition=condition,
            days_back=days_back
        )
        
        # If no real data, generate mock data for demonstration
        if not trends:
            trends = _generate_mock_trend_data(item_identifier, platform, condition, days_back)
            summary = _calculate_mock_summary(trends)
        
        return jsonify({
            "item_identifier": item_identifier,
            "platform": platform,
            "condition": condition,
            "time_range_days": days_back,
            "trends": trends,
            "summary": summary,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting market trends: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve market trends",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/market-trends/<item_identifier>/summary', methods=['GET'])
@rate_limit('/api/market-trends')
@auth_optional
def get_market_summary(item_identifier):
    """Get market summary statistics for an item"""
    try:
        # Get query parameters
        platform = request.args.get('platform')
        condition = request.args.get('condition')
        days_back = request.args.get('days_back', 30, type=int)
        
        logger.info(f"Getting market summary for {item_identifier}")
        
        # Get market summary
        summary = MarketTrend.get_market_summary(
            item_identifier=item_identifier,
            platform=platform,
            condition=condition,
            days_back=days_back
        )
        
        # If no real data, generate mock summary
        if not summary:
            mock_trends = _generate_mock_trend_data(item_identifier, platform, condition, days_back)
            summary = _calculate_mock_summary(mock_trends)
        
        return jsonify({
            "item_identifier": item_identifier,
            "summary": summary,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting market summary: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve market summary",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/market-trends/platforms', methods=['GET'])
@rate_limit('/api/market-trends')
def get_supported_platforms():
    """Get list of supported platforms"""
    try:
        platforms = [
            {"id": "ebay", "name": "eBay", "active": True},
            {"id": "poshmark", "name": "Poshmark", "active": True},
            {"id": "mercari", "name": "Mercari", "active": True},
            {"id": "depop", "name": "Depop", "active": False},
            {"id": "vinted", "name": "Vinted", "active": False},
            {"id": "facebook", "name": "Facebook Marketplace", "active": False},
        ]
        
        return jsonify({
            "platforms": platforms,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting platforms: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve platforms",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

@api_bp.route('/market-trends/conditions', methods=['GET'])
@rate_limit('/api/market-trends')
def get_supported_conditions():
    """Get list of supported item conditions"""
    try:
        conditions = [
            {"id": "new", "name": "New", "description": "Brand new with tags"},
            {"id": "excellent", "name": "Excellent", "description": "Like new, no visible wear"},
            {"id": "very_good", "name": "Very Good", "description": "Minor signs of wear"},
            {"id": "good", "name": "Good", "description": "Some signs of wear"},
            {"id": "fair", "name": "Fair", "description": "Noticeable wear"},
            {"id": "poor", "name": "Poor", "description": "Significant wear"},
        ]
        
        return jsonify({
            "conditions": conditions,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conditions: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to retrieve conditions",
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

def _generate_mock_trend_data(item_identifier, platform, condition, days_back):
    """Generate mock trend data for demonstration"""
    import random
    from datetime import datetime, timedelta
    
    trends = []
    base_price = 50 + (hash(item_identifier) % 200)  # Base price between 50-250
    
    for i in range(min(days_back, 30)):  # Generate up to 30 data points
        date = datetime.utcnow() - timedelta(days=days_back - i)
        
        # Add some realistic price variation
        variation = random.uniform(-0.2, 0.2)  # ±20% variation
        price = base_price * (1 + variation)
        
        # Add trend (slight upward trend for popular items)
        trend_factor = 1 + (i * 0.002)  # 0.2% increase per day
        price *= trend_factor
        
        trends.append({
            'id': f'mock-{i}',
            'item_identifier': item_identifier,
            'platform': platform or 'ebay',
            'condition': condition or 'good',
            'price': round(price, 2),
            'currency': 'USD',
            'listing_count': random.randint(5, 50),
            'sold_count': random.randint(1, 10),
            'confidence_score': random.uniform(0.7, 0.95),
            'recorded_at': date.isoformat(),
            'created_at': date.isoformat(),
        })
    
    return trends

def _calculate_mock_summary(trends):
    """Calculate summary statistics from trend data"""
    if not trends:
        return None
    
    prices = [trend['price'] for trend in trends]
    
    return {
        'average': round(sum(prices) / len(prices), 2),
        'median': round(sorted(prices)[len(prices) // 2], 2),
        'lowest': min(prices),
        'highest': max(prices),
        'count': len(trends),
        'period_days': len(trends)
    }
