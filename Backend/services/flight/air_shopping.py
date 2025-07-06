"""
Enhanced Air Shopping Service for Multi-Airline Support

This service provides enhanced air shopping functionality with multi-airline support,
integrating Phase 2.1 (Enhanced Air Shopping Transformer) and Phase 2.2 (Multi-Airline
Flight Card Generator) to deliver comprehensive flight search results.

Key Features:
- Multi-airline response processing
- Enhanced flight card generation with airline context
- Backward compatibility with existing API structure
- Comprehensive error handling and logging
- Performance optimization with caching

Author: FLIGHT Application - Phase 2.3
Created: 2025-07-02
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from .core import FlightService
from .decorators import async_rate_limited, async_cache
from .exceptions import ValidationError, FlightServiceError
from transformers.enhanced_air_shopping_transformer import transform_air_shopping_for_results_enhanced
from utils.multi_airline_flight_card_generator import generate_enhanced_flight_cards
from scripts.build_airshopping_rq import build_airshopping_request

logger = logging.getLogger(__name__)


class AirShoppingService(FlightService):
    """
    Enhanced Air Shopping Service with multi-airline support.
    
    This service orchestrates the complete air shopping flow:
    1. Raw flight search using FlightSearchService
    2. Enhanced transformation using EnhancedAirShoppingTransformer
    3. Enhanced flight card generation using MultiAirlineFlightCardGenerator
    4. Response optimization and caching
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Air Shopping Service.

        Args:
            config (Optional[Dict[str, Any]]): Service configuration
        """
        super().__init__(config)
        logger.info("Initialized AirShoppingService with multi-airline support")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await super().__aexit__(exc_type, exc_val, exc_tb)

    def _validate_search_criteria(self, criteria: Dict[str, Any]) -> None:
        """Validate search criteria."""
        if not criteria.get('odSegments'):
            raise ValidationError("At least one origin-destination segment is required")
        for segment in criteria['odSegments']:
            if not all(key in segment for key in ['origin', 'destination', 'departureDate']):
                raise ValidationError("Each segment must include origin, destination, and departureDate")

    def _build_search_payload(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Build the air shopping request payload."""
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

        num_adults = criteria.get('numAdults', criteria.get('num_adults', 1))
        num_children = criteria.get('numChildren', criteria.get('num_children', 0))
        num_infants = criteria.get('numInfants', criteria.get('num_infants', 0))

        # Determine cabin preference
        if trip_type == 'ROUND_TRIP' and len(criteria['odSegments']) >= 1:
            # For round-trip, use cabin preference from first segment
            cabin_preference = criteria['odSegments'][0].get('cabinPreference', 'ECONOMY')
            logger.info(f"[DEBUG] Round-trip: Using cabin preference from first segment: '{cabin_preference}'")
        else:
            # For one-way or multi-city, use global cabin preference
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
    
    @async_rate_limited(limit=50, window=60)
    @async_cache(timeout=300)
    async def search_flights_enhanced(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced flight search with multi-airline support and flight card generation.
        
        This method provides the complete enhanced air shopping experience:
        1. Performs raw flight search
        2. Applies enhanced transformation with multi-airline context
        3. Generates enhanced flight cards with competitive analysis
        4. Returns optimized response structure
        
        Args:
            search_criteria (Dict[str, Any]): Search criteria including:
                - trip_type: Type of trip (ONE_WAY, ROUND_TRIP, MULTI_CITY)
                - od_segments: Origin-destination segments
                - num_adults, num_children, num_infants: Passenger counts
                - cabin_preference: Cabin class preference
                - request_id: Optional request identifier
        
        Returns:
            Dict[str, Any]: Enhanced response with flight cards and metadata
        """
        request_id = search_criteria.get('request_id', str(uuid.uuid4()))
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting enhanced air shopping search - Request ID: {request_id}")
            
            # Step 1: Get raw flight search results
            try:
                self._validate_search_criteria(search_criteria)

                payload = self._build_search_payload(search_criteria)

                # Make the API request and return the raw response
                raw_response = await self._make_request(
                    endpoint='/entrygate/rest/request:airShopping',
                    payload=payload,
                    service_name='AirShopping',
                    request_id=request_id
                )

                search_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Raw search completed in {search_time:.3f}s - Request ID: {request_id}")

            except (ValidationError, FlightServiceError) as e:
                logger.error(f"Service error during raw flight search: {str(e)}")
                raise # Re-raise the exception to be handled by the calling route
            except Exception as e:
                logger.error(f"Unexpected error during raw flight search: {str(e)}", exc_info=True)
                raise FlightServiceError(f"An unexpected error occurred: {e}") from e
            
            # Step 2: Enhanced transformation with multi-airline support
            transform_start = datetime.now()
            filter_airlines = self.config.get('FILTER_UNSUPPORTED_AIRLINES', False)
            transformed_data = transform_air_shopping_for_results_enhanced(raw_response, filter_airlines)
            transform_time = (datetime.now() - transform_start).total_seconds()
            
            offers = transformed_data.get('offers', [])
            metadata = transformed_data.get('metadata', {})
            
            logger.info(f"Enhanced transformation completed in {transform_time:.3f}s - "
                       f"{metadata.get('total_offers', 0)} offers, "
                       f"Multi-airline: {metadata.get('is_multi_airline', False)} - "
                       f"Request ID: {request_id}")
            
            # Step 3: Generate enhanced flight cards
            card_start = datetime.now()
            enhanced_flight_cards = generate_enhanced_flight_cards(raw_response, offers)
            card_time = (datetime.now() - card_start).total_seconds()
            
            logger.info(f"Enhanced flight cards generated in {card_time:.3f}s - "
                       f"{len(enhanced_flight_cards)} cards - Request ID: {request_id}")

            # Step 4: Cache raw response for flight pricing
            cache_start = datetime.now()
            raw_response_cache_key = f"air_shopping_raw_{request_id}_{int(cache_start.timestamp())}"

            # Store raw response in backend cache for flight pricing
            try:
                from utils.cache_manager import cache_manager
                # Cache for 30 minutes (1800 seconds) - same as frontend session
                cache_manager.set(raw_response_cache_key, raw_response, ttl=1800)
                logger.info(f"Raw response cached with key: {raw_response_cache_key}")
            except Exception as cache_error:
                logger.warning(f"Failed to cache raw response: {cache_error}")
                # Continue without caching - fallback to sending raw response
                raw_response_cache_key = None

            # Step 5: Build optimized response
            total_time = (datetime.now() - start_time).total_seconds()

            response = {
                'offers': enhanced_flight_cards,
                'metadata': {
                    **metadata,
                    'enhanced_cards_count': len(enhanced_flight_cards),
                    'raw_response_cache_key': raw_response_cache_key,  # Key for backend to retrieve raw response
                    'performance': {
                        'search_time': search_time,
                        'transform_time': transform_time,
                        'card_generation_time': card_time,
                        'total_time': total_time
                    },
                    'request_id': request_id,
                    'service_version': '2.4-optimized'
                }
            }

            # Only include raw_response if caching failed (fallback)
            if raw_response_cache_key is None:
                response['raw_response'] = raw_response
                logger.warning("Including raw_response in frontend response due to cache failure")
            
            logger.info(f"Enhanced air shopping completed successfully in {total_time:.3f}s - "
                       f"Request ID: {request_id}")
            
            return response
            
        except Exception as e:
            error_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in enhanced air shopping after {error_time:.3f}s - "
                        f"Request ID: {request_id}: {e}", exc_info=True)
            raise
    
    async def search_flights_basic(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic flight search with legacy compatibility.
        
        This method provides backward compatibility with the existing API structure
        while using the enhanced infrastructure.
        
        Args:
            search_criteria (Dict[str, Any]): Search criteria
        
        Returns:
            Dict[str, Any]: Basic response compatible with legacy frontend
        """
        request_id = search_criteria.get('request_id', str(uuid.uuid4()))
        
        try:
            logger.info(f"Starting basic air shopping search - Request ID: {request_id}")
            
            # Use enhanced search but return simplified structure
            enhanced_response = await self.search_flights_enhanced(search_criteria)
            
            # Extract basic flight cards (remove enhanced features for compatibility)
            basic_offers = []
            for card in enhanced_response.get('offers', []):
                basic_offer = {
                    'id': card.get('id'),
                    'price': card.get('price'),
                    'currency': card.get('currency'),
                    'airline': card.get('airline'),
                    'departure': card.get('departure'),
                    'arrival': card.get('arrival'),
                    'duration': card.get('duration'),
                    'stops': card.get('stops'),
                    'stopDetails': card.get('stopDetails'),
                    'segments': card.get('segments'),
                    'baggage': card.get('baggage'),
                    'fare': card.get('fare'),
                    'priceBreakdown': card.get('priceBreakdown')
                }
                basic_offers.append(basic_offer)
            
            # Return legacy-compatible structure
            return {
                'offers': basic_offers,
                'raw_response': enhanced_response.get('raw_response'),
                'metadata': {
                    'total_offers': len(basic_offers),
                    'is_multi_airline': enhanced_response.get('metadata', {}).get('is_multi_airline', False),
                    'airline_count': enhanced_response.get('metadata', {}).get('airline_count', 1),
                    'request_id': request_id,
                    'service_version': '2.3-basic'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in basic air shopping - Request ID: {request_id}: {e}", exc_info=True)
            raise
    
    async def close(self):
        """Close the service and cleanup resources."""
        await super().close()


async def process_air_shopping_enhanced(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced orchestrator function for air shopping with multi-airline support.
    
    This function serves as the main entry point for enhanced air shopping operations,
    providing comprehensive multi-airline support with enhanced flight cards.
    
    Args:
        search_criteria (Dict[str, Any]): Search criteria
    
    Returns:
        Dict[str, Any]: Enhanced response with status and data
    """
    from quart import current_app
    
    config = current_app.config
    request_id = search_criteria.get('request_id', str(uuid.uuid4()))
    
    async with AirShoppingService(config) as service:
        try:
            # Use enhanced search for comprehensive results
            enhanced_data = await service.search_flights_enhanced(search_criteria)
            
            return {
                'status': 'success',
                'data': enhanced_data,
                'request_id': request_id
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced air shopping orchestrator - "
                        f"Request ID: {request_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'request_id': request_id
            }


async def process_air_shopping_basic(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic orchestrator function for backward compatibility.
    
    This function provides backward compatibility with existing frontend implementations
    while leveraging the enhanced infrastructure.
    
    Args:
        search_criteria (Dict[str, Any]): Search criteria
    
    Returns:
        Dict[str, Any]: Basic response compatible with legacy frontend
    """
    from quart import current_app
    
    config = current_app.config
    request_id = search_criteria.get('request_id', str(uuid.uuid4()))
    
    async with AirShoppingService(config) as service:
        try:
            # Use basic search for legacy compatibility
            basic_data = await service.search_flights_basic(search_criteria)
            
            return {
                'status': 'success',
                'data': basic_data,
                'request_id': request_id
            }
            
        except Exception as e:
            logger.error(f"Error in basic air shopping orchestrator - "
                        f"Request ID: {request_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'request_id': request_id
            }
