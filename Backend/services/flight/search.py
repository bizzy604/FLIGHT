"""
Flight Search Module

This module handles flight search operations using the Verteil NDC API.
"""
import logging
from typing import Dict, Any, List, Optional
import uuid

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
                endpoint='airshopping',
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
        """
        Validate the search criteria.
        
        Args:
            criteria: Search criteria to validate
            
        Raises:
            ValidationError: If the criteria are invalid
        """
        if not criteria.get('od_segments'):
            raise ValidationError("At least one origin-destination segment is required")
            
        for segment in criteria['od_segments']:
            if not all(key in segment for key in ['origin', 'destination', 'departure_date']):
                raise ValidationError("Each segment must include origin, destination, and departure_date")
    
    def _build_search_payload(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """
        Build the AirShopping request payload from search criteria.
        
        Args:
            criteria: Search criteria
            
        Returns:
            Dictionary containing the request payload
        """
        # This is a simplified example - adapt based on the actual API requirements
        payload = {
            'OriginDestinations': [
                {
                    'OriginLocation': {
                        'LocationCode': seg['origin']
                    },
                    'DestinationLocation': {
                        'LocationCode': seg['destination']
                    },
                    'DepartureDateTime': seg['departure_date']
                }
                for seg in criteria['od_segments']
            ],
            'TravelPreferences': {
                'CabinPref': [
                    {
                        'CabinType': criteria.get('cabin_preference', 'ECONOMY'),
                        'PreferLevel': 'Preferred'
                    }
                ]
            },
            'TravelerInfoSummary': {
                'SeatsRequested': [
                    {
                        'Code': 'ADT',
                        'Quantity': criteria.get('num_adults', 1)
                    },
                    {
                        'Code': 'CHD',
                        'Quantity': criteria.get('num_children', 0)
                    },
                    {
                        'Code': 'INF',
                        'Quantity': criteria.get('num_infants', 0)
                    }
                ]
            }
        }
        
        return payload
    
    def _process_search_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the AirShopping API response.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response data with enhanced flight information
        """
        processed = {
            'offers': [],
            'shopping_response_id': response.get('ShoppingResponseID'),
            'transaction_id': response.get('TransactionID')
        }
        
        # Process offers from the response
        if 'OffersGroup' in response and 'AirlineOffers' in response['OffersGroup']:
            for offer in response['OffersGroup']['AirlineOffers']:
                processed_offer = {
                    'offer_id': offer.get('OfferID'),
                    'price_info': offer.get('PriceInfo', {}),
                    'flights': []
                }
                
                # Add flight segments
                if 'FlightSegment' in offer:
                    for segment in offer['FlightSegment']:
                        departure = segment.get('Departure', {})
                        arrival = segment.get('Arrival', {})
                        duration = segment.get('Duration', 'PT0H0M')  # Default to 0h 0m if not provided
                        
                        # Process flight segment with enhanced data
                        processed_segment = {
                            'departure': {
                                'airport': departure.get('AirportCode', ''),
                                'city': self._get_city_name(departure.get('AirportCode', '')),
                                'time': departure.get('Time', ''),
                                'date': departure.get('Date', '')
                            },
                            'arrival': {
                                'airport': arrival.get('AirportCode', ''),
                                'city': self._get_city_name(arrival.get('AirportCode', '')),
                                'time': arrival.get('Time', ''),
                                'date': arrival.get('Date', '')
                            },
                            'marketing_airline': segment.get('MarketingAirline', {}).get('AirlineID', ''),
                            'flight_number': segment.get('FlightNumber', ''),
                            'cabin_class': segment.get('CabinType', 'ECONOMY'),
                            'duration': self._parse_duration(duration)  # Duration in minutes
                        }
                        
                        processed_offer['flights'].append(processed_segment)
                
                processed['offers'].append(processed_offer)
        
        return processed

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration string (e.g., "PT1H30M") to minutes.
        
        Args:
            duration_str: ISO 8601 duration string
            
        Returns:
            Duration in minutes
        """
        minutes = 0
        hour_match = re.search(r'\\d+', duration_str)
        minute_match = re.search(r'\\d+', duration_str)
        
        if hour_match:
            minutes += int(hour_match.group(1)) * 60
        if minute_match:
            minutes += int(minute_match.group(1))
            
        return minutes

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
        'od_segments': od_segments,
        'num_adults': adults,
        'num_children': children,
        'num_infants': infants,
        'cabin_preference': cabin_class,
        'fare_type': fare_type,
        'request_id': request_id
    }
    
    async with FlightSearchService(config=config or {}) as service:
        return await service.search_flights(criteria)


async def process_air_shopping(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process air shopping request.
    
    This is a backward-compatible wrapper around the FlightSearchService.
    """
    config = search_criteria.pop('config', {})
    async with FlightSearchService(config=config) as service:
        return await service.search_flights(search_criteria)
