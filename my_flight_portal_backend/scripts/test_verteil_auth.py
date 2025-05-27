"""
Test script to verify Verteil API authentication.

This script tests the OAuth2 authentication flow with the Verteil API
using the provided credentials.
"""
import os
import sys
import json
import logging
from flask import Flask
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import after setting up the path
from utils.auth import get_oauth_token, TokenManager

def create_test_app():
    """Create a test Flask app with configuration."""
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Configure the app
    app.config.update(
        TESTING=True,
        VERTEIL_API_BASE_URL=os.getenv('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com'),
        VERTEIL_TOKEN_ENDPOINT=os.getenv('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
        VERTEIL_USERNAME=os.getenv('VERTEIL_USERNAME'),
        VERTEIL_PASSWORD=os.getenv('VERTEIL_PASSWORD'),
        REQUEST_TIMEOUT=int(os.getenv('REQUEST_TIMEOUT', '30')),
        OAUTH2_TOKEN_EXPIRY_BUFFER=int(os.getenv('OAUTH2_TOKEN_EXPIRY_BUFFER', '60'))
    )
    
    return app

def test_oauth2_authentication(app):
    """Test OAuth2 authentication with Verteil API."""
    with app.app_context():
        try:
            logger.info("Testing OAuth2 authentication...")
            
            # Get token using the auth module
            token_data = get_oauth_token()
            
            logger.info("Successfully obtained OAuth2 token:")
            logger.info(f"Token Type: {token_data['token_type']}")
            logger.info(f"Expires In: {token_data['expires_in']} seconds")
            logger.info(f"Scope: {token_data.get('scope', 'N/A')}")
            
            return True
        except Exception as e:
            logger.error(f"Authentication test failed: {str(e)}", exc_info=True)
            return False

def test_token_manager(app):
    """Test the TokenManager class."""
    with app.app_context():
        try:
            logger.info("Testing TokenManager...")
            
            # Get token using TokenManager
            token_manager = TokenManager()
            token = token_manager.get_token()
            
            logger.info("Successfully obtained token using TokenManager")
            logger.info(f"Token: {token[:20]}...")  # Log first 20 chars of token
            
            # Test token caching
            logger.info("Testing token caching...")
            cached_token = token_manager.get_token()
            assert token == cached_token, "Token should be cached"
            
            # Test token refresh
            logger.info("Testing token refresh...")
            token_manager.clear_token()
            new_token = token_manager.get_token()
            
            logger.info("Token refresh test completed")
            return True
        except Exception as e:
            logger.error(f"TokenManager test failed: {str(e)}", exc_info=True)
            return False

def main():
    """Main function to run the tests."""
    # Create test app
    app = create_test_app()
    
    # Check required environment variables
    required_vars = [
        'VERTEIL_API_BASE_URL',
        'VERTEIL_USERNAME',
        'VERTEIL_PASSWORD'
    ]
    
    missing_vars = [var for var in required_vars if not app.config.get(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please create a .env file with the required variables (see .env.example)")
        return 1
    
    logger.info("Starting Verteil API authentication tests...")
    
    # Run tests
    success = True
    
    logger.info("\n=== Testing OAuth2 Authentication ===")
    if not test_oauth2_authentication(app):
        success = False
    
    logger.info("\n=== Testing TokenManager ===")
    if not test_token_manager(app):
        success = False
    
    if success:
        logger.info("\n✅ All tests passed successfully!")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
