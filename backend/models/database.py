"""
Database configuration and initialization for FlipLens
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import current_app
import logging
import os

logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app"""
    try:
        # Configure SQLAlchemy
        db.init_app(app)
        migrate.init_app(app, db)
        
        # Create tables if they don't exist
        with app.app_context():
            # Import all models to ensure they're registered
            from . import user, saved_item, search_history, market_trend, portfolio_item, price_alert, user_settings
            
            # Create all tables
            db.create_all()
            
            logger.info("Database initialized successfully")
            
            # Log database info
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
            logger.info(f"Database URL: {db_url}")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def get_db_stats():
    """Get database statistics for health checks"""
    try:
        from .user import User
        from .saved_item import SavedItem
        from .search_history import SearchHistory
        
        stats = {
            'users': User.query.count(),
            'saved_items': SavedItem.query.count(),
            'search_history': SearchHistory.query.count(),
            'status': 'healthy'
        }
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def reset_database():
    """Reset database (for development/testing only)"""
    if current_app.config.get('FLASK_ENV') not in ['development', 'testing']:
        raise ValueError("Database reset only allowed in development/testing environments")
    
    try:
        db.drop_all()
        db.create_all()
        logger.info("Database reset successfully")
    except Exception as e:
        logger.error(f"Failed to reset database: {str(e)}")
        raise
