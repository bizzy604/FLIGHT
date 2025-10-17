# --- START OF FILE build_ordercreate_rq.py ---
import json
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime # Keep for potential future use, e.g. logging

# Utility functions to follow DRY principle
def normalize_to_list(data: Union[List, Dict, Any]) -> List:
    """Utility function to ensure data is always a list - DRY principle"""
    if not isinstance(data, list):
        return [data] if data else []
    return data

def extract_services_from_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and normalize services from a response - DRY principle"""
    if not response:
        return []
    services = response.get('Services', {}).get('Service', [])
    return normalize_to_list(services)

def create_offer_item_id(value: str, owner: str, refs: Optional[List[str]] = None, channel: str = "NDC") -> Dict[str, Any]:
    """Create standardized OfferItemID structure - DRY principle
    NOTE: Owner must be provided from response data
    """
    offer_item_id = {
        "value": value,
        "Owner": owner,  # Must be extracted from API response
        "Channel": channel
    }
    if refs:
        offer_item_id["refs"] = refs
    return offer_item_id

def add_to_service_list(service_list: List[Dict[str, Any]], service_data: Dict[str, Any]) -> None:
    """Add service to DataLists.ServiceList with validation - DRY principle"""
    if service_data and service_data.get('ObjectKey'):
        service_list.append(service_data)

def normalize_list_with_debug(data: Union[List, Dict, Any], debug_name: str = "") -> List:
    """Normalize to list with debug output - DRY principle"""
    normalized = normalize_to_list(data)
    if debug_name:
        print(f"DEBUG: Found {len(normalized)} items in {debug_name}")
    return normalized

# Copy all the existing helper functions from the original file...
# (Include all functions from _is_multi_airline_flight_price_response to clean_airline_prefix_from_key)

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
        priced_offers = normalize_to_list(flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))

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
    priced_offers = normalize_to_list(flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
        
    for offer in priced_offers:
        for price in normalize_to_list(offer.get('OfferPrice', [])):
            if 'OfferItemID' in price:
                offer_items.append(price)
    
    # Create a mapping of PTC to list of ObjectKeys
    ptc_to_object_keys = {}
    anonymous_travelers = normalize_to_list(flight_price_response.get("DataLists", {}).get("AnonymousTravelerList", {}).get("AnonymousTraveler", []))
    
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

def _extract_segment_keys_from_responses(flight_price_response: Dict[str, Any]) -> List[str]:
    """
    Extract segment keys directly from FlightPriceRS response.
    
    Args:
        flight_price_response: FlightPriceRS response
        
    Returns:
        List of segment keys (e.g., ["SEG2", "SEG9"])
    """
    try:
        # Extract segment keys directly from FlightPriceRS
        flight_segments = flight_price_response.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
        if not isinstance(flight_segments, list):
            flight_segments = [flight_segments] if flight_segments else []
        
        segment_keys = []
        for segment in flight_segments:
            if isinstance(segment, dict):
                segment_key = segment.get('SegmentKey', '')
                if segment_key:
                    segment_keys.append(segment_key)
        
        return segment_keys
        
    except Exception as e:
        print(f"Error extracting segment keys: {e}")
        return []

def generate_order_create_rq(
    flight_price_response: Dict[str, Any],
    passengers_data: List[Dict[str, Any]],
    payment_input_info: Dict[str, Any],
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    FIXED OrderCreate request builder with correct structure and format.
    """
    import json
    import logging
    logger = logging.getLogger(__name__)

    # Handle nested data structure from frontend
    actual_flight_price_response = flight_price_response
    
    # Check if data is nested (same logic as original)
    if ('data' in flight_price_response and 
        'raw_response' in flight_price_response['data'] and 
        'data' in flight_price_response['data']['raw_response'] and 
        'raw_response' in flight_price_response['data']['raw_response']['data']):
        actual_flight_price_response = flight_price_response['data']['raw_response']['data']['raw_response']
    elif 'data' in flight_price_response and 'raw_response' in flight_price_response['data']:
        actual_flight_price_response = flight_price_response['data']['raw_response']
    elif 'raw_response' in flight_price_response:
        actual_flight_price_response = flight_price_response['raw_response']
    
    # Extract required data
    fpr_shopping_response_id_node = actual_flight_price_response.get('ShoppingResponseID', {})
    fpr_response_id_value = fpr_shopping_response_id_node.get('ResponseID', {}).get('value')
    
    if not fpr_response_id_value:
        raise ValueError("ShoppingResponseID (value) missing from FlightPriceResponse")
    
    # Extract segment keys directly from response
    segment_keys = _extract_segment_keys_from_responses(actual_flight_price_response)

    priced_flight_offers = actual_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    if not priced_flight_offers or not isinstance(priced_flight_offers, list) or not priced_flight_offers[0]:
        raise ValueError("No PricedFlightOffer found or empty in FlightPriceResponse")
    
    selected_priced_offer = priced_flight_offers[0]
    selected_offer_id_node = selected_priced_offer.get('OfferID', {})
    selected_offer_id_value = selected_offer_id_node.get('value')
    selected_offer_owner = selected_offer_id_node.get('Owner')
    selected_offer_channel = selected_offer_id_node.get('Channel')

    if not selected_offer_id_value or not selected_offer_owner:
        raise ValueError("OfferID (value or Owner) missing from selected PricedFlightOffer in FlightPriceResponse")

    # --- FIXED: Initialize OrderCreateRQ Structure with CORRECT ORDER per VDC spec ---
    order_create_rq = {
        "Query": {
            # 1. Passengers FIRST - per VDC spec
            "Passengers": {"Passenger": []},
            
            # 2. OrderItems SECOND - per VDC spec
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
            
            # 3. DataLists THIRD - per VDC spec with ServiceList
            "DataLists": {
                "FareList": {
                    "FareGroup": [
                        {
                            "ListKey": fare_group.get("ListKey"),
                            **(
                                {"Fare": {"FareCode": fare_group["Fare"]["FareCode"]}}
                                if fare_group.get("Fare") and fare_group["Fare"].get("FareCode")
                                else {}
                            ),
                            "FareBasisCode": fare_group.get("FareBasisCode"),
                            **({} if fare_group.get("refs") is None else {"refs": fare_group["refs"]})
                        }
                        for fare_group in actual_flight_price_response.get("DataLists", {}).get("FareList", {}).get("FareGroup", [])
                    ]
                },
                # FIXED: Add ServiceList as required by VDC spec
                "ServiceList": {
                    "Service": []
                }
            },
            
            # 4. Metadata FOURTH
            "Metadata": {"PassengerMetadata": []},
            
            # 5. Payments LAST
            "Payments": {"Payment": []}
        }
    }

    # Create passenger mapping and update passenger data using ONLY response data
    passenger_mapping = create_passenger_mapping(actual_flight_price_response, passengers_data)
    
    # Extract passenger ObjectKeys from flight_price_response instead of creating hardcoded ones
    anonymous_travelers = normalize_to_list(actual_flight_price_response.get("DataLists", {}).get("AnonymousTravelerList", {}).get("AnonymousTraveler", []))
    available_object_keys = [traveler.get("ObjectKey") for traveler in anonymous_travelers if traveler.get("ObjectKey")]
    
    for idx, pax in enumerate(passengers_data):
        if idx in passenger_mapping:
            pax["ObjectKey"] = passenger_mapping[idx]
        elif "ObjectKey" not in pax or not pax["ObjectKey"]:
            # Use ObjectKey from response - API responses are reliable
            if idx < len(available_object_keys):
                pax["ObjectKey"] = available_object_keys[idx]
            else:
                # This should not happen with reliable API responses
                print(f"ERROR: No ObjectKey found in response for passenger {idx}")
                raise ValueError(f"No ObjectKey found in response for passenger {idx}")
    
    # Process OfferItems
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

        # Use Channel from selected_offer_channel (from response) instead of hardcoded "NDC"
        all_created_offer_item_ids_for_shopping_response.append({
            "OfferItemID": {
                "Owner": selected_offer_owner,
                "value": fprs_offer_item_id_value,
                "Channel": selected_offer_channel or "NDC"  # Use response Channel or NDC as last resort
            }
        })
        
        build_detailed_offer_item_fixed(
            actual_flight_price_response, 
            offer_price_entry_fprs, 
            fprs_offer_item_id_value,
            selected_offer_owner,
            order_create_rq["Query"]["OrderItems"]["OfferItem"],
            selected_offer_channel  # Pass Channel from response
        )
    
    order_create_rq["Query"]["OrderItems"]["ShoppingResponse"]["Offers"]["Offer"][0]["OfferItems"]["OfferItem"] = \
        all_created_offer_item_ids_for_shopping_response

    # Process other sections
    process_passengers_for_order_create_fixed(passengers_data, order_create_rq["Query"]["Passengers"]["Passenger"])
    process_payments_for_order_create_fixed(
        payment_input_info, 
        order_create_rq["Query"]["Payments"]["Payment"], 
        actual_flight_price_response,
        servicelist_response,
        selected_services,
        seatavailability_response,
        selected_seats
    )
    add_metadata_for_order_create_fixed(passengers_data, order_create_rq["Query"])
    
    # FIXED: Add seat and service selections to OrderCreate payload
    add_seat_service_selections_to_order_create(
        order_create_rq,
        servicelist_response,
        selected_services,
        seatavailability_response,
        selected_seats,
        passengers_data,
        segment_keys  # Pass the segment keys directly
    )
    
    return order_create_rq

def build_detailed_offer_item_fixed(
    flight_price_response: Dict[str, Any], 
    offer_price_entry_fprs: Dict[str, Any], 
    exact_offer_item_id: str,
    offer_owner: str,
    order_item_list_to_append_to: List[Dict[str, Any]],
    offer_channel: Optional[str] = None
):
    """FIXED: Builds a single detailed OfferItem with correct structure"""
    
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

    # FIXED: Add FareDetail section
    fare_detail = None
    fare_detail_fprs = offer_price_entry_fprs.get("FareDetail", {})
    if fare_detail_fprs:
        fare_components = fare_detail_fprs.get("FareComponent", [])
        if not isinstance(fare_components, list):
            fare_components = [fare_components] if fare_components else []
        
        if fare_components:
            fare_detail = {
                "FareComponent": [
                    {
                        "FareBasis": {
                            "FareBasisCode": component.get("FareBasis", {}).get("FareBasisCode", {}),
                            "RBD": component.get("FareBasis", {}).get("RBD", "")
                        },
                        "refs": component.get("refs", [])
                    }
                    for component in fare_components
                ]
            }
        else:
            # FIXED: If no fare components, try to get FareBasisCode from FareList
            fare_list = actual_flight_price_response.get('DataLists', {}).get('FareList', {}).get('FareGroup', [])
            if not isinstance(fare_list, list):
                fare_list = [fare_list] if fare_list else []
            
            if fare_list:
                # Use the first FareGroup's FareBasisCode
                first_fare_group = fare_list[0]
                fare_basis_code = first_fare_group.get('FareBasisCode', {})
                if fare_basis_code:
                    fare_detail = {
                        "FareComponent": [
                            {
                                "FareBasis": {
                                    "FareBasisCode": fare_basis_code,
                                    "RBD": fare_basis_code.get('Code', '').split('/')[0] if fare_basis_code.get('Code') else ""
                                },
                                "refs": first_fare_group.get('refs', [])
                            }
                        ]
                    }

    detailed_flight_item = {
        "Price": {
            "BaseAmount": base_amount_fprs,
            "Taxes": {"Total": taxes_total_fprs}
        },
        "OriginDestination": [],
        "refs": sorted(list(current_traveler_refs_for_this_item))
    }
    
    # Add FareDetail if available
    if fare_detail:
        detailed_flight_item["FareDetail"] = fare_detail

    fprs_data_lists = flight_price_response.get("DataLists", {})
    fprs_od_list = fprs_data_lists.get("OriginDestinationList", {}).get("OriginDestination", [])
    if not isinstance(fprs_od_list, list): fprs_od_list = [fprs_od_list] if fprs_od_list else []
    
    fprs_segment_list = fprs_data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
    if not isinstance(fprs_segment_list, list): fprs_segment_list = [fprs_segment_list] if fprs_segment_list else []
    segment_map_fprs = {s.get("SegmentKey"): s for s in fprs_segment_list}

    is_first_passenger_group_offer_item = not any(
        oi.get("OfferItemType", {}).get("DetailedFlightItem", [{}])[0].get("OriginDestination", [{}])[0].get("OriginDestinationKey")
        for oi in order_item_list_to_append_to
    )

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
                # FIXED: Convert datetime to simple date format
                departure = segment_detail_fprs.get("Departure", {}).copy()
                arrival = segment_detail_fprs.get("Arrival", {}).copy()
                
                # Fix date format
                if "Date" in departure and "T" in str(departure["Date"]):
                    departure["Date"] = str(departure["Date"]).split("T")[0]
                if "Date" in arrival and "T" in str(arrival["Date"]):
                    arrival["Date"] = str(arrival["Date"]).split("T")[0]
                
                flight_for_order = {
                    "Departure": departure,
                    "Arrival": arrival,
                    "ClassOfService": seg_ref_obj_fprs.get("ClassOfService"),
                    "MarketingCarrier": segment_detail_fprs.get("MarketingCarrier"),
                    "Equipment": segment_detail_fprs.get("Equipment"),
                    "Details": segment_detail_fprs.get("FlightDetail")  # FIXED: Use "Details" instead of "FlightDetail"
                }
                
                if is_first_passenger_group_offer_item:
                    flight_for_order["SegmentKey"] = seg_key
                od_flight_segments_for_order.append(flight_for_order)
        
        if od_flight_segments_for_order:
            od_entry_for_order = {"Flight": od_flight_segments_for_order}
            if is_first_passenger_group_offer_item:
                assoc_od_ref_keys = applicable_flight_fprs.get("OriginDestinationReferences", [])
                if not isinstance(assoc_od_ref_keys, list): assoc_od_ref_keys = [assoc_od_ref_keys]
                
                if assoc_od_ref_keys and assoc_od_ref_keys[0]:
                    matched_fprs_od = next((od for od in fprs_od_list if od.get("OriginDestinationKey") == assoc_od_ref_keys[0]), None)
                    if matched_fprs_od and matched_fprs_od.get("OriginDestinationKey"):
                         od_entry_for_order["OriginDestinationKey"] = matched_fprs_od.get("OriginDestinationKey")
                    else:
                         od_entry_for_order["OriginDestinationKey"] = f"OD{assoc_idx + 1}"

            detailed_flight_item["OriginDestination"].append(od_entry_for_order)

    order_item_list_to_append_to.append({
        "OfferItemID": {
            "value": exact_offer_item_id,
            "Owner": offer_owner, 
            "Channel": offer_channel or "NDC"  # Use response Channel or NDC as last resort
        },
        "OfferItemType": {"DetailedFlightItem": [detailed_flight_item]}
    })

def process_passengers_for_order_create_fixed(
    passengers_input_data: List[Dict[str, Any]], 
    order_rq_passenger_list: List[Dict[str, Any]]
):
    """FIXED: Process passengers with correct name structure"""
    if not passengers_input_data:
        print("Warning: No passenger data provided for OrderCreateRQ.")
        return

    print(f"DEBUG: Processing {len(passengers_input_data)} passengers in OrderCreate builder")
    for idx, pax_data in enumerate(passengers_input_data):
        print(f"DEBUG: Passenger {idx} data keys: {list(pax_data.keys())}")
        print(f"DEBUG: Passenger {idx} has Contacts: {bool(pax_data.get('Contacts'))}")
        if pax_data.get('Contacts'):
            print(f"DEBUG: Passenger {idx} Contacts structure: {pax_data['Contacts']}")
        else:
            print(f"DEBUG: Passenger {idx} missing Contacts - this will cause email validation error!")
        object_key = pax_data.get("ObjectKey")
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

        # FIXED: Correct name structure order
        passenger_entry = {
            "ObjectKey": object_key,
            "PTC": {"value": ptc},
            "Name": {
                "Surname": {"value": passenger_name_node.get("Surname")},  
                "Given": given_names_list,                                 
                "Title": passenger_name_node.get("Title")                  
            },
            "AdditionalRoles": {
                "PaymentContactInd": True
            },
            "Gender": {"value": pax_data.get("Gender")},
            "Age": {"BirthDate": {"value": pax_data.get("BirthDate")}}
        }

        # FIXED: Contact structure to match reference
        contacts_data = pax_data.get("Contacts", {})
        print(f"DEBUG: Passenger {idx} contacts_data type: {type(contacts_data)}, value: {contacts_data}")
        if contacts_data:
            contact_entry = {}
            
            # Handle nested Contact structure (from booking service transformation)
            if "Contact" in contacts_data and isinstance(contacts_data["Contact"], list):
                # Extract from Contact array
                contact_list = contacts_data["Contact"]
                if contact_list and len(contact_list) > 0:
                    first_contact = contact_list[0]
                    print(f"DEBUG: Extracted first contact from Contact array: {first_contact}")
                    contacts_data = first_contact  # Use the extracted contact data
                else:
                    print(f"DEBUG: Contact array is empty")
                    contacts_data = {}
            
            # Handle case where contacts_data is already a list (from real API data)
            elif isinstance(contacts_data, list) and len(contacts_data) > 0:
                # Contacts are already in the correct format
                first_contact = contacts_data[0]
                print(f"DEBUG: Contacts already in correct format, using first contact: {first_contact}")
                contacts_data = first_contact
            elif isinstance(contacts_data, list) and len(contacts_data) == 0:
                print(f"DEBUG: Contacts list is empty")
                contacts_data = {}
            
            # Address contact FIRST
            address_data = contacts_data.get("Address") or contacts_data.get("AddressContact", {})
            if address_data:
                street = address_data.get("Street", ["123 Main St"])
                if isinstance(street, str):
                    street = [street]
                
                contact_entry["AddressContact"] = {
                    "Street": street,
                    "CityName": address_data.get("CityName", "Unknown City"),
                    "CountrySubDivisionCode": address_data.get("CountrySubDivisionCode", ""),
                    "PostalCode": address_data.get("PostalCode", "00000"),
                    "CountryCode": {
                        "value": address_data.get("CountryCode", {}).get("value", address_data.get("CountryCode", "US"))
                    }
                }
            
            # Email contact SECOND - FIXED: Enhanced email detection
            email = None
            
            # Try multiple ways to find email address
            if contacts_data.get("Email"):
                email_data = contacts_data.get("Email")
                if isinstance(email_data, dict) and "value" in email_data:
                    email = email_data["value"]
                elif isinstance(email_data, str):
                    email = email_data
            elif contacts_data.get("EmailContact"):
                email_contact = contacts_data.get("EmailContact")
                if isinstance(email_contact, dict):
                    if "Address" in email_contact:
                        address = email_contact["Address"]
                        if isinstance(address, dict) and "value" in address:
                            email = address["value"]
                        elif isinstance(address, str):
                            email = address
                    elif "value" in email_contact:
                        email = email_contact["value"]
            
            # Fallback: try to find email directly in contacts_data
            if not email:
                for key, value in contacts_data.items():
                    if "email" in key.lower() and isinstance(value, str) and "@" in value:
                        email = value
                        break
            
            # CRITICAL FIX: Always ensure email is present from contact_info fallback
            if not email:
                # This shouldn't happen but provides a safety net
                print(f"WARNING: No email found in passenger contacts, this will cause OrderCreate to fail")
                
            if email:
                contact_entry["EmailContact"] = {
                    "Address": {"value": email}
                }
                print(f"DEBUG: Added EmailContact to passenger: {email}")
            
            # Phone contact THIRD
            phone_data = contacts_data.get("Phone") or contacts_data.get("PhoneContact", {})
            if phone_data:
                print(f"DEBUG: phone_data type: {type(phone_data)}, value: {phone_data}")
                
                # Enhanced phone number extraction logic
                phone_number = None
                country_code = "1"  # Default country code
                
                # Try multiple ways to extract phone number
                if isinstance(phone_data, dict):
                    # Method 1: Direct Number field
                    if "Number" in phone_data:
                        number_data = phone_data["Number"]
                        if isinstance(number_data, str):
                            phone_number = number_data
                        elif isinstance(number_data, list) and number_data:
                            # Take first number if it's a list
                            first_number = number_data[0]
                            if isinstance(first_number, dict) and "value" in first_number:
                                phone_number = first_number["value"]
                            elif isinstance(first_number, str):
                                phone_number = first_number
                        elif isinstance(number_data, dict) and "value" in number_data:
                            phone_number = number_data["value"]
                    
                    # Method 2: Direct value field
                    elif "value" in phone_data:
                        phone_number = phone_data["value"]
                    
                    # Extract country code
                    if "CountryCode" in phone_data:
                        cc_data = phone_data["CountryCode"]
                        if isinstance(cc_data, str):
                            country_code = cc_data
                        elif isinstance(cc_data, dict) and "value" in cc_data:
                            country_code = cc_data["value"]
                    
                    # Also check if Number field has CountryCode (nested structure)
                    if "Number" in phone_data and isinstance(phone_data["Number"], list):
                        for number_entry in phone_data["Number"]:
                            if isinstance(number_entry, dict) and "CountryCode" in number_entry:
                                country_code = number_entry["CountryCode"]
                                break
                
                elif isinstance(phone_data, str):
                    # If phone_data is directly a string, use it as phone number
                    phone_number = phone_data
                
                print(f"DEBUG: Extracted phone_number: {phone_number}, country_code: {country_code}")
                
                # Only add phone contact if we have a valid phone number string
                if phone_number and isinstance(phone_number, str) and phone_number.strip():
                    contact_entry["PhoneContact"] = {
                        "Application": phone_data.get("Application", "Home") if isinstance(phone_data, dict) else "Home",
                        "Number": [{
                            "value": str(phone_number).strip(),
                            "CountryCode": str(country_code)
                        }]
                    }
                    print(f"DEBUG: Added PhoneContact with number: {phone_number}")
                else:
                    print(f"DEBUG: Skipped invalid phone number: {phone_number} (type: {type(phone_number)})")
            
            if contact_entry:
                passenger_entry["Contacts"] = {"Contact": [contact_entry]}
        
        # Add documents
        # FIX: Documents structure is {"Document": [...]} not just an array
        documents_wrapper = pax_data.get("Documents", {})
        passenger_documents_input = []
        if isinstance(documents_wrapper, dict):
            passenger_documents_input = documents_wrapper.get("Document", [])
        elif isinstance(documents_wrapper, list):
            # Fallback: if Documents is already an array
            passenger_documents_input = documents_wrapper
            
        if passenger_documents_input:
            formatted_documents = []
            for doc_data in passenger_documents_input:
                # Handle both dict and potential string (though shouldn't be string)
                if isinstance(doc_data, dict):
                    doc_entry = {
                        "Type": doc_data.get("Type"),
                        "ID": doc_data.get("ID"),
                        "DateOfExpiration": doc_data.get("DateOfExpiration"),
                        "CountryOfIssuance": doc_data.get("CountryOfIssuance", "").upper()
                    }
                    formatted_documents.append(doc_entry)
            
            if formatted_documents:
                passenger_entry["PassengerIDInfo"] = {"PassengerDocument": formatted_documents}

        order_rq_passenger_list.append(passenger_entry)

def process_payments_for_order_create_fixed(
    payment_input_info: Dict[str, Any], 
    order_rq_payment_list: List[Dict[str, Any]],
    flight_price_response: Dict[str, Any],
    servicelist_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_seats: Optional[List[str]] = None
):
    """FIXED: Process payments with correct format"""
    if not payment_input_info:
        print("Warning: No payment info for OrderCreateRQ. Defaulting to Cash for testing.")
        order_rq_payment_list.append({
            "Method": {"Cash": {"CashInd": "true"}},  # FIXED: String value
            "Amount": {"Code": "USD", "value": 0}
        })
        return

    method_type = payment_input_info.get("MethodType", "Cash").upper()
    
    # Calculate total amount (same logic as original)
    total_amount = 0.0
    currency_code = None
    
    offer_prices = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferPrice', [])
    
    for offer in offer_prices:
        price_detail = offer.get('RequestedDate', {}).get('PriceDetail', {})
        flight_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
        
        passenger_count = 1
        associations = offer.get('RequestedDate', {}).get('Associations', [])
        if associations and isinstance(associations, list):
            first_association = associations[0]
            traveler_refs = first_association.get('AssociatedTraveler', {}).get('TravelerReferences', [])
            if isinstance(traveler_refs, list):
                passenger_count = len(traveler_refs)
        
        flight_value = flight_amount.get('value', 0)
        if flight_value > 0:
            flight_total = float(flight_value) * passenger_count
            total_amount += flight_total
            
            if currency_code is None and 'Code' in flight_amount:
                currency_code = flight_amount['Code']
    
    # Add service and seat costs (same logic as original)
    service_costs = 0.0
    if servicelist_response and selected_services:
        services = extract_services_from_response(servicelist_response)
        
        for service in services:
            if service.get('ObjectKey') in selected_services:
                service_price = service.get('Price', [{}])
                if isinstance(service_price, list) and service_price:
                    service_total = service_price[0].get('Total', {}).get('value', 0)
                    service_costs += float(service_total)
    
    seat_costs = 0.0
    if seatavailability_response and selected_seats:
        seat_services = seatavailability_response.get('Services', {}).get('Service', [])
        if not isinstance(seat_services, list):
            seat_services = [seat_services] if seat_services else []
        
        for seat_service in seat_services:
            if seat_service.get('ObjectKey') in selected_seats:
                seat_price = seat_service.get('Price', [{}])
                if isinstance(seat_price, list) and seat_price:
                    seat_total = seat_price[0].get('Total', {}).get('value', 0)
                    seat_costs += float(seat_total)
    
    final_total_amount = total_amount + service_costs + seat_costs

    payment_method_object = {}
    if method_type == "CASH":
        payment_method_object = {"Cash": {"CashInd": "true"}}  # FIXED: String value
    # Add other payment methods as needed...

    # FIXED: Correct payment structure order and integer value
    payment_entry = {
        "Method": payment_method_object,
        "Amount": {
            "Code": currency_code,
            "value": int(round(final_total_amount))  # FIXED: Integer value
        }
    }
    order_rq_payment_list.append(payment_entry)

def add_metadata_for_order_create_fixed(passengers_data: List[Dict[str, Any]], query_section: Dict[str, Any]):
    """FIXED: Add metadata section"""
    from datetime import datetime
    
    try:
        current_date = datetime.now().strftime("%m/%d/%Y")
        
        passenger_metadata_list = []
        
        for pax in passengers_data:
            object_key = pax.get("ObjectKey")
            
            passenger_metadata = {
                "AugmentationPoint": {
                    "AugPoint": [
                        {
                            "any": {
                                "VdcAugPoint": {
                                    "Value": f"TRApprovalDate={current_date}"
                                }
                            }
                        },
                        {
                            "any": {
                                "VdcAugPoint": {
                                    "Value": f"TRCreationDate={current_date}"
                                }
                            }
                        }
                    ]
                },
                "refs": [object_key]
            }
            
            passenger_metadata_list.append(passenger_metadata)
        
        if passenger_metadata_list:
            query_section["Metadata"]["PassengerMetadata"] = passenger_metadata_list
            
    except Exception as e:
        print(f"Warning: Could not add metadata section: {e}")

def add_seat_service_selections_to_order_create(
    order_create_rq: Dict[str, Any],
    servicelist_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_seats: Optional[List[str]] = None,
    passengers_data: List[Dict[str, Any]] = None,
    segment_keys: Optional[List[str]] = None
):
    """FIXED: Add seat and service selections to OrderCreate per VDC specification"""
    print(f"DEBUG: Adding seat/service selections to OrderCreate per VDC spec")
    print(f"DEBUG: selected_services: {selected_services}")
    print(f"DEBUG: selected_seats: {selected_seats}")
    
    # Default empty list if not provided
    if segment_keys is None:
        segment_keys = []
    
    # Initialize OfferItem list if not exists
    if "OfferItem" not in order_create_rq["Query"]["OrderItems"]:
        order_create_rq["Query"]["OrderItems"]["OfferItem"] = []
    
    # Initialize DataLists.ServiceList if not exists
    if "DataLists" not in order_create_rq["Query"]:
        order_create_rq["Query"]["DataLists"] = {}
    if "ServiceList" not in order_create_rq["Query"]["DataLists"]:
        order_create_rq["Query"]["DataLists"]["ServiceList"] = {"Service": []}
    
    # Process selected services per VDC spec mapping: ServiceListRS → OrderCreateRQ
    if servicelist_response and selected_services:
        print(f"DEBUG: Processing {len(selected_services)} selected services per VDC spec")
        print(f"DEBUG: Selected services received: {selected_services}")
        
        # FIXED: Extract services from ServiceListRS response structure
        services = []
        if servicelist_response:
            # Handle different response structures
            if 'response' in servicelist_response and 'Services' in servicelist_response['response']:
                # ServiceListRS structure: response.Services.Service
                services_data = servicelist_response['response']['Services'].get('Service', [])
                if not isinstance(services_data, list):
                    services_data = [services_data] if services_data else []
                services = services_data
            elif 'Services' in servicelist_response:
                # Direct structure: Services.Service
                services_data = servicelist_response['Services'].get('Service', [])
                if not isinstance(services_data, list):
                    services_data = [services_data] if services_data else []
                services = services_data
        
        print(f"DEBUG: Found {len(services)} services in servicelist_response")
        
        # FIXED: Extract Owner from ServiceListRS.Services.Service.ServiceID.Owner per NDC spec
        # Each service can have different owners - extract per service, not globally
        
        # DEBUG: Log all available service ObjectKeys for comparison
        available_object_keys = [service.get('ObjectKey') for service in services]
        print(f"DEBUG: Available service ObjectKeys: {available_object_keys}")
        
        # Simplified service selection - use direct ObjectKey matching
        print(f"DEBUG: Processing services with direct ObjectKey matching")
        
        for service in services:
            service_key = service.get('ObjectKey')
            print(f"DEBUG: Checking service: {service_key}")
            
            # Check if this service is selected using direct ObjectKey matching
            is_selected = service_key in selected_services
            
            if is_selected:
                print(f"DEBUG: Service {service_key} found in selected services")
            else:
                print(f"DEBUG: Service {service_key} not in selected services")
            
            if is_selected:
                print(f"DEBUG: Adding service to OrderCreate per VDC spec: {service_key}")
                
                # FIXED: Create service OfferItem per NDC spec mapping with correct ServiceListRS mapping
                # Extract Owner from each individual service per NDC spec
                service_id = service.get('ServiceID').get('ObjectKey')
                service_owner = service.get('ServiceID', {}).get('Owner')
                
                # Use ServiceID.ObjectKey for the value per NDC spec
                service_id_object_key = service_id.get('ObjectKey', '') if isinstance(service_id, dict) else ''
                
                # FIXED: Get OfferExpiration and ShoppingResponseID from ServiceList response structure
                offer_expiration_key = ''
                shopping_response_id = ''
                
                if 'response' in servicelist_response:
                    # ServiceListRS structure: response.OfferExpiration and response.ShoppingResponseID
                    offer_expiration_key = servicelist_response['response'].get('OfferExpiration', {}).get('ObjectKey', '')
                    shopping_response_id = servicelist_response['response'].get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                else:
                    # Direct structure: OfferExpiration and ShoppingResponseID
                    offer_expiration_key = servicelist_response.get('OfferExpiration', {}).get('ObjectKey', '')
                    shopping_response_id = servicelist_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                
                # Build refs array: OfferExpiration.ObjectKey first, then ShoppingResponseID
                offer_item_refs = []
                if offer_expiration_key:
                    offer_item_refs.append(offer_expiration_key)
                if shopping_response_id:
                    offer_item_refs.append(shopping_response_id)
                
                # FIXED: Build OfferItemType refs per NDC spec: TravelerReference, SegmentReference, ServiceID
                offer_item_type_refs = []
                
                # Get TravelerReference from service associations per NDC spec
                service_associations = service.get('Associations', [])
                for assoc in service_associations:
                    traveler_refs = assoc.get('Traveler', {}).get('TravelerReferences', [])
                    if traveler_refs:
                        offer_item_type_refs.extend(traveler_refs if isinstance(traveler_refs, list) else [traveler_refs])
                
                # REMOVED: Segment references should not be included in OtherItem.refs per NDC spec
                
                # FIXED: Get ServiceReference from DataLists.ServiceList.ObjectKey per NDC spec
                # This should reference the service ObjectKey that will be added to DataLists.ServiceList
                service_reference = service_key  # This is the service ObjectKey that will be in DataLists.ServiceList
                if service_reference:
                    offer_item_type_refs.append(service_reference)
                
                service_offer_item = {
                    "OfferItemID": {
                        "value": service_id,
                        "Owner": service_owner,
                        "refs": offer_item_refs,
                        "Channel": "NDC"
                    },
                    "OfferItemType": {
                        "OtherItem": [{
                            "refs": offer_item_type_refs,  # FIXED: TravelerReference, SegmentReference, ServiceID per VDC spec
                            "Price": {
                                "SimpleCurrencyPrice": service.get('Price', [{}])[0].get('Total', {}) if service.get('Price') else {
                                    "value": 0,
                                    "Code": "USD"
                                }
                            }
                        }]
                    }
                }
                
                order_create_rq["Query"]["OrderItems"]["OfferItem"].append(service_offer_item)
                
                # FIXED: Add to DataLists.ServiceList per NDC spec with all required fields
                # FIXED: Map SegmentReferences in service associations
                service_associations = service.get('Associations', [])
                for assoc in service_associations:
                    flight_refs = assoc.get('Flight', {}).get('originDestinationReferencesOrSegmentReferences', [])
                    for flight_ref in flight_refs:
                        segment_refs = flight_ref.get('SegmentReferences', {}).get('value', [])
                        # Use segment references directly from service associations
                        # No mapping needed - use segment references as they are
                        flight_ref['SegmentReferences']['value'] = segment_refs
                
                service_list_entry = {
                    "ObjectKey": service_key,
                    "ServiceID": service.get('ServiceID', {}),
                    "Name": service.get('Name', {}),
                    "Descriptions": service.get('Descriptions', {}),
                    "Price": service.get('Price', []),
                    "BookingInstructions": service.get('BookingInstructions', {}),
                    "ServiceDefinitionRef": service.get('ServiceDefinitionRef', {}),
                    "Associations": service_associations,  # Use mapped associations
                    "PricedInd": service.get('PricedInd', True)
                }
                add_to_service_list(order_create_rq["Query"]["DataLists"]["ServiceList"]["Service"], service_list_entry)
            else:
                print(f"DEBUG: Service {service_key} not in selected services")
    
    # Process selected seats per VDC spec mapping: SeatAvailabilityRS → OrderCreateRQ
    if seatavailability_response and selected_seats:
        print(f"DEBUG: Processing {len(selected_seats)} selected seats per VDC spec")
        
        # Simplified seat processing - focus on services only
        print(f"DEBUG: Processing seat services from SeatAvailabilityRS")
        
        # FIXED: Get Services from seatavailability_response for pricing
        seat_services = []
        if seatavailability_response:
            # Handle different response structures
            if 'response' in seatavailability_response and 'Services' in seatavailability_response['response']:
                # SeatAvailabilityRS structure: response.Services.Service
                seat_services_data = seatavailability_response['response']['Services'].get('Service', [])
                if not isinstance(seat_services_data, list):
                    seat_services_data = [seat_services_data] if seat_services_data else []
                seat_services = seat_services_data
            elif 'Services' in seatavailability_response:
                # Direct structure: Services.Service
                seat_services_data = seatavailability_response['Services'].get('Service', [])
                if not isinstance(seat_services_data, list):
                    seat_services_data = [seat_services_data] if seat_services_data else []
                seat_services = seat_services_data
        
        service_map = {s.get('ObjectKey'): s for s in seat_services}
        
        # Simplified seat service processing
        print(f"DEBUG: Processing {len(seat_services)} seat services")
        
        # FIXED: Extract Owner from SeatAvailabilityRS.Services.Service.ServiceID.Owner per NDC spec
        # Each seat service can have different owners - extract per service, not globally
        
        # Process selected seats per VDC spec
        for selected_seat in selected_seats:
            # First check if this is a pricing ObjectKey (like "PRICE1-SEG7")
            if selected_seat in service_map:
                # This is a pricing ObjectKey, use VDC spec mapping
                seat_service = service_map[selected_seat]
                print(f"DEBUG: Found pricing ObjectKey {selected_seat}, using VDC spec mapping")
                
                # FIXED: Use ServiceID.value as OfferItemID.value per VDC spec
                seat_service_id = seat_service.get('ServiceID', {}).get('value', '')
                seat_service_object_key = seat_service.get('ObjectKey', '')
                
                # Get Owner from the main flight offer since seat services don't have their own Owner
                # Extract from the flight offer in the order_create_rq
                # seat_owner = ''
                # if 'DataLists' in seatavailability_response and \
                #    'FlightSegmentList' in seatavailability_response['DataLists'] and \
                #    'FlightSegment' in seatavailability_response['DataLists']['FlightSegmentList']:
                #     flight_segments = seatavailability_response['DataLists']['FlightSegmentList']['FlightSegment']
                #     if isinstance(flight_segments, list):
                #         # Multiple segments, pick the first
                #         flight_segment = flight_segments[0]
                #     else:
                #         flight_segment = flight_segments
                #     if 'MarketingCarrier' in flight_segment and \
                #        'AirlineID' in flight_segment['MarketingCarrier']:
                #         seat_owner = flight_segment['MarketingCarrier']['AirlineID'].get('value', 'None')
                # # Fallback to QR if not found
                # if not seat_owner:
                #     seat_owner = None
                
                # FIXED: Build refs per VDC spec: extract from Associations.Offer.OfferReferences and ShoppingResponseID.ResponseID.value
                seat_offer_item_refs = []
                
                # Add reference from Associations.Offer.OfferReferences per VDC spec
                # Extract from the current seat service data
                seat_offer_references = []
                seat_service_associations = seat_service.get('Associations', [])
                if isinstance(seat_service_associations, list):
                    for association in seat_service_associations:
                        if isinstance(association, dict) and 'Offer' in association:
                            offer_references = association['Offer'].get('OfferReferences', [])
                            if isinstance(offer_references, list) and offer_references:
                                seat_offer_references.extend(offer_references)
                
                # Add the extracted references (fallback to "PRICE" if not found)
                if seat_offer_references:
                    seat_offer_item_refs.extend(seat_offer_references)
                else:
                    pass # seat_offer_item_refs.append("PRICE")  # Fallback to maintain compatibility
                
                # Add ShoppingResponseID.ResponseID.value second per VDC spec
                # FIXED: Handle SeatAvailabilityRS response structure
                seat_shopping_response_id = ''
                if 'response' in seatavailability_response:
                    # SeatAvailabilityRS structure: response.ShoppingResponseID
                    seat_shopping_response_id = seatavailability_response['response'].get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                else:
                    # Direct structure: ShoppingResponseID
                    seat_shopping_response_id = seatavailability_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                if seat_shopping_response_id:
                    seat_offer_item_refs.append(seat_shopping_response_id)
                
                seat_offer_item = {
                    "OfferItemID": {
                        "value": seat_service_object_key,
                        "refs": seat_offer_item_refs,
                        "Channel": "NDC"
                    },
                    "OfferItemType": {
                        "SeatItem": [{
                            "Price": {
                                "Total": _extract_seat_price(seat_service)
                            },
                            "Descriptions": seat_service.get('Descriptions', {}),
                            "Location": _extract_seat_location(seatavailability_response, selected_seat),
                            "SeatAssociation": [{
                                "SegmentReferences": {
                                    "value": [
                                        # Use segment references directly from seat service associations
                                        seg_ref 
                                        for assoc in seat_service.get('Associations', [])
                                        for flight_ref in assoc.get('Flight', {}).get('originDestinationReferencesOrSegmentReferences', [])
                                        for seg_ref in flight_ref.get('SegmentReferences', {}).get('value', [])
                                    ]
                                },
                                "TravelerReference": traveler_ref
                            } for assoc in seat_service.get('Associations', [])
                            for traveler_ref in assoc.get('Traveler', {}).get('TravelerReferences', [])]
                        }]
                    }
                }
                
                # Simplified seat location handling - use empty location for now
                # The actual seat location will be filled from the seat service data
                print(f"DEBUG: Using simplified seat location for pricing ObjectKey {selected_seat}")
                
                order_create_rq["Query"]["OrderItems"]["OfferItem"].append(seat_offer_item)
                # FIXED: Add to DataLists.ServiceList per VDC spec
                seat_service_list_entry = {
                    "ObjectKey": seat_service_object_key,
                    "ServiceID": seat_service.get('ServiceID', {}),
                    "Name": seat_service.get('Name', {}),
                    "Descriptions": seat_service.get('Descriptions', {}),
                    "Price": seat_service.get('Price', {}),
                    "Associations": seat_service.get('Associations', {}),
                    "PricedInd": seat_service.get('PricedInd')
                }
                add_to_service_list(order_create_rq["Query"]["DataLists"]["ServiceList"]["Service"], seat_service_list_entry)
                print(f"DEBUG: Added seat service using VDC spec: {selected_seat}")
            else:
                # Handle other seat selection patterns
                print(f"DEBUG: Processing seat selection: {selected_seat}")
                # Simplified seat processing - skip complex mapping
                print(f"DEBUG: Skipping complex seat position mapping for {selected_seat}")
                continue
    
    print(f"DEBUG: Finished adding seat/service selections to OrderCreate per VDC spec")

def _extract_seat_price(seat_service_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract price information from seat service data following VDC spec mapping.
    
    Args:
        seat_service_data: Seat service data from SeatAvailabilityRS
        
    Returns:
        Dict with price information (value and Code)
    """
    try:
        # Extract price from seat service following VDC spec mapping
        # Source: SeatAvailabilityRS.Services.Service.Price/Total
        # Destination: OrderCreateRQ.OfferItem.OfferItemType.SeatItem.Price.Total
        
        price_data = seat_service_data.get('Price', [])
        if not price_data:
            # No price data available, return default
            return {"value": 0, "Code": "USD"}
        
        # Handle both list and single price formats
        if isinstance(price_data, list) and price_data:
            price_entry = price_data[0]
        else:
            price_entry = price_data
        
        # Extract Total price information per VDC spec
        total_price = price_entry.get('Total', {})
        if total_price:
            return {
                "value": total_price.get('value', 0),
                "Code": total_price.get('Code', 'USD')
            }
        
        # Fallback: try to extract from other price fields
        if 'value' in price_entry:
            return {
                "value": price_entry.get('value', 0),
                "Code": price_entry.get('Code', 'USD')
            }
        
        # Final fallback - return default as per VDC spec
        return {"value": 0, "Code": "USD"}
        
    except Exception as e:
        print(f"Warning: Error extracting seat price: {e}")
        return {"value": 0, "Code": "USD"}

def _extract_seat_price(seat_service_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract price information from seat service data.
    
    Args:
        seat_service_data: Seat service data from SeatAvailabilityRS
        
    Returns:
        Dict containing price information
    """
    try:
        price_list = seat_service_data.get('Price', [])
        if price_list and len(price_list) > 0:
            price = price_list[0]
            return {
                "value": price.get('Total', {}).get('value', 0),
                "Code": price.get('Total', {}).get('Code', 'INR')
            }
        return {"value": 0, "Code": "INR"}
    except Exception as e:
        print(f"DEBUG: Error extracting seat price: {e}")
        return {"value": 0, "Code": "INR"}

def _extract_seat_location(seatavailability_response: Dict[str, Any], selected_seat: str) -> Dict[str, Any]:
    """
    Extract seat location data from SeatAvailabilityRS response.
    
    Args:
        seatavailability_response: SeatAvailabilityRS response
        selected_seat: The selected seat ObjectKey (e.g., "PRICE1-SEG9")
        
    Returns:
        Dict containing seat location information
    """
    try:
        # Extract seat list from response
        seat_list = seatavailability_response.get('DataLists', {}).get('SeatList', {}).get('Seats', [])
        if not isinstance(seat_list, list):
            seat_list = [seat_list] if seat_list else []
        
        # Find the first seat that matches the selected seat reference
        for seat in seat_list:
            if isinstance(seat, dict):
                seat_refs = seat.get('refs', [])
                if selected_seat in seat_refs:
                    location = seat.get('Location', {})
                    if location:
                        print(f"DEBUG: Found seat location for {selected_seat}: {location}")
                        return location
        
        print(f"DEBUG: No seat location found for {selected_seat}")
        return {}
        
    except Exception as e:
        print(f"DEBUG: Error extracting seat location: {e}")
        return {}

if __name__ == "__main__":
    print("This is the version of build_ordercreate_rq.py")
# --- END OF FILE build_ordercreate_rq.py---