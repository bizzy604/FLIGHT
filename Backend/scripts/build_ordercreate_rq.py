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

def create_offer_item_id(value: str, owner: str = "SQ", refs: Optional[List[str]] = None, channel: str = "NDC") -> Dict[str, Any]:
    """Create standardized OfferItemID structure - DRY principle
    NOTE: Owner should come from response data, not hardcoded
    """
    offer_item_id = {
        "value": value,
        "Owner": owner,  # Should be extracted from API response, not hardcoded
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

    # --- FIXED: Initialize OrderCreateRQ Structure with CORRECT ORDER ---
    order_create_rq = {
        "Query": {
            # 1. Passengers FIRST
            "Passengers": {"Passenger": []},
            
            # 2. OrderItems SECOND  
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
            
            # 3. DataLists THIRD
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
            # Use ObjectKey from response instead of creating hardcoded "PAX{idx + 1}"
            if idx < len(available_object_keys):
                pax["ObjectKey"] = available_object_keys[idx]
            else:
                # Only fallback if absolutely no ObjectKeys found in response
                print(f"WARNING: No ObjectKey found in response for passenger {idx}, using fallback")
                pax["ObjectKey"] = f"PAX{idx + 1}"
    
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
        passengers_data
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
        passenger_documents_input = pax_data.get("Documents", [])
        if passenger_documents_input:
            formatted_documents = []
            for doc_data in passenger_documents_input:
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
        base_amount = price_detail.get('BaseAmount', {})
        taxes_total = price_detail.get('Taxes', {}).get('Total', {})
        
        passenger_count = 1
        associations = offer.get('RequestedDate', {}).get('Associations', [])
        if associations and isinstance(associations, list):
            first_association = associations[0]
            traveler_refs = first_association.get('AssociatedTraveler', {}).get('TravelerReferences', [])
            if isinstance(traveler_refs, list):
                passenger_count = len(traveler_refs)
        
        base_value = base_amount.get('value', 0)
        tax_value = taxes_total.get('value', 0)
        if base_value > 0:
            flight_total = float(base_value + tax_value) * passenger_count
            total_amount += flight_total
            
            if currency_code is None and 'Code' in base_amount:
                currency_code = base_amount['Code']
    
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
    passengers_data: List[Dict[str, Any]] = None
):
    """Add seat and service selections to the OrderCreate request structure using ONLY response data."""
    print(f"DEBUG: Adding seat/service selections to OrderCreate")
    print(f"DEBUG: selected_services: {selected_services}")
    print(f"DEBUG: selected_seats: {selected_seats}")
    
    # Initialize OfferItem list if not exists
    if "OfferItem" not in order_create_rq["Query"]["OrderItems"]:
        order_create_rq["Query"]["OrderItems"]["OfferItem"] = []
    
    # Initialize DataLists.ServiceList if not exists
    if "DataLists" not in order_create_rq["Query"]:
        order_create_rq["Query"]["DataLists"] = {}
    if "ServiceList" not in order_create_rq["Query"]["DataLists"]:
        order_create_rq["Query"]["DataLists"]["ServiceList"] = {"Service": []}
    
    # Add selected services using ONLY servicelist_response data
    if servicelist_response and selected_services:
        print(f"DEBUG: Processing {len(selected_services)} selected services")
        
        services = extract_services_from_response(servicelist_response)
        print(f"DEBUG: Found {len(services)} services in servicelist_response")
        
        # Extract Owner from servicelist_response, not hardcoded
        service_owner = servicelist_response.get('ShoppingResponseID', {}).get('Owner', 
                        servicelist_response.get('Owner', 'SQ'))  # Use response Owner or fallback
        
        for service in services:
            service_key = service.get('ObjectKey')
            print(f"DEBUG: Checking service: {service_key}")
            if service_key in selected_services:
                print(f"DEBUG: Adding service to OrderCreate: {service_key}")
                
                # Create service OfferItem using ONLY response data
                service_offer_item = {
                    "OfferItemID": {
                        "value": service_key,
                        "Owner": service_owner,  # From response, not hardcoded
                        "Channel": "NDC"  # Only acceptable hardcode for NDC protocol
                    },
                    "OfferItemType": {
                        "OtherItem": [
                            {
                                "refs": service.get('refs', [service_key]),  # Use actual refs from response
                                "Price": service.get('Price', [{}])[0] if service.get('Price') else {}
                            }
                        ]
                    }
                }
                
                order_create_rq["Query"]["OrderItems"]["OfferItem"].append(service_offer_item)
                
                # Add to DataLists.ServiceList using ONLY response data
                add_to_service_list(order_create_rq["Query"]["DataLists"]["ServiceList"]["Service"], service)
            else:
                print(f"DEBUG: Service {service_key} not in selected services")
    
    # Add selected seats using ONLY seatavailability_response data
    if seatavailability_response and selected_seats:
        print(f"DEBUG: Processing {len(selected_seats)} selected seats")
        print(f"DEBUG: SeatAvailability response top-level keys: {list(seatavailability_response.keys())}")
        
        # Map seat positions to their data from response
        seat_position_to_data = {}
        
        # Extract seats from DataLists.SeatList.Seats 
        datalists = seatavailability_response.get('DataLists', {})
        seats = normalize_to_list(datalists.get('SeatList', {}).get('Seats', []))
        print(f"DEBUG: Found {len(seats)} seats in response")
        
        for seat in seats:
            location = seat.get('Location', {})
            if location:
                row_num = location.get('Row', {}).get('Number', {}).get('value', '')
                column = location.get('Column', '')
                
                if row_num and column:
                    seat_position = f"{row_num}{column}"
                    seat_position_to_data[seat_position] = seat
                    if seat_position == '59A':  # Debug specific seat
                        print(f"DEBUG: Found seat {seat_position} with refs {seat.get('refs', [])}")
        
        print(f"DEBUG: Mapped {len(seat_position_to_data)} seat positions")
        
        # Get Services from seatavailability_response for pricing (ONLY from response)
        seat_services = normalize_to_list(seatavailability_response.get('Services', {}).get('Service', []))
        service_map = {s.get('ObjectKey'): s for s in seat_services}
        
        # Extract Owner from seatavailability_response, not hardcoded
        seat_owner = seatavailability_response.get('ShoppingResponseID', {}).get('Owner', 
                    seatavailability_response.get('Owner', 'SQ'))  # Use response Owner or fallback
        
        # Process selected seats using ONLY response data
        for selected_seat in selected_seats:
            # First check if this is a pricing ObjectKey (like "PRICE4-SEG2")
            if selected_seat in service_map:
                # This is a pricing ObjectKey, use it directly
                seat_service = service_map[selected_seat]
                print(f"DEBUG: Found pricing ObjectKey {selected_seat}, using service directly")
                
                # Create seat OfferItem using the pricing ObjectKey
                seat_offer_item = {
                    "OfferItemID": {
                        "value": selected_seat,
                        "Owner": seat_owner,
                        "Channel": "NDC"
                    },
                    "OfferItemType": {
                        "SeatItem": [
                            {
                                "Price": seat_service.get('Price', [{}])[0] if seat_service.get('Price') else {},
                                "Descriptions": seat_service.get('Descriptions', {}),
                                "Location": {},  # Will be filled from seat data if available
                                "SeatAssociation": seat_service.get('Associations', [])
                            }
                        ]
                    }
                }
                
                # Try to find corresponding seat data for location
                for seat_position, seat_data in seat_position_to_data.items():
                    refs = seat_data.get('refs', [])
                    if selected_seat in refs:
                        location = seat_data.get('Location', {})
                        seat_offer_item["OfferItemType"]["SeatItem"][0]["Location"] = location
                        print(f"DEBUG: Found seat location {seat_position} for pricing ObjectKey {selected_seat}")
                        break
                
                order_create_rq["Query"]["OrderItems"]["OfferItem"].append(seat_offer_item)
                
                # Add to DataLists.ServiceList
                add_to_service_list(order_create_rq["Query"]["DataLists"]["ServiceList"]["Service"], seat_service)
                print(f"DEBUG: Added seat service using pricing ObjectKey: {selected_seat}")
                
            elif selected_seat in seat_position_to_data:
                # This is a seat position (like "17H"), use existing logic
                seat_data = seat_position_to_data[selected_seat]
                refs = seat_data.get('refs', [])
                location = seat_data.get('Location', {})
                
                print(f"DEBUG: Adding seat {selected_seat} with pricing refs: {refs}")
                
                # Handle case where seats don't have proper pricing refs
                if refs and any(ref.startswith('SEAT-POSITION-') for ref in refs):
                    # This is a seat position reference, not a pricing ObjectKey
                    # We need to create a seat service entry
                    print(f"DEBUG: Seat {selected_seat} has position reference, creating seat service")
                    
                    # Create a seat service entry for this seat
                    seat_service_key = f"SEAT-SERVICE-{selected_seat}"
                    
                    # Create seat OfferItem with seat location information
                    seat_offer_item = {
                        "OfferItemID": {
                            "value": seat_service_key,
                            "Owner": seat_owner,  # From response, not hardcoded
                            "Channel": "NDC"  # Only acceptable hardcode for NDC protocol
                        },
                        "OfferItemType": {
                            "SeatItem": [
                                {
                                    "Location": location,  # From seat data in response
                                    "Price": {
                                        "Total": {
                                            "value": 0,  # Default price, should come from actual pricing
                                            "Code": "USD"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                    
                    order_create_rq["Query"]["OrderItems"]["OfferItem"].append(seat_offer_item)
                    print(f"DEBUG: Added seat service for {selected_seat}")
                    
                elif refs and not any(ref.startswith('SEAT-POSITION-') for ref in refs):
                    # This has actual pricing refs, use them
                    primary_ref = refs[0]
                    seat_service = service_map.get(primary_ref)
                    
                    if seat_service:
                        print(f"DEBUG: Adding seat service to OrderCreate: {primary_ref}")
                        
                        # Create seat OfferItem using ONLY response data
                        seat_offer_item = {
                            "OfferItemID": {
                                "value": primary_ref,
                                "Owner": seat_owner,  # From response, not hardcoded
                                "Channel": "NDC"  # Only acceptable hardcode for NDC protocol
                            },
                            "OfferItemType": {
                                "SeatItem": [
                                    {
                                        "Price": seat_service.get('Price', [{}])[0] if seat_service.get('Price') else {},
                                        "Descriptions": seat_service.get('Descriptions', {}),
                                        "Location": location,  # From seat data in response
                                        "SeatAssociation": seat_service.get('Associations', [])
                                    }
                                ]
                            }
                        }
                        
                        order_create_rq["Query"]["OrderItems"]["OfferItem"].append(seat_offer_item)
                        
                        # Add to DataLists.ServiceList using ONLY response data
                        add_to_service_list(order_create_rq["Query"]["DataLists"]["ServiceList"]["Service"], seat_service)
                    else:
                        print(f"DEBUG: No service found for seat ref {primary_ref}")
                else:
                    # No refs at all, create basic seat service
                    print(f"DEBUG: Seat {selected_seat} has no refs, creating basic seat service")
                    
                    seat_service_key = f"SEAT-BASIC-{selected_seat}"
                    
                    seat_offer_item = {
                        "OfferItemID": {
                            "value": seat_service_key,
                            "Owner": seat_owner,
                            "Channel": "NDC"
                        },
                        "OfferItemType": {
                            "SeatItem": [
                                {
                                    "Location": location,
                                    "Price": seat_service.get('Price', [{}])[0] if seat_service and seat_service.get('Price') else {
                                        "Total": {
                                            "value": 0,
                                            "Code": "USD"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                    
                    order_create_rq["Query"]["OrderItems"]["OfferItem"].append(seat_offer_item)
                    print(f"DEBUG: Added basic seat service for {selected_seat}")
                    
                    # Also add to DataLists.ServiceList for consistency
                    basic_seat_service = {
                        "ObjectKey": seat_service_key,
                        "Name": {"value": f"Seat {selected_seat}"},
                        "Price": [{"Total": {"value": 0, "Code": "USD"}}]
                    }
                    add_to_service_list(order_create_rq["Query"]["DataLists"]["ServiceList"]["Service"], basic_seat_service)
            else:
                print(f"DEBUG: Seat position or pricing ObjectKey {selected_seat} not found in seat availability response")
    
    print(f"DEBUG: Finished adding seat/service selections to OrderCreate")

if __name__ == "__main__":
    print("This is the version of build_ordercreate_rq.py")
# --- END OF FILE build_ordercreate_rq.py---