# --- START OF FILE build_ordercreate_rq.py ---
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime # Keep for potential future use, e.g. logging

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

    # Create passenger mapping and update passenger data
    passenger_mapping = create_passenger_mapping(actual_flight_price_response, passengers_data)
    
    for idx, pax in enumerate(passengers_data):
        if idx in passenger_mapping:
            pax["ObjectKey"] = passenger_mapping[idx]
        elif "ObjectKey" not in pax or not pax["ObjectKey"]:
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

        all_created_offer_item_ids_for_shopping_response.append({
            "OfferItemID": {
                "Owner": selected_offer_owner,
                "value": fprs_offer_item_id_value,
                "Channel": "NDC"  # FIXED: Add Channel
            }
        })
        
        build_detailed_offer_item_fixed(
            actual_flight_price_response, 
            offer_price_entry_fprs, 
            fprs_offer_item_id_value,
            selected_offer_owner,
            order_create_rq["Query"]["OrderItems"]["OfferItem"]
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
    
    return order_create_rq

def build_detailed_offer_item_fixed(
    flight_price_response: Dict[str, Any], 
    offer_price_entry_fprs: Dict[str, Any], 
    exact_offer_item_id: str,
    offer_owner: str,
    order_item_list_to_append_to: List[Dict[str, Any]]
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
            "Channel": "NDC"  # FIXED: Add Channel
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

    for idx, pax_data in enumerate(passengers_input_data):
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
        if contacts_data:
            contact_entry = {}
            
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
            
            # Email contact SECOND
            email = contacts_data.get("Email") or contacts_data.get("EmailContact", {}).get("Address")
            if isinstance(email, dict) and "value" in email:
                email = email["value"]
            if email:
                contact_entry["EmailContact"] = {
                    "Address": {"value": email}
                }
            
            # Phone contact THIRD
            phone_data = contacts_data.get("Phone") or contacts_data.get("PhoneContact", {})
            if phone_data:
                phone_number = phone_data.get("Number", phone_data.get("value", ""))
                country_code = phone_data.get("CountryCode", "1")
                if phone_number:
                    contact_entry["PhoneContact"] = {
                        "Application": phone_data.get("Application", "Home"),
                        "Number": [{
                            "value": str(phone_number),
                            "CountryCode": str(country_code)
                        }]
                    }
            
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
        services = servicelist_response.get('Services', {}).get('Service', [])
        if not isinstance(services, list):
            services = [services] if services else []
        
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
            object_key = pax.get("ObjectKey", "PAX1")
            
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

if __name__ == "__main__":
    print("This is the version of build_ordercreate_rq.py")
# --- END OF FILE build_ordercreate_rq.py---