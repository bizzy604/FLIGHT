"""
Flight Search Module - Simplified

This module handles flight search operations using the Verteil NDC API.
It is now ONLY responsible for building the request and making the API call.
All transformation logic has been moved to a dedicated transformer.
"""
import logging
import uuid
import sys
import os
import json
from typing import Dict, Any, List, Optional # ## FIX: Add this line ##

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts'))
from build_airshopping_rq import build_airshopping_request

from .core import FlightService
from .decorators import async_cache, async_rate_limited
from .exceptions import FlightServiceError, ValidationError
from .types import SearchCriteria

logger = logging.getLogger(__name__)

class FlightSearchService(FlightService):
    """Service for handling flight search operations. Returns RAW data."""
    
    @async_rate_limited(limit=100, window=60)
    @async_cache(timeout=300) # Caches the raw response
    async def search_flights_raw(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """
        Search for flights and return the RAW, untouched API response.
        
        Args:
            criteria: Search criteria including trip type, segments, passengers, etc.
            
        Returns:
            The raw JSON response dictionary from the airline API.
        """
        try:
            self._validate_search_criteria(criteria)
            
            request_id = criteria.get('request_id', str(uuid.uuid4()))
            payload = self._build_search_payload(criteria)
            
            # Make the API request and return the raw response
            response_data = await self._make_request(
                endpoint='/entrygate/rest/request:airShopping',
                payload=payload,
                service_name='AirShopping',
                request_id=request_id
            )
            


            logger.info(f"Successfully received raw AirShopping response for request_id: {request_id}")
            return response_data
            
        except (ValidationError, FlightServiceError) as e:
            logger.error(f"Service error during raw flight search: {str(e)}")
            raise # Re-raise the exception to be handled by the calling route
        except Exception as e:
            logger.error(f"Unexpected error during raw flight search: {str(e)}", exc_info=True)
            raise FlightServiceError(f"An unexpected error occurred: {e}") from e
    
    def _validate_search_criteria(self, criteria: SearchCriteria) -> None:
        if not criteria.get('odSegments'):
            raise ValidationError("At least one origin-destination segment is required")
        for segment in criteria['odSegments']:
            if not all(key in segment for key in ['origin', 'destination', 'departureDate']):
                raise ValidationError("Each segment must include origin, destination, and departureDate")
    
    def _build_search_payload(self, criteria: SearchCriteria) -> Dict[str, Any]:
        # Handle both tripType and trip_type parameter names
        trip_type = criteria.get('tripType', criteria.get('trip_type', 'ONE_WAY')).upper()
        trip_type_mapping = {'ONEWAY': 'ONE_WAY', 'ROUNDTRIP': 'ROUND_TRIP', 'ROUND_TRIP': 'ROUND_TRIP', 'MULTICITY': 'MULTI_CITY'}
        trip_type = trip_type_mapping.get(trip_type, 'ONE_WAY')

        # Override with trip_type parameter if present (route handler uses this name)
        if criteria.get('trip_type'):
            raw_trip_type = criteria.get('trip_type').upper()
            trip_type = trip_type_mapping.get(raw_trip_type, 'ONE_WAY')



        cabin_mapping = {'ECONOMY': 'Y', 'BUSINESS': 'C', 'FIRST': 'F', 'PREMIUM_ECONOMY': 'W'}
        
        od_segments = []
        for seg in criteria['odSegments']:
            od_segments.append({'Origin': seg['origin'], 'Destination': seg['destination'], 'DepartureDate': seg['departureDate']})
            


        num_adults = criteria.get('num_adults', 1)
        num_children = criteria.get('num_children', 0)
        num_infants = criteria.get('num_infants', 0)
        # Extract cabin preference from segments (for round trips) or global parameter (for one-way)
        cabin_preference = 'ECONOMY'  # default
        if criteria.get('odSegments') and len(criteria['odSegments']) == 2:
            # For round trips (2 segments), use cabin preference from first segment
            first_segment = criteria['odSegments'][0]
            cabin_preference = first_segment.get('cabinPreference', 'ECONOMY')
            logger.info(f"[DEBUG] Round-trip: Using cabin preference from first segment: '{cabin_preference}'")
        else:
            # For one-way flights (1 segment) or fallback, use global parameters
            cabin_preference = criteria.get('cabinClass') or criteria.get('cabinPreference', 'ECONOMY')
            logger.info(f"[DEBUG] One-way: Using global cabin preference: '{cabin_preference}'")

        cabin_code = cabin_mapping.get(cabin_preference.upper(), 'Y')
        logger.info(f"[DEBUG] Cabin preference: '{cabin_preference}' -> cabin_code: '{cabin_code}'")



        payload = build_airshopping_request(
            trip_type=trip_type, od_segments=od_segments, num_adults=num_adults,
            num_children=num_children, num_infants=num_infants,
            cabin_preference_code=cabin_code, fare_type_code="PUBL"
        )



        return payload


async def process_air_shopping(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy orchestrator function that gets raw data and then transforms it.

    DEPRECATED: Use AirShoppingService for new implementations.
    This function is maintained for backward compatibility only.
    """
    from quart import current_app
    # Import the legacy transformer for backward compatibility
    from utils.air_shopping_transformer import transform_air_shopping_for_results

    config = current_app.config
    service = FlightSearchService(config)
    try:
        # 1. Get the RAW response from the airline
        raw_response = await service.search_flights_raw(search_criteria)

        # 2. Transform the raw response into the simple format for the results page
        transformed_data = transform_air_shopping_for_results(raw_response)

        # 3. Return a successful structure
        return {
            'status': 'success',
            'data': transformed_data, # Contains {'offers': [...], 'raw_response': ...}
            'request_id': search_criteria.get('request_id', str(uuid.uuid4()))
        }
    except Exception as e:
        logger.error(f"Error in process_air_shopping orchestrator: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}
    finally:
        await service.close()