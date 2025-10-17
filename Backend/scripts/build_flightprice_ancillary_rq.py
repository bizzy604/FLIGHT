# --- START OF FILE build_flightprice_ancillary_rq.py ---

import json
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

# Set up logger
logger = logging.getLogger(__name__)

def normalize_to_list(data: Union[List, Dict, Any]) -> List:
    """Utility function to ensure data is always a list - DRY principle"""
    if not isinstance(data, list):
        return [data] if data else []
    return data

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
        travelers = normalize_to_list(data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', []))

        for traveler in travelers:
            object_key = traveler.get('ObjectKey', '')
            # Look for airline-prefixed keys like "26-PAX1", "KQ-PAX1"
            if re.match(r'^[A-Z0-9]{2,3}-', object_key):
                return True

        # Check ShoppingResponseID structure
        shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
        if isinstance(shopping_response_id, dict):
            response_id_value = shopping_response_id.get('ResponseID', {}).get('value', '')
            # Multi-airline shopping response IDs typically end with airline code
            if '-' in response_id_value and len(response_id_value.split('-')[-1]) <= 3:
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
        # Method 1: Extract from ShoppingResponseID
        shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
        if isinstance(shopping_response_id, dict):
            owner = shopping_response_id.get('Owner')
            if owner:
                return owner

        # Method 2: Extract from PricedFlightOffers
        priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        priced_offers = normalize_to_list(priced_offers)
        
        for offer in priced_offers:
            offer_id = offer.get('OfferID', {})
            if isinstance(offer_id, dict):
                owner = offer_id.get('Owner')
                if owner:
                    return owner

        # Method 3: Extract from DataLists AnonymousTravelerList
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', []))
        
        for traveler in travelers:
            object_key = traveler.get('ObjectKey', '')
            # Extract airline code from prefixed keys like "26-PAX1"
            match = re.match(r'^([A-Z0-9]{2,3})-', object_key)
            if match:
                return match.group(1)

        return None

    except Exception as e:
        logger.error(f"Error extracting airline from flight price response: {e}")
        return None

def clean_airline_prefix_from_key(key: str, airline_code: str) -> str:
    """
    Remove airline prefix from a key.

    Args:
        key: The key with potential airline prefix
        airline_code: The airline code to remove

    Returns:
        str: The cleaned key without airline prefix
    """
    if not key or not airline_code:
        return key
    
    prefix = f"{airline_code}-"
    if key.startswith(prefix):
        return key[len(prefix):]
    
    return key

def build_flightprice_ancillary_request(
    flight_price_response: Dict[str, Any],
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None,
    selected_offer_index: int = 0
) -> Dict[str, Any]:
    """
    Build FlightPrice request for pricing selected seats and ancillaries.
    
    CRITICAL: This function now creates SEPARATE requests based on NDC specification.
    According to reference examples (9_FlightPriceRQ.json), ancillary items should be 
    priced separately, not all together in one request.
    
    This function handles the case where PricedInd is false, requiring additional pricing
    for selected services and seats before proceeding to OrderCreate.
    
    Args:
        flight_price_response: The original FlightPrice response
        servicelist_response: ServiceList response containing available services
        seatavailability_response: SeatAvailability response containing available seats
        selected_services: List of selected service ObjectKeys
        selected_seats: List of selected seat ObjectKeys
        selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
        Dict containing the FlightPrice request for ancillary pricing
        
    Note: If both seats and services are provided, this will only price ONE type.
          Use build_flightprice_request_for_services() and build_flightprice_request_for_seats()
          separately for proper sequential pricing.
    """
    try:
        logger.info("Building FlightPrice request for ancillary pricing")
        logger.warning("⚠️ DEPRECATION WARNING: Use build_flightprice_request_for_services() or build_flightprice_request_for_seats() for separate pricing")
        
        # Detect if this is a multi-airline response
        is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)
        airline_code = _extract_airline_from_flight_price_response(flight_price_response)
        
        logger.info(f"Multi-airline context: {is_multi_airline}, Airline: {airline_code}")
        
        # Extract base offer information from FlightPrice response
        priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        priced_offers = normalize_to_list(priced_offers)
        
        if not priced_offers or selected_offer_index >= len(priced_offers):
            raise ValueError(f"No priced offers found or invalid offer index: {selected_offer_index}")
        
        selected_offer = priced_offers[selected_offer_index]
        offer_id = selected_offer.get('OfferID', {})
        
        # Build base request structure
        request = {
            "Travelers": {
                "Traveler": []
            },
            "Query": {
                "OriginDestination": [],
                "Offers": {
                    "Offer": []
                }
            },
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": []
                }
            },
            "ShoppingResponseID": flight_price_response.get('ShoppingResponseID', {})
        }
        
        # Extract and build traveler information
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', []))
        
        for traveler in travelers:
            traveler_obj = {
                "AnonymousTraveler": [{
                    "PTC": traveler.get('PTC', {})
                }]
            }
            request["Travelers"]["Traveler"].append(traveler_obj)
            
            # Add to DataLists
            clean_object_key = clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '')
            request["DataLists"]["AnonymousTravelerList"]["AnonymousTraveler"].append({
                "ObjectKey": clean_object_key,
                "PTC": traveler.get('PTC', {})
            })
        
        # Extract and build flight segment information
        flight_segment_list = data_lists.get('FlightSegmentList', {})
        flight_segments = normalize_to_list(flight_segment_list.get('FlightSegment', []) if isinstance(flight_segment_list, dict) else flight_segment_list)
        
        for segment in flight_segments:
            origin_dest = {
                "Flight": [{
                    "SegmentKey": clean_airline_prefix_from_key(segment.get('SegmentKey', ''), airline_code) if airline_code else segment.get('SegmentKey', ''),
                    "Departure": {
                        "AirportCode": segment.get('Departure', {}).get('AirportCode', {}),
                        "Date": segment.get('Departure', {}).get('Date', ''),
                        "Time": segment.get('Departure', {}).get('Time', ''),
                        "Terminal": segment.get('Departure', {}).get('Terminal', {})
                    },
                    "Arrival": {
                        "AirportCode": segment.get('Arrival', {}).get('AirportCode', {}),
                        "Date": segment.get('Arrival', {}).get('Date', ''),
                        "Time": segment.get('Arrival', {}).get('Time', ''),
                        "Terminal": segment.get('Arrival', {}).get('Terminal', {})
                    },
                    "MarketingCarrier": segment.get('MarketingCarrier', {}),
                    "OperatingCarrier": segment.get('OperatingCarrier', {})
                }]
            }
            request["Query"]["OriginDestination"].append(origin_dest)
        
        # Build offer with selected items
        offer_item_ids = []
        
        # Add flight item (always included)
        offer_prices = normalize_to_list(selected_offer.get('OfferPrice', []))
        if offer_prices:
            flight_offer_item_id = offer_prices[0].get('OfferItemID', '')
            if flight_offer_item_id:
                offer_item_ids.append({
                    "value": flight_offer_item_id,
                    "refs": [clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '') for traveler in travelers]
                })
        
        # Add selected services
        if servicelist_response and selected_services:
            services = normalize_to_list(servicelist_response.get('Services', {}).get('Service', []))
            logger.info(f"Processing {len(services)} services, looking for: {selected_services}")
            
            for service in services:
                service_key = service.get('ObjectKey', '')
                logger.info(f"Checking service: {service_key}, PricedInd: {service.get('PricedInd', False)}")
                if service_key in selected_services:
                    # Check if this service requires pricing
                    priced_ind = service.get('PricedInd', False)  # Missing PricedInd means requires pricing
                    if not priced_ind:  # Only add if PricedInd is false or missing
                        service_offer_item = {
                            "value": service_key,
                            "refs": [clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '') for traveler in travelers],
                            "Quantity": 1  # Default quantity, can be made configurable
                        }
                        offer_item_ids.append(service_offer_item)
                        logger.info(f"Added service for pricing: {service_key}")
                    else:
                        logger.info(f"Skipped service {service_key} - already priced")
                else:
                    logger.info(f"Skipped service {service_key} - not selected")
        
        # Add selected seats
        if seatavailability_response and selected_seats:
            services = normalize_to_list(seatavailability_response.get('Services', {}).get('Service', []))
            logger.info(f"Processing {len(services)} seat services, looking for: {selected_seats}")
            
            # Extract seat data from DataLists.SeatList for dynamic seat information
            seat_data_map = _extract_seat_data_from_response(seatavailability_response)
            logger.info(f"Extracted seat data for {len(seat_data_map)} seats")
            
            for service in services:
                service_key = service.get('ObjectKey', '')
                logger.info(f"Checking seat service: {service_key}, PricedInd: {service.get('PricedInd', False)}")
                if service_key in selected_seats:
                    # Check if this seat requires pricing
                    priced_ind = service.get('PricedInd', False)  # Missing PricedInd means requires pricing
                    if not priced_ind:  # Only add if PricedInd is false or missing
                        # Extract dynamic seat information
                        seat_info = _extract_seat_selection_info(service, seat_data_map, travelers, airline_code)
                        
                        seat_offer_item = {
                            "value": service_key,
                            "refs": [clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '') for traveler in travelers],
                            "SelectedSeat": [seat_info],
                            "Quantity": 1
                        }
                        offer_item_ids.append(seat_offer_item)
                        logger.info(f"Added seat for pricing: {service_key} with dynamic seat data")
                    else:
                        logger.info(f"Skipped seat {service_key} - already priced")
                else:
                    logger.info(f"Skipped seat {service_key} - not selected")
        
        # Build the offer
        offer = {
            "OfferID": {
                "ObjectKey": offer_id.get('value', ''),
                "value": offer_id.get('value', ''),
                "Owner": offer_id.get('Owner', ''),
                "Channel": offer_id.get('Channel', 'NDC')
            },
            "OfferItemIDs": {
                "OfferItemID": offer_item_ids
            }
        }
        
        request["Query"]["Offers"]["Offer"].append(offer)
        
        logger.info(f"Built FlightPrice ancillary request with {len(offer_item_ids)} offer items")
        return request
        
    except Exception as e:
        logger.error(f"Error building FlightPrice ancillary request: {e}")
        raise

def _extract_seat_data_from_response(seatavailability_response: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract seat data from SeatAvailabilityRS response DataLists.SeatList.
    
    Args:
        seatavailability_response: SeatAvailabilityRS response
        
    Returns:
        Dict mapping service ObjectKeys to their associated seat data
    """
    seat_data_map = {}
    
    try:
        # Extract seats from DataLists.SeatList
        data_lists = seatavailability_response.get('DataLists', {})
        seat_list = data_lists.get('SeatList', {})
        seats = normalize_to_list(seat_list.get('Seats', []))
        
        logger.info(f"Extracting seat data from {len(seats)} seats")
        
        for seat in seats:
            # Get the refs (service ObjectKeys) for this seat
            refs = seat.get('refs', [])
            if not isinstance(refs, list):
                refs = [refs] if refs else []
            
            # Create seat data structure
            seat_data = {
                'Location': seat.get('Location', {}),
                'Characteristics': seat.get('Characteristics', {}),
                'SeatAssociation': seat.get('SeatAssociation', []),
                'ObjectKey': seat.get('ObjectKey', '')
            }
            
            # Map this seat data to all its service ObjectKeys
            for ref in refs:
                if ref:
                    seat_data_map[ref] = seat_data
                    logger.debug(f"Mapped seat data for service {ref}: {seat_data}")
        
        return seat_data_map
        
    except Exception as e:
        logger.error(f"Error extracting seat data from response: {e}")
        return {}

def _extract_seat_selection_info(
    service: Dict[str, Any], 
    seat_data_map: Dict[str, Dict[str, Any]], 
    travelers: List[Dict[str, Any]], 
    airline_code: Optional[str]
) -> Dict[str, Any]:
    """
    Extract dynamic seat selection information for FlightPriceRQ.
    
    Args:
        service: Seat service from SeatAvailabilityRS.Services.Service
        seat_data_map: Map of seat ObjectKeys to their data
        travelers: List of travelers
        airline_code: Airline code for reference cleaning
        
    Returns:
        Dict containing SelectedSeat structure with dynamic data
    """
    try:
        service_key = service.get('ObjectKey', '')
        logger.info(f"Extracting seat selection info for service: {service_key}")
        
        # Get seat data from the map
        seat_data = seat_data_map.get(service_key, {})
        location = seat_data.get('Location', {})
        characteristics = seat_data.get('Characteristics', {})
        seat_associations = seat_data.get('SeatAssociation', [])
        
        # Extract location information
        row_info = location.get('Row', {})
        column_info = location.get('Column', {})
        
        # Build dynamic location structure
        location_structure = {}
        
        # Add Column if available
        if column_info:
            if isinstance(column_info, dict):
                location_structure['Column'] = column_info.get('Position', column_info.get('value', ''))
            else:
                location_structure['Column'] = str(column_info)
        
        # Add Row if available
        if row_info:
            if isinstance(row_info, dict):
                row_number = row_info.get('Position', row_info.get('Number', {}).get('value', ''))
                if row_number:
                    location_structure['Row'] = {
                        "Number": {"value": str(row_number)}
                    }
            else:
                location_structure['Row'] = {
                    "Number": {"value": str(row_info)}
                }
        
        # Add Characteristics if available
        if characteristics:
            characteristics_list = []
            if isinstance(characteristics, dict):
                # Handle different characteristic structures
                for key, value in characteristics.items():
                    if key == 'Characteristic' and isinstance(value, list):
                        characteristics_list.extend(value)
                    elif key == 'Code':
                        characteristics_list.append({"Code": value})
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and 'Code' in item:
                                characteristics_list.append(item)
                            elif isinstance(item, str):
                                characteristics_list.append({"Code": item})
            
            if characteristics_list:
                location_structure['Characteristics'] = {
                    "Characteristic": characteristics_list
                }
        
        # Build SeatAssociation from service associations
        seat_association_list = []
        
        # Extract associations from service
        service_associations = service.get('Associations', [])
        service_associations = normalize_to_list(service_associations)
        
        for assoc in service_associations:
            # Extract traveler references
            traveler_refs = []
            if 'Traveler' in assoc:
                traveler_data = assoc['Traveler']
                if isinstance(traveler_data, dict):
                    traveler_refs = traveler_data.get('TravelerReferences', [])
                elif isinstance(traveler_data, list):
                    for t in traveler_data:
                        if isinstance(t, dict):
                            traveler_refs.extend(t.get('TravelerReferences', []))
            
            # Extract segment references
            segment_refs = []
            if 'Flight' in assoc:
                flight_data = assoc['Flight']
                if isinstance(flight_data, dict):
                    origin_dest_refs = flight_data.get('originDestinationReferencesOrSegmentReferences', [])
                    for ref in origin_dest_refs:
                        if isinstance(ref, dict) and 'SegmentReferences' in ref:
                            seg_refs = ref['SegmentReferences'].get('value', [])
                            segment_refs.extend(seg_refs if isinstance(seg_refs, list) else [seg_refs])
            
            # Clean traveler references
            cleaned_traveler_refs = []
            for ref in traveler_refs:
                cleaned_ref = clean_airline_prefix_from_key(ref, airline_code) if airline_code else ref
                cleaned_traveler_refs.append(cleaned_ref)
            
            # Clean segment references
            cleaned_segment_refs = []
            for ref in segment_refs:
                cleaned_ref = clean_airline_prefix_from_key(ref, airline_code) if airline_code else ref
                cleaned_segment_refs.append(cleaned_ref)
            
            # Create seat association
            if cleaned_traveler_refs and cleaned_segment_refs:
                seat_association_list.append({
                    "SegmentReferences": {
                        "value": cleaned_segment_refs
                    },
                    "TravelerReference": cleaned_traveler_refs[0]  # Use first traveler reference
                })
        
        # Fallback: if no associations found, use default values
        if not seat_association_list:
            # Use first traveler as fallback
            first_traveler_ref = "PAX1"
            if travelers:
                first_traveler = travelers[0]
                first_traveler_ref = clean_airline_prefix_from_key(
                    first_traveler.get('ObjectKey', 'PAX1'), 
                    airline_code
                ) if airline_code else first_traveler.get('ObjectKey', 'PAX1')
            
            seat_association_list.append({
                "SegmentReferences": {
                    "value": ["SEG1"]  # Default segment reference
                },
                "TravelerReference": first_traveler_ref
            })
        
        # Build the complete seat selection structure
        seat_selection = {
            "Location": location_structure,
            "SeatAssociation": seat_association_list
        }
        
        logger.info(f"Built dynamic seat selection for {service_key}: {seat_selection}")
        return seat_selection
        
    except Exception as e:
        logger.error(f"Error extracting seat selection info: {e}")
        # Return fallback structure
        return {
            "Location": {
                "Column": "A",
                "Row": {"Number": {"value": "1"}},
                "Characteristics": {
                    "Characteristic": [{"Code": "O"}]
                }
            },
            "SeatAssociation": [{
                "SegmentReferences": {"value": ["SEG1"]},
                "TravelerReference": "PAX1"
            }]
        }

def detect_pricing_required(
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Detect if additional pricing is required for selected services and seats.
    
    Args:
        servicelist_response: ServiceList response
        seatavailability_response: SeatAvailability response
        selected_services: List of selected service ObjectKeys
        selected_seats: List of selected seat positions (e.g., ['47G', '48A'])
    
    Returns:
        Dict containing pricing requirements:
        {
            "requires_pricing": bool,
            "services_require_pricing": List[str],
            "seats_require_pricing": List[str],
            "total_items_require_pricing": int
        }
    """
    result = {
        "requires_pricing": False,
        "services_require_pricing": [],
        "seats_require_pricing": [],
        "total_items_require_pricing": 0
    }
    
    try:
        # Check services
        if servicelist_response and selected_services:
            services = normalize_to_list(servicelist_response.get('Services', {}).get('Service', []))

            # Create mapping from service IDs to ObjectKeys using ServiceID structure
            service_id_to_object_key = {}
            for service in services:
                object_key = service.get('ObjectKey', '')
                service_id_dict = service.get('ServiceID', {})

                if object_key and isinstance(service_id_dict, dict):
                    service_id_value = service_id_dict.get('value', '')
                    if service_id_value:
                        # Map ServiceID.value to ObjectKey (e.g., "SRV16" -> "1-ServiceIdAF-16")
                        service_id_to_object_key[service_id_value] = object_key

            logger.info(f"Service ID to ObjectKey mapping: {service_id_to_object_key}")

            for service in services:
                service_key = service.get('ObjectKey', '')
                priced_ind = service.get('PricedInd', False)  # Missing PricedInd means requires pricing

                # Check if this service is selected (by ObjectKey or by service ID)
                is_selected = False
                selected_object_key = None

                # First try direct ObjectKey match
                if service_key in selected_services:
                    is_selected = True
                    selected_object_key = service_key

                # Then try service ID match (e.g., "SRV16" matches "1-ServiceIdAF-16")
                else:
                    for selected_service in selected_services:
                        if selected_service in service_id_to_object_key:
                            if service_id_to_object_key[selected_service] == service_key:
                                is_selected = True
                                selected_object_key = service_key
                                break

                if is_selected:
                    logger.info(f"Service {service_key} is selected (PricedInd: {priced_ind})")
                    if not priced_ind:
                        result["services_require_pricing"].append(selected_object_key or service_key)
                        result["requires_pricing"] = True
                        logger.info(f"Service {service_key} requires pricing (PricedInd=false)")
                else:
                    logger.debug(f"Service {service_key} not selected")
        
        # Check seats - FIXED: Handle pricing ObjectKeys directly
        if seatavailability_response and selected_seats:
            # Get seat services from response
            services = normalize_to_list(seatavailability_response.get('Services', {}).get('Service', []))
            
            # Check each selected seat (which are pricing ObjectKeys)
            for selected_seat in selected_seats:
                # Find the service that matches this pricing ObjectKey
                for service in services:
                    service_key = service.get('ObjectKey', '')
                    if service_key == selected_seat:
                        priced_ind = service.get('PricedInd', False)  # Missing PricedInd means requires pricing
                        if not priced_ind:
                            result["seats_require_pricing"].append(selected_seat)
                            result["requires_pricing"] = True
                            break  # Found one that requires pricing, no need to check others for this seat
        
        result["total_items_require_pricing"] = len(result["services_require_pricing"]) + len(result["seats_require_pricing"])
        
        logger.info(f"Pricing detection result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error detecting pricing requirements: {e}")
        return result

def build_flightprice_request_for_services(
    flight_price_response: Dict[str, Any],
    servicelist_response: Dict[str, Any],
    selected_services: List[str],
    selected_offer_index: int = 0,
    base_offer_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build FlightPrice request ONLY for pricing selected services.
    
    According to NDC specification (reference: 9_FlightPriceRQ.json), ancillary items 
    should be priced separately. This function creates a request with:
    - Base flight offer item (always included)
    - Selected SERVICE items only (no seats)
    
    Args:
        flight_price_response: The original FlightPrice response
        servicelist_response: ServiceList response containing available services
        selected_services: List of selected service ObjectKeys
        selected_offer_index: Index of the selected offer (default: 0)
        base_offer_id: If provided, use this OfferID instead of extracting from response
                       (useful for chaining multiple pricing calls)
    
    Returns:
        Dict containing the FlightPrice request for service pricing
    """
    try:
        logger.info(f"🔧 Building FlightPrice request for SERVICES ONLY: {selected_services}")
        
        # Detect multi-airline context
        is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)
        airline_code = _extract_airline_from_flight_price_response(flight_price_response)
        
        logger.info(f"Multi-airline context: {is_multi_airline}, Airline: {airline_code}")
        
        # Extract base offer information
        priced_offers = normalize_to_list(flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
        
        if not priced_offers or selected_offer_index >= len(priced_offers):
            raise ValueError(f"No priced offers found or invalid offer index: {selected_offer_index}")
        
        selected_offer = priced_offers[selected_offer_index]
        offer_id = selected_offer.get('OfferID', {})
        
        # Use base_offer_id if provided (for chained calls)
        if base_offer_id:
            offer_id = {
                "ObjectKey": base_offer_id,
                "value": base_offer_id,
                "Owner": offer_id.get('Owner', ''),
                "Channel": offer_id.get('Channel', 'NDC')
            }
        
        # Build base request structure
        request = _build_base_flightprice_request(flight_price_response, airline_code)
        
        # Build offer with selected items
        offer_item_ids = []
        
        # Extract travelers for refs
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', []))
        
        # 1. Add flight item (always included)
        offer_prices = normalize_to_list(selected_offer.get('OfferPrice', []))
        if offer_prices:
            flight_offer_item_id = offer_prices[0].get('OfferItemID', '')
            if flight_offer_item_id:
                offer_item_ids.append({
                    "value": flight_offer_item_id,
                    "refs": [clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '') for traveler in travelers]
                })
        
        # 2. Add selected services ONLY
        services = normalize_to_list(servicelist_response.get('Services', {}).get('Service', []))
        logger.info(f"Processing {len(services)} services, looking for: {selected_services}")
        
        for service in services:
            service_key = service.get('ObjectKey', '')
            if service_key in selected_services:
                # Check if this service requires pricing
                priced_ind = service.get('PricedInd', False)
                if not priced_ind:
                    service_offer_item = {
                        "value": service_key,
                        "refs": [clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '') for traveler in travelers],
                        "Quantity": 1
                    }
                    offer_item_ids.append(service_offer_item)
                    logger.info(f"✅ Added service for pricing: {service_key}")
        
        # Build the offer
        offer = {
            "OfferID": {
                "ObjectKey": offer_id.get('value', ''),
                "value": offer_id.get('value', ''),
                "Owner": offer_id.get('Owner', ''),
                "Channel": offer_id.get('Channel', 'NDC')
            },
            "OfferItemIDs": {
                "OfferItemID": offer_item_ids
            }
        }
        
        request["Query"]["Offers"]["Offer"].append(offer)
        
        logger.info(f"✅ Built FlightPrice request for SERVICES with {len(offer_item_ids)} offer items")
        return request
        
    except Exception as e:
        logger.error(f"❌ Error building FlightPrice request for services: {e}")
        raise

def build_flightprice_request_for_seats(
    flight_price_response: Dict[str, Any],
    seatavailability_response: Dict[str, Any],
    selected_seats: List[str],
    selected_offer_index: int = 0,
    base_offer_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build FlightPrice request ONLY for pricing selected seats.
    
    According to NDC specification (reference: 9_FlightPriceRQ.json), ancillary items 
    should be priced separately. This function creates a request with:
    - Base flight offer item (always included)
    - Selected SEAT items only (no services)
    
    Args:
        flight_price_response: The original FlightPrice response
        seatavailability_response: SeatAvailability response containing available seats
        selected_seats: List of selected seat ObjectKeys
        selected_offer_index: Index of the selected offer (default: 0)
        base_offer_id: If provided, use this OfferID instead of extracting from response
                       (useful for chaining multiple pricing calls)
    
    Returns:
        Dict containing the FlightPrice request for seat pricing
    """
    try:
        logger.info(f"🔧 Building FlightPrice request for SEATS ONLY: {selected_seats}")
        
        # Detect multi-airline context
        is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)
        airline_code = _extract_airline_from_flight_price_response(flight_price_response)
        
        logger.info(f"Multi-airline context: {is_multi_airline}, Airline: {airline_code}")
        
        # Extract base offer information
        priced_offers = normalize_to_list(flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
        
        if not priced_offers or selected_offer_index >= len(priced_offers):
            raise ValueError(f"No priced offers found or invalid offer index: {selected_offer_index}")
        
        selected_offer = priced_offers[selected_offer_index]
        offer_id = selected_offer.get('OfferID', {})
        
        # Use base_offer_id if provided (for chained calls)
        if base_offer_id:
            offer_id = {
                "ObjectKey": base_offer_id,
                "value": base_offer_id,
                "Owner": offer_id.get('Owner', ''),
                "Channel": offer_id.get('Channel', 'NDC')
            }
        
        # Build base request structure
        request = _build_base_flightprice_request(flight_price_response, airline_code)
        
        # Build offer with selected items
        offer_item_ids = []
        
        # Extract travelers for refs
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', []))
        
        # 1. Add flight item (always included)
        offer_prices = normalize_to_list(selected_offer.get('OfferPrice', []))
        if offer_prices:
            flight_offer_item_id = offer_prices[0].get('OfferItemID', '')
            if flight_offer_item_id:
                offer_item_ids.append({
                    "value": flight_offer_item_id,
                    "refs": [clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '') for traveler in travelers]
                })
        
        # 2. Add selected seats ONLY
        services = normalize_to_list(seatavailability_response.get('Services', {}).get('Service', []))
        logger.info(f"Processing {len(services)} seat services, looking for: {selected_seats}")
        
        # Extract seat data from DataLists.SeatList for dynamic seat information
        seat_data_map = _extract_seat_data_from_response(seatavailability_response)
        logger.info(f"Extracted seat data for {len(seat_data_map)} seats")
        
        for service in services:
            service_key = service.get('ObjectKey', '')
            if service_key in selected_seats:
                # Check if this seat requires pricing
                priced_ind = service.get('PricedInd', False)
                if not priced_ind:
                    # Extract dynamic seat information
                    seat_info = _extract_seat_selection_info(service, seat_data_map, travelers, airline_code)
                    
                    seat_offer_item = {
                        "value": service_key,
                        "refs": [clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '') for traveler in travelers],
                        "SelectedSeat": [seat_info],
                        "Quantity": 1
                    }
                    offer_item_ids.append(seat_offer_item)
                    logger.info(f"✅ Added seat for pricing: {service_key} with dynamic seat data")
        
        # Build the offer
        offer = {
            "OfferID": {
                "ObjectKey": offer_id.get('value', ''),
                "value": offer_id.get('value', ''),
                "Owner": offer_id.get('Owner', ''),
                "Channel": offer_id.get('Channel', 'NDC')
            },
            "OfferItemIDs": {
                "OfferItemID": offer_item_ids
            }
        }
        
        request["Query"]["Offers"]["Offer"].append(offer)
        
        logger.info(f"✅ Built FlightPrice request for SEATS with {len(offer_item_ids)} offer items")
        return request
        
    except Exception as e:
        logger.error(f"❌ Error building FlightPrice request for seats: {e}")
        raise

def _build_base_flightprice_request(
    flight_price_response: Dict[str, Any],
    airline_code: Optional[str]
) -> Dict[str, Any]:
    """
    Build the base structure for a FlightPrice request (common parts).
    
    Args:
        flight_price_response: The original FlightPrice response
        airline_code: Airline code for reference cleaning
    
    Returns:
        Dict containing base request structure with Travelers, OriginDestination, and DataLists
    """
    request = {
        "Travelers": {
            "Traveler": []
        },
        "Query": {
            "OriginDestination": [],
            "Offers": {
                "Offer": []
            }
        },
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": []
            }
        },
        "ShoppingResponseID": flight_price_response.get('ShoppingResponseID', {})
    }
    
    # Extract and build traveler information
    data_lists = flight_price_response.get('DataLists', {})
    travelers = normalize_to_list(data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', []))
    
    for traveler in travelers:
        traveler_obj = {
            "AnonymousTraveler": [{
                "PTC": traveler.get('PTC', {})
            }]
        }
        request["Travelers"]["Traveler"].append(traveler_obj)
        
        # Add to DataLists
        clean_object_key = clean_airline_prefix_from_key(traveler.get('ObjectKey', ''), airline_code) if airline_code else traveler.get('ObjectKey', '')
        request["DataLists"]["AnonymousTravelerList"]["AnonymousTraveler"].append({
            "ObjectKey": clean_object_key,
            "PTC": traveler.get('PTC', {})
        })
    
    # Extract and build flight segment information
    flight_segment_list = data_lists.get('FlightSegmentList', {})
    flight_segments = normalize_to_list(flight_segment_list.get('FlightSegment', []) if isinstance(flight_segment_list, dict) else flight_segment_list)
    
    for segment in flight_segments:
        origin_dest = {
            "Flight": [{
                "SegmentKey": clean_airline_prefix_from_key(segment.get('SegmentKey', ''), airline_code) if airline_code else segment.get('SegmentKey', ''),
                "Departure": {
                    "AirportCode": segment.get('Departure', {}).get('AirportCode', {}),
                    "Date": segment.get('Departure', {}).get('Date', ''),
                    "Time": segment.get('Departure', {}).get('Time', ''),
                    "Terminal": segment.get('Departure', {}).get('Terminal', {})
                },
                "Arrival": {
                    "AirportCode": segment.get('Arrival', {}).get('AirportCode', {}),
                    "Date": segment.get('Arrival', {}).get('Date', ''),
                    "Time": segment.get('Arrival', {}).get('Time', ''),
                    "Terminal": segment.get('Arrival', {}).get('Terminal', {})
                },
                "MarketingCarrier": segment.get('MarketingCarrier', {}),
                "OperatingCarrier": segment.get('OperatingCarrier', {})
            }]
        }
        request["Query"]["OriginDestination"].append(origin_dest)
    
    return request

# --- END OF FILE build_flightprice_ancillary_rq.py ---
