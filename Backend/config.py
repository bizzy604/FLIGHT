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
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    DEBUG = False
    TESTING = False
    
    # API settings
    API_PREFIX = '/api'
    
    # Verteil NDC API settings
    VERTEIL_API_BASE_URL = os.environ.get('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com')
    VERTEIL_USERNAME = os.environ.get('VERTEIL_USERNAME')
    VERTEIL_PASSWORD = os.environ.get('VERTEIL_PASSWORD')
    VERTEIL_THIRD_PARTY_ID = os.environ.get('VERTEIL_THIRD_PARTY_ID')
    VERTEIL_OFFICE_ID = os.environ.get('VERTEIL_OFFICE_ID')
    VERTEIL_TOKEN_ENDPOINT_PATH = os.environ.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token') # Path for token endpoint
    
    # API Endpoints (Note: VERTEIL_TOKEN_ENDPOINT_PATH is now the source for the token path)
    # VERTEIL_TOKEN_ENDPOINT = '/entrygate/rest/request:authenticate' # Old, replaced by VERTEIL_TOKEN_ENDPOINT_PATH
    VERTEIL_AIR_SHOPPING_ENDPOINT = '/entrygate/rest/request:airShopping' # Example, specific endpoints used in services

    # Verteil API Interaction Settings (matching FlightService defaults)
    VERTEIL_API_TIMEOUT = int(os.environ.get('VERTEIL_API_TIMEOUT', 30))
    VERTEIL_MAX_RETRIES = int(os.environ.get('VERTEIL_MAX_RETRIES', 3))
    VERTEIL_RETRY_DELAY = int(os.environ.get('VERTEIL_RETRY_DELAY', 1))
    
    # General request timeout (can be different from specific API timeout)
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))
    
    # OAuth2 Settings
    OAUTH2_TOKEN_EXPIRY_BUFFER = 60  # seconds before actual expiry to consider token expired
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
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
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_dict.get(config_name, config_dict['default'])
