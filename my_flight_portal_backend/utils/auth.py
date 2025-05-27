"""
Authentication utilities for Verteil API

This module handles OAuth2 authentication with the Verteil API, including token
management and request authentication.
"""
import base64
import logging
import requests
from flask import current_app
from typing import Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

class AuthError(Exception):
    """Custom exception for authentication errors"""
    pass

def get_basic_auth_token() -> str:
    """
    Generate Basic Auth token for Verteil API
    
    Returns:
        str: Base64 encoded Basic Auth token
    """
    credentials = f"{current_app.config['VERTEIL_USERNAME']}:{current_app.config['VERTEIL_PASSWORD']}"
    return base64.b64encode(credentials.encode()).decode()

def get_oauth_token() -> Dict[str, Any]:
    """
    Get OAuth2 access token from Verteil API
    
    Returns:
        Dict containing access token and token metadata
        
    Raises:
        AuthError: If authentication fails
    """
    token_url = f"{current_app.config['VERTEIL_API_BASE_URL']}{current_app.config['VERTEIL_TOKEN_ENDPOINT']}"
    
    try:
        logger.debug(f"Requesting OAuth2 token from {token_url}")
        
        # Request token using client credentials flow with Basic Auth
        response = requests.post(
            token_url,
            auth=(
                current_app.config['VERTEIL_USERNAME'],
                current_app.config['VERTEIL_PASSWORD']
            ),
            data={
                'grant_type': 'client_credentials',
                'scope': 'api'
            },
            timeout=current_app.config['REQUEST_TIMEOUT']
        )
        
        response.raise_for_status()
        
        try:
            token_data = response.json()
            required_fields = ['access_token', 'token_type', 'expires_in']
            if not all(field in token_data for field in required_fields):
                raise ValueError("Missing required token fields in response")
                
            logger.debug("Successfully obtained OAuth2 token")
            
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
    """
    _instance = None
    _token = None
    _token_expiry = 0
    _token_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenManager, cls).__new__(cls)
        return cls._instance

    def get_token(self) -> str:
        """
        Get a valid OAuth2 token, refreshing if necessary.
        
        Returns:
            str: Valid access token in 'Bearer <token>' format
            
        Raises:
            AuthError: If token cannot be obtained
        """
        import time
        
        current_time = int(time.time())
        buffer = current_app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER', 60)
        
        # If token is expired or about to expire (within buffer seconds)
        if not self._token or self._token_expiry - current_time < buffer:
            try:
                logger.debug("Token expired or not found, requesting new token")
                self._token_data = get_oauth_token()
                self._token = f"{self._token_data['token_type']} {self._token_data['access_token']}"
                self._token_expiry = current_time + self._token_data['expires_in']
                logger.debug(f"New token obtained, expires in {self._token_data['expires_in']} seconds")
            except Exception as e:
                logger.error(f"Failed to obtain OAuth2 token: {str(e)}")
                raise AuthError(f"Failed to obtain access token: {str(e)}") from e
        
        return self._token
        
    def clear_token(self) -> None:
        """
        Clear the current token, forcing a refresh on next request.
        Useful for handling 401 Unauthorized responses.
        """
        self._token = None
        self._token_data = None
        self._token_expiry = 0
        logger.debug("Token cache cleared")
