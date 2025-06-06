"""
Authentication utilities for Verteil API

This module handles OAuth2 authentication with the Verteil API, including token
management and request authentication.
"""
import base64
import logging
import requests
import threading
import time
import os
from flask import current_app
from typing import Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

class AuthError(Exception):
    """Custom exception for authentication errors"""
    pass

def get_basic_auth_token(config: Dict[str, str]) -> str:
    """
    Generate Basic Auth token for Verteil API
    
    Args:
        config: Configuration dictionary containing VERTEIL_USERNAME and VERTEIL_PASSWORD
        
    Returns:
        str: Base64 encoded Basic Auth token
        
    Raises:
        AuthError: If required configuration is missing
    """
    if not config or 'VERTEIL_USERNAME' not in config or 'VERTEIL_PASSWORD' not in config:
        raise AuthError("Missing VERTEIL_USERNAME or VERTEIL_PASSWORD in config")
        
    credentials = f"{config['VERTEIL_USERNAME']}:{config['VERTEIL_PASSWORD']}"
    return base64.b64encode(credentials.encode()).decode()

def get_oauth_token(config: Dict[str, str]) -> Dict[str, Any]:
    """
    Get access token from Verteil API using Basic Authentication
    
    Args:
        config: Configuration dictionary containing required settings.
               Must include VERTEIL_API_BASE_URL, VERTEIL_TOKEN_ENDPOINT,
               VERTEIL_USERNAME, and VERTEIL_PASSWORD.
        
    Returns:
        Dict containing access token and token metadata
        
    Raises:
        AuthError: If authentication fails or required config is missing
    """
    logger.info("Starting authentication request...")
    
    # Validate required configuration
    required = ['VERTEIL_API_BASE_URL', 'VERTEIL_TOKEN_ENDPOINT', 
               'VERTEIL_USERNAME', 'VERTEIL_PASSWORD',
               'VERTEIL_THIRD_PARTY_ID', 'VERTEIL_OFFICE_ID']
    missing = [key for key in required if not config.get(key)]
    if missing:
        error_msg = f"Missing required configuration: {', '.join(missing)}"
        logger.error(error_msg)
        raise AuthError(error_msg)
    
    token_url = f"{config['VERTEIL_API_BASE_URL'].rstrip('/')}{config['VERTEIL_TOKEN_ENDPOINT']}"
    logger.info(f"Requesting authentication from: {token_url}")
    
    # Prepare the request with Basic Auth and required headers
    auth = (config['VERTEIL_USERNAME'], config['VERTEIL_PASSWORD'])
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Third-Party-ID': config['VERTEIL_THIRD_PARTY_ID'],
        'X-Office-ID': config['VERTEIL_OFFICE_ID']
    }
    
    # The request body for authentication
    payload = {
        'username': config['VERTEIL_USERNAME'],
        'password': config['VERTEIL_PASSWORD']
    }
    
    try:
        logger.info("Generating Basic Auth token...")
        basic_auth_token = get_basic_auth_token(config)
        logger.debug("Basic Auth token generated successfully")
        
        # Prepare headers for the token request
        headers = {
            'Authorization': f'Basic {basic_auth_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Log the request details (without sensitive data)
        logger.debug(f"Making token request to: {token_url}")
        logger.debug(f"Request headers: { {k: v if k != 'Authorization' else 'Basic [REDACTED]' for k, v in headers.items()} }")
        
        # Make the token request
        response = requests.post(
            token_url,
            headers=headers,
            data={'grant_type': 'client_credentials'},
            timeout=30
        )
        
        # Log response status and headers
        logger.info(f"Token request response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        # Check for HTTP errors
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            error_msg = f"HTTP error occurred: {http_err}"
            if response.text:
                error_msg += f" - Response: {response.text}"
            logger.error(error_msg)
            raise AuthError(f"Failed to obtain token: {http_err}. Response: {response.text}")
        
        # Parse the response
        try:
            token_data = response.json()
            logger.debug(f"Token response: { {k: v if k != 'access_token' else '[REDACTED]' for k, v in token_data.items()} }")
        except ValueError as json_err:
            error_msg = f"Failed to parse JSON response: {response.text}"
            logger.error(error_msg)
            raise AuthError(f"Invalid token response: {error_msg}")
        
        # Validate required fields in response
        required_fields = ['access_token', 'token_type', 'expires_in']
        missing_fields = [field for field in required_fields if field not in token_data]
        if missing_fields:
            error_msg = f"Missing required fields in token response: {', '.join(missing_fields)}"
            logger.error(f"{error_msg}. Full response: {token_data}")
            raise AuthError(f"Invalid token response: {error_msg}")
            
        logger.info("Successfully obtained OAuth2 token")
        return {
            'access_token': token_data['access_token'],
            'token_type': token_data['token_type'],
            'expires_in': int(token_data['expires_in']),
            'scope': token_data.get('scope', '')
        }
            
    except (ValueError, KeyError) as e:
        logger.error(f"Invalid token response format: {response.text}")
        raise AuthError("Invalid token response format from authentication server") from e
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to get OAuth token: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - {e.response.text}"
        raise AuthError(error_msg) from e
    except (KeyError, ValueError) as e:
        raise AuthError(f"Invalid token response: {str(e)}") from e

class TokenManager:
    """
    Manages OAuth2 token lifecycle including caching and automatic renewal.
    
    Implements the singleton pattern to ensure only one token manager exists.
    Tokens are cached in memory and reused until they expire (12 hours).
    """
    _instance = None
    _token = None
    _token_expiry = 0
    _token_data = None
    _config = None
    _lock = None  # For thread safety

    def __new__(cls):
        if cls._instance is None:
            with threading.Lock():
                if cls._instance is None:  # Double-checked locking pattern
                    cls._instance = super(TokenManager, cls).__new__(cls)
                    cls._lock = threading.Lock()
                    logger.info("Initialized new TokenManager instance")
        return cls._instance
        
    @classmethod
    def get_instance(cls) -> 'TokenManager':
        """Get the singleton instance of TokenManager."""
        return cls()
        
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set the configuration for the token manager.
        
        Args:
            config: Dictionary containing configuration values
        """
        with self._lock:
            self._config = config

    def _get_effective_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Determine which configuration to use.
        
        Args:
            config: Optional config to use, falls back to instance config or env vars
            
        Returns:
            Dict containing the effective configuration
        """
        effective_config = {}
        
        # Priority 1: Use provided config
        if config is not None:
            effective_config.update(config)
        # Priority 2: Use instance config
        elif self._config is not None:
            effective_config.update(self._config)
            
        # Priority 3: Try to get from current_app if available
        try:
            from flask import current_app
            if current_app:
                app_config = {
                    'VERTEIL_API_BASE_URL': current_app.config.get('VERTEIL_API_BASE_URL'),
                    'VERTEIL_TOKEN_ENDPOINT': current_app.config.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
                    'VERTEIL_USERNAME': current_app.config.get('VERTEIL_USERNAME'),
                    'VERTEIL_PASSWORD': current_app.config.get('VERTEIL_PASSWORD'),
                    'VERTEIL_THIRD_PARTY_ID': current_app.config.get('VERTEIL_THIRD_PARTY_ID'),
                    'VERTEIL_OFFICE_ID': current_app.config.get('VERTEIL_OFFICE_ID'),
                    'OAUTH2_TOKEN_EXPIRY_BUFFER': current_app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER', 300)
                }
                effective_config.update({k: v for k, v in app_config.items() if v is not None})
        except (RuntimeError, ImportError):
            # Not in an app context or Flask not available
            pass
            
        # Priority 4: Fall back to environment variables
        env_config = {
            'VERTEIL_API_BASE_URL': os.environ.get('VERTEIL_API_BASE_URL'),
            'VERTEIL_TOKEN_ENDPOINT': os.environ.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
            'VERTEIL_USERNAME': os.environ.get('VERTEIL_USERNAME'),
            'VERTEIL_PASSWORD': os.environ.get('VERTEIL_PASSWORD'),
            'VERTEIL_THIRD_PARTY_ID': os.environ.get('VERTEIL_THIRD_PARTY_ID'),
            'VERTEIL_OFFICE_ID': os.environ.get('VERTEIL_OFFICE_ID'),
            'OAUTH2_TOKEN_EXPIRY_BUFFER': int(os.environ.get('OAUTH2_TOKEN_EXPIRY_BUFFER', '300'))
        }
        effective_config.update({k: v for k, v in env_config.items() if v is not None})
        
        return effective_config

    def _is_token_valid(self, buffer_seconds: int = 300) -> bool:
        """
        Check if the current token is still valid.
        
        Args:
            buffer_seconds: Number of seconds before expiry to consider token invalid
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self._token or not self._token_expiry:
            return False
            
        current_time = int(time.time())
        return self._token_expiry - current_time > buffer_seconds

    def get_token(self, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a valid OAuth2 token, reusing cached token if still valid.
        
        Args:
            config: Optional configuration dictionary. If not provided, uses the one set via set_config
                   or falls back to current_app.config or environment variables.
            
        Returns:
            str: Valid access token in 'Bearer <token>' format
            
        Raises:
            AuthError: If token cannot be obtained
        """
        import time
        
        # Get effective config first to ensure we have all required settings
        effective_config = self._get_effective_config(config)
        
        # Update instance config if not set
        if not self._config:
            with self._lock:
                if not self._config:  # Double-checked locking
                    self._config = effective_config
                    logger.info("Updated TokenManager config")
        
        # Check if we have a valid token first
        if self._is_token_valid():
            logger.debug("Using cached token")
            return self._token
            
        # Token not valid, acquire lock to refresh it
        with self._lock:
            # Check again in case another thread refreshed the token while we were waiting for the lock
            if self._is_token_valid():
                logger.debug("Using token refreshed by another thread")
                return self._token
                
            try:
                logger.info("Token expired or not found, requesting new token")
                
                # Get new token data
                self._token_data = get_oauth_token(effective_config)
                
                if not self._token_data or 'access_token' not in self._token_data:
                    raise AuthError("Invalid token response: missing access_token")
                
                # Calculate expiry time (with a small buffer)
                expires_in = int(self._token_data.get('expires_in', 43200))  # Default 12 hours if not provided
                self._token_expiry = int(time.time()) + expires_in
                
                # Format the token for Authorization header
                token_type = self._token_data.get('token_type', 'Bearer')
                access_token = self._token_data['access_token']
                
                self._token = f"{token_type} {access_token}"
                
                logger.info(f"New token obtained, expires in {expires_in} seconds (at {time.ctime(self._token_expiry)})")
                logger.debug(f"Token preview: {self._token[:20]}...")
                
            except Exception as e:
                logger.error(f"Failed to obtain OAuth2 token: {str(e)}", exc_info=True)
                raise AuthError(f"Failed to obtain access token: {str(e)}") from e
                
        return self._token
        
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token.
        
        Returns:
            Dict containing token information including expiry time
        """
        current_time = int(time.time())
        expires_in = max(0, self._token_expiry - current_time) if self._token_expiry else 0
        
        return {
            'has_token': bool(self._token),
            'expires_in_seconds': expires_in,
            'expires_at': self._token_expiry,
            'expires_at_human': time.ctime(self._token_expiry) if self._token_expiry else 'N/A'
        }
        
    def clear_token(self) -> None:
        """
        Clear the current token, forcing a refresh on next request.
        Useful for handling 401 Unauthorized responses.
        """
        self._token = None
        self._token_data = None
        self._token_expiry = 0
        logger.debug("Token cache cleared")
