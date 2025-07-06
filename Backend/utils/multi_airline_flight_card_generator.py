"""
Multi-Airline Flight Card Generator

This module provides enhanced flight card generation functionality with multi-airline
support. It generates airline-aware flight cards with proper context, ThirdParty ID
mapping, and enhanced display features for multi-airline responses.

Author: FLIGHT Application
Created: 2025-07-02
"""

import logging
from typing import Any, Dict, List, Optional

# Import Phase 1 core infrastructure modules
from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor
from services.airline_mapping_service import AirlineMappingService

# Import existing utilities
from utils.airline_data import get_airline_logo_url

logger = logging.getLogger(__name__)


class MultiAirlineFlightCardGenerator:
    """
    Enhanced flight card generator with multi-airline support.
    """
    
    def __init__(self, response: Dict[str, Any]):
        """
        Initialize the flight card generator.
        
        Args:
            response (Dict[str, Any]): The raw air shopping response
        """
        self.response = response
        self.is_multi_airline = MultiAirlineDetector.is_multi_airline_response(response)
        self.reference_extractor = EnhancedReferenceExtractor(response)
        self.refs = self.reference_extractor.extract_references()
        
        logger.info(f"Initialized flight card generator for {'multi' if self.is_multi_airline else 'single'}-airline response")
    
    def generate_flight_cards(self, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate enhanced flight cards from transformed offers.
        
        Args:
            offers (List[Dict[str, Any]]): List of transformed offers
            
        Returns:
            List[Dict[str, Any]]: List of enhanced flight cards
        """
        try:
            enhanced_cards = []
            
            for offer in offers:
                enhanced_card = self._generate_single_flight_card(offer)
                if enhanced_card:
                    enhanced_cards.append(enhanced_card)
            
            # Multi-airline support is handled in individual card generation

            logger.info(f"Generated {len(enhanced_cards)} enhanced flight cards")
            return enhanced_cards

        except Exception as e:
            logger.error(f"Error generating flight cards: {e}", exc_info=True)
            return offers  # Return original offers as fallback
    
    def _generate_single_flight_card(self, offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate an enhanced flight card for a single offer.
        
        Args:
            offer (Dict[str, Any]): The transformed offer data
            
        Returns:
            Optional[Dict[str, Any]]: Enhanced flight card or None if generation fails
        """
        try:
            airline_code = offer.get('airline', {}).get('code', '??')
            airline_context = offer.get('airline_context', {})
            
            # Base flight card structure (compatible with existing frontend)
            flight_card = {
                # Core identification
                "id": offer.get('id'),
                "offer_index": offer.get('offer_index'),
                "original_offer_id": offer.get('original_offer_id'),
                
                # Airline information
                "airline": {
                    "code": airline_code,
                    "name": AirlineMappingService.get_airline_display_name(airline_code),
                    "logo": get_airline_logo_url(airline_code),
                    "flightNumber": offer.get('airline', {}).get('flightNumber', '')
                },
                
                # Flight timing and routing
                "departure": offer.get('departure'),
                "arrival": offer.get('arrival'),
                "duration": offer.get('duration'),
                "stops": offer.get('stops', 0),
                "stopDetails": offer.get('stopDetails', []),
                
                # Pricing information
                "price": offer.get('price', 0),
                "currency": offer.get('currency', 'USD'),

                # Flight details
                "segments": offer.get('segments', []),
                
                # Essential airline context for multi-airline support
                "airline_context": {
                    "shopping_response_id": airline_context.get('shopping_response_id'),
                    "third_party_id": airline_context.get('third_party_id')
                }
            }
            
            return flight_card
            
        except Exception as e:
            logger.error(f"Error generating flight card for offer {offer.get('id')}: {e}", exc_info=True)
            return None

def generate_enhanced_flight_cards(response: Dict[str, Any], offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main function to generate enhanced flight cards with multi-airline support.
    
    Args:
        response (Dict[str, Any]): The raw air shopping response
        offers (List[Dict[str, Any]]): List of transformed offers
        
    Returns:
        List[Dict[str, Any]]: List of enhanced flight cards
    """
    generator = MultiAirlineFlightCardGenerator(response)
    return generator.generate_flight_cards(offers)
