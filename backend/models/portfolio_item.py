"""
Portfolio Item model for FlipLens application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging

from .database import db

logger = logging.getLogger(__name__)

class PortfolioItem(db.Model):
    """Model for user's portfolio items (owned items)"""
    
    __tablename__ = 'portfolio_items'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Item details
    item_name = db.Column(db.String(500), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(200), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(100), nullable=True)
    condition = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    
    # Purchase information
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False)
    purchase_platform = db.Column(db.String(100), nullable=True)
    purchase_location = db.Column(db.String(200), nullable=True)
    
    # Current market data
    current_market_price = db.Column(db.Numeric(10, 2), nullable=True)
    last_price_update = db.Column(db.DateTime, nullable=True)
    
    # FlipLens Rating (custom calculated rating)
    fliplens_rating = db.Column(db.Float, nullable=True)  # 0.0 to 10.0
    rating_factors = db.Column(db.JSON, nullable=True)  # Breakdown of rating factors
    
    # Status and tracking
    status = db.Column(db.String(20), default='owned', nullable=False)  # owned, listed, sold
    listing_price = db.Column(db.Numeric(10, 2), nullable=True)
    listing_platform = db.Column(db.String(100), nullable=True)
    listing_date = db.Column(db.DateTime, nullable=True)
    
    sale_price = db.Column(db.Numeric(10, 2), nullable=True)
    sale_date = db.Column(db.DateTime, nullable=True)
    sale_platform = db.Column(db.String(100), nullable=True)
    
    # Additional data
    images = db.Column(db.JSON, nullable=True)  # Array of image URLs
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref='portfolio_items')
    
    def __init__(self, user_id, item_name, purchase_price, purchase_date, condition, **kwargs):
        self.user_id = user_id
        self.item_name = item_name
        self.purchase_price = purchase_price
        self.purchase_date = purchase_date
        self.condition = condition
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<PortfolioItem {self.item_name} by User {self.user_id}>'
    
    def calculate_fliplens_rating(self):
        """Calculate FlipLens rating based on multiple factors"""
        try:
            factors = {}
            total_score = 0
            max_score = 0
            
            # Factor 1: Market demand (based on search volume, sold listings)
            # Mock calculation - in production, use real market data
            demand_score = 7.5  # 0-10
            factors['market_demand'] = demand_score
            total_score += demand_score
            max_score += 10
            
            # Factor 2: Price volatility (lower volatility = higher rating)
            volatility_score = 6.0  # 0-10 (10 = low volatility)
            factors['price_stability'] = volatility_score
            total_score += volatility_score
            max_score += 10
            
            # Factor 3: Profit potential
            if self.current_market_price and self.purchase_price:
                profit_margin = (float(self.current_market_price) - float(self.purchase_price)) / float(self.purchase_price)
                profit_score = min(10, max(0, profit_margin * 20))  # 50% profit = 10 points
            else:
                profit_score = 5.0  # Default if no market price
            factors['profit_potential'] = profit_score
            total_score += profit_score
            max_score += 10
            
            # Factor 4: Condition factor
            condition_scores = {
                'new': 10,
                'excellent': 8,
                'very good': 7,
                'good': 6,
                'fair': 4,
                'poor': 2
            }
            condition_score = condition_scores.get(self.condition.lower(), 5)
            factors['condition'] = condition_score
            total_score += condition_score
            max_score += 10
            
            # Factor 5: Brand recognition (mock data)
            brand_scores = {
                'nike': 9,
                'adidas': 8,
                'supreme': 10,
                'louis vuitton': 10,
                'gucci': 9,
                'prada': 8
            }
            brand_score = brand_scores.get(self.brand.lower() if self.brand else '', 5)
            factors['brand_value'] = brand_score
            total_score += brand_score
            max_score += 10
            
            # Calculate final rating (0-10 scale)
            final_rating = (total_score / max_score) * 10
            
            self.fliplens_rating = round(final_rating, 1)
            self.rating_factors = factors
            
            return self.fliplens_rating
            
        except Exception as e:
            logger.error(f"Failed to calculate FlipLens rating: {str(e)}")
            self.fliplens_rating = 5.0  # Default rating
            return self.fliplens_rating
    
    def calculate_profit_loss(self):
        """Calculate current profit or loss"""
        if not self.current_market_price:
            return None
        
        if self.status == 'sold' and self.sale_price:
            return float(self.sale_price) - float(self.purchase_price)
        else:
            return float(self.current_market_price) - float(self.purchase_price)
    
    def get_profit_percentage(self):
        """Calculate profit percentage"""
        profit = self.calculate_profit_loss()
        if profit is None:
            return None
        
        return (profit / float(self.purchase_price)) * 100
    
    def update_market_price(self, new_price):
        """Update current market price"""
        self.current_market_price = new_price
        self.last_price_update = datetime.utcnow()
        self.calculate_fliplens_rating()  # Recalculate rating
    
    def mark_as_listed(self, listing_price, platform):
        """Mark item as listed for sale"""
        self.status = 'listed'
        self.listing_price = listing_price
        self.listing_platform = platform
        self.listing_date = datetime.utcnow()
    
    def mark_as_sold(self, sale_price, platform):
        """Mark item as sold"""
        self.status = 'sold'
        self.sale_price = sale_price
        self.sale_platform = platform
        self.sale_date = datetime.utcnow()
    
    def to_dict(self):
        """Convert portfolio item to dictionary"""
        profit_loss = self.calculate_profit_loss()
        profit_percentage = self.get_profit_percentage()
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_name': self.item_name,
            'brand': self.brand,
            'model': self.model,
            'size': self.size,
            'color': self.color,
            'condition': self.condition,
            'category': self.category,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_platform': self.purchase_platform,
            'purchase_location': self.purchase_location,
            'current_market_price': float(self.current_market_price) if self.current_market_price else None,
            'last_price_update': self.last_price_update.isoformat() if self.last_price_update else None,
            'fliplens_rating': self.fliplens_rating,
            'rating_factors': self.rating_factors,
            'status': self.status,
            'listing_price': float(self.listing_price) if self.listing_price else None,
            'listing_platform': self.listing_platform,
            'listing_date': self.listing_date.isoformat() if self.listing_date else None,
            'sale_price': float(self.sale_price) if self.sale_price else None,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'sale_platform': self.sale_platform,
            'profit_loss': profit_loss,
            'profit_percentage': profit_percentage,
            'images': self.images,
            'notes': self.notes,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def create_portfolio_item(cls, user_id, item_data):
        """Create a new portfolio item"""
        try:
            portfolio_item = cls(
                user_id=user_id,
                item_name=item_data['item_name'],
                purchase_price=item_data['purchase_price'],
                purchase_date=datetime.fromisoformat(item_data['purchase_date'].replace('Z', '+00:00')),
                condition=item_data['condition'],
                brand=item_data.get('brand'),
                model=item_data.get('model'),
                size=item_data.get('size'),
                color=item_data.get('color'),
                category=item_data.get('category'),
                purchase_platform=item_data.get('purchase_platform'),
                purchase_location=item_data.get('purchase_location'),
                notes=item_data.get('notes', ''),
                tags=item_data.get('tags', '')
            )
            
            # Calculate initial rating
            portfolio_item.calculate_fliplens_rating()
            
            db.session.add(portfolio_item)
            db.session.commit()
            
            logger.info(f"Portfolio item created for user {user_id}: {portfolio_item.item_name}")
            return portfolio_item
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create portfolio item: {str(e)}")
            raise
