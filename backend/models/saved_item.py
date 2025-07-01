"""
SavedItem model for FlipLens application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging

from .database import db

logger = logging.getLogger(__name__)

class SavedItem(db.Model):
    """Model for items saved by users"""
    
    __tablename__ = 'saved_items'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # eBay item data
    ebay_item_id = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # URLs and images
    image_url = db.Column(db.Text, nullable=True)
    item_url = db.Column(db.Text, nullable=True)
    
    # Item details
    condition = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Business logic fields
    estimated_profit = db.Column(db.Numeric(10, 2), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    market_data = db.Column(db.JSON, nullable=True)  # Store market analysis data
    
    # User notes and tags
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
    
    # Status tracking
    status = db.Column(db.String(20), default='saved', nullable=False)  # saved, purchased, sold, archived
    purchase_price = db.Column(db.Numeric(10, 2), nullable=True)
    purchase_date = db.Column(db.DateTime, nullable=True)
    sale_price = db.Column(db.Numeric(10, 2), nullable=True)
    sale_date = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint to prevent duplicate saves
    __table_args__ = (
        db.UniqueConstraint('user_id', 'ebay_item_id', name='unique_user_item'),
    )
    
    def __init__(self, user_id, ebay_item_id, title, price, currency='USD', **kwargs):
        self.user_id = user_id
        self.ebay_item_id = ebay_item_id
        self.title = title
        self.price = price
        self.currency = currency
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<SavedItem {self.ebay_item_id} by User {self.user_id}>'
    
    def calculate_profit(self, selling_price=None, platform_fee_rate=0.10, shipping_cost=None):
        """Calculate estimated profit"""
        try:
            if selling_price is None:
                selling_price = float(self.price)
            
            if shipping_cost is None:
                shipping_cost = float(self.shipping_cost or 0)
            
            # Calculate fees
            platform_fee = selling_price * platform_fee_rate
            total_costs = platform_fee + shipping_cost
            
            # Estimated profit (assuming we buy at a discount)
            estimated_buy_price = selling_price * 0.3  # Assume 70% discount from market price
            profit = selling_price - total_costs - estimated_buy_price
            
            self.estimated_profit = round(profit, 2)
            return self.estimated_profit
            
        except Exception as e:
            logger.error(f"Failed to calculate profit for item {self.id}: {str(e)}")
            return None
    
    def update_market_data(self, market_data):
        """Update market analysis data"""
        try:
            self.market_data = market_data
            
            # Extract confidence score from market data
            if isinstance(market_data, dict):
                self.confidence_score = market_data.get('confidence_score', 0.5)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update market data for item {self.id}: {str(e)}")
            db.session.rollback()
    
    def add_tag(self, tag):
        """Add a tag to the item"""
        if not self.tags:
            self.tags = tag
        else:
            tags_list = [t.strip() for t in self.tags.split(',')]
            if tag not in tags_list:
                tags_list.append(tag)
                self.tags = ','.join(tags_list)
    
    def remove_tag(self, tag):
        """Remove a tag from the item"""
        if self.tags:
            tags_list = [t.strip() for t in self.tags.split(',')]
            if tag in tags_list:
                tags_list.remove(tag)
                self.tags = ','.join(tags_list) if tags_list else None
    
    def get_tags_list(self):
        """Get tags as a list"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]
    
    def mark_purchased(self, purchase_price, purchase_date=None):
        """Mark item as purchased"""
        self.status = 'purchased'
        self.purchase_price = purchase_price
        self.purchase_date = purchase_date or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_sold(self, sale_price, sale_date=None):
        """Mark item as sold"""
        self.status = 'sold'
        self.sale_price = sale_price
        self.sale_date = sale_date or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def calculate_actual_profit(self):
        """Calculate actual profit if item was purchased and sold"""
        if self.status == 'sold' and self.purchase_price and self.sale_price:
            return float(self.sale_price) - float(self.purchase_price)
        return None
    
    def to_dict(self):
        """Convert saved item to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ebay_item_id': self.ebay_item_id,
            'title': self.title,
            'price': float(self.price) if self.price else None,
            'currency': self.currency,
            'image_url': self.image_url,
            'item_url': self.item_url,
            'condition': self.condition,
            'location': self.location,
            'shipping_cost': float(self.shipping_cost) if self.shipping_cost else None,
            'estimated_profit': float(self.estimated_profit) if self.estimated_profit else None,
            'confidence_score': self.confidence_score,
            'market_data': self.market_data,
            'notes': self.notes,
            'tags': self.get_tags_list(),
            'is_favorite': self.is_favorite,
            'status': self.status,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'sale_price': float(self.sale_price) if self.sale_price else None,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'actual_profit': self.calculate_actual_profit(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def create_saved_item(cls, user_id, item_data):
        """Create a new saved item with validation"""
        try:
            # Check if item already saved by user
            existing = cls.query.filter_by(
                user_id=user_id,
                ebay_item_id=item_data['ebay_item_id']
            ).first()
            
            if existing:
                raise ValueError("Item already saved by user")
            
            # Create new saved item
            saved_item = cls(
                user_id=user_id,
                ebay_item_id=item_data['ebay_item_id'],
                title=item_data['title'],
                price=item_data['price'],
                currency=item_data.get('currency', 'USD'),
                image_url=item_data.get('image_url'),
                item_url=item_data.get('item_url'),
                condition=item_data.get('condition'),
                location=item_data.get('location'),
                shipping_cost=item_data.get('shipping_cost'),
                notes=item_data.get('notes', '')
            )
            
            # Calculate initial profit estimate
            saved_item.calculate_profit()
            
            db.session.add(saved_item)
            db.session.commit()
            
            logger.info(f"Item {saved_item.ebay_item_id} saved by user {user_id}")
            return saved_item
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create saved item: {str(e)}")
            raise
    
    def update_item(self, updates):
        """Update saved item with new data"""
        try:
            allowed_fields = [
                'title', 'price', 'currency', 'image_url', 'item_url',
                'condition', 'location', 'shipping_cost', 'notes', 'tags',
                'is_favorite', 'status'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(self, field):
                    setattr(self, field, value)
            
            self.updated_at = datetime.utcnow()
            
            # Recalculate profit if price changed
            if 'price' in updates or 'shipping_cost' in updates:
                self.calculate_profit()
            
            db.session.commit()
            logger.info(f"Saved item {self.id} updated")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update saved item {self.id}: {str(e)}")
            raise
    
    def delete_item(self):
        """Delete saved item"""
        try:
            db.session.delete(self)
            db.session.commit()
            logger.info(f"Saved item {self.id} deleted")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete saved item {self.id}: {str(e)}")
            raise
