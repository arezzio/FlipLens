import os
import logging
import re
from typing import Optional, List

logger = logging.getLogger(__name__)

class Config:
    """Base configuration class with enhanced security and validation"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Server Configuration
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    # API Configuration
    EBAY_BASE_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
    EBAY_SANDBOX_URL = "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///fliplens.db')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'fliplens.log')
    
    # Security Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '3600'))  # 1 hour
    
    @classmethod
    def get_ebay_api_key(cls) -> Optional[str]:
        """Get eBay API key dynamically"""
        return os.environ.get('EBAY_API_KEY')
    
    @classmethod
    def get_ebay_app_id(cls) -> Optional[str]:
        """Get eBay App ID dynamically"""
        return os.environ.get('EBAY_APP_ID')
    
    @classmethod
    def get_ebay_cert_id(cls) -> Optional[str]:
        """Get eBay Cert ID dynamically"""
        return os.environ.get('EBAY_CERT_ID')
    
    @classmethod
    def get_ebay_dev_id(cls) -> Optional[str]:
        """Get eBay Dev ID dynamically"""
        return os.environ.get('EBAY_DEV_ID')
    
    @classmethod
    def get_ebay_use_sandbox(cls) -> bool:
        """Get eBay sandbox setting dynamically"""
        return os.environ.get('EBAY_USE_SANDBOX', 'true').lower() == 'true'
    
    @classmethod
    def validate_api_key_format(cls, api_key: str, key_type: str = 'generic') -> bool:
        """Validate API key format based on type"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic length validation
        if len(api_key) < 10:
            return False
        
        # eBay API key format validation (App ID format)
        if key_type == 'ebay':
            # eBay App ID format: typically alphanumeric with hyphens
            ebay_pattern = r'^[A-Za-z0-9\-]+$'
            return bool(re.match(ebay_pattern, api_key))
        
        # Generic API key validation
        # Should not contain spaces, should be alphanumeric with common symbols
        generic_pattern = r'^[A-Za-z0-9\-_\.]+$'
        return bool(re.match(generic_pattern, api_key))
    
    @classmethod
    def get_api_key(cls, key_name: str, required: bool = True) -> Optional[str]:
        """Safely get API key with validation and secure logging"""
        api_key = os.environ.get(key_name)
        
        if not api_key:
            if required:
                logger = logging.getLogger(__name__)
                logger.error(f"Required API key {key_name} is not set")
                raise ValueError(f"Required API key {key_name} is not configured")
            return None
        
        # Validate format
        if not cls.validate_api_key_format(api_key, 'ebay' if 'EBAY' in key_name else 'generic'):
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid format for API key {key_name}")
            raise ValueError(f"Invalid format for API key {key_name}")
        
        # Log successful configuration (without exposing the key)
        logger = logging.getLogger(__name__)
        logger.info(f"API key {key_name} configured successfully (length: {len(api_key)})")
        
        return api_key
    
    @classmethod
    def validate_required_keys(cls) -> List[str]:
        """Validate that required environment variables are set with enhanced error reporting"""
        missing_keys = []
        
        # Required for eBay API functionality
        try:
            ebay_key = cls.get_api_key('EBAY_API_KEY', required=True)
            if not ebay_key:
                missing_keys.append('EBAY_API_KEY')
        except ValueError:
            missing_keys.append('EBAY_API_KEY (invalid format)')
        
        # Validate SECRET_KEY in production
        if cls.is_production():
            try:
                secret_key = cls.get_api_key('SECRET_KEY', required=True)
                if not secret_key or secret_key == 'dev-secret-key':
                    missing_keys.append('SECRET_KEY (must be set in production)')
            except ValueError:
                missing_keys.append('SECRET_KEY (invalid format)')
        
        return missing_keys
    
    @classmethod
    def get_ebay_url(cls) -> str:
        """Get the appropriate eBay API URL based on sandbox setting"""
        return cls.EBAY_SANDBOX_URL if cls.get_ebay_use_sandbox() else cls.EBAY_BASE_URL
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.FLASK_ENV.lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.FLASK_ENV.lower() == 'development'
    
    @classmethod
    def is_testing(cls) -> bool:
        """Check if running in testing environment"""
        return cls.FLASK_ENV.lower() == 'testing'
    
    @classmethod
    def get_secure_config_summary(cls) -> dict:
        """Get a secure configuration summary for logging (no sensitive data)"""
        return {
            'environment': cls.FLASK_ENV,
            'ebay_sandbox_enabled': cls.get_ebay_use_sandbox(),
            'cors_origins_count': len(cls.CORS_ORIGINS),
            'rate_limit_enabled': cls.RATE_LIMIT_ENABLED,
            'rate_limit_requests': cls.RATE_LIMIT_REQUESTS,
            'rate_limit_window': cls.RATE_LIMIT_WINDOW,
            'api_keys_configured': {
                'EBAY_API_KEY': bool(cls.get_ebay_api_key()),
                'EBAY_APP_ID': bool(cls.get_ebay_app_id()),
                'EBAY_CERT_ID': bool(cls.get_ebay_cert_id()),
                'EBAY_DEV_ID': bool(cls.get_ebay_dev_id()),
                'SECRET_KEY': bool(cls.SECRET_KEY and cls.SECRET_KEY != 'dev-secret-key')
            }
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        """Initialize development-specific settings"""
        # Enable detailed logging in development
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

class ProductionConfig(Config):
    """Production configuration with enhanced security"""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings"""
        # Ensure secure settings in production
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key':
            raise ValueError("SECRET_KEY must be set in production environment")
        
        # Validate required API keys
        missing_keys = cls.validate_required_keys()
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
        
        # Configure production logging
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=cls.LOG_FILE
        )

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use test database
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Disable logging during tests
    LOG_LEVEL = 'ERROR'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 