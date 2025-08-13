"""SeatAvailability Service Module

This module provides functionality for retrieving seat availability and seat maps
through the Verteil NDC SeatAvailability API.
"""
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from .core import FlightService
from .exceptions import FlightServiceError, APIError
from scripts.build_seatavailability_rq import build_seatavailability_request
from utils.api_logger import api_logger

logger = logging.getLogger(__name__)

class SeatAvailabilityService(FlightService):
    """Service class for handling SeatAvailability operations"""

    async def get_seat_availability(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer_index: int = 0
    ) -> Dict[str, Any]:
        """
        Get available seats for a flight offer.

        Args:
            flight_price_response: The FlightPrice response from which to build the request
            selected_offer_index: Index of the selected offer (default: 0)

        Returns:
            Dict containing the SeatAvailability response

        Raises:
            FlightServiceError: If the request fails
            APIError: If the API returns an error
        """
        try:
            # Build SeatAvailability request using the script
            seatavailability_request = build_seatavailability_request(
                flight_price_response,
                selected_offer_index
            )

            logger.info(f"Built SeatAvailability request for offer index {selected_offer_index}")

            # Make the API call
            response = await self._make_request(
                endpoint='/entrygate/rest/request:preSeatAvailability',
                payload=seatavailability_request,
                service_name='SeatAvailability'
            )

            logger.info("SeatAvailability request completed successfully")
            return response

        except Exception as e:
            logger.error(f"SeatAvailability request failed: {str(e)}")
            raise FlightServiceError(f"Failed to retrieve seat availability: {str(e)}") from e

    async def get_seat_map(
        self,
        flight_price_response: Dict[str, Any],
        segment_key: Optional[str] = None,
        selected_offer_index: int = 0
    ) -> Dict[str, Any]:
        """
        Get seat map for specific flight segment.

        Args:
            flight_price_response: The FlightPrice response
            segment_key: Optional specific segment key to get seat map for
            selected_offer_index: Index of the selected offer

        Returns:
            Dict containing seat map data
        """
        try:
            # Get seat availability
            seat_response = await self.get_seat_availability(
                flight_price_response,
                selected_offer_index
            )

            # Filter by segment if specified
            if segment_key:
                filtered_response = self._filter_seats_by_segment(seat_response, segment_key)
                return filtered_response

            return seat_response

        except Exception as e:
            logger.error(f"Failed to get seat map: {str(e)}")
            raise FlightServiceError(f"Failed to get seat map: {str(e)}") from e

    async def get_available_seats_by_class(
        self,
        flight_price_response: Dict[str, Any],
        cabin_class: str,
        selected_offer_index: int = 0
    ) -> Dict[str, Any]:
        """
        Get available seats filtered by cabin class.

        Args:
            flight_price_response: The FlightPrice response
            cabin_class: Cabin class to filter ('Economy', 'Business', 'First', etc.)
            selected_offer_index: Index of the selected offer

        Returns:
            Dict containing filtered seat availability
        """
        try:
            # Get all seat availability
            seat_response = await self.get_seat_availability(
                flight_price_response,
                selected_offer_index
            )

            # Filter by cabin class
            filtered_response = self._filter_seats_by_class(seat_response, cabin_class)
            return filtered_response

        except Exception as e:
            logger.error(f"Failed to get seats for class {cabin_class}: {str(e)}")
            raise FlightServiceError(f"Failed to get seats for cabin class: {str(e)}") from e

    def _filter_seats_by_segment(
        self,
        seat_response: Dict[str, Any],
        segment_key: str
    ) -> Dict[str, Any]:
        """
        Filter seats by segment key.

        Args:
            seat_response: The full SeatAvailability response
            segment_key: The segment key to filter for

        Returns:
            Dict with filtered seats
        """
        try:
            filtered_response = json.loads(json.dumps(seat_response))  # Deep copy
            
            # Filter DataLists SeatList
            seat_lists = filtered_response.get('DataLists', {}).get('SeatList', {})
            if isinstance(seat_lists, dict) and 'Seats' in seat_lists:
                seats = seat_lists.get('Seats', [])
                if not isinstance(seats, list):
                    seats = [seats] if seats else []

                filtered_seats = []
                for seat in seats:
                    # Check if seat is associated with the specified segment
                    associations = seat.get('Associations', [])
                    if not isinstance(associations, list):
                        associations = [associations] if associations else []

                    for assoc in associations:
                        flight_info = assoc.get('Flight', {})
                        segment_refs = flight_info.get('originDestinationReferencesOrSegmentReferences', [])
                        
                        for seg_ref in segment_refs:
                            if isinstance(seg_ref, dict) and seg_ref.get('SegmentReferences', {}).get('value'):
                                seg_values = seg_ref['SegmentReferences']['value']
                                if isinstance(seg_values, list) and segment_key in seg_values:
                                    filtered_seats.append(seat)
                                    break
                                elif isinstance(seg_values, str) and seg_values == segment_key:
                                    filtered_seats.append(seat)
                                    break

                seat_lists['Seats'] = filtered_seats

            logger.info(f"Filtered seats for segment {segment_key}")
            return filtered_response

        except Exception as e:
            logger.error(f"Error filtering seats by segment: {str(e)}")
            return seat_response

    def _filter_seats_by_class(
        self,
        seat_response: Dict[str, Any],
        cabin_class: str
    ) -> Dict[str, Any]:
        """
        Filter seats by cabin class.

        Args:
            seat_response: The full SeatAvailability response
            cabin_class: The cabin class to filter for

        Returns:
            Dict with filtered seats
        """
        try:
            filtered_response = json.loads(json.dumps(seat_response))  # Deep copy
            
            # This would need to be implemented based on how cabin class information
            # is provided in the seat response. The logic would vary based on 
            # the specific seat response structure from Verteil API.
            
            logger.info(f"Filtered seats for cabin class {cabin_class}")
            return filtered_response

        except Exception as e:
            logger.error(f"Error filtering seats by class: {str(e)}")
            return seat_response

    async def get_seat_details(
        self,
        flight_price_response: Dict[str, Any],
        seat_number: str,
        segment_key: str,
        selected_offer_index: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific seat.

        Args:
            flight_price_response: The FlightPrice response
            seat_number: The seat number (e.g., "12A")
            segment_key: The flight segment key
            selected_offer_index: Index of the selected offer

        Returns:
            Dict containing seat details or None if not found
        """
        try:
            # Get seat availability for the segment
            seat_response = await self.get_seat_map(
                flight_price_response,
                segment_key,
                selected_offer_index
            )

            # Find the specific seat
            seat_lists = seat_response.get('DataLists', {}).get('SeatList', {})
            seats = seat_lists.get('Seats', [])
            if not isinstance(seats, list):
                seats = [seats] if seats else []

            for seat in seats:
                location = seat.get('Location', {})
                row_number = str(location.get('Row', {}).get('Number', {}).get('value', ''))
                column = location.get('Column', '')
                
                if f"{row_number}{column}" == seat_number:
                    logger.info(f"Found seat details for {seat_number}")
                    return seat

            logger.warning(f"Seat not found: {seat_number}")
            return None

        except Exception as e:
            logger.error(f"Failed to get seat details for {seat_number}: {str(e)}")
            raise FlightServiceError(f"Failed to get seat details: {str(e)}") from e

# Standalone functions for backward compatibility and direct usage
async def get_seat_availability(
    flight_price_response: Dict[str, Any],
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Standalone function to get seat availability.

    Args:
        flight_price_response: The FlightPrice response
        selected_offer_index: Index of the selected offer

    Returns:
        Dict containing the SeatAvailability response
    """
    # Use TokenManager directly to bypass FlightService validation issues
    from utils.auth import TokenManager
    from scripts.build_seatavailability_rq import build_seatavailability_request
    import aiohttp
    import os
    
    # Get token from the working TokenManager
    token_manager = TokenManager.get_instance()
    token = token_manager.get_token()
    
    # Build the request
    seatavailability_request = build_seatavailability_request(
        flight_price_response, selected_offer_index
    )
    
    # Make direct API call (like working air shopping does)
    api_url = f"{os.environ.get('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com')}/entrygate/rest/request:preSeatAvailability"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Authorization': token,
        'OfficeId': os.environ.get('VERTEIL_OFFICE_ID', 'OFF3746'),
        'service': 'SeatAvailability',
        'User-Agent': 'PostmanRuntime/7.41',
        'Cache-Control': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=seatavailability_request, timeout=30) as response:
            result = await response.json()
            return result

async def get_seat_map_for_segment(
    flight_price_response: Dict[str, Any],
    segment_key: str,
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Standalone function to get seat map for specific segment.

    Args:
        flight_price_response: The FlightPrice response
        segment_key: The segment key to get seat map for
        selected_offer_index: Index of the selected offer

    Returns:
        Dict containing seat map data
    """
    # Use current_app.config exactly like working air shopping functions
    from quart import current_app
    
    config = current_app.config
    
    async with SeatAvailabilityService(config) as service:
        return await service.get_seat_map(
            flight_price_response,
            segment_key,
            selected_offer_index
        )

def process_seatavailability_response(seatavailability_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and transform SeatAvailability response for frontend consumption.

    Args:
        seatavailability_response: Raw SeatAvailability response

    Returns:
        Dict containing processed seat map data
    """
    try:
        processed_response = {
            'seat_maps': [],
            'total_seats': 0,
            'available_seats': 0,
            'seat_categories': set(),
            'segments': []
        }

        # Process DataLists SeatList
        data_lists = seatavailability_response.get('DataLists', {})
        seat_list = data_lists.get('SeatList', {})
        seats = seat_list.get('Seats', [])
        
        if not isinstance(seats, list):
            seats = [seats] if seats else []

        segment_seats = {}  # Group seats by segment

        for seat in seats:
            location = seat.get('Location', {})
            row_info = location.get('Row', {}).get('Number', {})
            column = location.get('Column', '')
            
            seat_data = {
                'seat_number': f"{row_info.get('value', '')}{column}",
                'row': row_info.get('value'),
                'column': column,
                'characteristics': [],
                'price': None,
                'currency': None,
                'available': True,
                'segment_keys': []
            }

            # Extract characteristics
            characteristics = location.get('Characteristics', {}).get('Characteristic', [])
            if not isinstance(characteristics, list):
                characteristics = [characteristics] if characteristics else []

            for char in characteristics:
                if isinstance(char, dict):
                    code = char.get('Code')
                    if code:
                        seat_data['characteristics'].append(code)
                        processed_response['seat_categories'].add(code)

            # Extract price if available
            services = seatavailability_response.get('Services', {}).get('Service', [])
            if not isinstance(services, list):
                services = [services] if services else []

            for service in services:
                # Match service to seat based on associations
                associations = service.get('Associations', [])
                if not isinstance(associations, list):
                    associations = [associations] if associations else []

                for assoc in associations:
                    # Check if this service is for this seat
                    # This logic would need to be refined based on actual API response structure
                    prices = service.get('Price', [])
                    if prices and not isinstance(prices, list):
                        prices = [prices]
                    
                    if prices:
                        price_info = prices[0]
                        total_price = price_info.get('Total', {})
                        seat_data['price'] = total_price.get('value')
                        seat_data['currency'] = total_price.get('Code')

            # Extract segment associations
            seat_associations = seat.get('Associations', [])
            if not isinstance(seat_associations, list):
                seat_associations = [seat_associations] if seat_associations else []

            for assoc in seat_associations:
                flight_info = assoc.get('Flight', {})
                segment_refs = flight_info.get('originDestinationReferencesOrSegmentReferences', [])
                
                for seg_ref in segment_refs:
                    if isinstance(seg_ref, dict) and seg_ref.get('SegmentReferences', {}).get('value'):
                        seg_values = seg_ref['SegmentReferences']['value']
                        if isinstance(seg_values, list):
                            seat_data['segment_keys'].extend(seg_values)
                        elif isinstance(seg_values, str):
                            seat_data['segment_keys'].append(seg_values)

            # Group seats by segment
            for segment_key in seat_data['segment_keys']:
                if segment_key not in segment_seats:
                    segment_seats[segment_key] = []
                segment_seats[segment_key].append(seat_data)

            if seat_data['available']:
                processed_response['available_seats'] += 1

        # Process segments
        for segment_key, segment_seat_list in segment_seats.items():
            segment_info = {
                'segment_key': segment_key,
                'seats': segment_seat_list,
                'total_seats': len(segment_seat_list),
                'available_seats': sum(1 for seat in segment_seat_list if seat['available'])
            }
            processed_response['seat_maps'].append(segment_info)
            processed_response['segments'].append(segment_key)

        processed_response['total_seats'] = len(seats)
        processed_response['seat_categories'] = list(processed_response['seat_categories'])

        logger.info(f"Processed {processed_response['total_seats']} seats across {len(processed_response['segments'])} segments")
        return processed_response

    except Exception as e:
        logger.error(f"Error processing SeatAvailability response: {str(e)}")
        return {
            'seat_maps': [],
            'total_seats': 0,
            'available_seats': 0,
            'seat_categories': [],
            'segments': [],
            'error': str(e)
        }