"""
Tests for the authentication module.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.auth import get_oauth_token, TokenManager, AuthError

def create_test_app():
    """Create a test Flask app with configuration."""
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        VERTEIL_API_BASE_URL='https://api.stage.verteil.com',
        VERTEIL_TOKEN_ENDPOINT='/oauth2/token',
        VERTEIL_USERNAME='test_user',
        VERTEIL_PASSWORD='test_password',
        REQUEST_TIMEOUT=10,
        OAUTH2_TOKEN_EXPIRY_BUFFER=60
    )
    return app

class TestAuth(unittest.TestCase):
    """Test cases for authentication utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_test_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Sample successful token response
        self.valid_token_response = {
            'access_token': 'test_access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'api'
        }

    def tearDown(self):
        """Clean up after tests."""
        self.ctx.pop()

    @patch('requests.post')
    def test_get_oauth_token_success(self, mock_post):
        """Test successful OAuth2 token retrieval."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.valid_token_response
        mock_post.return_value = mock_response

        # Call the function
        with self.app.app_context():
            token_data = get_oauth_token()

        # Assertions
        self.assertEqual(token_data['access_token'], 'test_access_token')
        self.assertEqual(token_data['token_type'], 'Bearer')
        self.assertEqual(token_data['expires_in'], 3600)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_get_oauth_token_invalid_response(self, mock_post):
        """Test handling of invalid API response."""
        # Mock an invalid response (missing required fields)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': 'invalid_request'}
        mock_post.return_value = mock_response

        # Call the function and expect an exception
        with self.app.app_context():
            with self.assertRaises(AuthError):
                get_oauth_token()

    @patch('requests.post')
    def test_token_manager_singleton(self, mock_post):
        """Test that TokenManager is a singleton."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.valid_token_response
        mock_post.return_value = mock_response

        # Get two instances of TokenManager
        with self.app.app_context():
            manager1 = TokenManager()
            manager2 = TokenManager()
            
            # Both should be the same instance
            self.assertIs(manager1, manager2)
            
            # Get tokens
            token1 = manager1.get_token()
            token2 = manager2.get_token()
            
            # Should be the same token
            self.assertEqual(token1, token2)
            
            # Should only make one API call
            mock_post.assert_called_once()

    @patch('requests.post')
    def test_token_refresh(self, mock_post):
        """Test that tokens are refreshed when expired."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.valid_token_response
        mock_post.return_value = mock_response

        with self.app.app_context():
            manager = TokenManager()
            
            # First call - should get a new token
            token1 = manager.get_token()
            
            # Second call - should use cached token
            token2 = manager.get_token()
            
            # Clear the token
            manager.clear_token()
            
            # Third call - should get a new token
            token3 = manager.get_token()
            
            # Should have made two API calls (first and third)
            self.assertEqual(mock_post.call_count, 2)
            self.assertEqual(token1, token2)
            self.assertEqual(token1, token3)  # Same token value, but from different requests

if __name__ == '__main__':
    unittest.main()
