from flask import Blueprint

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import route modules
from . import search, health, saved_items, auth, market_trends, portfolio, alerts, profile, settings