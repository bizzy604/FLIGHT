# --- START OF FILE build_seatavailability_rq.py ---

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Set up logger
logger = logging.getLogger(__name__)

def _is_multi_airline_flight_price_response(flight_price_response: Dict[str, Any]) -> bool:
    """
    Check if the flight price response is from a multi-airline context.

    Args:
        flight_price_response: The FlightPrice response

    Returns:
        bool: True if multi-airline response, False otherwise
    """
    try:
        # Check for airline-prefixed references in DataLists
        data_lists = flight_price_response.get('DataLists', {})
        travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        if not isinstance(travelers, list):
            travelers = [travelers] if travelers else []

        for traveler in travelers:
            object_key = traveler.get('ObjectKey', '')
            # Look for airline-prefixed keys like "26-PAX1", "KQ-PAX1"
            if re.match(r'^[A-Z0-9]{2,3}-', object_key):
                return True

        # Check flight segments for airline prefixes
        segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        if not isinstance(segments, list):
            segments = [segments] if segments else []

        for segment in segments:
            segment_key = segment.get('SegmentKey', '')
            if re.match(r'^[A-Z0-9]{2,3}-', segment_key):
                return True

        return False

    except Exception as e:
        logger.error(f"Error detecting multi-airline flight price response: {e}")
        return False

def _extract_airline_from_flight_price_response(flight_price_response: Dict[str, Any]) -> Optional[str]:
    """
    Extract airline code from flight price response.

    Args:
        flight_price_response: The FlightPrice response

    Returns:
        str: The airline code or None if not found
    """
    try:
        # Method 1: Extract from ShoppingResponseID Owner
        shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
        if isinstance(shopping_response_id, dict):
            owner = shopping_response_id.get('Owner')
            if owner:
                return owner

        # Method 2: Extract from PricedFlightOffers
        priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        if not isinstance(priced_offers, list):
            priced_offers = [priced_offers] if priced_offers else []

        if priced_offers:
            first_offer = priced_offers[0]
            offer_id = first_offer.get('OfferID', {})
            owner = offer_id.get('Owner')
            if owner:
                return owner

        # Method 3: Extract from airline-prefixed ObjectKeys
        data_lists = flight_price_response.get('DataLists', {})
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
        logger.error(f"Error extracting airline from flight price response: {e}")
        return None

def _filter_airline_specific_data_for_seatavailability(flight_price_response: Dict[str, Any], airline_code: str) -> Dict[str, Any]:
    """
    Filter flight price response data to only include airline-specific elements for SeatAvailability.

    Args:
        flight_price_response: The original FlightPrice response
        airline_code: The airline code to filter for

    Returns:
        Dict: Filtered flight price response with only airline-specific data
    """
    try:
        # Create a deep copy to avoid modifying the original
        filtered_response = json.loads(json.dumps(flight_price_response))
        data_lists = filtered_response.get('DataLists', {})

        # Filter AnonymousTravelerList
        travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        if not isinstance(travelers, list):
            travelers = [travelers] if travelers else []

        filtered_travelers = []
        for traveler in travelers:
            object_key = traveler.get('ObjectKey', '')
            # Include travelers that belong to this airline or have no airline prefix
            if object_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z0-9]{2,3}-', object_key):
                # Transform airline-prefixed keys to standard keys for SeatAvailability
                if object_key.startswith(f"{airline_code}-"):
                    traveler_copy = traveler.copy()
                    traveler_copy['ObjectKey'] = object_key.replace(f"{airline_code}-", "")
                    filtered_travelers.append(traveler_copy)
                else:
                    filtered_travelers.append(traveler)

        if filtered_travelers:
            data_lists['AnonymousTravelerList']['AnonymousTraveler'] = filtered_travelers

        # Filter FlightSegmentList
        segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        if not isinstance(segments, list):
            segments = [segments] if segments else []

        filtered_segments = []
        for segment in segments:
            segment_key = segment.get('SegmentKey', '')
            # Include segments that belong to this airline or have no airline prefix
            if segment_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z0-9]{2,3}-', segment_key):
                # Transform airline-prefixed keys to standard keys
                if segment_key.startswith(f"{airline_code}-"):
                    segment_copy = segment.copy()
                    segment_copy['SegmentKey'] = segment_key.replace(f"{airline_code}-", "")
                    filtered_segments.append(segment_copy)
                else:
                    filtered_segments.append(segment)

        if filtered_segments:
            data_lists['FlightSegmentList']['FlightSegment'] = filtered_segments

        # Filter FareList
        fare_groups = data_lists.get('FareList', {}).get('FareGroup', [])
        if not isinstance(fare_groups, list):
            fare_groups = [fare_groups] if fare_groups else []

        filtered_fare_groups = []
        for fare_group in fare_groups:
            list_key = fare_group.get('ListKey', '')
            # Include fare groups that belong to this airline or have no airline prefix
            if list_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z0-9]{2,3}-', list_key):
                # Transform airline-prefixed keys to standard keys
                if list_key.startswith(f"{airline_code}-"):
                    fare_group_copy = fare_group.copy()
                    fare_group_copy['ListKey'] = list_key.replace(f"{airline_code}-", "")
                    filtered_fare_groups.append(fare_group_copy)
                else:
                    filtered_fare_groups.append(fare_group)

        if filtered_fare_groups:
            data_lists['FareList']['FareGroup'] = filtered_fare_groups

        logger.info(f"Filtered SeatAvailability data for airline {airline_code}: {len(filtered_travelers)} travelers, {len(filtered_segments)} segments, {len(filtered_fare_groups)} fare groups")
        return filtered_response

    except Exception as e:
        logger.error(f"Error filtering airline-specific data for SeatAvailability: {e}")
        return flight_price_response

def build_seatavailability_request(
    flight_price_response: Dict[str, Any],
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Build SeatAvailability request from FlightPrice response following VDC API documentation mappings.

    Args:
        flight_price_response: The FlightPriceResponse JSON as a Python dictionary
        selected_offer_index: Index of the selected offer (default: 0)

    Returns:
        dict: The generated SeatAvailabilityRQ as a Python dictionary

    Mappings from VDC documentation:
    FlightPriceRS → SeatAvailabilityRQ
    - DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey → Travelers/Traveler/AnonymousTraveler/ObjectKey
    - DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value → Travelers/Traveler/AnonymousTraveler/PTC/value
    - DataLists/FlightSegmentList/FlightSegment/SegmentKey → Query/OriginDestination/FlightSegmentReference/ref
    - PricedFlightOffers/PricedFlightOffer/OfferID/value → Query/Offers/Offer/OfferID/value
    - PricedFlightOffers/PricedFlightOffer/OfferID/Owner → Query/Offers/Offer/OfferID/Owner
    - PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID → Query/Offers/Offer/OfferItemIDs/OfferItemID/value
    - DataLists/FareList/FareGroup/ListKey → DataLists/FareList/FareGroup/ListKey
    - DataLists/FareList/FareGroup/FareBasisCode/Code → DataLists/FareList/FareGroup/FareBasisCode/Code
    - DataLists/FlightSegmentList/FlightSegment/* → DataLists/FlightSegmentList/FlightSegment/*
    - ShoppingResponseID/ResponseID/value → ShoppingResponseID/ResponseID/value
    """
    logger.info(f"Building SeatAvailability request for offer index {selected_offer_index}")

    # Check if this is a multi-airline flight price response
    is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)
    logger.info(f"Multi-airline SeatAvailability detected: {is_multi_airline}")

    # Handle nested data structure from frontend
    actual_flight_price_response = flight_price_response
    
    # Check if data is nested under various frontend structures
    if ('data' in flight_price_response and 
        'raw_response' in flight_price_response['data'] and 
        'data' in flight_price_response['data']['raw_response'] and 
        'raw_response' in flight_price_response['data']['raw_response']['data']):
        actual_flight_price_response = flight_price_response['data']['raw_response']['data']['raw_response']
        logger.info("Using data.raw_response.data.raw_response structure")
    elif 'data' in flight_price_response and 'raw_response' in flight_price_response['data']:
        actual_flight_price_response = flight_price_response['data']['raw_response']
        logger.info("Using data.raw_response structure")
    elif 'raw_response' in flight_price_response:
        actual_flight_price_response = flight_price_response['raw_response']
        logger.info("Using raw_response structure")

    # Extract airline code for filtering if multi-airline
    airline_code = None
    if is_multi_airline:
        airline_code = _extract_airline_from_flight_price_response(actual_flight_price_response)
        logger.info(f"Extracted airline code for SeatAvailability: {airline_code}")

        if airline_code:
            # Filter the flight price response to only include airline-specific data
            actual_flight_price_response = _filter_airline_specific_data_for_seatavailability(actual_flight_price_response, airline_code)
            logger.info(f"Filtered flight price response for airline {airline_code}")

    # Extract PricedFlightOffers
    priced_flight_offers = actual_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    if not isinstance(priced_flight_offers, list):
        priced_flight_offers = [priced_flight_offers] if priced_flight_offers else []

    if not priced_flight_offers or selected_offer_index >= len(priced_flight_offers):
        raise ValueError(f"Invalid selected_offer_index {selected_offer_index} or no PricedFlightOffers found")

    selected_offer = priced_flight_offers[selected_offer_index]

    # Extract OfferID details
    offer_id = selected_offer.get('OfferID', {})
    offer_id_value = offer_id.get('value')
    offer_owner = offer_id.get('Owner')
    offer_channel = offer_id.get('Channel')

    if not offer_id_value or not offer_owner:
        raise ValueError("OfferID value or Owner missing from selected PricedFlightOffer")

    # Extract OfferPrice details
    offer_prices = selected_offer.get('OfferPrice', [])
    if not isinstance(offer_prices, list):
        offer_prices = [offer_prices] if offer_prices else []

    # Extract ShoppingResponseID
    shopping_response_id = actual_flight_price_response.get('ShoppingResponseID', {})
    shopping_response_id_value = shopping_response_id.get('ResponseID', {}).get('value')

    if not shopping_response_id_value:
        raise ValueError("ShoppingResponseID ResponseID value missing from FlightPriceResponse")

    # Extract DataLists
    data_lists = actual_flight_price_response.get('DataLists', {})

    # Build Travelers section
    travelers = []
    anonymous_travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
    if not isinstance(anonymous_travelers, list):
        anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []

    # Group all anonymous travelers into a single Traveler object
    if anonymous_travelers:
        anonymous_traveler_list = []
        for traveler in anonymous_travelers:
            if isinstance(traveler, dict):
                anonymous_traveler_list.append({
                    "ObjectKey": traveler.get('ObjectKey'),
                    "PTC": traveler.get('PTC', {})
                })
        
        # Create single Traveler object with all AnonymousTraveler entries
        if anonymous_traveler_list:
            travelers.append({
                "AnonymousTraveler": anonymous_traveler_list
            })

    # Build OriginDestination section with FlightSegmentReference
    origin_destinations = []
    flight_segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
    if not isinstance(flight_segments, list):
        flight_segments = [flight_segments] if flight_segments else []

    # Analyze flight segments to detect round trip vs one-way/connecting
    def _detect_round_trip(segments):
        """Detect if segments represent a round trip by checking departure/arrival patterns"""
        if len(segments) < 2:
            return False
            
        # Extract departure and arrival airports for all segments
        airports = []
        for segment in segments:
            dep_airport = segment.get('Departure', {}).get('AirportCode', {}).get('value')
            arr_airport = segment.get('Arrival', {}).get('AirportCode', {}).get('value')
            if dep_airport and arr_airport:
                airports.append((dep_airport, arr_airport))
        
        if len(airports) < 2:
            return False
            
        # Check if the final destination of the journey returns to the origin
        first_origin = airports[0][0]
        last_destination = airports[-1][1]
        
        # For round trip: final destination should match first origin
        return first_origin == last_destination

    def _group_round_trip_segments(segments):
        """Group segments into outbound and return journeys for round trips"""
        outbound_segments = []
        return_segments = []
        
        # Simple heuristic: find the midpoint where return journey begins
        # This is when we start heading back toward the original departure airport
        first_origin = segments[0].get('Departure', {}).get('AirportCode', {}).get('value')
        
        # Find the segment where we start returning to the original origin
        return_start_idx = len(segments)
        for i, segment in enumerate(segments):
            arr_airport = segment.get('Arrival', {}).get('AirportCode', {}).get('value')
            if arr_airport == first_origin and i > 0:
                return_start_idx = i
                break
        
        # If no clear return detected, split in half
        if return_start_idx == len(segments):
            midpoint = len(segments) // 2
            return_start_idx = midpoint
            
        outbound_segments = segments[:return_start_idx]
        return_segments = segments[return_start_idx:]
        
        return outbound_segments, return_segments

    # Check if this is a round trip
    is_round_trip = _detect_round_trip(flight_segments)
    
    if is_round_trip and len(flight_segments) > 1:
        # Handle round trip: create separate OriginDestination for outbound and return
        outbound_segments, return_segments = _group_round_trip_segments(flight_segments)
        
        # Create outbound OriginDestination
        if outbound_segments:
            outbound_refs = []
            for segment in outbound_segments:
                segment_key = segment.get('SegmentKey')
                if segment_key:
                    outbound_refs.append({"ref": segment_key})
            
            if outbound_refs:
                origin_destinations.append({
                    "FlightSegmentReference": outbound_refs
                })
        
        # Create return OriginDestination
        if return_segments:
            return_refs = []
            for segment in return_segments:
                segment_key = segment.get('SegmentKey')
                if segment_key:
                    return_refs.append({"ref": segment_key})
            
            if return_refs:
                origin_destinations.append({
                    "FlightSegmentReference": return_refs
                })
    else:
        # Handle one-way or connecting flights: group all segments together
        flight_segment_refs = []
        for segment in flight_segments:
            if isinstance(segment, dict):
                segment_key = segment.get('SegmentKey')
                if segment_key:
                    flight_segment_refs.append({"ref": segment_key})

        # Create single OriginDestination with all segments
        if flight_segment_refs:
            origin_destinations.append({
                "FlightSegmentReference": flight_segment_refs
            })

    # Build OfferItemIDs
    offer_item_ids = []
    for offer_price in offer_prices:
        offer_item_id = offer_price.get('OfferItemID')
        if offer_item_id:
            offer_item_ids.append({"value": offer_item_id})

    # Build DataLists for SeatAvailability (includes FlightSegmentList and FareList)
    seat_datalists = {}

    # Add FlightSegmentList to DataLists
    if flight_segments:
        processed_segments = []
        for segment in flight_segments:
            if isinstance(segment, dict):
                # Build Departure section
                departure_section = {
                    "AirportCode": segment.get('Departure', {}).get('AirportCode', {}),
                    "Date": segment.get('Departure', {}).get('Date'),
                    "Time": segment.get('Departure', {}).get('Time')
                }
                
                # Add AirportName only if it has actual content
                departure_airport_name = segment.get('Departure', {}).get('AirportName')
                if departure_airport_name:
                    departure_section["AirportName"] = departure_airport_name
                
                # Build Arrival section
                arrival_section = {
                    "AirportCode": segment.get('Arrival', {}).get('AirportCode', {}),
                    "Date": segment.get('Arrival', {}).get('Date'),
                    "Time": segment.get('Arrival', {}).get('Time')
                }
                
                # Add AirportName only if it has actual content
                arrival_airport_name = segment.get('Arrival', {}).get('AirportName')
                if arrival_airport_name:
                    arrival_section["AirportName"] = arrival_airport_name
                
                processed_segment = {
                    "SegmentKey": segment.get('SegmentKey'),
                    "Departure": departure_section,
                    "Arrival": arrival_section,
                    "MarketingCarrier": segment.get('MarketingCarrier', {}),
                    "Equipment": segment.get('Equipment', {}),
                    "FlightDetail": segment.get('FlightDetail', {})
                }
                
                # Add Terminal only if it has actual content (not empty dict)
                departure_terminal = segment.get('Departure', {}).get('Terminal', {})
                if departure_terminal and departure_terminal.get('Name'):
                    processed_segment["Departure"]["Terminal"] = departure_terminal
                    
                arrival_terminal = segment.get('Arrival', {}).get('Terminal', {})
                if arrival_terminal and arrival_terminal.get('Name'):
                    processed_segment["Arrival"]["Terminal"] = arrival_terminal
                    
                processed_segments.append(processed_segment)

        if processed_segments:
            seat_datalists["FlightSegmentList"] = {
                "FlightSegment": processed_segments
            }

    # Add FareList to DataLists
    fare_groups = data_lists.get('FareList', {}).get('FareGroup', [])
    if not isinstance(fare_groups, list):
        fare_groups = [fare_groups] if fare_groups else []

    if fare_groups:
        processed_fare_groups = []
        for fare_group in fare_groups:
            if isinstance(fare_group, dict):
                # Build VDC-compliant Fare structure (only FareCode, no FareDetail)
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
                # Note: VDC documentation doesn't include 'refs' field in SeatAvailability FareGroup
                
                processed_fare_groups.append(processed_fare_group)

        if processed_fare_groups:
            seat_datalists["FareList"] = {
                "FareGroup": processed_fare_groups
            }

    # Build the SeatAvailability request
    seatavailability_request = {
        "Travelers": {
            "Traveler": travelers
        },
        "Query": {
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
        },
        "DataLists": seat_datalists,
        "ShoppingResponseID": {
            "ResponseID": {
                "value": shopping_response_id_value
            }
        }
    }

    logger.info(f"Successfully built SeatAvailability request for airline {offer_owner}")
    return seatavailability_request

def main():
    """Main function to generate and save SeatAvailabilityRQ from FlightPriceRS."""
    import sys
    from pathlib import Path

    input_file_name = "flightpriceRS.json" 
    input_file_path = Path(input_file_name)
    output_file_path = Path("seatavailability_request_generated.json")

    if not input_file_path.exists():
        print(f"Error: Input file '{input_file_path}' not found.")
        sys.exit(1)

    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            flight_price_response_content = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file '{input_file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading input file '{input_file_path}': {e}")
        sys.exit(1)

    try:
        # Build SeatAvailability request for the first offer
        seatavailability_rq_payload = build_seatavailability_request(flight_price_response_content, selected_offer_index=0)
        
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(seatavailability_rq_payload, f, indent=2, ensure_ascii=False)
        print(f"SeatAvailabilityRQ successfully generated and saved to '{output_file_path}'")
            
    except ValueError as ve:
        print(f"ValueError during request generation: {ve}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during request generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

# --- USAGE EXAMPLES ---
"""
Usage Examples for SeatAvailability Request Builder:

1. Standard usage with FlightPrice response:
   result = build_seatavailability_request(flight_price_response, selected_offer_index=0)

2. Multi-airline response handling:
   # Automatically detects multi-airline response and filters airline-specific data
   result = build_seatavailability_request(multi_airline_flight_price_response, selected_offer_index=1)

3. Integration with existing backend services:
   from scripts.build_seatavailability_rq import build_seatavailability_request
   
   async def get_seat_availability(flight_price_response):
       seatavailability_request = build_seatavailability_request(flight_price_response)
       # Use seatavailability_request to call VDC SeatAvailability API
       return seatavailability_request

The function automatically:
- Detects multi-airline vs single-airline responses
- Filters airline-specific data for multi-airline scenarios  
- Transforms airline-prefixed keys to standard keys (26-PAX1 → PAX1, 26-SEG2 → SEG2)
- Maps all required fields according to VDC API documentation
- Handles nested frontend data structures
- Maintains reference consistency across the booking flow
- Builds proper FlightSegmentReference structures for seat maps
- Includes comprehensive DataLists with FlightSegmentList and FareList

Key features:
- Full VDC API documentation mapping compliance
- Multi-airline support with automatic filtering
- Robust error handling and validation
- Airline prefix transformation for clean API calls
- Compatible with existing backend architecture
- Optimized for seat map retrieval and pricing
- Supports cabin-specific seat availability requests
"""

# --- END OF FILE build_seatavailability_rq.py ---