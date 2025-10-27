"""VDC OAuth2 authentication client."""

import httpx
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings
from app.core.exceptions import AuthenticationError


class VDCAuthClient:
    """
    Simplified VDC OAuth2 authentication client.
    
    Features:
    - Token caching with automatic refresh
    - No disk persistence (stateless)
    - Automatic token renewal before expiry
    """
    
    def __init__(self):
        self.username = settings.VDC_USERNAME
        self.password = settings.VDC_PASSWORD
        self.office_id = settings.VDC_OFFICE_ID
        self.token_url = settings.VDC_TOKEN_URL
        
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._refresh_buffer = 300  # Refresh 5 minutes before expiry
    
    async def get_token(self) -> str:
        """
        Get valid access token.
        
        Returns:
            Valid access token
            
        Raises:
            AuthenticationError: If token retrieval fails
        """
        # Check if token is still valid
        if self._token and self._token_expires_at:
            buffer_time = self._token_expires_at - timedelta(seconds=self._refresh_buffer)
            if datetime.now() < buffer_time:
                return self._token
        
        # Request new token
        await self._refresh_token()
        return self._token
    
    async def _refresh_token(self):
        """
        Request new access token from VDC.
        
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Generate Basic Auth token
            import base64
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    headers={
                        'Authorization': f'Basic {encoded_credentials}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    data={
                        "grant_type": "client_credentials"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                self._token = data["access_token"]
                expires_in = data.get("expires_in", 39600)  # Default 11 hours
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
        except httpx.HTTPStatusError as e:
            raise AuthenticationError(
                f"VDC authentication failed: {e.response.status_code}"
            )
        except httpx.RequestError as e:
            raise AuthenticationError(f"VDC authentication request failed: {str(e)}")
        except KeyError:
            raise AuthenticationError("Invalid token response from VDC")


# Global auth client instance
_auth_client: Optional[VDCAuthClient] = None


def get_auth_client() -> VDCAuthClient:
    """Get global auth client instance."""
    global _auth_client
    if _auth_client is None:
        _auth_client = VDCAuthClient()
    return _auth_client
