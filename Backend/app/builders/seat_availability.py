"""
SeatAvailability Request Builder

Builds VDC-compliant SeatAvailability requests from FlightPrice responses.
Follows clean architecture and VDC API specification.
"""

import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SeatAvailabilityRequestBuilder:
    """
    Builds SeatAvailability requests following VDC specification.
    
    Mappings (FlightPriceRS → SeatAvailabilityRQ):
    - DataLists/AnonymousTravelerList → Travelers/Traveler/AnonymousTraveler
    - DataLists/FlightSegmentList → Query/OriginDestination/FlightSegmentReference
    - PricedFlightOffers/OfferID → Query/Offers/Offer/OfferID
    - PricedFlightOffers/OfferPrice/OfferItemID → Query/Offers/OfferItemIDs
    - DataLists/FareList → DataLists/FareList
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
        Build SeatAvailability request.
        
        Args:
            flight_price_response: FlightPrice response dict
            selected_offer_index: Index of selected offer (always 0 for FlightPrice)
            
        Returns:
            VDC-compliant SeatAvailability request
            
        Raises:
            ValueError: If required data missing
        """
        self.logger.info(f"Building SeatAvailability request for offer {selected_offer_index}")
        
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
        datalists_section = self._build_datalists_section(data_lists)
        
        # Construct request
        request = {
            "Travelers": travelers_section,
            "Query": query_section,
            "DataLists": datalists_section,
            "ShoppingResponseID": {
                "ResponseID": {
                    "value": shopping_response_value
                }
            }
        }
        
        self.logger.info(f"Successfully built SeatAvailability request for airline {offer_owner}")
        return request
    
    def _build_travelers_section(self, data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """Build Travelers section."""
        anonymous_travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        if not isinstance(anonymous_travelers, list):
            anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
        
        # Group all travelers into single Traveler object
        traveler_list = []
        for traveler in anonymous_travelers:
            if isinstance(traveler, dict):
                traveler_list.append({
                    "ObjectKey": traveler.get('ObjectKey'),
                    "PTC": traveler.get('PTC', {})
                })
        
        return {
            "Traveler": [{
                "AnonymousTraveler": traveler_list
            }] if traveler_list else []
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
        # Build OriginDestination with FlightSegmentReference
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
        Build OriginDestination with FlightSegmentReference.
        Detects round-trip vs one-way and groups segments accordingly.
        """
        if not flight_segments:
            return []
        
        # Check if round trip
        is_round_trip = self._detect_round_trip(flight_segments)
        
        if is_round_trip and len(flight_segments) > 1:
            # Split into outbound and return
            outbound, return_segs = self._group_round_trip_segments(flight_segments)
            
            origin_destinations = []
            
            # Outbound OD
            if outbound:
                outbound_refs = [{"ref": seg.get('SegmentKey')} for seg in outbound if seg.get('SegmentKey')]
                if outbound_refs:
                    origin_destinations.append({"FlightSegmentReference": outbound_refs})
            
            # Return OD
            if return_segs:
                return_refs = [{"ref": seg.get('SegmentKey')} for seg in return_segs if seg.get('SegmentKey')]
                if return_refs:
                    origin_destinations.append({"FlightSegmentReference": return_refs})
            
            return origin_destinations
        else:
            # One-way or connecting: group all segments together
            segment_refs = [{"ref": seg.get('SegmentKey')} for seg in flight_segments if seg.get('SegmentKey')]
            
            return [{
                "FlightSegmentReference": segment_refs
            }] if segment_refs else []
    
    def _detect_round_trip(self, segments: List[Dict[str, Any]]) -> bool:
        """Detect if segments represent a round trip."""
        if len(segments) < 2:
            return False
        
        # Extract airports
        airports = []
        for segment in segments:
            dep_airport = segment.get('Departure', {}).get('AirportCode', {}).get('value')
            arr_airport = segment.get('Arrival', {}).get('AirportCode', {}).get('value')
            if dep_airport and arr_airport:
                airports.append((dep_airport, arr_airport))
        
        if len(airports) < 2:
            return False
        
        # Check if final destination returns to origin
        first_origin = airports[0][0]
        last_destination = airports[-1][1]
        
        return first_origin == last_destination
    
    def _group_round_trip_segments(
        self, 
        segments: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Group segments into outbound and return for round trips."""
        first_origin = segments[0].get('Departure', {}).get('AirportCode', {}).get('value')
        
        # Find where return journey begins
        return_start_idx = len(segments)
        for i, segment in enumerate(segments):
            arr_airport = segment.get('Arrival', {}).get('AirportCode', {}).get('value')
            if arr_airport == first_origin and i > 0:
                return_start_idx = i
                break
        
        # If no clear return, split in half
        if return_start_idx == len(segments):
            return_start_idx = len(segments) // 2
        
        outbound = segments[:return_start_idx]
        return_segs = segments[return_start_idx:]
        
        return outbound, return_segs
    
    def _build_datalists_section(self, data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """Build DataLists section with FlightSegmentList and FareList."""
        datalists = {}
        
        # Add FlightSegmentList
        flight_segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        if not isinstance(flight_segments, list):
            flight_segments = [flight_segments] if flight_segments else []
        
        if flight_segments:
            processed_segments = []
            for segment in flight_segments:
                if isinstance(segment, dict):
                    processed_segment = self._process_flight_segment(segment)
                    processed_segments.append(processed_segment)
            
            if processed_segments:
                datalists["FlightSegmentList"] = {
                    "FlightSegment": processed_segments
                }
        
        # Add FareList
        fare_groups = data_lists.get('FareList', {}).get('FareGroup', [])
        if not isinstance(fare_groups, list):
            fare_groups = [fare_groups] if fare_groups else []
        
        if fare_groups:
            processed_fare_groups = []
            for fare_group in fare_groups:
                if isinstance(fare_group, dict):
                    # VDC spec: only FareCode, no FareDetail
                    fare_structure = {}
                    if fare_group.get('Fare', {}).get('FareCode'):
                        fare_structure = {
                            "FareCode": fare_group.get('Fare', {}).get('FareCode', {})
                        }
                    
                    processed_fare_group = {
                        "ListKey": fare_group.get('ListKey'),
                        "Fare": fare_structure,
                        "FareBasisCode": fare_group.get('FareBasisCode', {})
                    }
                    processed_fare_groups.append(processed_fare_group)
            
            if processed_fare_groups:
                datalists["FareList"] = {
                    "FareGroup": processed_fare_groups
                }
        
        return datalists
    
    def _process_flight_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single flight segment for DataLists."""
        # Build Departure
        departure = {
            "AirportCode": segment.get('Departure', {}).get('AirportCode', {}),
            "Date": segment.get('Departure', {}).get('Date'),
            "Time": segment.get('Departure', {}).get('Time')
        }
        
        # Add optional fields only if present
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
        
        # Add optional fields only if present
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
    
    # Multi-airline support methods
    
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
            
            # Filter fare groups
            fare_groups = data_lists.get('FareList', {}).get('FareGroup', [])
            if not isinstance(fare_groups, list):
                fare_groups = [fare_groups] if fare_groups else []
            
            filtered_fare_groups = []
            for fare_group in fare_groups:
                list_key = fare_group.get('ListKey', '')
                if list_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z0-9]{2,3}-', list_key):
                    fare_group_copy = fare_group.copy()
                    if list_key.startswith(f"{airline_code}-"):
                        fare_group_copy['ListKey'] = list_key.replace(f"{airline_code}-", "")
                    filtered_fare_groups.append(fare_group_copy)
            
            if filtered_fare_groups:
                data_lists['FareList']['FareGroup'] = filtered_fare_groups
            
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
