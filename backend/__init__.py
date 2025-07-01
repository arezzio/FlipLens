from flask import Flask
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
from config.settings import config

def create_app(test_config=None):
    """Application factory pattern for Flask app with enhanced security"""
    
    # Load environment variables FIRST, before any configuration
    load_dotenv()
    
    # Create Flask app instance
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure the app
    if test_config is None:
        # Get configuration based on environment
        config_name = os.environ.get('FLASK_ENV', 'development')
        app.config.from_object(config[config_name])
        
        # Initialize environment-specific settings
        config[config_name].init_app(app)
        
        # Log configuration status
        logger = logging.getLogger(__name__)
        logger.info(f"Flask app configured for {config_name} environment")
        
        # Validate required environment variables in production
        if config_name == 'production':
            missing_keys = app.config.get('Config').validate_required_keys()
            if missing_keys:
                logger.error(f"Missing required environment variables: {missing_keys}")
                raise ValueError(f"Missing required environment variables: {missing_keys}")
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Configure CORS with proper origins
    cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:3000'])
    CORS(app, origins=cors_origins)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Register security middleware
    try:
        from utils.security import register_security_middleware
        register_security_middleware(app)
    except ImportError as e:
        logger.warning(f"Security middleware not available: {e}")
    
    # Register blueprints
    try:
        from routes import api_bp
        app.register_blueprint(api_bp)
    except ImportError:
        # If routes module is not available, create a simple blueprint
        from flask import Blueprint
        api_bp = Blueprint('api', __name__, url_prefix='/api')
        
        @api_bp.route('/health')
        def health_check():
            return {
                "status": "healthy",
                "service": "FlipLens Backend",
                "version": "1.0.0",
                "environment": app.config.get('FLASK_ENV', 'development'),
                "security": "enabled"
            }
        
        app.register_blueprint(api_bp)
    
    # Register error handlers
    try:
        from utils.error_handlers import register_error_handlers
        register_error_handlers(app)
    except ImportError:
        # Simple error handlers if utils module is not available
        @app.errorhandler(404)
        def not_found(error):
            return {"error": "Not Found"}, 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return {"error": "Internal Server Error"}, 500
    
    # Simple route for testing
    @app.route('/')
    def home():
        return {
            "message": "FlipLens API is running",
            "version": "1.0.0",
            "environment": app.config.get('FLASK_ENV', 'development'),
            "ebay_sandbox": app.config.get('EBAY_USE_SANDBOX', True),
            "security": "enabled"
        }
    
    return app 