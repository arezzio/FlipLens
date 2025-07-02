"""
User Settings model for FlipLens application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging

from .database import db

logger = logging.getLogger(__name__)

class UserSettings(db.Model):
    """Model for user application settings"""
    
    __tablename__ = 'user_settings'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    push_notifications = db.Column(db.Boolean, default=True, nullable=False)
    price_alert_notifications = db.Column(db.Boolean, default=True, nullable=False)
    market_update_notifications = db.Column(db.Boolean, default=False, nullable=False)
    newsletter_notifications = db.Column(db.Boolean, default=False, nullable=False)
    
    # App preferences
    dark_mode = db.Column(db.Boolean, default=False, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    language = db.Column(db.String(5), default='en', nullable=False)
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    
    # Display preferences
    items_per_page = db.Column(db.Integer, default=20, nullable=False)
    default_sort_order = db.Column(db.String(50), default='created_at_desc', nullable=False)
    show_profit_percentage = db.Column(db.Boolean, default=True, nullable=False)
    show_fliplens_rating = db.Column(db.Boolean, default=True, nullable=False)
    
    # Privacy settings
    profile_visibility = db.Column(db.String(20), default='private', nullable=False)  # private, public
    share_analytics = db.Column(db.Boolean, default=False, nullable=False)
    
    # Platform integrations
    ebay_connected = db.Column(db.Boolean, default=False, nullable=False)
    ebay_username = db.Column(db.String(100), nullable=True)
    poshmark_connected = db.Column(db.Boolean, default=False, nullable=False)
    poshmark_username = db.Column(db.String(100), nullable=True)
    mercari_connected = db.Column(db.Boolean, default=False, nullable=False)
    mercari_username = db.Column(db.String(100), nullable=True)
    
    # Advanced settings
    auto_update_market_prices = db.Column(db.Boolean, default=True, nullable=False)
    price_update_frequency = db.Column(db.String(20), default='daily', nullable=False)  # hourly, daily, weekly
    enable_experimental_features = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('settings', uselist=False))
    
    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<UserSettings for User {self.user_id}>'
    
    def to_dict(self):
        """Convert user settings to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notifications': {
                'email_notifications': self.email_notifications,
                'push_notifications': self.push_notifications,
                'price_alert_notifications': self.price_alert_notifications,
                'market_update_notifications': self.market_update_notifications,
                'newsletter_notifications': self.newsletter_notifications,
            },
            'app_preferences': {
                'dark_mode': self.dark_mode,
                'currency': self.currency,
                'language': self.language,
                'timezone': self.timezone,
            },
            'display_preferences': {
                'items_per_page': self.items_per_page,
                'default_sort_order': self.default_sort_order,
                'show_profit_percentage': self.show_profit_percentage,
                'show_fliplens_rating': self.show_fliplens_rating,
            },
            'privacy_settings': {
                'profile_visibility': self.profile_visibility,
                'share_analytics': self.share_analytics,
            },
            'platform_integrations': {
                'ebay': {
                    'connected': self.ebay_connected,
                    'username': self.ebay_username,
                },
                'poshmark': {
                    'connected': self.poshmark_connected,
                    'username': self.poshmark_username,
                },
                'mercari': {
                    'connected': self.mercari_connected,
                    'username': self.mercari_username,
                },
            },
            'advanced_settings': {
                'auto_update_market_prices': self.auto_update_market_prices,
                'price_update_frequency': self.price_update_frequency,
                'enable_experimental_features': self.enable_experimental_features,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def update_settings(self, settings_data):
        """Update user settings"""
        try:
            # Update notification preferences
            if 'notifications' in settings_data:
                notifications = settings_data['notifications']
                self.email_notifications = notifications.get('email_notifications', self.email_notifications)
                self.push_notifications = notifications.get('push_notifications', self.push_notifications)
                self.price_alert_notifications = notifications.get('price_alert_notifications', self.price_alert_notifications)
                self.market_update_notifications = notifications.get('market_update_notifications', self.market_update_notifications)
                self.newsletter_notifications = notifications.get('newsletter_notifications', self.newsletter_notifications)
            
            # Update app preferences
            if 'app_preferences' in settings_data:
                app_prefs = settings_data['app_preferences']
                self.dark_mode = app_prefs.get('dark_mode', self.dark_mode)
                self.currency = app_prefs.get('currency', self.currency)
                self.language = app_prefs.get('language', self.language)
                self.timezone = app_prefs.get('timezone', self.timezone)
            
            # Update display preferences
            if 'display_preferences' in settings_data:
                display_prefs = settings_data['display_preferences']
                self.items_per_page = display_prefs.get('items_per_page', self.items_per_page)
                self.default_sort_order = display_prefs.get('default_sort_order', self.default_sort_order)
                self.show_profit_percentage = display_prefs.get('show_profit_percentage', self.show_profit_percentage)
                self.show_fliplens_rating = display_prefs.get('show_fliplens_rating', self.show_fliplens_rating)
            
            # Update privacy settings
            if 'privacy_settings' in settings_data:
                privacy = settings_data['privacy_settings']
                self.profile_visibility = privacy.get('profile_visibility', self.profile_visibility)
                self.share_analytics = privacy.get('share_analytics', self.share_analytics)
            
            # Update platform integrations
            if 'platform_integrations' in settings_data:
                platforms = settings_data['platform_integrations']
                
                if 'ebay' in platforms:
                    ebay = platforms['ebay']
                    self.ebay_connected = ebay.get('connected', self.ebay_connected)
                    self.ebay_username = ebay.get('username', self.ebay_username)
                
                if 'poshmark' in platforms:
                    poshmark = platforms['poshmark']
                    self.poshmark_connected = poshmark.get('connected', self.poshmark_connected)
                    self.poshmark_username = poshmark.get('username', self.poshmark_username)
                
                if 'mercari' in platforms:
                    mercari = platforms['mercari']
                    self.mercari_connected = mercari.get('connected', self.mercari_connected)
                    self.mercari_username = mercari.get('username', self.mercari_username)
            
            # Update advanced settings
            if 'advanced_settings' in settings_data:
                advanced = settings_data['advanced_settings']
                self.auto_update_market_prices = advanced.get('auto_update_market_prices', self.auto_update_market_prices)
                self.price_update_frequency = advanced.get('price_update_frequency', self.price_update_frequency)
                self.enable_experimental_features = advanced.get('enable_experimental_features', self.enable_experimental_features)
            
            self.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Settings updated for user {self.user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update settings for user {self.user_id}: {str(e)}")
            return False
    
    @classmethod
    def get_or_create_settings(cls, user_id):
        """Get existing settings or create default settings for user"""
        try:
            settings = cls.query.filter_by(user_id=user_id).first()
            
            if not settings:
                settings = cls(user_id=user_id)
                db.session.add(settings)
                db.session.commit()
                logger.info(f"Created default settings for user {user_id}")
            
            return settings
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to get/create settings for user {user_id}: {str(e)}")
            raise
    
    @classmethod
    def reset_to_defaults(cls, user_id):
        """Reset user settings to defaults"""
        try:
            settings = cls.query.filter_by(user_id=user_id).first()
            
            if settings:
                # Reset to default values
                settings.email_notifications = True
                settings.push_notifications = True
                settings.price_alert_notifications = True
                settings.market_update_notifications = False
                settings.newsletter_notifications = False
                settings.dark_mode = False
                settings.currency = 'USD'
                settings.language = 'en'
                settings.timezone = 'UTC'
                settings.items_per_page = 20
                settings.default_sort_order = 'created_at_desc'
                settings.show_profit_percentage = True
                settings.show_fliplens_rating = True
                settings.profile_visibility = 'private'
                settings.share_analytics = False
                settings.auto_update_market_prices = True
                settings.price_update_frequency = 'daily'
                settings.enable_experimental_features = False
                settings.updated_at = datetime.utcnow()
                
                db.session.commit()
                logger.info(f"Reset settings to defaults for user {user_id}")
                return settings
            
            return None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to reset settings for user {user_id}: {str(e)}")
            raise
