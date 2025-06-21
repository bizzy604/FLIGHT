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
from quart import current_app
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
    username = config.get('VERTEIL_USERNAME')
    password = config.get('VERTEIL_PASSWORD')
    
    if not username or not password:
        raise AuthError("Missing VERTEIL_USERNAME or VERTEIL_PASSWORD in config")
    
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded_credentials}"

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
    required_config = [
        'VERTEIL_API_BASE_URL',
        'VERTEIL_TOKEN_ENDPOINT',
        'VERTEIL_USERNAME',
        'VERTEIL_PASSWORD'
    ]
    
    missing = [key for key in required_config if not config.get(key)]
    if missing:
        raise AuthError(f"Missing required configuration: {', '.join(missing)}")
    
    url = f"{config['VERTEIL_API_BASE_URL'].rstrip('/')}/{config['VERTEIL_TOKEN_ENDPOINT'].lstrip('/')}"
    headers = {
        'Authorization': get_basic_auth_token(config),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to get OAuth token: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - {e.response.text}"
        raise AuthError(error_msg) from e

class TokenManager:
    """
    Manages OAuth2 token lifecycle including caching and automatic renewal.
    
    Implements the singleton pattern to ensure only one token manager exists.
    Tokens are cached in memory and reused until they expire.
    """
    _instance = None
    _token = None
    _token_data = None
    _token_expiry = 0
    _config = None
    _lock = threading.RLock()
    _is_refreshing = False
    _last_refresh_attempt = 0
    REFRESH_COOLDOWN = 5  # seconds to wait before retrying after a failed refresh
    
    # Metrics
    _metrics = {
        'token_generations': 0,
        'token_refreshes': 0,
        'concurrent_refresh_attempts': 0,
        'last_token_generation_time': 0,
        'last_token_refresh_time': 0,
        'concurrent_refresh_peaks': 0,
        'total_token_requests': 0
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TokenManager, cls).__new__(cls)
        return cls._instance
    
    def _increment_metric(self, metric_name: str, amount: int = 1) -> None:
        """Thread-safe metric increment"""
        with self._lock:
            if metric_name in self._metrics:
                self._metrics[metric_name] += amount
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get a copy of current metrics"""
        with self._lock:
            return self._metrics.copy()
    
    def clear_metrics(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._metrics = {
                'token_generations': 0,
                'token_refreshes': 0,
                'concurrent_refresh_attempts': 0,
                'last_token_generation_time': 0,
                'last_token_refresh_time': 0,
                'concurrent_refresh_peaks': 0,
                'total_token_requests': 0
            }
    
    @classmethod
    def get_instance(cls) -> 'TokenManager':
        """Get the singleton instance of TokenManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
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
        else:
            try:
                if current_app:
                    app_config = {
                        'VERTEIL_API_BASE_URL': current_app.config.get('VERTEIL_API_BASE_URL'),
                        'VERTEIL_TOKEN_ENDPOINT': current_app.config.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
                        'VERTEIL_USERNAME': current_app.config.get('VERTEIL_USERNAME'),
                        'VERTEIL_PASSWORD': current_app.config.get('VERTEIL_PASSWORD'),
                        'VERTEIL_THIRD_PARTY_ID': current_app.config.get('VERTEIL_THIRD_PARTY_ID'),
                        'VERTEIL_OFFICE_ID': current_app.config.get('VERTEIL_OFFICE_ID'),
                        'OAUTH2_TOKEN_EXPIRY_BUFFER': int(current_app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER', 300))
                    }
                    effective_config.update({k: v for k, v in app_config.items() if v is not None})
            except RuntimeError:
                # current_app not available
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
            buffer_seconds: Number of seconds before expiry to consider token invalid.
                          If the token will expire within this many seconds, it's considered invalid.
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self._token or not self._token_data or not self._token_expiry:
            return False
            
        current_time = int(time.time())
        return current_time < (self._token_expiry - buffer_seconds)
    
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
        self._increment_metric('total_token_requests')
        
        # If we have a valid token, return it
        if self._is_token_valid():
            return f"Bearer {self._token}"
        
        # If we're already refreshing, wait a bit and check again
        if self._is_refreshing:
            self._increment_metric('concurrent_refresh_attempts')
            time_since_refresh = time.time() - self._last_refresh_attempt
            
            # If it's been a while since we started refreshing, something might be wrong
            if time_since_refresh > 30:  # 30 second timeout
                self._is_refreshing = False
                logger.warning("Token refresh seems to be stuck. Resetting refresh lock.")
            else:
                # Wait a bit and check again
                time.sleep(0.5)
                if self._is_token_valid():
                    return f"Bearer {self._token}"
                
                # If we're still here, we need to get a new token
                logger.warning("Concurrent token refresh detected. Waiting for refresh to complete.")
                
                # Wait for the refresh to complete
                start_time = time.time()
                while time.time() - start_time < 5:  # 5 second timeout
                    if not self._is_refreshing and self._is_token_valid():
                        return f"Bearer {self._token}"
                    time.sleep(0.1)
                
                logger.error("Timed out waiting for token refresh to complete.")
        
        # If we get here, we need to refresh the token
        with self._lock:
            # Double-check in case another thread already refreshed
            if self._is_token_valid():
                return f"Bearer {self._token}"
                
            # Check cooldown
            current_time = time.time()
            if current_time - self._last_refresh_attempt < self.REFRESH_COOLDOWN:
                raise AuthError("Token refresh on cooldown. Please try again later.")
            
            try:
                self._is_refreshing = True
                self._last_refresh_attempt = current_time
                
                # Get effective config
                effective_config = self._get_effective_config(config)
                
                logger.info("Fetching new OAuth2 token...")
                token_data = get_oauth_token(effective_config)
                
                if not token_data or 'access_token' not in token_data:
                    raise AuthError("Invalid token response: missing access_token")
                
                # Calculate expiry time with a small buffer
                expires_in = int(token_data.get('expires_in', 3600))  # Default to 1 hour
                self._token_expiry = int(time.time()) + expires_in
                self._token = token_data['access_token']
                self._token_data = token_data
                
                self._increment_metric('token_generations')
                self._metrics['last_token_generation_time'] = int(time.time())
                
                logger.info(f"Successfully obtained new token. Expires in {expires_in} seconds.")
                
                return f"Bearer {self._token}"
                
            except Exception as e:
                self.clear_token()
                if isinstance(e, AuthError):
                    raise
                raise AuthError(f"Failed to get token: {str(e)}") from e
                
            finally:
                self._is_refreshing = False
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token.
        
        Returns:
            Dict containing token information including expiry time
        """
        if not self._token or not self._token_data:
            return {
                'has_token': False,
                'is_valid': False,
                'expires_in': 0,
                'expiry_time': 0,
                'token_type': None,
                'metrics': self.get_metrics()
            }
            
        current_time = int(time.time())
        expires_in = max(0, self._token_expiry - current_time) if self._token_expiry else 0
        
        return {
            'has_token': True,
            'is_valid': self._is_token_valid(),
            'expires_in': expires_in,
            'expiry_time': self._token_expiry,
            'token_type': self._token_data.get('token_type'),
            'metrics': self.get_metrics()
        }
    
    def clear_token(self) -> None:
        """
        Clear the current token, forcing a refresh on next request.
        Useful for handling 401 Unauthorized responses.
        """
        with self._lock:
            self._token = None
            self._token_data = None
            self._token_expiry = 0
            self._increment_metric('token_refreshes')
            self._metrics['last_token_refresh_time'] = int(time.time())
