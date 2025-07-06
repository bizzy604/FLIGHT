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
from .search import FlightSearchService
from .decorators import async_rate_limited, async_cache
from transformers.enhanced_air_shopping_transformer import transform_air_shopping_for_results_enhanced
from utils.multi_airline_flight_card_generator import generate_enhanced_flight_cards

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
        self.search_service = None
        logger.info("Initialized AirShoppingService with multi-airline support")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await super().__aenter__()
        self.search_service = FlightSearchService(self.config)
        await self.search_service.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.search_service:
            await self.search_service.__aexit__(exc_type, exc_val, exc_tb)
        await super().__aexit__(exc_type, exc_val, exc_tb)
    
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
            if not self.search_service:
                self.search_service = FlightSearchService(self.config)
            
            raw_response = await self.search_service.search_flights_raw(search_criteria)
            search_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Raw search completed in {search_time:.3f}s - Request ID: {request_id}")
            
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

            # Step 4: Build comprehensive response
            total_time = (datetime.now() - start_time).total_seconds()

            response = {
                'offers': enhanced_flight_cards,
                'raw_response': raw_response,
                'metadata': {
                    **metadata,
                    'enhanced_cards_count': len(enhanced_flight_cards),
                    'performance': {
                        'search_time': search_time,
                        'transform_time': transform_time,
                        'card_generation_time': card_time,
                        'total_time': total_time
                    },
                    'request_id': request_id,
                    'service_version': '2.3-enhanced'
                }
            }
            
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
        if self.search_service:
            await self.search_service.close()
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
