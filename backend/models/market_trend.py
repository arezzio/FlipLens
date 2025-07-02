"""
Market Trend model for FlipLens application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging

from .database import db

logger = logging.getLogger(__name__)

class MarketTrend(db.Model):
    """Model for tracking market price trends"""
    
    __tablename__ = 'market_trends'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    item_identifier = db.Column(db.String(200), nullable=False, index=True)  # Item name/model
    platform = db.Column(db.String(50), nullable=False, index=True)  # eBay, Poshmark, etc.
    condition = db.Column(db.String(50), nullable=False, index=True)  # new, used, refurbished
    
    # Price data
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Market data
    listing_count = db.Column(db.Integer, default=1, nullable=False)
    sold_count = db.Column(db.Integer, default=0, nullable=False)
    average_days_to_sell = db.Column(db.Float, nullable=True)
    
    # Metadata
    data_source = db.Column(db.String(100), nullable=True)  # API source
    confidence_score = db.Column(db.Float, default=0.5, nullable=False)
    
    # Timestamps
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_item_platform_condition', 'item_identifier', 'platform', 'condition'),
        db.Index('idx_recorded_at', 'recorded_at'),
    )
    
    def __init__(self, item_identifier, platform, condition, price, **kwargs):
        self.item_identifier = item_identifier
        self.platform = platform
        self.condition = condition
        self.price = price
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<MarketTrend {self.item_identifier} on {self.platform}>'
    
    def to_dict(self):
        """Convert market trend to dictionary"""
        return {
            'id': self.id,
            'item_identifier': self.item_identifier,
            'platform': self.platform,
            'condition': self.condition,
            'price': float(self.price) if self.price else None,
            'currency': self.currency,
            'listing_count': self.listing_count,
            'sold_count': self.sold_count,
            'average_days_to_sell': self.average_days_to_sell,
            'data_source': self.data_source,
            'confidence_score': self.confidence_score,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def get_price_trends(cls, item_identifier, platform=None, condition=None, 
                        days_back=30, limit=1000):
        """Get price trends for an item"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            query = cls.query.filter(
                cls.item_identifier == item_identifier,
                cls.recorded_at >= cutoff_date
            )
            
            if platform:
                query = query.filter(cls.platform == platform)
            
            if condition:
                query = query.filter(cls.condition == condition)
            
            trends = query.order_by(cls.recorded_at.asc()).limit(limit).all()
            
            return [trend.to_dict() for trend in trends]
            
        except Exception as e:
            logger.error(f"Failed to get price trends: {str(e)}")
            return []
    
    @classmethod
    def get_market_summary(cls, item_identifier, platform=None, condition=None, days_back=30):
        """Get market summary statistics"""
        try:
            from datetime import timedelta
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            query = cls.query.filter(
                cls.item_identifier == item_identifier,
                cls.recorded_at >= cutoff_date
            )
            
            if platform:
                query = query.filter(cls.platform == platform)
            
            if condition:
                query = query.filter(cls.condition == condition)
            
            # Calculate statistics
            stats = query.with_entities(
                func.avg(cls.price).label('average'),
                func.min(cls.price).label('lowest'),
                func.max(cls.price).label('highest'),
                func.count(cls.price).label('count')
            ).first()
            
            if not stats or stats.count == 0:
                return None
            
            # Calculate median (approximate)
            prices = [float(trend.price) for trend in query.all()]
            prices.sort()
            median = prices[len(prices) // 2] if prices else 0
            
            return {
                'average': float(stats.average) if stats.average else 0,
                'median': median,
                'lowest': float(stats.lowest) if stats.lowest else 0,
                'highest': float(stats.highest) if stats.highest else 0,
                'count': stats.count,
                'period_days': days_back
            }
            
        except Exception as e:
            logger.error(f"Failed to get market summary: {str(e)}")
            return None
    
    @classmethod
    def record_price_data(cls, item_identifier, platform, condition, price, **kwargs):
        """Record new price data point"""
        try:
            trend = cls(
                item_identifier=item_identifier,
                platform=platform,
                condition=condition,
                price=price,
                **kwargs
            )
            
            db.session.add(trend)
            db.session.commit()
            
            logger.info(f"Recorded price data for {item_identifier}: ${price}")
            return trend
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record price data: {str(e)}")
            raise
