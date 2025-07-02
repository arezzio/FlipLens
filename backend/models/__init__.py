"""
Database models for FlipLens application
"""

from .database import db, init_db
from .user import User
from .saved_item import SavedItem
from .search_history import SearchHistory
from .market_trend import MarketTrend
from .portfolio_item import PortfolioItem
from .price_alert import PriceAlert, AlertNotification
from .user_settings import UserSettings

__all__ = [
    'db', 'init_db', 'User', 'SavedItem', 'SearchHistory',
    'MarketTrend', 'PortfolioItem', 'PriceAlert', 'AlertNotification', 'UserSettings'
]