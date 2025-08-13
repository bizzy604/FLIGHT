"""ServiceList Service Module

This module provides functionality for retrieving ancillary services (meals, baggage, etc.)
through the Verteil NDC ServiceList API.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from .core import FlightService
from .exceptions import FlightServiceError, APIError
from scripts.build_servicelist_rq import build_servicelist_request
from utils.api_logger import api_logger

logger = logging.getLogger(__name__)

class ServiceListService(FlightService):
    """Service class for handling ServiceList operations"""

    async def get_service_list(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer_index: int = 0
    ) -> Dict[str, Any]:
        """
        Get available ancillary services for a flight offer.

        Args:
            flight_price_response: The FlightPrice response from which to build the request
            selected_offer_index: Index of the selected offer (default: 0)

        Returns:
            Dict containing the ServiceList response

        Raises:
            FlightServiceError: If the request fails
            APIError: If the API returns an error
        """
        try:
            # Build ServiceList request using the script
            servicelist_request = build_servicelist_request(
                flight_price_response,
                selected_offer_index
            )

            logger.info(f"Built ServiceList request for offer index {selected_offer_index}")

            # Make the API call
            response = await self._make_request(
                endpoint='/entrygate/rest/request:preServiceList',
                payload=servicelist_request,
                service_name='ServiceList'
            )

            logger.info("ServiceList request completed successfully")
            return response

        except Exception as e:
            logger.error(f"ServiceList request failed: {str(e)}")
            raise FlightServiceError(f"Failed to retrieve service list: {str(e)}") from e

    async def get_services_with_pricing(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer_index: int = 0,
        service_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get available services with pricing information.

        Args:
            flight_price_response: The FlightPrice response
            selected_offer_index: Index of the selected offer
            service_types: Optional list of service types to filter (e.g., ['MEAL', 'BAGGAGE'])

        Returns:
            Dict containing filtered services with pricing
        """
        try:
            # Get all services
            service_response = await self.get_service_list(
                flight_price_response,
                selected_offer_index
            )

            # Filter services if service_types is specified
            if service_types:
                filtered_response = self._filter_services_by_type(service_response, service_types)
                return filtered_response

            return service_response

        except Exception as e:
            logger.error(f"Failed to get services with pricing: {str(e)}")
            raise FlightServiceError(f"Failed to get services with pricing: {str(e)}") from e

    def _filter_services_by_type(
        self,
        service_response: Dict[str, Any],
        service_types: List[str]
    ) -> Dict[str, Any]:
        """
        Filter services by type.

        Args:
            service_response: The full ServiceList response
            service_types: List of service types to include

        Returns:
            Dict with filtered services
        """
        try:
            filtered_response = json.loads(json.dumps(service_response))  # Deep copy
            
            services = filtered_response.get('Services', {}).get('Service', [])
            if not isinstance(services, list):
                services = [services] if services else []

            filtered_services = []
            for service in services:
                service_name = service.get('Name', {}).get('value', '').upper()
                
                # Check if service matches any of the requested types
                for service_type in service_types:
                    if service_type.upper() in service_name:
                        filtered_services.append(service)
                        break

            # Update the response with filtered services
            if filtered_services:
                filtered_response['Services']['Service'] = filtered_services
            else:
                filtered_response['Services'] = {'Service': []}

            logger.info(f"Filtered {len(filtered_services)} services for types: {service_types}")
            return filtered_response

        except Exception as e:
            logger.error(f"Error filtering services by type: {str(e)}")
            return service_response

    async def get_service_details(
        self,
        flight_price_response: Dict[str, Any],
        service_id: str,
        selected_offer_index: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific service.

        Args:
            flight_price_response: The FlightPrice response
            service_id: The ID of the service to get details for
            selected_offer_index: Index of the selected offer

        Returns:
            Dict containing service details or None if not found
        """
        try:
            # Get all services
            service_response = await self.get_service_list(
                flight_price_response,
                selected_offer_index
            )

            # Find the specific service
            services = service_response.get('Services', {}).get('Service', [])
            if not isinstance(services, list):
                services = [services] if services else []

            for service in services:
                if service.get('ServiceID', {}).get('value') == service_id:
                    logger.info(f"Found service details for ID: {service_id}")
                    return service

            logger.warning(f"Service not found with ID: {service_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to get service details for ID {service_id}: {str(e)}")
            raise FlightServiceError(f"Failed to get service details: {str(e)}") from e

# Standalone functions for backward compatibility and direct usage
async def get_service_list(
    flight_price_response: Dict[str, Any],
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Standalone function to get service list.

    Args:
        flight_price_response: The FlightPrice response
        selected_offer_index: Index of the selected offer

    Returns:
        Dict containing the ServiceList response
    """
    # Use centralized TokenManager configuration like working services
    from utils.auth import TokenManager
    
    token_manager = TokenManager.get_instance()
    if token_manager._config:
        config = token_manager._config
        logger.info(f"Using TokenManager config: {list(config.keys())}")
    else:
        # Fallback to environment loading if TokenManager not configured
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        config = {
            'VERTEIL_USERNAME': os.getenv('VERTEIL_USERNAME'),
            'VERTEIL_PASSWORD': os.getenv('VERTEIL_PASSWORD'),
            'VERTEIL_API_BASE_URL': os.getenv('VERTEIL_API_BASE_URL'),
            'VERTEIL_TOKEN_ENDPOINT_PATH': os.getenv('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
            'VERTEIL_OFFICE_ID': os.getenv('VERTEIL_OFFICE_ID'),
            'VERTEIL_THIRD_PARTY_ID': os.getenv('VERTEIL_THIRD_PARTY_ID'),
        }
        logger.info(f"Using environment config: {list(config.keys())}")
    
    async with ServiceListService(config) as service:
        return await service.get_service_list(flight_price_response, selected_offer_index)

async def get_services_by_type(
    flight_price_response: Dict[str, Any],
    service_types: List[str],
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Standalone function to get services filtered by type.

    Args:
        flight_price_response: The FlightPrice response
        service_types: List of service types to filter
        selected_offer_index: Index of the selected offer

    Returns:
        Dict containing filtered services
    """
    # Use current_app.config exactly like working air shopping functions
    from quart import current_app
    
    config = current_app.config
    
    async with ServiceListService(config) as service:
        return await service.get_services_with_pricing(
            flight_price_response,
            selected_offer_index,
            service_types
        )

def process_servicelist_response(servicelist_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and transform ServiceList response for frontend consumption.

    Args:
        servicelist_response: Raw ServiceList response

    Returns:
        Dict containing processed service data
    """
    try:
        processed_response = {
            'services': [],
            'total_services': 0,
            'service_categories': set()
        }

        services = servicelist_response.get('Services', {}).get('Service', [])
        if not isinstance(services, list):
            services = [services] if services else []

        for service in services:
            service_data = {
                'service_id': service.get('ServiceID', {}).get('value'),
                'object_key': service.get('ObjectKey'),
                'name': service.get('Name', {}).get('value'),
                'descriptions': [],
                'price': None,
                'currency': None,
                'priced_ind': service.get('PricedInd', False),
                'booking_instructions': service.get('BookingInstructions', {}),
                'associations': service.get('Associations', [])
            }

            # Extract descriptions
            descriptions = service.get('Descriptions', {}).get('Description', [])
            if not isinstance(descriptions, list):
                descriptions = [descriptions] if descriptions else []

            for desc in descriptions:
                if isinstance(desc, dict) and desc.get('Text', {}).get('value'):
                    service_data['descriptions'].append(desc['Text']['value'])

            # Extract price information
            prices = service.get('Price', [])
            if not isinstance(prices, list):
                prices = [prices] if prices else []

            if prices:
                price_info = prices[0]  # Use first price
                total_price = price_info.get('Total', {})
                service_data['price'] = total_price.get('value')
                service_data['currency'] = total_price.get('Code')

            # Determine service category from name
            service_name = service_data['name'] or ''
            if 'MEAL' in service_name.upper():
                service_data['category'] = 'MEAL'
            elif 'BAG' in service_name.upper() or 'LUGGAGE' in service_name.upper():
                service_data['category'] = 'BAGGAGE'
            elif 'SEAT' in service_name.upper():
                service_data['category'] = 'SEAT'
            else:
                service_data['category'] = 'OTHER'

            processed_response['service_categories'].add(service_data['category'])
            processed_response['services'].append(service_data)

        processed_response['total_services'] = len(processed_response['services'])
        processed_response['service_categories'] = list(processed_response['service_categories'])

        logger.info(f"Processed {processed_response['total_services']} services")
        return processed_response

    except Exception as e:
        logger.error(f"Error processing ServiceList response: {str(e)}")
        return {
            'services': [],
            'total_services': 0,
            'service_categories': [],
            'error': str(e)
        }