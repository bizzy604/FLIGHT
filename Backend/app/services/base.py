"""Base service class for all VDC services."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from app.core.auth import VDCAuthClient
from app.core.exceptions import VDCAPIError
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class BaseVDCService(ABC):
    """
    Base class for all VDC API services.
    
    Provides:
    - Authentication handling
    - HTTP client management
    - Common error handling
    - Request/response logging
    """
    
    def __init__(
        self, 
        auth_client: VDCAuthClient,
        http_client: httpx.AsyncClient
    ):
        self.auth = auth_client
        self.http = http_client
        self.api_url = settings.VDC_API_BASE_URL
    
    async def _make_request(
        self, 
        service_name: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        airline_owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to VDC API.
        
        Args:
            service_name: VDC service name (e.g., 'AirShopping')
            payload: Request payload
            headers: Optional additional headers
            airline_owner: Optional airline code for ThirdpartyId header
            
        Returns:
            API response dict
            
        Raises:
            VDCAPIError: On API errors
        """
        # Get authentication token
        token = await self.auth.get_token()
        
        # Build headers
        request_headers = {
            "Authorization": f"Bearer {token}",  # Add Bearer prefix
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Service": service_name,
            "OfficeId": self.auth.office_id,
            **(headers or {})
        }
        
        # Add ThirdpartyId if airline specified (for single-airline requests)
        if airline_owner:
            request_headers["ThirdpartyId"] = airline_owner
            logger.debug(f"Setting ThirdpartyId header: {airline_owner}")
        
        logger.info(f"🔵 Making {service_name} request to VDC API")
        logger.debug(f"Request payload: {payload}")
        
        # Make request
        try:
            response = await self.http.post(
                f"{self.api_url}:{service_name}",
                json=payload,
                headers=request_headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"✅ {service_name} request successful")
            logger.debug(f"Response: {response_data}")
            
            return response_data
            
        except httpx.HTTPStatusError as e:
            error_detail = None
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
            
            logger.error(
                f"🔴 {service_name} API error: {e.response.status_code}",
                exc_info=True
            )
            
            raise VDCAPIError(
                f"VDC {service_name} API error: {e.response.status_code}",
                status_code=e.response.status_code,
                response=error_detail
            )
            
        except httpx.RequestError as e:
            logger.error(f"🔴 {service_name} request failed: {str(e)}", exc_info=True)
            raise VDCAPIError(f"{service_name} request failed: {str(e)}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the service workflow."""
        pass
