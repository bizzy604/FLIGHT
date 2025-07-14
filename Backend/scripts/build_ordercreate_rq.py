# --- START OF FILE build_ordercreate_rq.py (Consolidated) ---
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime # Keep for potential future use, e.g. logging

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
            # Look for airline-prefixed keys like "KL-PAX1", "QR-PAX1"
            if re.match(r'^[A-Z]{2,3}-', object_key):
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
        print(f"Error detecting multi-airline flight price response: {e}")
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

            # Try to extract from ResponseID value (format: base-id-AIRLINE)
            response_id_value = shopping_response_id.get('ResponseID', {}).get('value', '')
            if '-' in response_id_value:
                airline_code = response_id_value.split('-')[-1]
                if len(airline_code) <= 3:  # Valid airline code length
                    return airline_code

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

        return None

    except Exception as e:
        print(f"Error extracting airline from flight price response: {e}")
        return None

def _filter_airline_specific_data_for_order_create(flight_price_response: Dict[str, Any], airline_code: str) -> Dict[str, Any]:
    """
    Filter flight price response data to only include airline-specific elements for OrderCreate.

    Args:
        flight_price_response: The original FlightPrice response
        airline_code: The airline code to filter for

    Returns:
        Dict: Filtered flight price response with only airline-specific data
    """
    try:
        # Create a deep copy to avoid modifying the original
        filtered_response = json.loads(json.dumps(flight_price_response))

        # Filter DataLists
        data_lists = filtered_response.get('DataLists', {})

        # Filter AnonymousTravelerList
        travelers = data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        if not isinstance(travelers, list):
            travelers = [travelers] if travelers else []

        filtered_travelers = []
        traveler_key_mapping = {}

        for traveler in travelers:
            object_key = traveler.get('ObjectKey', '')
            # Include travelers that belong to this airline or have no airline prefix
            if object_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z]{2,3}-', object_key):
                # Transform airline-prefixed keys to standard keys
                if object_key.startswith(f"{airline_code}-"):
                    new_key = object_key.replace(f"{airline_code}-", "")
                    traveler_copy = traveler.copy()
                    traveler_copy['ObjectKey'] = new_key
                    traveler_key_mapping[object_key] = new_key
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
            if segment_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z]{2,3}-', segment_key):
                # Transform airline-prefixed keys to standard keys
                if segment_key.startswith(f"{airline_code}-"):
                    segment_copy = segment.copy()
                    segment_copy['SegmentKey'] = segment_key.replace(f"{airline_code}-", "")
                    filtered_segments.append(segment_copy)
                else:
                    filtered_segments.append(segment)

        if filtered_segments:
            data_lists['FlightSegmentList']['FlightSegment'] = filtered_segments

        # Filter FlightList
        flights = data_lists.get('FlightList', {}).get('Flight', [])
        if not isinstance(flights, list):
            flights = [flights] if flights else []

        filtered_flights = []
        for flight in flights:
            flight_key = flight.get('FlightKey', '')
            # Include flights that belong to this airline or have no airline prefix
            if flight_key.startswith(f"{airline_code}-") or not re.match(r'^[A-Z]{2,3}-', flight_key):
                # Transform airline-prefixed keys to standard keys
                if flight_key.startswith(f"{airline_code}-"):
                    flight_copy = flight.copy()
                    flight_copy['FlightKey'] = flight_key.replace(f"{airline_code}-", "")
                    filtered_flights.append(flight_copy)
                else:
                    filtered_flights.append(flight)

        if filtered_flights:
            data_lists['FlightList']['Flight'] = filtered_flights

        print(f"Filtered OrderCreate data for airline {airline_code}: {len(filtered_travelers)} travelers, {len(filtered_segments)} segments, {len(filtered_flights)} flights")
        return filtered_response

    except Exception as e:
        print(f"Error filtering airline-specific data for OrderCreate: {e}")
        return flight_price_response

def create_passenger_mapping(flight_price_response: Dict[str, Any], passengers_data: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Create a mapping of passenger indices to their corresponding ObjectKeys from the flight price response.
    
    Args:
        flight_price_response: The FlightPriceResponse JSON
        passengers_data: List of passenger input data
        
    Returns:
        Dict mapping passenger indices to ObjectKeys
    """
    # Get all offer items from the flight price response
    offer_items = []
    priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    if not isinstance(priced_offers, list):
        priced_offers = [priced_offers] if priced_offers else []
        
    for offer in priced_offers:
        offer_prices = offer.get('OfferPrice', [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        for price in offer_prices:
            if 'OfferItemID' in price:
                offer_items.append(price)
    
    # Create a mapping of PTC to list of ObjectKeys
    ptc_to_object_keys = {}
    anonymous_travelers = flight_price_response.get("DataLists", {}).get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
    if not isinstance(anonymous_travelers, list):
        anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
    
    for traveler in anonymous_travelers:
        ptc = traveler.get("PTC", {}).get("value")
        object_key = traveler.get("ObjectKey")
        if ptc and object_key:
            if ptc not in ptc_to_object_keys:
                ptc_to_object_keys[ptc] = []
            ptc_to_object_keys[ptc].append(object_key)
    
    # Create mapping of passenger indices to ObjectKeys
    passenger_mapping = {}
    used_object_keys = set()
    
    # First pass: Try to match by existing ObjectKey
    for idx, pax in enumerate(passengers_data):
        pax_ptc = pax.get("PTC")
        pax_key = pax.get("ObjectKey")
        
        if pax_key and pax_ptc in ptc_to_object_keys:
            # If the key exists and matches the PTC, keep it
            if pax_key in ptc_to_object_keys.get(pax_ptc, []):
                passenger_mapping[idx] = pax_key
                used_object_keys.add(pax_key)
    
    # Second pass: Assign remaining ObjectKeys based on PTC
    for idx, pax in enumerate(passengers_data):
        if idx in passenger_mapping:
            continue
            
        pax_ptc = pax.get("PTC")
        if pax_ptc in ptc_to_object_keys:
            for key in ptc_to_object_keys[pax_ptc]:
                if key not in used_object_keys:
                    passenger_mapping[idx] = key
                    used_object_keys.add(key)
                    break
    
    return passenger_mapping

def generate_order_create_rq(
    flight_price_response: Dict[str, Any],
    passengers_data: List[Dict[str, Any]],
    payment_input_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhanced OrderCreate request builder with multi-airline support.

    Args:
        flight_price_response: The FlightPriceResponse JSON as a Python dictionary.
        passengers_data: A list of dictionaries, where each dictionary contains
                         details for one passenger.
        payment_input_info: A dictionary containing payment details.

    Returns:
        dict: The generated OrderCreateRQ as a Python dictionary.
    """
    import json
    import logging
    logger = logging.getLogger(__name__)

    # DEBUG: Log the input data structure
    logger.info(f"[DEBUG] build_ordercreate_rq - Input flight_price_response keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
    logger.info(f"[DEBUG] build_ordercreate_rq - Input flight_price_response type: {type(flight_price_response)}")

    # Check if this is a multi-airline flight price response
    is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)
    logger.info(f"[DEBUG] Multi-airline OrderCreate detected: {is_multi_airline}")

    # Extract airline code for filtering
    airline_code = None
    if is_multi_airline:
        airline_code = _extract_airline_from_flight_price_response(flight_price_response)
        logger.info(f"[DEBUG] Extracted airline code for OrderCreate: {airline_code}")

        if airline_code:
            # Filter the flight price response to only include airline-specific data
            flight_price_response = _filter_airline_specific_data_for_order_create(flight_price_response, airline_code)
            logger.info(f"[DEBUG] Filtered flight price response for airline {airline_code}")
    
    # --- 1. Extract Key Information from FlightPriceResponse ---
    # Handle nested data structure from frontend
    actual_flight_price_response = flight_price_response
    
    # Check if data is nested under 'data.raw_response.data.raw_response' (deep frontend structure)
    if ('data' in flight_price_response and 
        'raw_response' in flight_price_response['data'] and 
        'data' in flight_price_response['data']['raw_response'] and 
        'raw_response' in flight_price_response['data']['raw_response']['data']):
        actual_flight_price_response = flight_price_response['data']['raw_response']['data']['raw_response']
        logger.info(f"[DEBUG] build_ordercreate_rq - Using data.raw_response.data.raw_response structure, keys: {list(actual_flight_price_response.keys())}")
    # Check if data is nested under 'data.raw_response' (frontend structure)
    elif 'data' in flight_price_response and 'raw_response' in flight_price_response['data']:
        actual_flight_price_response = flight_price_response['data']['raw_response']
        logger.info(f"[DEBUG] build_ordercreate_rq - Using data.raw_response structure, keys: {list(actual_flight_price_response.keys())}")
    # Check if data is nested under 'raw_response' (top-level)
    elif 'raw_response' in flight_price_response:
        actual_flight_price_response = flight_price_response['raw_response']
        logger.info(f"[DEBUG] build_ordercreate_rq - Using raw_response structure, keys: {list(actual_flight_price_response.keys())}")
    else:
        logger.info(f"[DEBUG] build_ordercreate_rq - Using direct structure, keys: {list(actual_flight_price_response.keys())}")
    
    fpr_shopping_response_id_node = actual_flight_price_response.get('ShoppingResponseID', {})
    logger.info(f"[DEBUG] build_ordercreate_rq - ShoppingResponseID node: {fpr_shopping_response_id_node}")
    
    fpr_response_id_value = fpr_shopping_response_id_node.get('ResponseID', {}).get('value')
    logger.info(f"[DEBUG] build_ordercreate_rq - Extracted ResponseID value: {fpr_response_id_value}")

    if not fpr_response_id_value:
        logger.error(f"[DEBUG] build_ordercreate_rq - ShoppingResponseID extraction failed. Full structure: {json.dumps(flight_price_response, indent=2, default=str)}")
        raise ValueError("ShoppingResponseID (value) missing from FlightPriceResponse")

    priced_flight_offers = actual_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    logger.info(f"[DEBUG] build_ordercreate_rq - PricedFlightOffers structure: {type(priced_flight_offers)}, length: {len(priced_flight_offers) if isinstance(priced_flight_offers, list) else 'Not a list'}")
    
    if not priced_flight_offers or not isinstance(priced_flight_offers, list) or not priced_flight_offers[0]:
        logger.error(f"[DEBUG] build_ordercreate_rq - PricedFlightOffer extraction failed. PricedFlightOffers: {actual_flight_price_response.get('PricedFlightOffers')}")
        raise ValueError("No PricedFlightOffer found or empty in FlightPriceResponse")
    
    selected_priced_offer = priced_flight_offers[0]
    selected_offer_id_node = selected_priced_offer.get('OfferID', {})
    selected_offer_id_value = selected_offer_id_node.get('value')
    selected_offer_owner = selected_offer_id_node.get('Owner')
    selected_offer_channel = selected_offer_id_node.get('Channel')

    if not selected_offer_id_value or not selected_offer_owner:
        raise ValueError("OfferID (value or Owner) missing from selected PricedFlightOffer in FlightPriceResponse")

    # --- 2. Initialize OrderCreateRQ Structure ---
    order_create_rq = {
        "Query": {
            "OrderItems": {
                "ShoppingResponse": {
                    "Owner": selected_offer_owner,
                    "ResponseID": {"value": fpr_response_id_value},
                    "Offers": {
                        "Offer": [{
                            "OfferID": {
                                "ObjectKey": selected_offer_id_value,
                                "value": selected_offer_id_value,
                                "Owner": selected_offer_owner,
                                "Channel": selected_offer_channel
                            },
                            "OfferItems": {"OfferItem": []} 
                        }]
                    }
                },
                "OfferItem": [] 
            },
            "DataLists": {
                "FareList": {
                    "FareGroup": [
                        {
                            "ListKey": fare_group_node.get("ListKey"),
                            **(
                                {"Fare": {"FareCode": fare_group_node["Fare"]["FareCode"]}}
                                if fare_group_node.get("Fare") and fare_group_node["Fare"].get("FareCode")
                                else {}
                            ),
                            "FareBasisCode": fare_group_node.get("FareBasisCode"),
                            **({} if fare_group_node.get("refs") is None else {"refs": fare_group_node["refs"]})
                        }
                        for fare_group_node in actual_flight_price_response.get("DataLists", {}).get("FareList", {}).get("FareGroup", [])
                    ]
                }
                # Add other DataLists if Verteil requires them (e.g., PenaltyList, ServiceList)
                # For example, your OrderCreateRS shows Penalties, so they might be needed here or are implicit.
            },
            "Passengers": {"Passenger": []},
            "Payments": {"Payment": []},
            **({"Metadata": flight_price_response["Metadata"]} if "Metadata" in flight_price_response and flight_price_response["Metadata"] is not None else {})
        }
    }

    # --- 3. Create passenger mapping and update passenger data ---
    passenger_mapping = create_passenger_mapping(actual_flight_price_response, passengers_data)
    
    # Update passenger data with the correct ObjectKeys
    for idx, pax in enumerate(passengers_data):
        if idx in passenger_mapping:
            pax["ObjectKey"] = passenger_mapping[idx]
        elif "ObjectKey" not in pax or not pax["ObjectKey"]:
            # Generate fallback ObjectKey if not mapped and not already present
            pax["ObjectKey"] = f"PAX{idx + 1}"
    
    # --- 4. Process OfferItems and link to ShoppingResponse.Offers ---
    offer_price_list_fprs = selected_priced_offer.get('OfferPrice', [])
    if not isinstance(offer_price_list_fprs, list):
        offer_price_list_fprs = [offer_price_list_fprs] if offer_price_list_fprs else []

    if not offer_price_list_fprs:
        raise ValueError("No OfferPrice entries found in the selected PricedFlightOffer")

    all_created_offer_item_ids_for_shopping_response = []

    for offer_price_entry_fprs in offer_price_list_fprs:
        fprs_offer_item_id_value = offer_price_entry_fprs.get("OfferItemID")
        if not fprs_offer_item_id_value:
            print(f"Warning: Missing OfferItemID in an OfferPrice entry: {offer_price_entry_fprs}")
            continue

        all_created_offer_item_ids_for_shopping_response.append({
            "OfferItemID": {
                "Owner": selected_offer_owner,
                "value": fprs_offer_item_id_value
            }
        })
        
        build_detailed_offer_item(
            actual_flight_price_response, 
            offer_price_entry_fprs, 
            fprs_offer_item_id_value,
            selected_offer_owner,
            order_create_rq["Query"]["OrderItems"]["OfferItem"]
        )
    
    order_create_rq["Query"]["OrderItems"]["ShoppingResponse"]["Offers"]["Offer"][0]["OfferItems"]["OfferItem"] = \
        all_created_offer_item_ids_for_shopping_response

    # --- 4. Process Other Sections ---
    process_passengers_for_order_create(passengers_data, order_create_rq["Query"]["Passengers"]["Passenger"])
    process_payments_for_order_create(payment_input_info, order_create_rq["Query"]["Payments"]["Payment"], actual_flight_price_response)
    
    return order_create_rq

def build_detailed_offer_item(
    flight_price_response: Dict[str, Any], 
    offer_price_entry_fprs: Dict[str, Any], 
    exact_offer_item_id: str,
    offer_owner: str,
    order_item_list_to_append_to: List[Dict[str, Any]]
):
    """Builds a single detailed OfferItem for OrderCreateRQ.Query.OrderItems.OfferItem[]"""
    
    requested_date_fprs = offer_price_entry_fprs.get("RequestedDate", {})
    price_detail_fprs = requested_date_fprs.get("PriceDetail", {})
    base_amount_fprs = price_detail_fprs.get("BaseAmount", {})
    taxes_total_fprs = price_detail_fprs.get("Taxes", {}).get("Total", {})

    current_traveler_refs_for_this_item = set()
    associations_fprs = requested_date_fprs.get("Associations", [])
    if not isinstance(associations_fprs, list):
        associations_fprs = [associations_fprs] if associations_fprs else []
    
    for assoc_fprs in associations_fprs:
        assoc_traveler_fprs = assoc_fprs.get("AssociatedTraveler", {})
        p_refs = assoc_traveler_fprs.get("TravelerReferences", [])
        if not isinstance(p_refs, list): p_refs = [p_refs] if p_refs else []
        for p_ref_val in p_refs:
            if p_ref_val: current_traveler_refs_for_this_item.add(p_ref_val)

    if not current_traveler_refs_for_this_item:
        print(f"Warning: No TravelerReferences for OfferItemID {exact_offer_item_id}. Skipping OfferItem detail.")
        return

    detailed_flight_item = {
        "Price": {
            "BaseAmount": base_amount_fprs,
            "Taxes": {"Total": taxes_total_fprs}
        },
        "OriginDestination": [],
        "refs": sorted(list(current_traveler_refs_for_this_item))
    }

    fprs_data_lists = flight_price_response.get("DataLists", {})
    fprs_od_list = fprs_data_lists.get("OriginDestinationList", {}).get("OriginDestination", [])
    if not isinstance(fprs_od_list, list): fprs_od_list = [fprs_od_list] if fprs_od_list else []
    
    fprs_segment_list = fprs_data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
    if not isinstance(fprs_segment_list, list): fprs_segment_list = [fprs_segment_list] if fprs_segment_list else []
    segment_map_fprs = {s.get("SegmentKey"): s for s in fprs_segment_list}

    # Determine if this is the first "type" of OfferItem being added (e.g., first ADT group, then CHD, etc.)
    # This helps decide whether to add OriginDestinationKey
    is_first_passenger_group_offer_item = not any(
        oi.get("OfferItemType", {}).get("DetailedFlightItem", [{}])[0].get("OriginDestination", [{}])[0].get("OriginDestinationKey")
        for oi in order_item_list_to_append_to
    )


    # The associations_fprs are for a specific PTC's price from FlightPriceRS.
    # Each association within that usually corresponds to an OD (e.g., outbound, inbound).
    for assoc_idx, assoc_fprs in enumerate(associations_fprs):
        applicable_flight_fprs = assoc_fprs.get("ApplicableFlight", {})
        flight_segment_refs_in_assoc = applicable_flight_fprs.get("FlightSegmentReference", [])
        if not isinstance(flight_segment_refs_in_assoc, list):
            flight_segment_refs_in_assoc = [flight_segment_refs_in_assoc] if flight_segment_refs_in_assoc else []

        od_flight_segments_for_order = []
        for seg_ref_obj_fprs in flight_segment_refs_in_assoc:
            seg_key = seg_ref_obj_fprs.get("ref")
            segment_detail_fprs = segment_map_fprs.get(seg_key)
            if segment_detail_fprs:
                flight_for_order = {
                    "Departure": segment_detail_fprs.get("Departure"),
                    "Arrival": segment_detail_fprs.get("Arrival"),
                    "ClassOfService": seg_ref_obj_fprs.get("ClassOfService"),
                    "MarketingCarrier": segment_detail_fprs.get("MarketingCarrier"),
                    "Equipment": segment_detail_fprs.get("Equipment"),
                    "FlightDetail": segment_detail_fprs.get("FlightDetail")
                }
                if is_first_passenger_group_offer_item: # Only add SegmentKey to the first flight segment
                    flight_for_order["SegmentKey"] = seg_key
                od_flight_segments_for_order.append(flight_for_order)
        
        if od_flight_segments_for_order:
            od_entry_for_order = {"Flight": od_flight_segments_for_order}
            if is_first_passenger_group_offer_item:
                # Try to find the corresponding OD key from FlightPriceRS DataLists
                assoc_od_ref_keys = applicable_flight_fprs.get("OriginDestinationReferences", [])
                if not isinstance(assoc_od_ref_keys, list): assoc_od_ref_keys = [assoc_od_ref_keys]
                
                if assoc_od_ref_keys and assoc_od_ref_keys[0]:
                    # Find this OD in fprs_od_list to use its key
                    # Your sample OrderCreateRQ uses OD1, OD2. These might align with the order from FlightPriceRS.
                    # A more robust way is to map using the actual keys if possible,
                    # but for now, we'll try to use the key from FlightPriceRS or assign sequentially.
                    matched_fprs_od = next((od for od in fprs_od_list if od.get("OriginDestinationKey") == assoc_od_ref_keys[0]), None)
                    if matched_fprs_od and matched_fprs_od.get("OriginDestinationKey"):
                         od_entry_for_order["OriginDestinationKey"] = matched_fprs_od.get("OriginDestinationKey")
                    else: # Fallback if not found by direct key match (e.g. if FlightPriceRS doesn't have OD1/OD2 keys)
                         od_entry_for_order["OriginDestinationKey"] = f"OD{assoc_idx + 1}" # e.g. OD1, OD2

            detailed_flight_item["OriginDestination"].append(od_entry_for_order)

    order_item_list_to_append_to.append({
        "OfferItemID": {"Owner": offer_owner, "value": exact_offer_item_id},
        "OfferItemType": {"DetailedFlightItem": [detailed_flight_item]}
    })


def process_passengers_for_order_create(
    passengers_input_data: List[Dict[str, Any]], 
    order_rq_passenger_list: List[Dict[str, Any]],
    flight_price_response: Dict[str, Any] = None
):
    if not passengers_input_data:
        print("Warning: No passenger data provided for OrderCreateRQ.")
        return

    # First, count infants and adults
    infants = [p for p in passengers_input_data if p.get("PTC") == "INF"]
    adults = [p for p in passengers_input_data if p.get("PTC") == "ADT"]
    
    # Validate that there are enough adults for the infants
    if infants and not adults:
        raise ValueError("At least one adult is required when traveling with an infant")
    
    # Ensure there are at least as many adults as infants
    if len(infants) > len(adults):
        raise ValueError(f"Not enough adults for the number of infants. Found {len(adults)} adults but {len(infants)} infants.")

    # Process each passenger
    for idx, pax_data in enumerate(passengers_input_data):
        object_key = pax_data.get("ObjectKey")
        # Generate ObjectKey if missing
        if not object_key:
            object_key = f"PAX{idx + 1}"
        ptc = pax_data.get("PTC")

        passenger_name_node = pax_data.get("Name", {})
        given_names_list = []
        given_names_input = passenger_name_node.get("Given", [])
        if isinstance(given_names_input, list):
            for gn in given_names_input:
                if isinstance(gn, str): 
                    given_names_list.append({"value": gn})
                elif isinstance(gn, dict) and "value" in gn: 
                    given_names_list.append(gn)
        elif isinstance(given_names_input, str): 
            given_names_list.append({"value": given_names_input})

        passenger_entry = {
            "ObjectKey": object_key,
            "PTC": {"value": ptc},
            "Name": {
                "Title": passenger_name_node.get("Title"),
                "Given": given_names_list,
                "Surname": {"value": passenger_name_node.get("Surname")}
            },
            "Gender": {"value": pax_data.get("Gender")},
            "Age": {"BirthDate": {"value": pax_data.get("BirthDate")}}
        }

        if "Contacts" in pax_data and pax_data["Contacts"]:
            passenger_entry["Contacts"] = pax_data["Contacts"]
        
        # Handle infant passenger association
        if ptc == "INF":
            # Find the index of this infant in the list of all infants
            infant_indices = [i for i, p in enumerate(passengers_input_data) if p.get("PTC") == "INF"]
            infant_idx = infant_indices.index(idx)
            
            # Get the corresponding adult's ObjectKey
            if infant_idx < len(adults):
                adult_key = adults[infant_idx].get("ObjectKey")
                passenger_entry["PassengerAssociation"] = adult_key
            else:
                # Fallback to first adult if we have more infants than adults (shouldn't happen due to earlier validation)
                passenger_entry["PassengerAssociation"] = adults[0].get("ObjectKey")
            
            # Set default title if not provided
            if not passenger_entry["Name"].get("Title"):
                passenger_entry["Name"]["Title"] = "Mstr" if pax_data.get("Gender", "").lower() == "male" else "Miss"
        
        passenger_documents_input = pax_data.get("Documents", [])
        if passenger_documents_input:
            formatted_documents = []
            for doc_data in passenger_documents_input:
                doc_entry = {
                    "Type": doc_data.get("Type"),
                    "ID": doc_data.get("ID")
                }
                doc_type_upper = str(doc_data.get("Type", "")).upper()

                if doc_type_upper in ["PT", "NI"]:
                    if not doc_data.get("DateOfExpiration"):
                        raise ValueError(f"DateOfExpiration is mandatory for doc type {doc_type_upper} for pax {object_key}")
                    if not doc_data.get("CountryOfIssuance"):
                        raise ValueError(f"CountryOfIssuance is mandatory for doc type {doc_type_upper} for pax {object_key}")
                
                if doc_type_upper == "ID" and not doc_data.get("CountryOfIssuance"):
                    raise ValueError(f"CountryOfIssuance is mandatory for doc type ID for pax {object_key}")

                # Add fields if they exist in doc_data
                for field_key in ["DateOfExpiration", "DateOfIssue", "CountryOfResidence"]:
                    if field_key in doc_data and doc_data[field_key] is not None:
                        doc_entry[field_key] = doc_data[field_key]
                
                # Ensure CountryOfIssuance is in uppercase
                if "CountryOfIssuance" in doc_data and doc_data["CountryOfIssuance"] is not None:
                    doc_entry["CountryOfIssuance"] = doc_data["CountryOfIssuance"].upper()
                
                formatted_documents.append(doc_entry)
            
            if formatted_documents:
                passenger_entry["PassengerIDInfo"] = {"PassengerDocument": formatted_documents}

        order_rq_passenger_list.append(passenger_entry)


def process_payments_for_order_create(
    payment_input_info: Dict[str, Any], 
    order_rq_payment_list: List[Dict[str, Any]],
    flight_price_response: Dict[str, Any] 
):
    if not payment_input_info:
        print("Warning: No payment info for OrderCreateRQ. Defaulting to Cash for testing.")
        order_rq_payment_list.append({"Amount": {"Code": "USD", "value": 0}, "Method": {"Cash": {"CashInd": True}}})
        return

    method_type = payment_input_info.get("MethodType", "Cash").upper()
    payment_details_input = payment_input_info.get("Details", {})

    # If Details is empty but we have card data at top level, use the top level data
    if not payment_details_input and method_type == "PAYMENTCARD":
        # Check if card details are at the top level (new backend format)
        if any(key in payment_input_info for key in ['CardNumberToken', 'CardType', 'CardHolderName']):
            payment_details_input = payment_input_info
    
    # Initialize total amount
    total_amount = 0.0
    currency_code = None
    
    # Get all offer prices from the flight price response
    offer_prices = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferPrice', [])
    
    # Calculate total amount from each offer item
    for offer in offer_prices:
        # Get price detail and total amount
        price_detail = offer.get('RequestedDate', {}).get('PriceDetail', {})
        total_amount_obj = price_detail.get('TotalAmount', {})
        simple_price = total_amount_obj.get('SimpleCurrencyPrice', {})
        
        # Get passenger count from associations
        passenger_count = 1  # Default to 1 if no associations found
        associations = offer.get('RequestedDate', {}).get('Associations', [])
        if associations and isinstance(associations, list):
            first_association = associations[0]
            traveler_refs = first_association.get('AssociatedTraveler', {}).get('TravelerReferences', [])
            if isinstance(traveler_refs, list):
                passenger_count = len(traveler_refs)
        
        # Calculate amount for this offer
        if 'value' in simple_price:
            amount = float(simple_price['value']) * passenger_count
            total_amount += amount
            
            # Set currency from the first valid offer
            if currency_code is None and 'Code' in simple_price:
                currency_code = simple_price['Code']
    
    # Create payment amount object with the calculated total
    payment_amount_for_rq = {"Code": currency_code, "value": round(total_amount, 2)}

    payment_method_object = {}
    if method_type == "CASH":
        # For CASH, check if CashInd is at top level when Details is empty
        cash_details = payment_details_input
        if not cash_details and 'CashInd' in payment_input_info:
            cash_details = payment_input_info

        payment_method_object = {"Cash": {"CashInd": cash_details.get("CashInd", True)}}
    elif method_type == "PAYMENTCARD":
        card_input_details = payment_details_input
        payment_card_node = {}

        # CardNumber (Token) - Schema says integer, but tokens are usually strings.
        # **CRITICAL CLARIFICATION POINT WITH VERTEIL**
        if "CardNumberToken" not in card_input_details: raise ValueError("CardNumberToken mandatory for PaymentCard.")
        card_num_input = card_input_details["CardNumberToken"]
        try:
            # Attempt conversion to int if Verteil schema strictly demands it for certain types of values.
            # For typical alphanumeric payment tokens, this will fail and string should be used.
            # payment_card_node["CardNumber"] = {"value": int(card_num_input)}
            payment_card_node["CardNumber"] = {"value": str(card_num_input)} # Safer default for tokens
        except ValueError:
            payment_card_node["CardNumber"] = {"value": str(card_num_input)} # Fallback to string if not purely numeric
            print(f"Warning: CardNumber.value for PaymentCard is documented as integer, but value '{card_num_input}' is not purely numeric. Sending as string.")


        if not card_input_details.get("EffectiveExpireDate", {}).get("Expiration"): raise ValueError("EffectiveExpireDate.Expiration (MMYY) mandatory.")
        payment_card_node["EffectiveExpireDate"] = {"Expiration": card_input_details["EffectiveExpireDate"]["Expiration"]}
        if card_input_details.get("EffectiveExpireDate", {}).get("Effective"):
            payment_card_node["EffectiveExpireDate"]["Effective"] = card_input_details["EffectiveExpireDate"]["Effective"]

        if "CardType" not in card_input_details: raise ValueError("CardType mandatory.")
        payment_card_node["CardType"] = card_input_details["CardType"]

        payment_card_node["Amount"] = {"value": round(total_amount, 2), "Code": currency_code}

        if "CardCode" not in card_input_details: raise ValueError("CardCode mandatory.")
        payment_card_node["CardCode"] = card_input_details["CardCode"]
        
        if "CardHolderName" not in card_input_details or not card_input_details.get("CardHolderName", {}).get("value"):
            raise ValueError("CardHolderName.value is mandatory for PaymentCard (or use refs if payer is passenger).")
        # Schema: "CardHolderName": { "refs": [], "value": "string" }
        ch_name_node = {"value": card_input_details["CardHolderName"].get("value")}
        if "refs" in card_input_details["CardHolderName"]: # If refs are provided (e.g. passenger ref)
            ch_name_node["refs"] = card_input_details["CardHolderName"]["refs"]
        else: # Default to empty refs list if not provided, as per schema example
            ch_name_node["refs"] = []
        payment_card_node["CardHolderName"] = ch_name_node


        if "CardHolderBillingAddress" in card_input_details:
            addr = card_input_details["CardHolderBillingAddress"]
            if not all(k in addr for k in ["Street", "PostalCode", "CityName"]) or \
               not addr.get("CountryCode", {}).get("value"):
                raise ValueError("If CardHolderBillingAddress provided, Street, PostalCode, CityName, CountryCode.value are mandatory.")
            
            # Ensure Street is a list of strings, not list of objects for OrderCreateRQ
            street_input = addr["Street"]
            if isinstance(street_input, list) and all(isinstance(s, str) for s in street_input):
                addr["Street"] = street_input # Already a list of strings
            elif isinstance(street_input, str):
                 addr["Street"] = [street_input]
            else: # If it's list of objects, extract values or adjust as per exact need
                 addr["Street"] = [s.get("value") for s in street_input if isinstance(s, dict) and "value" in s]
            
            payment_card_node["CardHolderBillingAddress"] = addr


        if "SeriesCode" in card_input_details and card_input_details["SeriesCode"].get("value"):
            payment_card_node["SeriesCode"] = {"value": str(card_input_details["SeriesCode"]["value"])}

        if "SecurePaymentVersion2" in card_input_details:
            payment_card_node["SecurePaymentVersion2"] = card_input_details["SecurePaymentVersion2"]
        
        if "ProductTypeCode" in card_input_details: # Schema shows [...], implies list or optional
            payment_card_node["ProductTypeCode"] = card_input_details["ProductTypeCode"]
            
        payment_method_object = {"PaymentCard": payment_card_node}

    elif method_type == "EASYPAY":
        ep_details = payment_details_input

        # If Details is empty but we have EasyPay data at top level, use the top level data
        if not ep_details and any(key in payment_input_info for key in ['AccountNumber', 'ExpirationDate']):
            ep_details = payment_input_info


        if "AccountNumber" not in ep_details or "ExpirationDate" not in ep_details:
            raise ValueError("AccountNumber and ExpirationDate are mandatory for EasyPay.")
        payment_method_object = {"EasyPay": {
            "AccountNumber": str(ep_details["AccountNumber"]),
            "ExpirationDate": ep_details["ExpirationDate"]
        }}
    elif method_type == "OTHER":
        # For OTHER, check if Remarks is at top level when Details is empty
        other_details = payment_details_input
        if not other_details and 'Remarks' in payment_input_info:
            other_details = payment_input_info

        remarks_input = other_details.get("Remarks", [])
        formatted_remarks = []
        if isinstance(remarks_input, list):
            for r_item in remarks_input:
                if isinstance(r_item, str): formatted_remarks.append({"value": r_item})
                elif isinstance(r_item, dict) and "value" in r_item: formatted_remarks.append(r_item)
        elif isinstance(remarks_input, str): # Single remark string
            formatted_remarks.append({"value": remarks_input})
        
        payment_method_object = {"Other": {"Remarks": {"Remark": formatted_remarks}}} if formatted_remarks else {"Other": {}}
    else:
        print(f"Warning: Unknown Payment.MethodType '{method_type}'. Defaulting to Cash.")
        payment_method_object = {"Cash": {"CashInd": True}}

    payment_entry = {"Amount": payment_amount_for_rq, "Method": payment_method_object}
    order_rq_payment_list.append(payment_entry)

if __name__ == "__main__":
    # This script is meant to be imported, not run directly
    print("This script provides functions for building OrderCreate requests.")
# --- END OF FILE build_ordercreate_rq.py (Consolidated) ---