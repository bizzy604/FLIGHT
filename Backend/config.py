"""
Configuration settings for the Flight Booking Portal.

This module contains configuration classes for different environments.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration with default settings."""
    # Quart settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    DEBUG = False
    TESTING = False
    
    # API settings
    API_PREFIX = '/api'
    
    # CORS settings
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://flight-pearl.vercel.app"
    ]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    CORS_EXPOSE_HEADERS = ["Content-Type"]
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Verteil NDC API settings
    VERTEIL_API_BASE_URL = os.environ.get('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com')
    VERTEIL_USERNAME = os.environ.get('VERTEIL_USERNAME')
    VERTEIL_PASSWORD = os.environ.get('VERTEIL_PASSWORD')
    VERTEIL_CLIENT_ID = os.environ.get('VERTEIL_CLIENT_ID')
    VERTEIL_CLIENT_SECRET = os.environ.get('VERTEIL_CLIENT_SECRET')
    VERTEIL_OFFICE_ID = os.environ.get('VERTEIL_OFFICE_ID', 'OFF3746')
    VERTEIL_THIRD_PARTY_ID = os.environ.get('VERTEIL_THIRD_PARTY_ID', 'KQ')

    # Redis configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Cache settings
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate limiting
    RATELIMIT_DEFAULT = '200 per day;50 per hour;10 per minute'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Enable or disable API key authentication
    API_KEY_AUTH_ENABLED = os.environ.get('API_KEY_AUTH_ENABLED', 'False').lower() == 'true'
    
    # API Keys (comma-separated list)
    API_KEYS = os.environ.get('API_KEYS', '').split(',')
    
    # Enable or disable request deduplication
    REQUEST_DEDUPLICATION_ENABLED = True
    
    # Request deduplication settings
    REQUEST_DEDUPLICATION_TTL = 5  # seconds
    
    # Enable or disable response compression
    COMPRESS_RESPONSES = True
    
    # OAuth2 Settings
    OAUTH2_TOKEN_EXPIRY_BUFFER = 60  # seconds before actual expiry to consider token expired
    
    # General request timeout (can be different from specific API timeout)
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))
    
    @staticmethod
    def init_app(app):
        pass
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


# Dictionary to map config names to classes
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Retrieve configuration based on environment.
    
    Args:
        config_name: Name of the configuration to use (development, testing, production)
        
    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.environ.get('QUART_ENV', 'development')
    
    return config_dict.get(config_name, config_dict['default'])
