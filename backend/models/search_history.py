"""
SearchHistory model for FlipLens application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging

from .database import db

logger = logging.getLogger(__name__)

class SearchHistory(db.Model):
    """Model for tracking user search history and analytics"""
    
    __tablename__ = 'search_history'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Search details
    query = db.Column(db.String(500), nullable=False)
    results_count = db.Column(db.Integer, default=0, nullable=False)
    search_duration = db.Column(db.Float, nullable=True)  # Search time in seconds
    
    # Search metadata
    filters_applied = db.Column(db.JSON, nullable=True)  # Store search filters
    sort_order = db.Column(db.String(50), nullable=True)
    limit_requested = db.Column(db.Integer, default=20, nullable=False)
    
    # Results metadata
    avg_price = db.Column(db.Numeric(10, 2), nullable=True)
    min_price = db.Column(db.Numeric(10, 2), nullable=True)
    max_price = db.Column(db.Numeric(10, 2), nullable=True)
    top_conditions = db.Column(db.JSON, nullable=True)  # Most common conditions
    top_locations = db.Column(db.JSON, nullable=True)   # Most common locations
    
    # User interaction
    items_saved_from_search = db.Column(db.Integer, default=0, nullable=False)
    search_success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __init__(self, user_id, query, **kwargs):
        self.user_id = user_id
        self.query = query
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<SearchHistory "{self.query}" by User {self.user_id}>'
    
    def analyze_results(self, search_results):
        """Analyze search results and update metadata"""
        try:
            if not search_results:
                self.results_count = 0
                return
            
            self.results_count = len(search_results)
            
            # Extract prices
            prices = []
            conditions = []
            locations = []
            
            for item in search_results:
                try:
                    price = float(item.get('price', 0))
                    if price > 0:
                        prices.append(price)
                except (ValueError, TypeError):
                    pass
                
                condition = item.get('condition', '').strip()
                if condition:
                    conditions.append(condition)
                
                location = item.get('location', '').strip()
                if location:
                    locations.append(location)
            
            # Calculate price statistics
            if prices:
                self.avg_price = round(sum(prices) / len(prices), 2)
                self.min_price = min(prices)
                self.max_price = max(prices)
            
            # Analyze conditions
            if conditions:
                condition_counts = {}
                for condition in conditions:
                    condition_counts[condition] = condition_counts.get(condition, 0) + 1
                
                # Store top 5 conditions
                sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)
                self.top_conditions = dict(sorted_conditions[:5])
            
            # Analyze locations
            if locations:
                location_counts = {}
                for location in locations:
                    location_counts[location] = location_counts.get(location, 0) + 1
                
                # Store top 5 locations
                sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
                self.top_locations = dict(sorted_locations[:5])
            
            logger.info(f"Search analysis completed for query '{self.query}': {self.results_count} results")
            
        except Exception as e:
            logger.error(f"Failed to analyze search results: {str(e)}")
    
    def mark_error(self, error_message):
        """Mark search as failed with error message"""
        self.search_success = False
        self.error_message = error_message
        self.results_count = 0
    
    def increment_saved_items(self):
        """Increment count of items saved from this search"""
        self.items_saved_from_search += 1
    
    def to_dict(self):
        """Convert search history to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query': self.query,
            'results_count': self.results_count,
            'search_duration': self.search_duration,
            'filters_applied': self.filters_applied,
            'sort_order': self.sort_order,
            'limit_requested': self.limit_requested,
            'avg_price': float(self.avg_price) if self.avg_price else None,
            'min_price': float(self.min_price) if self.min_price else None,
            'max_price': float(self.max_price) if self.max_price else None,
            'top_conditions': self.top_conditions,
            'top_locations': self.top_locations,
            'items_saved_from_search': self.items_saved_from_search,
            'search_success': self.search_success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def create_search_record(cls, user_id, query, search_start_time=None, **kwargs):
        """Create a new search history record"""
        try:
            search_record = cls(
                user_id=user_id,
                query=query,
                **kwargs
            )
            
            # Calculate search duration if start time provided
            if search_start_time:
                search_record.search_duration = (datetime.utcnow() - search_start_time).total_seconds()
            
            db.session.add(search_record)
            db.session.commit()
            
            logger.info(f"Search record created for user {user_id}: '{query}'")
            return search_record
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create search record: {str(e)}")
            raise
    
    @classmethod
    def get_user_search_stats(cls, user_id, days=30):
        """Get search statistics for a user"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            searches = cls.query.filter(
                cls.user_id == user_id,
                cls.created_at >= cutoff_date
            ).all()
            
            if not searches:
                return {
                    'total_searches': 0,
                    'successful_searches': 0,
                    'avg_results_per_search': 0,
                    'most_common_queries': [],
                    'total_items_saved': 0
                }
            
            total_searches = len(searches)
            successful_searches = sum(1 for s in searches if s.search_success)
            total_results = sum(s.results_count for s in searches)
            total_saved = sum(s.items_saved_from_search for s in searches)
            
            # Most common queries
            query_counts = {}
            for search in searches:
                query_counts[search.query] = query_counts.get(search.query, 0) + 1
            
            most_common = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'success_rate': round(successful_searches / total_searches * 100, 1) if total_searches > 0 else 0,
                'avg_results_per_search': round(total_results / total_searches, 1) if total_searches > 0 else 0,
                'most_common_queries': most_common,
                'total_items_saved': total_saved,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get search stats for user {user_id}: {str(e)}")
            return None
    
    @classmethod
    def get_popular_queries(cls, days=7, limit=20):
        """Get most popular search queries across all users"""
        try:
            from datetime import timedelta
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            popular_queries = db.session.query(
                cls.query,
                func.count(cls.id).label('search_count'),
                func.avg(cls.results_count).label('avg_results')
            ).filter(
                cls.created_at >= cutoff_date,
                cls.search_success == True
            ).group_by(
                cls.query
            ).order_by(
                func.count(cls.id).desc()
            ).limit(limit).all()
            
            return [
                {
                    'query': query,
                    'search_count': search_count,
                    'avg_results': round(float(avg_results), 1) if avg_results else 0
                }
                for query, search_count, avg_results in popular_queries
            ]
            
        except Exception as e:
            logger.error(f"Failed to get popular queries: {str(e)}")
            return []
