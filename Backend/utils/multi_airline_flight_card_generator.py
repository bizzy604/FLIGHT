"""
Multi-Airline Flight Card Generator

This module provides enhanced flight card generation functionality with multi-airline
support. It generates airline-aware flight cards with proper context, ThirdParty ID
mapping, and enhanced display features for multi-airline responses.

Author: FLIGHT Application
Created: 2025-07-02
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Import Phase 1 core infrastructure modules
from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor
from services.airline_mapping_service import AirlineMappingService

# Import existing utilities
from utils.airline_data import get_airline_name, get_airline_logo_url

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
            
            # Add multi-airline specific enhancements
            if self.is_multi_airline:
                try:
                    enhanced_cards = self._add_multi_airline_enhancements(enhanced_cards)
                except Exception as e:
                    logger.error(f"Error adding multi-airline enhancements: {e}", exc_info=True)
                    # Continue with basic enhanced cards even if multi-airline enhancements fail

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
                    "flightNumber": offer.get('airline', {}).get('flightNumber', ''),
                    # Enhanced airline context
                    "region": airline_context.get('region'),
                    "is_supported": airline_context.get('is_supported', True),
                    "third_party_id": airline_context.get('third_party_id'),
                    "supported_features": airline_context.get('supported_features', [])
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
                "priceBreakdown": offer.get('priceBreakdown', {}),
                
                # Flight details
                "segments": self._enhance_segments(offer.get('segments', []), airline_code),
                "baggage": offer.get('baggage', {}),
                "fare": offer.get('fare', {}),
                
                # Multi-airline specific enhancements
                "airline_context": {
                    "is_multi_airline_response": self.is_multi_airline,
                    "shopping_response_id": airline_context.get('shopping_response_id'),
                    "third_party_id": airline_context.get('third_party_id'),
                    "airline_priority": self._calculate_airline_priority(airline_code),
                    "feature_compatibility": self._get_feature_compatibility(airline_code),
                    "booking_requirements": self._get_booking_requirements(airline_code)
                },
                
                # Enhanced display features
                "display_enhancements": {
                    "airline_badge": self._generate_airline_badge(airline_code),
                    "price_confidence": self._calculate_price_confidence(offer),
                    "booking_complexity": self._assess_booking_complexity(airline_code),
                    "recommendation_score": self._calculate_recommendation_score(offer, airline_code)
                },
                
                # Time limits and expiration
                "time_limits": self._generate_time_limits(offer, airline_code),
                
                # Compatibility flags
                "compatibility": {
                    "supports_online_checkin": AirlineMappingService.supports_feature(airline_code, 'online_checkin'),
                    "supports_seat_selection": AirlineMappingService.supports_feature(airline_code, 'seat_selection'),
                    "supports_meal_selection": AirlineMappingService.supports_feature(airline_code, 'meal_selection'),
                    "supports_baggage_upgrade": AirlineMappingService.supports_feature(airline_code, 'baggage_upgrade'),
                    "supports_cancellation": AirlineMappingService.supports_feature(airline_code, 'cancellation'),
                    "supports_changes": AirlineMappingService.supports_feature(airline_code, 'changes')
                }
            }
            
            return flight_card
            
        except Exception as e:
            logger.error(f"Error generating flight card for offer {offer.get('id')}: {e}", exc_info=True)
            return None
    
    def _enhance_segments(self, segments: List[Dict[str, Any]], primary_airline: str) -> List[Dict[str, Any]]:
        """
        Enhance segment information with airline-specific context.
        
        Args:
            segments (List[Dict[str, Any]]): Original segments
            primary_airline (str): Primary airline code for the offer
            
        Returns:
            List[Dict[str, Any]]: Enhanced segments
        """
        enhanced_segments = []
        
        for segment in segments:
            segment_airline = segment.get('airline', {}).get('code', primary_airline)
            
            enhanced_segment = segment.copy()
            enhanced_segment['airline_context'] = {
                'is_codeshare': segment_airline != primary_airline,
                'operating_airline': segment_airline,
                'marketing_airline': primary_airline,
                'third_party_id': AirlineMappingService.get_third_party_id(segment_airline),
                'is_supported': AirlineMappingService.validate_airline_code(segment_airline)
            }
            
            enhanced_segments.append(enhanced_segment)
        
        return enhanced_segments
    
    def _add_multi_airline_enhancements(self, flight_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add multi-airline specific enhancements to flight cards.
        
        Args:
            flight_cards (List[Dict[str, Any]]): List of flight cards
            
        Returns:
            List[Dict[str, Any]]: Enhanced flight cards with multi-airline features
        """
        # Group cards by airline
        airline_groups = {}
        for card in flight_cards:
            airline_code = card.get('airline', {}).get('code', '??')
            if airline_code not in airline_groups:
                airline_groups[airline_code] = []
            airline_groups[airline_code].append(card)
        
        # Add airline comparison features
        for card in flight_cards:
            airline_code = card.get('airline', {}).get('code', '??')
            
            # Add airline comparison context
            card['multi_airline_context'] = {
                'total_airlines_in_response': len(airline_groups),
                'airline_offer_count': len(airline_groups.get(airline_code, [])),
                'airline_rank_by_price': self._get_airline_price_rank(card, flight_cards),
                'airline_rank_by_features': self._get_airline_feature_rank(airline_code),
                'competitive_advantages': self._get_competitive_advantages(card, flight_cards),
                'price_comparison': self._get_price_comparison(card, flight_cards)
            }
            
            # Add multi-airline display hints
            card['display_enhancements']['multi_airline_hints'] = {
                'show_airline_badge': True,
                'highlight_best_price': self._is_best_price_for_airline(card, airline_groups[airline_code]),
                'highlight_best_features': self._has_best_features_for_airline(airline_code),
                'show_comparison_tooltip': True
            }
        
        return flight_cards
    
    def _calculate_airline_priority(self, airline_code: str) -> int:
        """Calculate priority score for airline (1-10, higher is better)."""
        airline_info = AirlineMappingService.get_airline_info(airline_code)
        
        # Base priority on region and features
        region_priority = {
            'Europe': 8,
            'Middle East': 9,
            'Africa': 7,
            'Asia': 8,
            'Americas': 8
        }
        
        base_score = region_priority.get(airline_info.get('region', ''), 5)
        feature_bonus = len(airline_info.get('supported_features', [])) // 2
        
        return min(10, base_score + feature_bonus)
    
    def _get_feature_compatibility(self, airline_code: str) -> Dict[str, bool]:
        """Get feature compatibility for airline."""
        return {
            'advanced_booking': AirlineMappingService.supports_feature(airline_code, 'advanced_booking'),
            'real_time_updates': AirlineMappingService.supports_feature(airline_code, 'real_time_updates'),
            'mobile_boarding': AirlineMappingService.supports_feature(airline_code, 'mobile_boarding'),
            'lounge_access': AirlineMappingService.supports_feature(airline_code, 'lounge_access')
        }
    
    def _get_booking_requirements(self, airline_code: str) -> Dict[str, Any]:
        """Get booking requirements for airline."""
        return {
            'requires_phone_verification': airline_code in ['EK', 'QR'],  # Example requirements
            'requires_passport_info': True,
            'advance_booking_days': 1,
            'payment_methods': ['credit_card', 'debit_card'],
            'documentation_required': ['passport', 'visa'] if airline_code in ['EK', 'QR'] else ['passport']
        }
    
    def _generate_airline_badge(self, airline_code: str) -> Dict[str, Any]:
        """Generate airline badge information."""
        airline_info = AirlineMappingService.get_airline_info(airline_code)
        
        return {
            'text': airline_code,
            'color': self._get_airline_color(airline_code),
            'tooltip': f"{airline_info.get('display_name', airline_code)} - {airline_info.get('region', 'Unknown')}",
            'priority': self._calculate_airline_priority(airline_code)
        }
    
    def _get_airline_color(self, airline_code: str) -> str:
        """Get color scheme for airline badge."""
        color_map = {
            'EK': '#FF6B35',  # Emirates orange
            'QR': '#5C0A2B',  # Qatar burgundy
            'KL': '#006DB7',  # KLM blue
            'AF': '#002157',  # Air France blue
            'LHG': '#F9BA00', # Lufthansa yellow
            'ET': '#228B22',  # Ethiopian green
            'KQ': '#E31837'   # Kenya Airways red
        }
        return color_map.get(airline_code, '#6B7280')  # Default gray
    
    def _calculate_price_confidence(self, offer: Dict[str, Any]) -> str:
        """Calculate price confidence level."""
        price = offer.get('price', 0)
        airline_code = offer.get('airline', {}).get('code', '??')
        
        # Simple confidence calculation based on airline and price range
        if AirlineMappingService.validate_airline_code(airline_code):
            if price > 1000:
                return 'high'
            elif price > 500:
                return 'medium'
            else:
                return 'high'  # Low prices from known airlines are confident
        else:
            return 'low'
    
    def _assess_booking_complexity(self, airline_code: str) -> str:
        """Assess booking complexity for airline."""
        feature_count = len(AirlineMappingService.get_airline_info(airline_code).get('supported_features', []))
        
        if feature_count >= 8:
            return 'simple'
        elif feature_count >= 5:
            return 'moderate'
        else:
            return 'complex'
    
    def _calculate_recommendation_score(self, offer: Dict[str, Any], airline_code: str) -> float:
        """Calculate recommendation score (0.0 - 1.0)."""
        price_score = min(1.0, 1000 / max(offer.get('price', 1000), 100))  # Inverse price score
        airline_score = self._calculate_airline_priority(airline_code) / 10.0
        feature_score = len(AirlineMappingService.get_airline_info(airline_code).get('supported_features', [])) / 10.0
        
        return round((price_score * 0.4 + airline_score * 0.3 + feature_score * 0.3), 2)
    
    def _generate_time_limits(self, offer: Dict[str, Any], airline_code: str) -> Dict[str, Any]:
        """Generate time limits for offer."""
        # Default expiration times based on airline
        default_expiration_hours = {
            'EK': 24,
            'QR': 24,
            'KL': 12,
            'AF': 12,
            'LHG': 8,
            'ET': 6,
            'KQ': 4
        }
        
        hours = default_expiration_hours.get(airline_code, 6)
        expiration_time = datetime.now() + timedelta(hours=hours)
        
        return {
            'offer_expiration': expiration_time.isoformat(),
            'payment_deadline': (expiration_time - timedelta(hours=1)).isoformat(),
            'booking_deadline': (expiration_time - timedelta(minutes=30)).isoformat()
        }
    
    def _get_airline_price_rank(self, card: Dict[str, Any], all_cards: List[Dict[str, Any]]) -> int:
        """Get price rank for airline among all airlines."""
        airline_code = card.get('airline', {}).get('code', '??')
        price = card.get('price', 0)
        
        # Get best price for each airline
        airline_best_prices = {}
        for other_card in all_cards:
            other_airline = other_card.get('airline', {}).get('code', '??')
            other_price = other_card.get('price', 0)
            
            if other_airline not in airline_best_prices or other_price < airline_best_prices[other_airline]:
                airline_best_prices[other_airline] = other_price
        
        # Rank airlines by their best price
        sorted_airlines = sorted(airline_best_prices.items(), key=lambda x: x[1])
        
        for rank, (airline, _) in enumerate(sorted_airlines, 1):
            if airline == airline_code:
                return rank
        
        return len(sorted_airlines)
    
    def _get_airline_feature_rank(self, airline_code: str) -> int:
        """Get feature rank for airline."""
        try:
            all_airlines = AirlineMappingService.get_supported_airlines()

            # Sort airlines by feature count
            airline_features = []
            for code in all_airlines:
                feature_count = len(AirlineMappingService.get_airline_info(code).get('supported_features', []))
                airline_features.append((code, feature_count))

            sorted_airlines = sorted(airline_features, key=lambda x: x[1], reverse=True)

            for rank, (code, _) in enumerate(sorted_airlines, 1):
                if code == airline_code:
                    return rank

            return len(sorted_airlines)
        except Exception as e:
            logger.error(f"Error calculating airline feature rank for {airline_code}: {e}")
            return 5  # Default middle rank
    
    def _get_competitive_advantages(self, card: Dict[str, Any], all_cards: List[Dict[str, Any]]) -> List[str]:
        """Get competitive advantages for this card."""
        advantages = []
        airline_code = card.get('airline', {}).get('code', '??')
        price = card.get('price', 0)
        
        # Check if this is the lowest price
        min_price = min(other_card.get('price', float('inf')) for other_card in all_cards)
        if price == min_price:
            advantages.append('lowest_price')
        
        # Check feature advantages
        feature_count = len(AirlineMappingService.get_airline_info(airline_code).get('supported_features', []))
        max_features = max(
            len(AirlineMappingService.get_airline_info(other_card.get('airline', {}).get('code', '??')).get('supported_features', []))
            for other_card in all_cards
        )
        
        if feature_count == max_features:
            advantages.append('most_features')
        
        # Check airline priority
        priority = self._calculate_airline_priority(airline_code)
        if priority >= 8:
            advantages.append('premium_airline')
        
        return advantages
    
    def _get_price_comparison(self, card: Dict[str, Any], all_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get price comparison information."""
        price = card.get('price', 0)
        all_prices = [other_card.get('price', 0) for other_card in all_cards]
        
        min_price = min(all_prices)
        max_price = max(all_prices)
        avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
        
        return {
            'is_lowest': price == min_price,
            'is_highest': price == max_price,
            'vs_average': round(((price - avg_price) / avg_price * 100), 1) if avg_price > 0 else 0,
            'vs_lowest': round(((price - min_price) / min_price * 100), 1) if min_price > 0 else 0,
            'savings_vs_highest': round(max_price - price, 2) if max_price > price else 0
        }
    
    def _is_best_price_for_airline(self, card: Dict[str, Any], airline_cards: List[Dict[str, Any]]) -> bool:
        """Check if this is the best price for this airline."""
        price = card.get('price', 0)
        min_airline_price = min(other_card.get('price', float('inf')) for other_card in airline_cards)
        return price == min_airline_price
    
    def _has_best_features_for_airline(self, airline_code: str) -> bool:
        """Check if this airline has the best features."""
        feature_count = len(AirlineMappingService.get_airline_info(airline_code).get('supported_features', []))
        return feature_count >= 8  # Threshold for "best features"


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
