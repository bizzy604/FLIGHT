"""
Tests for the TokenManager class in utils.auth
"""
import os
import sys
import time
import threading
import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the TokenManager
from utils.auth import TokenManager, AuthError


class TestTokenManager(unittest.TestCase):
    """Test cases for TokenManager"""

    def setUp(self):
        """Set up test environment"""
        # Get the singleton instance and clear any existing state
        self.token_manager = TokenManager.get_instance()
        self.token_manager.clear_token()
        self.token_manager.clear_metrics()
        
        # Mock configuration
        self.test_config = {
            'VERTEIL_API_BASE_URL': 'https://api.example.com',
            'VERTEIL_TOKEN_ENDPOINT': '/oauth2/token',
            'VERTEIL_USERNAME': 'test_user',
            'VERTEIL_PASSWORD': 'test_pass',
            'VERTEIL_THIRD_PARTY_ID': 'test_third_party',
            'VERTEIL_OFFICE_ID': 'test_office',
            'OAUTH2_TOKEN_EXPIRY_BUFFER': 300
        }
        self.token_manager.set_config(self.test_config)
        
        # Sample token response
        self.sample_token_response = {
            'access_token': 'test_access_token_123',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read write'
        }

    def tearDown(self):
        """Clean up after each test"""
        self.token_manager.clear_token()
        self.token_manager.clear_metrics()

    @patch('utils.auth.get_oauth_token')
    def test_get_token_first_time(self, mock_get_oauth):
        """Test getting a token for the first time"""
        # Setup mock
        mock_get_oauth.return_value = self.sample_token_response
        
        # Get token
        token = self.token_manager.get_token(self.test_config)
        
        # Verify
        self.assertIsNotNone(token)
        self.assertTrue(token.startswith('Bearer '))
        self.assertEqual(token, 'Bearer test_access_token_123')
        
        # Check metrics
        metrics = self.token_manager.get_metrics()
        self.assertEqual(metrics['token_generations'], 1)
        self.assertEqual(metrics['token_refreshes'], 1)
        self.assertEqual(metrics['total_token_requests'], 1)

    @patch('utils.auth.get_oauth_token')
    def test_token_caching(self, mock_get_oauth):
        """Test that tokens are cached and reused"""
        # Setup mock
        mock_get_oauth.return_value = self.sample_token_response
        
        # First call - should generate a new token
        token1 = self.token_manager.get_token(self.test_config)
        
        # Second call - should use cached token
        mock_get_oauth.reset_mock()
        token2 = self.token_manager.get_token(self.test_config)
        
        # Verify
        self.assertEqual(token1, token2)
        mock_get_oauth.assert_not_called()
        
        # Check metrics
        metrics = self.token_manager.get_metrics()
        self.assertEqual(metrics['token_generations'], 1)
        self.assertEqual(metrics['token_refreshes'], 1)
        self.assertEqual(metrics['total_token_requests'], 2)

    @patch('utils.auth.get_oauth_token')
    def test_token_refresh_after_expiry(self, mock_get_oauth):
        """Test that tokens are refreshed after expiry"""
        # Setup mock for first token
        first_token = dict(self.sample_token_response, access_token='token1')
        second_token = dict(self.sample_token_response, access_token='token2')
        mock_get_oauth.side_effect = [first_token, second_token]
        
        # Get first token
        token1 = self.token_manager.get_token(self.test_config)
        
        # Force token to expire
        self.token_manager._token_expiry = int(time.time()) - 10
        
        # Get token again - should refresh
        token2 = self.token_manager.get_token(self.test_config)
        
        # Verify
        self.assertNotEqual(token1, token2)
        self.assertEqual(token2, 'Bearer token2')
        self.assertEqual(mock_get_oauth.call_count, 2)
        
        # Check metrics
        metrics = self.token_manager.get_metrics()
        self.assertEqual(metrics['token_generations'], 2)
        self.assertEqual(metrics['token_refreshes'], 2)

    @patch('utils.auth.get_oauth_token')
    def test_concurrent_token_requests(self, mock_get_oauth):
        """Test that concurrent requests don't cause multiple token refreshes"""
        # Make token generation slow to simulate network latency
        def slow_token_gen(*args, **kwargs):
            time.sleep(0.5)
            return dict(self.sample_token_response, access_token='concurrent_token')
            
        mock_get_oauth.side_effect = slow_token_gen
        
        results = []
        
        def get_token():
            token = self.token_manager.get_token(self.test_config)
            results.append(token)
        
        # Start multiple threads that will request tokens simultaneously
        threads = [threading.Thread(target=get_token) for _ in range(5)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        
        # All threads should get the same token
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(results[0], 'Bearer concurrent_token')
        
        # Should only generate token once despite multiple requests
        self.assertEqual(mock_get_oauth.call_count, 1)
        
        # Check metrics
        metrics = self.token_manager.get_metrics()
        self.assertEqual(metrics['token_generations'], 1)
        self.assertEqual(metrics['token_refreshes'], 1)
        self.assertEqual(metrics['total_token_requests'], 5)
        self.assertGreaterEqual(metrics['concurrent_refresh_attempts'], 4)  # At least 4 threads should have waited

    @patch('utils.auth.get_oauth_token')
    def test_clear_token(self, mock_get_oauth):
        """Test that clear_token forces a refresh on next request"""
        # Setup mock
        mock_get_oauth.return_value = self.sample_token_response
        
        # Get initial token
        token1 = self.token_manager.get_token(self.test_config)
        
        # Clear token
        self.token_manager.clear_token()
        
        # Get token again - should generate new token
        mock_get_oauth.return_value = dict(self.sample_token_response, access_token='new_token')
        token2 = self.token_manager.get_token(self.test_config)
        
        # Verify
        self.assertNotEqual(token1, token2)
        self.assertEqual(token2, 'Bearer new_token')
        self.assertEqual(mock_get_oauth.call_count, 2)

    @patch('utils.auth.get_oauth_token')
    def test_metrics_clear(self, mock_get_oauth):
        """Test that metrics can be cleared"""
        # Setup mock
        mock_get_oauth.return_value = self.sample_token_response
        
        # Make some requests
        self.token_manager.get_token(self.test_config)
        self.token_manager.get_token(self.test_config)
        
        # Clear metrics
        self.token_manager.clear_metrics()
        
        # Verify metrics were reset
        metrics = self.token_manager.get_metrics()
        self.assertEqual(metrics['total_token_requests'], 0)
        self.assertEqual(metrics['token_generations'], 0)
        self.assertEqual(metrics['token_refreshes'], 0)
        
        # Timestamps should be preserved
        self.assertGreater(metrics['last_token_generation_time'], 0)
        self.assertGreater(metrics['last_token_refresh_time'], 0)

    @patch('utils.auth.get_oauth_token')
    def test_token_validation(self, mock_get_oauth):
        """Test token validation logic with detailed debugging"""
        # Enable debug logging for this test
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('token_test.log', mode='w')
            ]
        )
        logger = logging.getLogger(__name__)
        
        # Print test environment info
        logger.info("=== Starting Token Validation Test ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Current time: {time.time()} ({time.ctime()})")
        
        # Setup mock with short expiry
        test_token = "test_token_123"
        expires_in = 10  # 10 seconds
        mock_response = dict(
            self.sample_token_response,
            access_token=test_token,
            expires_in=expires_in
        )
        mock_get_oauth.return_value = mock_response
        
        # Print initial state
        logger.info("\n=== Initial TokenManager State ===")
        logger.info(f"_token: {getattr(self.token_manager, '_token', 'Not set')}")
        logger.info(f"_token_expiry: {getattr(self.token_manager, '_token_expiry', 'Not set')}")
        logger.info(f"_token_data: {getattr(self.token_manager, '_token_data', 'Not set')}")
        logger.info(f"_config: {getattr(self.token_manager, '_config', 'Not set')}")
        logger.info(f"_is_refreshing: {getattr(self.token_manager, '_is_refreshing', 'Not set')}")
        logger.info("=== Mock Response ===")
        logger.info(f"{mock_response}")
        logger.info("======================")
        
        # 1. Test getting initial token
        logger.info("\n=== Step 1: Getting initial token ===")
        start_time = time.time()
        token = self.token_manager.get_token(self.test_config)
        elapsed = time.time() - start_time
        
        logger.info(f"Token obtained in {elapsed:.4f} seconds")
        logger.info(f"Token: {token}")
        
        # 2. Verify token is valid right after getting it
        logger.info("\n=== Step 2: Verifying token is valid ===")
        logger.info("Calling _is_token_valid()...")
        logger.info("TokenManager state before validation:")
        logger.info(f"_token: {getattr(self.token_manager, '_token', 'Not set')}")
        logger.info(f"_token_expiry: {getattr(self.token_manager, '_token_expiry', 'Not set')} ({time.ctime(getattr(self.token_manager, '_token_expiry', 0)) if getattr(self.token_manager, '_token_expiry', 0) else 'N/A'})")
        logger.info(f"_token_data: {getattr(self.token_manager, '_token_data', 'Not set')}")
        
        # Use the same small buffer for validation
        is_valid = self.token_manager._is_token_valid(buffer_seconds=0.1)
        
        # Print validation result
        current_time = time.time()
        logger.info(f"Validation result: {is_valid}")
        logger.info(f"Current time: {current_time} ({time.ctime(current_time)})")
        if hasattr(self.token_manager, '_token_expiry'):
            expiry = self.token_manager._token_expiry
            logger.info(f"Token expiry: {expiry} ({time.ctime(expiry) if expiry else 'N/A'})")
            if expiry:
                logger.info(f"Time until expiry: {expiry - current_time:.2f} seconds")
        
        # This is the assertion that's failing
        self.assertTrue(is_valid, f"Token should be valid after getting it. Current time: {current_time}, Expiry: {getattr(self.token_manager, '_token_expiry', 'Not set')}")
        
        # 3. Force token to expire and verify it's invalid
        logger.info("\n=== Step 3: Forcing token to expire ===")
        self.token_manager._token_expiry = int(time.time()) - 1
        logger.info(f"Set token expiry to: {self.token_manager._token_expiry} ({time.ctime(self.token_manager._token_expiry)})")
        
        # 4. Verify token is now invalid
        logger.info("\n=== Step 4: Verifying token is now invalid ===")
        is_valid = self.token_manager._is_token_valid()
        logger.info(f"Validation result after expiry: {is_valid}")
        logger.info(f"Current time: {time.time()} ({time.ctime()})")
        logger.info(f"Token expiry: {self.token_manager._token_expiry} ({time.ctime(self.token_manager._token_expiry)})")
        
        self.assertFalse(is_valid, "Token should be invalid after expiry")
        
        logger.info("\n=== Test completed successfully ===")
        return
        """Test token validation logic"""
        # Enable debug logging for this test
        import logging
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        # Print test environment info
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Setup mock with short expiry
        test_token = "test_token_123"
        mock_response = dict(
            self.sample_token_response,
            access_token=test_token,
            expires_in=10  # 10 seconds
        )
        mock_get_oauth.return_value = mock_response
        
        # Print initial state
        logger.info("=== Initial TokenManager State ===")
        logger.info(f"_token: {getattr(self.token_manager, '_token', 'Not set')}")
        logger.info(f"_token_expiry: {getattr(self.token_manager, '_token_expiry', 'Not set')}")
        logger.info(f"_token_data: {getattr(self.token_manager, '_token_data', 'Not set')}")
        logger.info(f"_config: {getattr(self.token_manager, '_config', 'Not set')}")
        logger.info("=== Mock Response ===")
        logger.info(f"{mock_response}")
        logger.info("=====================")
        
        logger.info("1. Getting initial token...")
        # Get token
        token = self.token_manager.get_token(self.test_config)
        logger.debug(f"Got token: {token}")
        logger.debug(f"Token manager state: token={self.token_manager._token}, expiry={self.token_manager._token_expiry}")
        
        self.assertIsNotNone(token, "Token should not be None")
        self.assertEqual(token, f"Bearer {test_token}", "Token format is incorrect")
        
        logger.info("2. Verifying token is valid...")
        # Token should be valid
        logger.debug("Calling _is_token_valid()...")
        is_valid = self.token_manager._is_token_valid()
        logger.debug(f"Token valid: {is_valid}, expiry: {self.token_manager._token_expiry} (in {self.token_manager._token_expiry - int(time.time())} seconds)")
        
        # Debug: Print token manager state
        logger.debug(f"Token manager state - token: {self.token_manager._token}, expiry: {self.token_manager._token_expiry}, data: {self.token_manager._token_data}")
        
        if not is_valid:
            logger.error("Token is not valid! Possible reasons:")
            if not self.token_manager._token:
                logger.error("- No token is set")
            if not self.token_manager._token_expiry:
                logger.error("- No token expiry is set")
            elif self.token_manager._token_expiry <= int(time.time()):
                logger.error(f"- Token expired {int(time.time()) - self.token_manager._token_expiry} seconds ago")
            else:
                logger.error("- Unknown reason")
        
        self.assertTrue(is_valid, "Token should be valid after getting it")
        
        logger.info("3. Forcing token to expire...")
        # Force token to expire
        self.token_manager._token_expiry = int(time.time()) - 1
        logger.debug(f"Set expiry to past: {self.token_manager._token_expiry} (current time: {int(time.time())})")
        
        logger.info("4. Verifying token is now invalid...")
        # Token should be invalid
        is_valid = self.token_manager._is_token_valid()
        logger.debug(f"Token valid after expiry: {is_valid}, expiry: {self.token_manager._token_expiry} (in {self.token_manager._token_expiry - int(time.time())} seconds)")
        self.assertFalse(is_valid, f"Token should be invalid after expiry. Current time: {int(time.time())}, Expiry: {self.token_manager._token_expiry}")


if __name__ == '__main__':
    unittest.main()
