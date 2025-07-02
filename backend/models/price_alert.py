"""
Price Alert model for FlipLens application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging

from .database import db

logger = logging.getLogger(__name__)

class PriceAlert(db.Model):
    """Model for user price alerts"""
    
    __tablename__ = 'price_alerts'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Alert target
    item_identifier = db.Column(db.String(200), nullable=False, index=True)
    platform = db.Column(db.String(50), nullable=True)  # Specific platform or 'all'
    condition = db.Column(db.String(50), nullable=True)  # Specific condition or 'all'
    
    # Alert conditions
    alert_type = db.Column(db.String(20), nullable=False)  # 'price_drop', 'price_increase', 'threshold'
    threshold_price = db.Column(db.Numeric(10, 2), nullable=True)  # Target price for threshold alerts
    percentage_change = db.Column(db.Float, nullable=True)  # Percentage for increase/decrease alerts
    
    # Alert settings
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    notification_method = db.Column(db.String(20), default='email', nullable=False)  # email, push, both
    
    # Tracking data
    baseline_price = db.Column(db.Numeric(10, 2), nullable=True)  # Price when alert was created
    last_checked_price = db.Column(db.Numeric(10, 2), nullable=True)
    last_triggered = db.Column(db.DateTime, nullable=True)
    trigger_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Metadata
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref='price_alerts')
    
    def __init__(self, user_id, item_identifier, alert_type, **kwargs):
        self.user_id = user_id
        self.item_identifier = item_identifier
        self.alert_type = alert_type
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<PriceAlert {self.item_identifier} for User {self.user_id}>'
    
    def check_alert_condition(self, current_price):
        """Check if alert condition is met"""
        try:
            if not self.is_active:
                return False
            
            current_price = float(current_price)
            self.last_checked_price = current_price
            
            if self.alert_type == 'threshold':
                if self.threshold_price:
                    threshold = float(self.threshold_price)
                    return current_price <= threshold
            
            elif self.alert_type == 'price_drop':
                if self.baseline_price and self.percentage_change:
                    baseline = float(self.baseline_price)
                    drop_threshold = baseline * (1 - self.percentage_change / 100)
                    return current_price <= drop_threshold
            
            elif self.alert_type == 'price_increase':
                if self.baseline_price and self.percentage_change:
                    baseline = float(self.baseline_price)
                    increase_threshold = baseline * (1 + self.percentage_change / 100)
                    return current_price >= increase_threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert condition: {str(e)}")
            return False
    
    def trigger_alert(self):
        """Mark alert as triggered"""
        self.last_triggered = datetime.utcnow()
        self.trigger_count += 1
        self.updated_at = datetime.utcnow()
    
    def update_baseline_price(self, price):
        """Update baseline price for percentage-based alerts"""
        self.baseline_price = price
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the alert"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert price alert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_identifier': self.item_identifier,
            'platform': self.platform,
            'condition': self.condition,
            'alert_type': self.alert_type,
            'threshold_price': float(self.threshold_price) if self.threshold_price else None,
            'percentage_change': self.percentage_change,
            'is_active': self.is_active,
            'notification_method': self.notification_method,
            'baseline_price': float(self.baseline_price) if self.baseline_price else None,
            'last_checked_price': float(self.last_checked_price) if self.last_checked_price else None,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def create_alert(cls, user_id, alert_data):
        """Create a new price alert"""
        try:
            alert = cls(
                user_id=user_id,
                item_identifier=alert_data['item_identifier'],
                alert_type=alert_data['alert_type'],
                platform=alert_data.get('platform'),
                condition=alert_data.get('condition'),
                threshold_price=alert_data.get('threshold_price'),
                percentage_change=alert_data.get('percentage_change'),
                notification_method=alert_data.get('notification_method', 'email'),
                baseline_price=alert_data.get('baseline_price'),
                notes=alert_data.get('notes', '')
            )
            
            db.session.add(alert)
            db.session.commit()
            
            logger.info(f"Price alert created for user {user_id}: {alert.item_identifier}")
            return alert
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create price alert: {str(e)}")
            raise
    
    @classmethod
    def get_active_alerts_for_item(cls, item_identifier):
        """Get all active alerts for a specific item"""
        try:
            alerts = cls.query.filter(
                cls.item_identifier == item_identifier,
                cls.is_active == True
            ).all()
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get alerts for item {item_identifier}: {str(e)}")
            return []
    
    @classmethod
    def check_all_alerts(cls, item_identifier, current_price):
        """Check all alerts for an item and trigger if conditions are met"""
        try:
            alerts = cls.get_active_alerts_for_item(item_identifier)
            triggered_alerts = []
            
            for alert in alerts:
                if alert.check_alert_condition(current_price):
                    alert.trigger_alert()
                    triggered_alerts.append(alert)
            
            if triggered_alerts:
                db.session.commit()
                logger.info(f"Triggered {len(triggered_alerts)} alerts for {item_identifier}")
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Failed to check alerts: {str(e)}")
            return []


class AlertNotification(db.Model):
    """Model for alert notifications sent to users"""
    
    __tablename__ = 'alert_notifications'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('price_alerts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification details
    notification_type = db.Column(db.String(20), nullable=False)  # email, push
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, sent, failed
    sent_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    trigger_price = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    alert = db.relationship('PriceAlert', backref='notifications')
    user = db.relationship('User', backref='alert_notifications')
    
    def __init__(self, alert_id, user_id, notification_type, title, message, **kwargs):
        self.alert_id = alert_id
        self.user_id = user_id
        self.notification_type = notification_type
        self.title = title
        self.message = message
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message):
        """Mark notification as failed"""
        self.status = 'failed'
        self.error_message = error_message
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message,
            'trigger_price': float(self.trigger_price) if self.trigger_price else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
