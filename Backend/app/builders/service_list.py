"""
ServiceList Request Builder

Builds VDC-compliant ServiceList requests from FlightPrice responses.
Follows clean architecture and VDC API specification.
"""

import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ServiceListRequestBuilder:
    """
    Builds ServiceList requests following VDC specification.
    
    Mappings (FlightPriceRS → ServiceListRQ):
    - DataLists/AnonymousTravelerList → Travelers/Traveler/AnonymousTraveler
    - DataLists/FlightSegmentList → Query/OriginDestination/Flight
    - PricedFlightOffers/OfferID → Query/Offers/Offer/OfferID
    - PricedFlightOffers/OfferPrice/OfferItemID → Query/Offers/OfferItemIDs
    - ShoppingResponseID → ShoppingResponseID
    """
    
    def __init__(self):
        """Initialize builder."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def build(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer_index: int = 0
    ) -> Dict[str, Any]:
        """
        Build ServiceList request.
        
        Args:
            flight_price_response: FlightPrice response dict
            selected_offer_index: Index of selected offer (always 0 for FlightPrice)
            
        Returns:
            VDC-compliant ServiceList request
            
        Raises:
            ValueError: If required data missing
        """
        self.logger.info(f"Building ServiceList request for offer {selected_offer_index}")
        
        # Check if multi-airline response
        is_multi_airline = self._is_multi_airline_response(flight_price_response)
        
        # Extract airline code if multi-airline
        airline_code = None
        if is_multi_airline:
            airline_code = self._extract_airline_code(flight_price_response)
            if airline_code:
                flight_price_response = self._filter_airline_data(
                    flight_price_response, 
                    airline_code
                )
        
        # Extract required data
        priced_offers = self._get_priced_offers(flight_price_response)
        selected_offer = priced_offers[selected_offer_index]
        
        # Extract offer details
        offer_id = selected_offer.get('OfferID', {})
        offer_id_value = offer_id.get('value')
        offer_owner = offer_id.get('Owner')
        offer_channel = offer_id.get('Channel', 'NDC')
        
        if not offer_id_value or not offer_owner:
            raise ValueError("OfferID value or Owner missing from PricedFlightOffer")
        
        # Extract offer prices
        offer_prices = selected_offer.get('OfferPrice', [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        # Extract shopping response ID
        shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
        shopping_response_value = shopping_response_id.get('ResponseID', {}).get('value')
        
        if not shopping_response_value:
            raise ValueError("ShoppingResponseID missing from FlightPriceResponse")
        
        # Extract DataLists
        data_lists = flight_price_response.get('DataLists', {})
        
        # Build request sections
        travelers_section = self._build_travelers_section(data_lists)
        query_section = self._build_query_section(
            data_lists, 
            offer_id_value,
            offer_owner,
            offer_channel,
            offer_prices
        )
        
        # Construct request
        request = {
            "Travelers": travelers_section,
            "Query": query_section,
            "ShoppingResponseID": {
                "ResponseID": {
                    "value": shopping_response_value
                }
            }
        }
        
        self.logger.info(f"Successfully built ServiceList request for airline {offer_owner}")
        return request
    
    def _build_travelers_section(self, data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """Build Travelers section."""
        anonymous_travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        if not isinstance(anonymous_travelers, list):
            anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
        
        # Each traveler gets its own Traveler object for ServiceList
        travelers = []
        for traveler in anonymous_travelers:
            if isinstance(traveler, dict):
                travelers.append({
                    "AnonymousTraveler": [{
                        "ObjectKey": traveler.get('ObjectKey'),
                        "PTC": traveler.get('PTC', {})
                    }]
                })
        
        return {
            "Traveler": travelers
        }
    
    def _build_query_section(
        self,
        data_lists: Dict[str, Any],
        offer_id_value: str,
        offer_owner: str,
        offer_channel: str,
        offer_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build Query section with OriginDestination and Offers."""
        # Build OriginDestination with Flight details
        flight_segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        if not isinstance(flight_segments, list):
            flight_segments = [flight_segments] if flight_segments else []
        
        origin_destinations = self._build_origin_destinations(flight_segments)
        
        # Build OfferItemIDs
        offer_item_ids = []
        for offer_price in offer_prices:
            offer_item_id = offer_price.get('OfferItemID')
            if offer_item_id:
                offer_item_ids.append({"value": offer_item_id})
        
        return {
            "OriginDestination": origin_destinations,
            "Offers": {
                "Offer": [{
                    "OfferID": {
                        "value": offer_id_value,
                        "Owner": offer_owner,
                        "Channel": offer_channel
                    },
                    "OfferItemIDs": {
                        "OfferItemID": offer_item_ids
                    }
                }]
            }
        }
    
    def _build_origin_destinations(
        self, 
        flight_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build OriginDestination with Flight details.
        Groups segments by origin-destination pairs.
        """
        if not flight_segments:
            return []
        
        # Group segments by OD pairs
        od_groups = {}
        for segment in flight_segments:
            if isinstance(segment, dict):
                departure_airport = segment.get('Departure', {}).get('AirportCode', {}).get('value')
                arrival_airport = segment.get('Arrival', {}).get('AirportCode', {}).get('value')
                
                if departure_airport and arrival_airport:
                    od_key = f"{departure_airport}-{arrival_airport}"
                    if od_key not in od_groups:
                        od_groups[od_key] = []
                    od_groups[od_key].append(segment)
        
        # Build OriginDestination entries
        origin_destinations = []
        for od_key, segments in od_groups.items():
            flights = []
            for segment in segments:
                flight_entry = self._build_flight_entry(segment)
                flights.append(flight_entry)
            
            if flights:
                origin_destinations.append({"Flight": flights})
        
        return origin_destinations
    
    def _build_flight_entry(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Flight entry from segment."""
        # Build Departure
        departure = {
            "AirportCode": segment.get('Departure', {}).get('AirportCode', {}),
            "Date": segment.get('Departure', {}).get('Date'),
            "Time": segment.get('Departure', {}).get('Time')
        }
        
        # Add optional fields
        if segment.get('Departure', {}).get('AirportName'):
            departure["AirportName"] = segment.get('Departure', {}).get('AirportName')
        
        departure_terminal = segment.get('Departure', {}).get('Terminal', {})
        if departure_terminal and departure_terminal.get('Name'):
            departure["Terminal"] = departure_terminal
        
        # Build Arrival
        arrival = {
            "AirportCode": segment.get('Arrival', {}).get('AirportCode', {}),
            "Date": segment.get('Arrival', {}).get('Date'),
            "Time": segment.get('Arrival', {}).get('Time')
        }
        
        # Add optional fields
        if segment.get('Arrival', {}).get('AirportName'):
            arrival["AirportName"] = segment.get('Arrival', {}).get('AirportName')
        
        arrival_terminal = segment.get('Arrival', {}).get('Terminal', {})
        if arrival_terminal and arrival_terminal.get('Name'):
            arrival["Terminal"] = arrival_terminal
        
        return {
            "SegmentKey": segment.get('SegmentKey'),
            "Departure": departure,
            "Arrival": arrival,
            "MarketingCarrier": segment.get('MarketingCarrier', {}),
            "Equipment": segment.get('Equipment', {}),
            "FlightDetail": segment.get('FlightDetail', {})
        }
    
    # Multi-airline support methods (same as SeatAvailability)
    
    def _is_multi_airline_response(self, response: Dict[str, Any]) -> bool:
        """Check if response is from multi-airline search."""
        try:
            data_lists = response.get('DataLists', {})
            travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
            if not isinstance(travelers, list):
                travelers = [travelers] if travelers else []
            
            for traveler in travelers:
                object_key = traveler.get('ObjectKey', '')
                if re.match(r'^[A-Z0-9]{2,3}-', object_key):
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error detecting multi-airline response: {e}")
            return False
    
    def _extract_airline_code(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract airline code from response."""
        try:
            # Method 1: From ShoppingResponseID
            shopping_response_id = response.get('ShoppingResponseID', {})
            owner = shopping_response_id.get('Owner')
            if owner:
                return owner
            
            # Method 2: From OfferID
            priced_offers = response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if not isinstance(priced_offers, list):
                priced_offers = [priced_offers] if priced_offers else []
            
            if priced_offers:
                offer_id = priced_offers[0].get('OfferID', {})
                owner = offer_id.get('Owner')
                if owner:
                    return owner
            
            # Method 3: From prefixed ObjectKey
            data_lists = response.get('DataLists', {})
            travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
            if not isinstance(travelers, list):
                travelers = [travelers] if travelers else []
            
            for traveler in travelers:
                object_key = traveler.get('ObjectKey', '')
                match = re.match(r'^([A-Z0-9]{2,3})-', object_key)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting airline code: {e}")
            return None
    
    def _filter_airline_data(
        self, 
        response: Dict[str, Any], 
        airline_code: str
    ) -> Dict[str, Any]:
        """Filter response to only include airline-specific data."""
        import json
        
        try:
            filtered = json.loads(json.dumps(response))
            data_lists = filtered.get('DataLists', {})
            
            # Filter travelers
            travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
            if not isinstance(travelers, list):
                travelers = [travelers] if travelers else []
            
            filtered_travelers = []
            for traveler in travelers:
                object_key = traveler.get('ObjectKey', '')
                if object_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z0-9]{2,3}-', object_key):
                    traveler_copy = traveler.copy()
                    if object_key.startswith(f"{airline_code}-"):
                        traveler_copy['ObjectKey'] = object_key.replace(f"{airline_code}-", "")
                    filtered_travelers.append(traveler_copy)
            
            if filtered_travelers:
                data_lists['AnonymousTravelerList']['AnonymousTraveler'] = filtered_travelers
            
            # Filter segments
            segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
            if not isinstance(segments, list):
                segments = [segments] if segments else []
            
            filtered_segments = []
            for segment in segments:
                segment_key = segment.get('SegmentKey', '')
                if segment_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z0-9]{2,3}-', segment_key):
                    segment_copy = segment.copy()
                    if segment_key.startswith(f"{airline_code}-"):
                        segment_copy['SegmentKey'] = segment_key.replace(f"{airline_code}-", "")
                    filtered_segments.append(segment_copy)
            
            if filtered_segments:
                data_lists['FlightSegmentList']['FlightSegment'] = filtered_segments
            
            self.logger.info(f"Filtered data for airline {airline_code}")
            return filtered
        except Exception as e:
            self.logger.error(f"Error filtering airline data: {e}")
            return response
    
    def _get_priced_offers(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and normalize priced offers."""
        priced_offers = response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        if not isinstance(priced_offers, list):
            priced_offers = [priced_offers] if priced_offers else []
        
        if not priced_offers:
            raise ValueError("No PricedFlightOffers found in response")
        
        return priced_offers
