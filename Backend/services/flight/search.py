"""
Flight Search Module

This module handles flight search operations using the Verteil NDC API.
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import uuid
import sys
import os

# Add the scripts directory to the path to import the request builder
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts'))
from build_airshopping_rq import build_airshopping_request

from .core import FlightService
from .decorators import async_cache, async_rate_limited
from .exceptions import FlightServiceError, ValidationError
from .types import SearchCriteria, FlightSearchResponse, ODSegment

logger = logging.getLogger(__name__)

class FlightSearchService(FlightService):
    """Service for handling flight search operations."""
    
    @async_rate_limited(limit=100, window=60)
    @async_cache(timeout=300)
    async def search_flights(self, criteria: SearchCriteria) -> FlightSearchResponse:
        """
        Search for flights based on the given criteria.
        
        Args:
            criteria: Search criteria including trip type, segments, passengers, etc.
            
        Returns:
            FlightSearchResponse containing search results or error information
            
        Raises:
            ValidationError: If the search criteria are invalid
            APIError: If there's an error communicating with the API
        """
        try:
            # Validate input
            self._validate_search_criteria(criteria)
            
            # Generate a request ID if not provided
            request_id = criteria.get('request_id', str(uuid.uuid4()))
            
            # Build the request payload
            payload = self._build_search_payload(criteria)
            
            # Make the API request
            response = await self._make_request(
                endpoint='/entrygate/rest/request:airShopping',
                payload=payload,
                service_name='AirShopping',
                request_id=request_id
            )
            
            # Process and return the response
            return {
                'status': 'success',
                'data': self._process_search_response(response),
                'request_id': request_id
            }
            
        except ValidationError as e:
            logger.error(f"Validation error in search_flights: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'request_id': criteria.get('request_id')
            }
        except Exception as e:
            logger.error(f"Error in search_flights: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': f"Failed to search flights: {str(e)}",
                'request_id': criteria.get('request_id')
            }
    
    def _validate_search_criteria(self, criteria: SearchCriteria) -> None:
        if not criteria.get('odSegments'): # Changed to camelCase
            raise ValidationError("At least one origin-destination segment is required")
            
        for segment in criteria['odSegments']: # Changed to camelCase
            if not all(key in segment for key in ['origin', 'destination', 'departureDate']): # Ensure these nested keys are also correct (they seem to be from your logs)
                raise ValidationError("Each segment must include origin, destination, and departureDate")
    
    def _build_search_payload(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """
        Build the AirShopping request payload from search criteria using the request builder.
        
        Args:
            criteria: Search criteria
            
        Returns:
            Dictionary containing the request payload
        """
        try:
            # Extract trip type from criteria, default to ONE_WAY
            trip_type = criteria.get('trip_type', 'ONE_WAY').upper()
            
            # Map trip types to the expected format
            trip_type_mapping = {
                'ONEWAY': 'ONE_WAY',
                'ONE_WAY': 'ONE_WAY',
                'ROUNDTRIP': 'ROUND_TRIP', 
                'ROUND_TRIP': 'ROUND_TRIP',
                'MULTICITY': 'MULTI_CITY',
                'MULTI_CITY': 'MULTI_CITY'
            }
            
            trip_type = trip_type_mapping.get(trip_type, 'ONE_WAY')
            
            # Build segments for the request and extract cabin preferences
            od_segments = []
            cabin_preferences_per_segment = []
            
            # Map cabin preference to the expected codes
            cabin_mapping = {
                'ECONOMY': 'Y',
                'BUSINESS': 'C', 
                'FIRST': 'F',
                'PREMIUM_ECONOMY': 'W'
            }
            
            for seg in criteria['odSegments']:
                od_segments.append({
                    'Origin': seg['origin'],
                    'Destination': seg['destination'],
                    'DepartureDate': seg['departureDate']
                })
                
                # Extract cabin preference for this segment
                if 'cabinPreference' in seg:
                    segment_cabin_code = cabin_mapping.get(seg['cabinPreference'].upper(), 'Y')
                    cabin_preferences_per_segment.append(segment_cabin_code)
                else:
                    # Fallback to global cabin preference
                    global_cabin_preference = criteria.get('cabinPreference', 'ECONOMY')
                    segment_cabin_code = cabin_mapping.get(global_cabin_preference.upper(), 'Y')
                    cabin_preferences_per_segment.append(segment_cabin_code)
            
            # Use per-segment cabin preferences if available, otherwise fallback to single cabin code
            cabin_preference = criteria.get('cabinPreference', 'ECONOMY')
            fallback_cabin_code = cabin_mapping.get(cabin_preference.upper(), 'Y')
            
            # Get passenger counts (handle both camelCase and snake_case)
            num_adults = criteria.get('numAdults', criteria.get('num_adults', 1))
            num_children = criteria.get('numChildren', criteria.get('num_children', 0))
            num_infants = criteria.get('numInfants', criteria.get('num_infants', 0))
            
            # Use the request builder to create the payload
            payload = build_airshopping_request(
                trip_type=trip_type,
                od_segments=od_segments,
                num_adults=num_adults,
                num_children=num_children,
                num_infants=num_infants,
                cabin_preference_code=fallback_cabin_code,
                cabin_preferences=cabin_preferences_per_segment,
                fare_type_code="PUBL"
            )
            
            logger.info(f"Built AirShopping payload for {trip_type} with {len(od_segments)} segments")
            return payload
            
        except Exception as e:
            logger.error(f"Error building AirShopping payload: {str(e)}")
            raise ValidationError(f"Failed to build search payload: {str(e)}") from e
    
    def _process_search_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the AirShopping API response with enhanced structure for frontend display.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response data with enhanced flight information and metadata
        """
        # Extract ShoppingResponseID from metadata structure
        shopping_response_id = self._extract_shopping_response_id(response)
        
        processed = {
            'offers': [],
            'shopping_response_id': shopping_response_id,
            'transaction_id': response.get('TransactionID'),
            'metadata': {
                'total_offers': 0,
                'search_timestamp': time.time(),
                'currency': 'USD',  # Default currency
                'search_criteria': response.get('SearchCriteria', {})
            },
            'raw_response': response  # Store complete response for pricing requests
        }
        
        # Process offers from the response
        if 'OffersGroup' in response and 'AirlineOffers' in response['OffersGroup']:
            airline_offers = response['OffersGroup']['AirlineOffers']
            if not isinstance(airline_offers, list):
                airline_offers = [airline_offers]
                
            for airline_offer_group in airline_offers:
                # Each airline_offer_group contains an AirlineOffer array
                if 'AirlineOffer' in airline_offer_group:
                    airline_offers_list = airline_offer_group['AirlineOffer']
                    if not isinstance(airline_offers_list, list):
                        airline_offers_list = [airline_offers_list]
                    
                    for offer in airline_offers_list:
                        # Extract OfferID from the offer
                        offer_id = offer.get('OfferID', {}).get('value', '') if isinstance(offer.get('OfferID'), dict) else offer.get('OfferID', '')
                        
                        processed_offer = {
                            'id': offer_id,
                            'offer_id': offer_id,
                            'price': self._extract_price_info_from_priced_offer(offer.get('PricedOffer', {})),
                            'flights': [],
                            'offer_items': offer.get('OfferItem', []),  # Store offer items for pricing
                            'airline': self._extract_airline_info(airline_offer_group),
                            'booking_class': offer.get('BookingClass', 'ECONOMY'),
                            'fare_basis': offer.get('FareBasis', ''),
                            'refundable': offer.get('Refundable', False),
                            'changeable': offer.get('Changeable', False),
                            'total_price': offer.get('TotalPrice', {})
                        }
                        
                        # Extract flight segments from PricedOffer structure
                        self._extract_flight_segments_from_priced_offer(offer.get('PricedOffer', {}), processed_offer, response)
                        
                        # Calculate total journey time and stops
                        if processed_offer['flights']:
                            processed_offer['total_duration'] = sum(f['duration'] for f in processed_offer['flights'])
                            processed_offer['total_stops'] = sum(f['stops'] for f in processed_offer['flights'])
                            processed_offer['is_direct'] = processed_offer['total_stops'] == 0
                        
                        processed['offers'].append(processed_offer)
        
        processed['metadata']['total_offers'] = len(processed['offers'])
        
        # Sort offers by price (lowest first)
        processed['offers'].sort(key=lambda x: x.get('price', {}).get('total', float('inf')))
        
        return processed
    
    def _extract_shopping_response_id(self, response: Dict[str, Any]) -> str:
        """
        Extract ShoppingResponseID from the metadata structure.
        
        Args:
            response: Raw API response
            
        Returns:
            ShoppingResponseID string or None if not found
        """
        try:
            # Navigate to the metadata structure
            metadata = response.get('Metadata', {})
            other_metadata = metadata.get('Other', {})
            
            if isinstance(other_metadata, dict):
                other_metadata_list = other_metadata.get('OtherMetadata', [])
                if not isinstance(other_metadata_list, list):
                    other_metadata_list = [other_metadata_list]
                
                for other_meta in other_metadata_list:
                    if isinstance(other_meta, dict):
                        desc_metadatas = other_meta.get('DescriptionMetadatas', {})
                        desc_metadata_list = desc_metadatas.get('DescriptionMetadata', [])
                        
                        if not isinstance(desc_metadata_list, list):
                            desc_metadata_list = [desc_metadata_list]
                        
                        for desc_metadata in desc_metadata_list:
                            if isinstance(desc_metadata, dict) and desc_metadata.get('MetadataKey') == 'SHOPPING_RESPONSE_IDS':
                                aug_point = desc_metadata.get('AugmentationPoint', {})
                                aug_points = aug_point.get('AugPoint', [])
                                
                                if not isinstance(aug_points, list):
                                    aug_points = [aug_points]
                                
                                for point in aug_points:
                                    if isinstance(point, dict):
                                        shopping_id = point.get('Key')
                                        if shopping_id:
                                            logger.info(f"Found ShoppingResponseID: {shopping_id}")
                                            return shopping_id
            
            logger.warning("ShoppingResponseID not found in metadata structure")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting ShoppingResponseID: {str(e)}")
            return None

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration string (e.g., "PT1H30M") to minutes.
        
        Args:
            duration_str: ISO 8601 duration string
            
        Returns:
            Duration in minutes
        """
        import re
        
        if not duration_str or duration_str == 'PT0H0M':
            return 0
            
        minutes = 0
        
        # Extract hours
        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            minutes += int(hour_match.group(1)) * 60
            
        # Extract minutes
        minute_match = re.search(r'(\d+)M', duration_str)
        if minute_match:
            minutes += int(minute_match.group(1))
            
        return minutes
    
    def _format_duration(self, duration_str: str) -> str:
        """
        Format duration string for display (e.g., "1h 30m").
        
        Args:
            duration_str: ISO 8601 duration string
            
        Returns:
            Formatted duration string
        """
        total_minutes = self._parse_duration(duration_str)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "0m"
    
    def _extract_price_info(self, price_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and structure price information.
        
        Args:
            price_info: Raw price information from API
            
        Returns:
            Structured price information
        """
        if not price_info:
            return {'total': 0, 'currency': 'USD', 'breakdown': {}}
            
        # Handle different price structures
        total_price = 0
        currency = 'USD'
        breakdown = {}
        
        if 'TotalAmount' in price_info:
            total_price = float(price_info['TotalAmount'].get('Value', 0))
            currency = price_info['TotalAmount'].get('Code', 'USD')
        elif 'BaseAmount' in price_info:
            total_price = float(price_info['BaseAmount'].get('Value', 0))
            currency = price_info['BaseAmount'].get('Code', 'USD')
            
        # Extract fare breakdown if available
        if 'FareDetail' in price_info:
            fare_detail = price_info['FareDetail']
            breakdown = {
                'base_fare': fare_detail.get('BaseFare', {}).get('Value', 0),
                'taxes': fare_detail.get('Taxes', {}).get('Value', 0),
                'fees': fare_detail.get('Fees', {}).get('Value', 0)
            }
            
        return {
            'total': total_price,
            'currency': currency,
            'breakdown': breakdown,
            'formatted': f"{currency} {total_price:,.2f}"
        }
    
    def _extract_airline_info(self, offer: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract airline information from offer.
        
        Args:
            offer: Flight offer data
            
        Returns:
            Airline information
        """
        airline_code = ''
        
        # Try to get airline from flight segments
        if 'FlightSegment' in offer:
            segments = offer['FlightSegment']
            if not isinstance(segments, list):
                segments = [segments]
            if segments:
                airline_code = segments[0].get('MarketingAirline', {}).get('AirlineID', '')
        
        return {
            'code': airline_code,
            'name': self._get_airline_name(airline_code)
        }
    
    def _get_airline_name(self, airline_code: str) -> str:
        """
        Get airline name from airline code using the comprehensive airline data.
        
        Args:
            airline_code: IATA airline code
            
        Returns:
            Airline name or a generic name with the code if not found
        """
        try:
            # Import the get_airline_name function from utils.airline_data
            from utils.airline_data import get_airline_name
            
            # Get the airline name using the centralized function
            return get_airline_name(airline_code, log_missing=False)
            
        except ImportError as e:
            # Fallback to a simple mapping if the import fails
            logger.warning(f"Could not import get_airline_name: {str(e)}")
            airline_map = {
                'AA': 'American Airlines',
                'DL': 'Delta Air Lines',
                'UA': 'United Airlines',
                'BA': 'British Airways',
                'LH': 'Lufthansa',
                'AF': 'Air France',
                'KL': 'KLM Royal Dutch Airlines',
                'WA': 'Western Airlines',
                'EK': 'Emirates',
                'QR': 'Qatar Airways',
                'SQ': 'Singapore Airlines',
                'CX': 'Cathay Pacific',
                'TK': 'Turkish Airlines',
                'LX': 'Swiss International Air Lines',
                'OS': 'Austrian Airlines',
                'SN': 'Brussels Airlines',
                'AI': 'Air India',
                '6E': 'IndiGo',
                'UK': 'Vistara',
                'SG': 'SpiceJet',
                'AC': 'Air Canada',
                'VS': 'Virgin Atlantic',
                'JL': 'Japan Airlines',
                'NH': 'All Nippon Airways',
                'QF': 'Qantas',
                'G8': 'Go Air',
                'KQ': 'Kenya Airways',
                'EY': 'Etihad Airways',
                'WN': 'Southwest Airlines',
                'AS': 'Alaska Airlines',
                'HA': 'Hawaiian Airlines',
                'F9': 'Frontier Airlines',
                'B6': 'JetBlue Airways',
                'NK': 'Spirit Airlines',
                'VB': 'VivaAerobus',
                'AM': 'Aeromexico',
                'WS': 'WestJet',
                'GA': 'Garuda Indonesia',
                'MH': 'Malaysia Airlines',
                'PR': 'Philippine Airlines',
                'BR': 'EVA Air',
                'CI': 'China Airlines',
                'NZ': 'Air New Zealand',
                'VA': 'Virgin Australia',
                'FZ': 'flydubai',
                'G9': 'Air Arabia',
                'JQ': 'Jetstar',
                '3U': 'Sichuan Airlines',
                'HU': 'Hainan Airlines',
                'SC': 'Shandong Airlines',
                'FM': 'Shanghai Airlines',
                'MF': 'Xiamen Airlines',
                'KY': 'Kunming Airlines',
                'CZ': 'China Southern Airlines',
                'MU': 'China Eastern Airlines',
                'CA': 'Air China',
                '8L': 'Lucky Air',
                '9C': 'Spring Airlines',
                'HO': 'Juneyao Airlines',
                'GS': 'Tianjin Airlines',
                'PN': 'China West Air',
                'G5': 'China Express Airlines',
                'EU': 'Chengdu Airlines',
                'DR': 'Ruili Airlines',
                'UQ': 'Urumqi Air',
                'A6': 'Air Travel',
                'GT': 'Guangxi Beibu Gulf Airlines',
                'QW': 'Qingdao Airlines',
                'LT': 'LongJiang Airlines',
                'GJ': 'Loong Air',
                'RY': 'Jiangxi Air',
                'VD': 'Henan Airlines',
                'DZ': 'Donghai Airlines',
                'GX': 'GX Airlines'
            }
            return airline_map.get(airline_code, f"Airline {airline_code}")
    
    def _extract_price_info_from_priced_offer(self, priced_offer: dict) -> dict:
        """
        Extract price information from PricedOffer structure.
        
        Args:
            priced_offer: PricedOffer data from the response
            
        Returns:
            Formatted price information
        """
        price_info = {
            'total': 0,
            'base': 0,
            'taxes': 0,
            'currency': 'USD',
            'discount': 0
        }
        
        if 'OfferPrice' in priced_offer:
            offer_prices = priced_offer['OfferPrice']
            if not isinstance(offer_prices, list):
                offer_prices = [offer_prices]
            
            for offer_price in offer_prices:
                if 'PriceDetail' in offer_price:
                    price_detail = offer_price['PriceDetail']
                    
                    # Extract total amount
                    if 'TotalAmount' in price_detail:
                        total_amount = price_detail['TotalAmount']
                        if 'SimpleCurrencyPrice' in total_amount:
                            price_info['total'] = total_amount['SimpleCurrencyPrice'].get('value', 0)
                            price_info['currency'] = total_amount['SimpleCurrencyPrice'].get('Code', 'USD')
                    
                    # Extract base amount
                    if 'BaseAmount' in price_detail:
                        base_amount = price_detail['BaseAmount']
                        price_info['base'] = base_amount.get('value', 0)
                    
                    # Extract taxes
                    if 'Taxes' in price_detail and 'Total' in price_detail['Taxes']:
                        taxes = price_detail['Taxes']['Total']
                        price_info['taxes'] = taxes.get('value', 0)
                    
                    # Extract discount
                    if 'Discount' in price_detail:
                        discounts = price_detail['Discount']
                        if not isinstance(discounts, list):
                            discounts = [discounts]
                        
                        total_discount = 0
                        for discount in discounts:
                            if 'DiscountAmount' in discount:
                                total_discount += discount['DiscountAmount'].get('value', 0)
                        price_info['discount'] = total_discount
        
        return price_info
    
    def _extract_flight_segments_from_priced_offer(self, priced_offer: dict, processed_offer: dict, full_response: dict):
        """
        Extract flight segments from PricedOffer structure and add them to processed_offer.
        
        Args:
            priced_offer: PricedOffer data from the response
            processed_offer: The offer being processed
            full_response: The complete API response containing DataLists
        """
        if 'OfferPrice' in priced_offer:
            offer_prices = priced_offer['OfferPrice']
            if not isinstance(offer_prices, list):
                offer_prices = [offer_prices]
            
            for offer_price in offer_prices:
                if 'RequestedDate' in offer_price and 'Associations' in offer_price['RequestedDate']:
                    associations = offer_price['RequestedDate']['Associations']
                    if not isinstance(associations, list):
                        associations = [associations]
                    
                    for association in associations:
                        if 'ApplicableFlight' in association:
                            applicable_flight = association['ApplicableFlight']
                            
                            # Extract flight segment references
                            if 'FlightSegmentReference' in applicable_flight:
                                segment_refs = applicable_flight['FlightSegmentReference']
                                if not isinstance(segment_refs, list):
                                    segment_refs = [segment_refs]
                                
                                for segment_ref in segment_refs:
                                    segment_id = segment_ref.get('ref', '')
                                    
                                    # Look up actual segment details from DataLists
                                    segment_details = self._get_flight_segment_details(segment_id, full_response)
                                     
                                    if segment_details:
                                         processed_offer['flights'].append(segment_details)
    
    def _get_flight_segment_details(self, segment_id: str, full_response: dict) -> dict:
        """
        Get flight segment details from the DataLists section of the response.
        
        Args:
            segment_id: The segment reference ID
            full_response: The complete API response containing DataLists
            
        Returns:
            Processed flight segment details
        """
        # Look up segment in DataLists
        if 'DataLists' in full_response and 'FlightSegmentList' in full_response['DataLists']:
            flight_segments = full_response['DataLists']['FlightSegmentList'].get('FlightSegment', [])
            if not isinstance(flight_segments, list):
                flight_segments = [flight_segments]
            
            for segment in flight_segments:
                if segment.get('SegmentKey') == segment_id:
                    # Extract departure information
                    departure = segment.get('Departure', {})
                    departure_airport = departure.get('AirportCode', {})
                    departure_airport_code = departure_airport.get('value', '') if isinstance(departure_airport, dict) else departure_airport
                    
                    # Extract arrival information
                    arrival = segment.get('Arrival', {})
                    arrival_airport = arrival.get('AirportCode', {})
                    arrival_airport_code = arrival_airport.get('value', '') if isinstance(arrival_airport, dict) else arrival_airport
                    
                    # Extract airline information
                    marketing_carrier = segment.get('MarketingCarrier', {})
                    airline_id = marketing_carrier.get('AirlineID', {})
                    airline_code = airline_id.get('value', '') if isinstance(airline_id, dict) else airline_id
                    airline_name = marketing_carrier.get('Name', '')
                    
                    # Extract flight number
                    flight_number_obj = marketing_carrier.get('FlightNumber', {})
                    flight_number = flight_number_obj.get('value', '') if isinstance(flight_number_obj, dict) else flight_number_obj
                    
                    # Extract duration
                    flight_detail = segment.get('FlightDetail', {})
                    duration_obj = flight_detail.get('FlightDuration', {})
                    duration_str = duration_obj.get('Value', 'PT0H0M') if isinstance(duration_obj, dict) else duration_obj
                    
                    return {
                        'segment_id': segment_id,
                        'departure': {
                            'airport': departure_airport_code,
                            'city': self._get_city_name(departure_airport_code),
                            'time': departure.get('Time', ''),
                            'date': departure.get('Date', ''),
                            'terminal': departure.get('Terminal', {}).get('Name', '') if isinstance(departure.get('Terminal'), dict) else departure.get('Terminal', '')
                        },
                        'arrival': {
                            'airport': arrival_airport_code,
                            'city': self._get_city_name(arrival_airport_code),
                            'time': arrival.get('Time', ''),
                            'date': arrival.get('Date', ''),
                            'terminal': arrival.get('Terminal', {}).get('Name', '') if isinstance(arrival.get('Terminal'), dict) else arrival.get('Terminal', '')
                        },
                        'airline': {
                            'code': airline_code,
                            'name': airline_name or self._get_airline_name(airline_code)
                        },
                        'flight_number': flight_number,
                        'aircraft': segment.get('Equipment', {}).get('AircraftCode', ''),
                        'cabin_class': 'ECONOMY',  # This would need to be extracted from fare details
                        'booking_class': '',  # This would need to be extracted from fare details
                        'duration': self._parse_duration(duration_str),
                        'duration_formatted': self._format_duration(duration_str),
                        'stops': 0,  # Direct flight, stops would be calculated based on connections
                        'meal_service': '',
                        'baggage_allowance': {}
                    }
        
        # Return basic structure if segment not found
        return {
            'segment_id': segment_id,
            'departure': {
                'airport': '',
                'city': '',
                'time': '',
                'date': '',
                'terminal': ''
            },
            'arrival': {
                'airport': '',
                'city': '',
                'time': '',
                'date': '',
                'terminal': ''
            },
            'airline': {
                'code': '',
                'name': ''
            },
            'flight_number': '',
            'aircraft': '',
            'cabin_class': 'ECONOMY',
            'booking_class': '',
            'duration': 0,
            'duration_formatted': '0h 0m',
            'stops': 0,
            'meal_service': '',
            'baggage_allowance': {}
        }

    def _get_city_name(self, airport_code: str) -> str:
        """
        Get city name from airport code.
        
        Args:
            airport_code: IATA airport code
            
        Returns:
            City name or the airport code if not found
        """
        airport_map = {
            'JFK': 'New York',
            'LAX': 'Los Angeles',
            'LHR': 'London',
            'CDG': 'Paris',
            'FRA': 'Frankfurt',
            'DEL': 'Delhi',
            'BOM': 'Mumbai',
            'SIN': 'Singapore',
            'HKG': 'Hong Kong',
            'DXB': 'Dubai',
            'ZRH': 'Zurich',
            'MUC': 'Munich',
            'AMS': 'Amsterdam',
            'ATL': 'Atlanta',
            'PEK': 'Beijing',
            'CAN': 'Guangzhou',
            'DFW': 'Dallas',
            'ORD': 'Chicago',
            'SFO': 'San Francisco',
            'EWR': 'Newark',
            'IAH': 'Houston',
            'BOS': 'Boston',
            'CLT': 'Charlotte',
            'PHX': 'Phoenix',
            'PHL': 'Philadelphia',
            'MIA': 'Miami',
            'JFK': 'New York',
            'LAX': 'Los Angeles',

        }
        
        return airport_map.get(airport_code, airport_code)
    

# Helper functions for backward compatibility
async def search_flights(
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: str = "ECONOMY",
    fare_type: str = "PBL",
    request_id: Optional[str] = None,
    trip_type: str = "ONE_WAY",
    od_segments: Optional[List[Dict[str, str]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> FlightSearchResponse:
    """
    Search for flights with the given criteria.
    
    This is a backward-compatible wrapper around the FlightSearchService.
    """
    if od_segments is None:
        od_segments = []
        
    criteria = {
        'trip_type': trip_type,
        'odSegments': od_segments,
        'num_adults': adults,
        'num_children': children,
        'num_infants': infants,
        'cabin_preference': cabin_class,
        'fare_type': fare_type,
        'request_id': request_id
    }
    
    effective_config = config
    if effective_config is None:
        logger.warning("Config not passed to search_flights_sync, attempting to use current_app.config.")
        try:
            from quart import current_app
            effective_config = current_app.config
        except (RuntimeError, ImportError):
            logger.error("Cannot access current_app.config in search_flights.")
            raise FlightServiceError("Configuration not available for FlightSearchService in search_flights.")
    
    if not effective_config: # Handle case where config might be an empty dict
        logger.error("Effective config is empty in search_flights.")
        raise FlightServiceError("Effective configuration is empty for FlightSearchService in search_flights.")

    logger.info(f"Config for FlightSearchService in search_flights: USERNAME={effective_config.get('VERTEIL_USERNAME')}, PASSWORD_PRESENT={'yes' if effective_config.get('VERTEIL_PASSWORD') else 'no'}")
    # Use a single service instance to avoid creating multiple TokenManager instances
    service = FlightSearchService(effective_config)
    try:
        return await service.search_flights(criteria)
    finally:
        await service.close()


async def process_air_shopping(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process air shopping request with enhanced response structure and storage.
    
    This function provides enhanced flight search capabilities with:
    - Structured response data for frontend display
    - Response caching for subsequent pricing requests
    - Enhanced error handling and validation
    - Data transformation from Verteil API to frontend-compatible format
    
    Args:
        search_criteria: Search criteria dictionary
        
    Returns:
        Enhanced flight search response with structured offers
    """
    import time
    from utils.cache_manager import cache_manager
    from utils.data_transformer import transform_verteil_to_frontend
    
    effective_config: Optional[Dict[str, Any]] = None
    logger.info("Processing air shopping request with enhanced features")
    
    # Add debug logging for search criteria
    logger.info(f"[DEBUG] Search criteria received in process_air_shopping: {search_criteria}")
    
    try:
        from quart import current_app
        effective_config = current_app.config
    except (RuntimeError, ImportError):
        logger.error("Cannot access current_app.config in process_air_shopping.")
        raise FlightServiceError("Configuration not available for FlightSearchService in process_air_shopping.")

    if not effective_config:
        logger.error("Effective config is empty in process_air_shopping.")
        raise FlightServiceError("Effective configuration is empty for FlightSearchService in process_air_shopping.")

    logger.info(f"Config for FlightSearchService: USERNAME={effective_config.get('VERTEIL_USERNAME')}, PASSWORD_PRESENT={'yes' if effective_config.get('VERTEIL_PASSWORD') else 'no'}")
    
    # Generate cache key for this search
    request_id = search_criteria.get('request_id', str(uuid.uuid4()))
    cache_key = f"air_shopping_response:{request_id}"
    
    service = FlightSearchService(effective_config)
    try:
        # Perform the search
        result = await service.search_flights(search_criteria)
        
        # If successful, transform data and store the response for subsequent pricing requests
        if result.get('status') == 'success' and result.get('data'):
            # Transform Verteil API response to frontend-compatible format
            raw_response = result['data'].get('raw_response', {})
            if raw_response:
                logger.info("Transforming Verteil API response to frontend format")
                # Check if round trip transformation is enabled
                enable_roundtrip = search_criteria.get('enableRoundtrip', False)
                transformed_data = transform_verteil_to_frontend(raw_response, enable_roundtrip=enable_roundtrip)
                
                # Extract offers from the transformed data (now returns a dict with 'offers' and 'reference_data')
                if isinstance(transformed_data, dict) and 'offers' in transformed_data:
                    offers_list = transformed_data['offers']
                    reference_data = transformed_data.get('reference_data', {})
                else:
                    # Fallback for backward compatibility
                    offers_list = transformed_data if isinstance(transformed_data, list) else []
                    reference_data = {}
                
                # Apply filtering and sorting if specified
                filtered_offers = _apply_filters_and_sorting(offers_list, search_criteria)
                
                # Add filtered and sorted offers to the result
                result['data']['offers'] = filtered_offers
                result['data']['total_offers'] = len(filtered_offers)
                result['data']['total_unfiltered_offers'] = len(offers_list)
                result['data']['reference_data'] = reference_data
                
                logger.info(f"Successfully transformed {len(offers_list)} flight offers, {len(filtered_offers)} after filtering")
            else:
                logger.warning("No response data found for transformation")
                result['data']['offers'] = []
                result['data']['total_offers'] = 0
                result['data']['total_unfiltered_offers'] = 0
            
            # Store the complete response for 30 minutes
            cache_manager.set(cache_key, result['data'], ttl=1800)
            
            # Also store with shopping_response_id for easy retrieval
            shopping_response_id = result['data'].get('shopping_response_id')
            if shopping_response_id:
                shopping_cache_key = f"air_shopping_by_id:{shopping_response_id}"
                cache_manager.set(shopping_cache_key, result['data'], ttl=1800)
                
            logger.info(f"Stored air shopping response in cache with keys: {cache_key}, {shopping_cache_key if shopping_response_id else 'N/A'}")
            
            # Add cache information to response metadata
            if 'metadata' not in result['data']:
                result['data']['metadata'] = {}
            result['data']['metadata']['cached'] = True
            result['data']['metadata']['cache_key'] = cache_key
            result['data']['metadata']['expires_at'] = time.time() + 1800
        
        return result
        
    except Exception as e:
        logger.error(f"Error in enhanced process_air_shopping: {str(e)}", exc_info=True)
        raise
    finally:
        await service.close()


def _apply_filters_and_sorting(offers: List[Dict[str, Any]], search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Apply filtering and sorting to flight offers based on search criteria.
    
    Args:
        offers: List of transformed flight offers
        search_criteria: Search criteria containing filters and sorting options
        
    Returns:
        Filtered and sorted list of flight offers
    """
    filtered_offers = offers.copy()
    filters = search_criteria.get('filters', {})
    
    # Apply price range filter
    if 'priceRange' in filters:
        price_range = filters['priceRange']
        min_price = price_range.get('min')
        max_price = price_range.get('max')
        
        if min_price is not None or max_price is not None:
            filtered_offers = [
                offer for offer in filtered_offers
                if _price_in_range(offer.get('totalPrice', {}).get('amount', 0), min_price, max_price)
            ]
            logger.info(f"Applied price filter: {len(offers)} -> {len(filtered_offers)} offers")
    
    # Apply airlines filter
    if 'airlines' in filters and filters['airlines']:
        airline_codes = [code.upper() for code in filters['airlines']]
        filtered_offers = [
            offer for offer in filtered_offers
            if any(segment.get('airline', {}).get('code', '').upper() in airline_codes 
                  for itinerary in offer.get('itineraries', [])
                  for segment in itinerary.get('segments', []))
        ]
        logger.info(f"Applied airlines filter {airline_codes}: {len(offers)} -> {len(filtered_offers)} offers")
    
    # Apply max stops filter
    if 'maxStops' in filters:
        max_stops = filters['maxStops']
        filtered_offers = [
            offer for offer in filtered_offers
            if all(len(itinerary.get('segments', [])) - 1 <= max_stops 
                  for itinerary in offer.get('itineraries', []))
        ]
        logger.info(f"Applied max stops filter ({max_stops}): {len(offers)} -> {len(filtered_offers)} offers")
    
    # Apply departure time range filter
    if 'departureTimeRange' in filters:
        time_range = filters['departureTimeRange']
        min_time = time_range.get('min')
        max_time = time_range.get('max')
        
        if min_time or max_time:
            filtered_offers = [
                offer for offer in filtered_offers
                if _departure_time_in_range(offer, min_time, max_time)
            ]
            logger.info(f"Applied departure time filter: {len(offers)} -> {len(filtered_offers)} offers")
    
    # Apply sorting
    sort_by = search_criteria.get('sortBy', 'price')
    sort_order = search_criteria.get('sortOrder', 'asc')
    
    if sort_by and filtered_offers:
        reverse_order = sort_order == 'desc'
        
        if sort_by == 'price':
            filtered_offers.sort(key=lambda x: x.get('totalPrice', {}).get('amount', 0), reverse=reverse_order)
        elif sort_by == 'duration':
            filtered_offers.sort(key=lambda x: _get_total_duration(x), reverse=reverse_order)
        elif sort_by == 'departure':
            filtered_offers.sort(key=lambda x: _get_earliest_departure(x), reverse=reverse_order)
        elif sort_by == 'arrival':
            filtered_offers.sort(key=lambda x: _get_latest_arrival(x), reverse=reverse_order)
        elif sort_by == 'stops':
            filtered_offers.sort(key=lambda x: _get_max_stops(x), reverse=reverse_order)
        
        logger.info(f"Applied sorting: {sort_by} {sort_order}")
    
    return filtered_offers


def _price_in_range(price: float, min_price: Optional[float], max_price: Optional[float]) -> bool:
    """Check if price is within the specified range."""
    if min_price is not None and price < min_price:
        return False
    if max_price is not None and price > max_price:
        return False
    return True


def _departure_time_in_range(offer: Dict[str, Any], min_time: Optional[str], max_time: Optional[str]) -> bool:
    """Check if departure time is within the specified range."""
    try:
        for itinerary in offer.get('itineraries', []):
            segments = itinerary.get('segments', [])
            if segments:
                departure_time = segments[0].get('departure', {}).get('time', '')
                if departure_time:
                    # Extract time part (HH:MM) from datetime string
                    time_part = departure_time.split('T')[1][:5] if 'T' in departure_time else departure_time[:5]
                    
                    if min_time and time_part < min_time:
                        return False
                    if max_time and time_part > max_time:
                        return False
        return True
    except Exception:
        return True  # If parsing fails, don't filter out


def _get_total_duration(offer: Dict[str, Any]) -> int:
    """Get total duration in minutes for sorting."""
    total_duration = 0
    for itinerary in offer.get('itineraries', []):
        duration_str = itinerary.get('duration', 'PT0M')
        total_duration += _parse_duration(duration_str)
    return total_duration


def _get_earliest_departure(offer: Dict[str, Any]) -> str:
    """Get earliest departure time for sorting."""
    earliest = '9999-12-31T23:59:59'
    for itinerary in offer.get('itineraries', []):
        segments = itinerary.get('segments', [])
        if segments:
            departure_time = segments[0].get('departure', {}).get('time', '')
            if departure_time and departure_time < earliest:
                earliest = departure_time
    return earliest


def _get_latest_arrival(offer: Dict[str, Any]) -> str:
    """Get latest arrival time for sorting."""
    latest = '0000-01-01T00:00:00'
    for itinerary in offer.get('itineraries', []):
        segments = itinerary.get('segments', [])
        if segments:
            arrival_time = segments[-1].get('arrival', {}).get('time', '')
            if arrival_time and arrival_time > latest:
                latest = arrival_time
    return latest


def _get_max_stops(offer: Dict[str, Any]) -> int:
    """Get maximum number of stops for sorting."""
    max_stops = 0
    for itinerary in offer.get('itineraries', []):
        stops = len(itinerary.get('segments', [])) - 1
        if stops > max_stops:
            max_stops = stops
    return max_stops


def _parse_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration string to minutes."""
    try:
        # Simple parser for PT1H30M format
        if not duration_str.startswith('PT'):
            return 0
        
        duration_str = duration_str[2:]  # Remove 'PT'
        hours = 0
        minutes = 0
        
        if 'H' in duration_str:
            hours_part, duration_str = duration_str.split('H')
            hours = int(hours_part)
        
        if 'M' in duration_str:
            minutes_part = duration_str.split('M')[0]
            minutes = int(minutes_part)
        
        return hours * 60 + minutes
    except Exception:
        return 0


def search_flights_sync(
    origin: str,
    destination: str, 
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: str = "ECONOMY",
    trip_type: str = "oneway",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for flight search.
    
    This function provides backward compatibility with the old synchronous interface.
    """
    import asyncio
    
    # Validate required parameters
    if not origin:
        raise FlightServiceError("Origin is required")
    if not destination:
        raise FlightServiceError("Destination is required") 
    if not departure_date:
        raise FlightServiceError("Departure date is required")
    
    # Build od_segments
    od_segments = [{
        'origin': origin,
        'destination': destination,
        'departureDate': departure_date
    }]
    
    if return_date and trip_type.lower() == 'roundtrip':
        od_segments.append({
            'origin': destination,
            'destination': origin,
            'departureDate': return_date
        })
    
    # Convert trip_type to expected format
    if trip_type.lower() in ['roundtrip', 'round_trip']:
        trip_type = 'ROUND_TRIP'
    else:
        trip_type = 'ONE_WAY'
    
    # Handle config - try to get from Quart app context if not provided
    effective_config = config
    if effective_config is None:
        try:
            from quart import current_app
            effective_config = current_app.config
        except (RuntimeError, ImportError):
            # If we can't get config, pass None and let the async function handle it
            effective_config = None
    
    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(search_flights(
        adults=adults,
        children=children,
        infants=infants,
        cabin_class=cabin_class,
        trip_type=trip_type,
        od_segments=od_segments,
        config=effective_config
    ))
    
    # Check if the result contains an error and raise an exception
    if isinstance(result, dict) and result.get('status') == 'error':
        raise FlightServiceError(result.get('error', 'Unknown error occurred'))
    
    return result
