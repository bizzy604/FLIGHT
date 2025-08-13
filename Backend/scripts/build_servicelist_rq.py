# --- START OF FILE build_servicelist_rq.py ---

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

def _filter_airline_specific_data_for_servicelist(flight_price_response: Dict[str, Any], airline_code: str) -> Dict[str, Any]:
    """
    Filter flight price response data to only include airline-specific elements for ServiceList.

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
                # Transform airline-prefixed keys to standard keys for ServiceList
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

        logger.info(f"Filtered ServiceList data for airline {airline_code}: {len(filtered_travelers)} travelers, {len(filtered_segments)} segments, {len(filtered_fare_groups)} fare groups")
        return filtered_response

    except Exception as e:
        logger.error(f"Error filtering airline-specific data for ServiceList: {e}")
        return flight_price_response

def build_servicelist_request(
    flight_price_response: Dict[str, Any],
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Build ServiceList request from FlightPrice response following VDC API documentation mappings.

    Args:
        flight_price_response: The FlightPriceResponse JSON as a Python dictionary
        selected_offer_index: Index of the selected offer (default: 0)

    Returns:
        dict: The generated ServiceListRQ as a Python dictionary

    Mappings from VDC documentation:
    FlightPriceRS → ServiceListRQ
    - DataLists/AnonymousTravelerList/AnonymousTraveler/ObjectKey → Travelers/Traveler/AnonymousTraveler/ObjectKey
    - DataLists/AnonymousTravelerList/AnonymousTraveler/PTC/value → Travelers/Traveler/AnonymousTraveler/PTC/value
    - DataLists/FlightSegmentList/FlightSegment/SegmentKey → Query/OriginDestination/Flight/SegmentKey
    - PricedFlightOffers/PricedFlightOffer/OfferID/value → Query/Offers/Offer/OfferID/value
    - PricedFlightOffers/PricedFlightOffer/OfferID/Owner → Query/Offers/Offer/OfferID/Owner
    - PricedFlightOffers/PricedFlightOffer/OfferPrice/OfferItemID → Query/Offers/Offer/OfferItemIDs/OfferItemID/value
    - ShoppingResponseID/ResponseID/value → ShoppingResponseID/ResponseID/value
    """
    logger.info(f"Building ServiceList request for offer index {selected_offer_index}")

    # Check if this is a multi-airline flight price response
    is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)
    logger.info(f"Multi-airline ServiceList detected: {is_multi_airline}")

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
        logger.info(f"Extracted airline code for ServiceList: {airline_code}")

        if airline_code:
            # Filter the flight price response to only include airline-specific data
            actual_flight_price_response = _filter_airline_specific_data_for_servicelist(actual_flight_price_response, airline_code)
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

    for traveler in anonymous_travelers:
        if isinstance(traveler, dict):
            traveler_entry = {
                "AnonymousTraveler": [{
                    "ObjectKey": traveler.get('ObjectKey'),
                    "PTC": traveler.get('PTC', {})
                }]
            }
            travelers.append(traveler_entry)

    # Build OriginDestination section with flight details
    origin_destinations = []
    flight_segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
    if not isinstance(flight_segments, list):
        flight_segments = [flight_segments] if flight_segments else []

    # Group segments by origin-destination pairs
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
    for od_key, segments in od_groups.items():
        flights = []
        for segment in segments:
            flight_entry = {
                "SegmentKey": segment.get('SegmentKey'),
                "Departure": {
                    "AirportCode": segment.get('Departure', {}).get('AirportCode', {}),
                    "Date": segment.get('Departure', {}).get('Date'),
                    "Time": segment.get('Departure', {}).get('Time'),
                    "AirportName": segment.get('Departure', {}).get('AirportName'),
                    "Terminal": segment.get('Departure', {}).get('Terminal', {})
                },
                "Arrival": {
                    "AirportCode": segment.get('Arrival', {}).get('AirportCode', {}),
                    "Date": segment.get('Arrival', {}).get('Date'),
                    "Time": segment.get('Arrival', {}).get('Time'),
                    "AirportName": segment.get('Arrival', {}).get('AirportName'),
                    "Terminal": segment.get('Arrival', {}).get('Terminal', {})
                },
                "MarketingCarrier": segment.get('MarketingCarrier', {}),
                "Equipment": segment.get('Equipment', {}),
                "FlightDetail": segment.get('FlightDetail', {})
            }
            flights.append(flight_entry)

        if flights:
            origin_destinations.append({"Flight": flights})

    # Build OfferItemIDs
    offer_item_ids = []
    for offer_price in offer_prices:
        offer_item_id = offer_price.get('OfferItemID')
        if offer_item_id:
            offer_item_ids.append({"value": offer_item_id})

    # Build the ServiceList request
    servicelist_request = {
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
        "ShoppingResponseID": {
            "ResponseID": {
                "value": shopping_response_id_value
            }
        }
    }

    logger.info(f"Successfully built ServiceList request for airline {offer_owner}")
    return servicelist_request

def main():
    """Main function to generate and save ServiceListRQ from FlightPriceRS."""
    import sys
    from pathlib import Path

    input_file_name = "flightpriceRS.json" 
    input_file_path = Path(input_file_name)
    output_file_path = Path("servicelist_request_generated.json")

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
        # Build ServiceList request for the first offer
        servicelist_rq_payload = build_servicelist_request(flight_price_response_content, selected_offer_index=0)
        
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(servicelist_rq_payload, f, indent=2, ensure_ascii=False)
        print(f"ServiceListRQ successfully generated and saved to '{output_file_path}'")
            
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
Usage Examples for ServiceList Request Builder:

1. Standard usage with FlightPrice response:
   result = build_servicelist_request(flight_price_response, selected_offer_index=0)

2. Multi-airline response handling:
   # Automatically detects multi-airline response and filters airline-specific data
   result = build_servicelist_request(multi_airline_flight_price_response, selected_offer_index=2)

3. Integration with existing backend services:
   from scripts.build_servicelist_rq import build_servicelist_request
   
   async def get_services(flight_price_response):
       servicelist_request = build_servicelist_request(flight_price_response)
       # Use servicelist_request to call VDC ServiceList API
       return servicelist_request

The function automatically:
- Detects multi-airline vs single-airline responses
- Filters airline-specific data for multi-airline scenarios  
- Transforms airline-prefixed keys to standard keys (26-PAX1 → PAX1)
- Maps all required fields according to VDC API documentation
- Handles nested frontend data structures
- Maintains reference consistency across the booking flow

Key features:
- Full VDC API documentation mapping compliance
- Multi-airline support with automatic filtering
- Robust error handling and validation
- Airline prefix transformation for clean API calls
- Compatible with existing backend architecture
"""

# --- END OF FILE build_servicelist_rq.py ---