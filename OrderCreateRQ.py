# --- START OF FILE build_ordercreate_rq.py (Consolidated) ---
import json
from typing import Dict, Any, List
from datetime import datetime # Keep for potential future use, e.g. logging

def generate_order_create_rq(
    flight_price_response: Dict[str, Any],
    passengers_data: List[Dict[str, Any]], 
    payment_input_info: Dict[str, Any]     
) -> Dict[str, Any]:
    """
    Generate OrderCreateRQ from FlightPriceResponse with dynamic passenger (including documents) 
    and payment data.
    
    Args:
        flight_price_response: The FlightPriceResponse JSON as a Python dictionary.
        passengers_data: A list of dictionaries, where each dictionary contains
                         details for one passenger.
        payment_input_info: A dictionary containing payment details.
        
    Returns:
        dict: The generated OrderCreateRQ as a Python dictionary.
    """
    # --- 1. Extract Key Information from FlightPriceResponse ---
    fpr_shopping_response_id_node = flight_price_response.get('ShoppingResponseID', {})
    fpr_response_id_value = fpr_shopping_response_id_node.get('ResponseID', {}).get('value')
    fpr_owner = fpr_shopping_response_id_node.get('Owner')

    if not fpr_response_id_value or not fpr_owner:
        raise ValueError("ShoppingResponseID (value or Owner) missing from FlightPriceResponse")

    priced_flight_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    if not priced_flight_offers or not isinstance(priced_flight_offers, list) or not priced_flight_offers[0]:
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
                    "Owner": fpr_owner,
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
                "FareList": flight_price_response.get("DataLists", {}).get("FareList", {"FareGroup": []}),
                # Add other DataLists if Verteil requires them (e.g., PenaltyList, ServiceList)
                # For example, your OrderCreateRS shows Penalties, so they might be needed here or are implicit.
            },
            "Passengers": {"Passenger": []},
            "Payments": {"Payment": []},
            "Metadata": flight_price_response.get("Metadata", {"Other": {"OtherMetadata": []}})
        }
    }

    # --- 3. Process OfferItems and link to ShoppingResponse.Offers ---
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
            flight_price_response, 
            offer_price_entry_fprs, 
            fprs_offer_item_id_value,
            selected_offer_owner,
            order_create_rq["Query"]["OrderItems"]["OfferItem"]
        )
    
    order_create_rq["Query"]["OrderItems"]["ShoppingResponse"]["Offers"]["Offer"][0]["OfferItems"]["OfferItem"] = \
        all_created_offer_item_ids_for_shopping_response

    # --- 4. Process Other Sections ---
    process_passengers_for_order_create(passengers_data, order_create_rq["Query"]["Passengers"]["Passenger"])
    process_payments_for_order_create(payment_input_info, order_create_rq["Query"]["Payments"]["Payment"], flight_price_response)
    
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
                    "FlightDetail": segment_detail_fprs.get("FlightDetail"),
                    "SegmentKey": seg_key
                }
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
    order_rq_passenger_list: List[Dict[str, Any]]
):
    if not passengers_input_data:
        print("Warning: No passenger data provided for OrderCreateRQ.")
        return

    for pax_data in passengers_input_data:
        passenger_name_node = pax_data.get("Name", {})
        given_names_list = []
        given_names_input = passenger_name_node.get("Given", [])
        if isinstance(given_names_input, list):
            for gn in given_names_input:
                if isinstance(gn, str): given_names_list.append({"value": gn})
                elif isinstance(gn, dict) and "value" in gn: given_names_list.append(gn)
        elif isinstance(given_names_input, str): given_names_list.append({"value": given_names_input})

        passenger_entry = {
            "ObjectKey": pax_data.get("ObjectKey"),
            "PTC": {"value": pax_data.get("PTC")},
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
        
        if pax_data.get("PTC") == "INF" and "PassengerAssociation" in pax_data:
            passenger_entry["PassengerAssociation"] = pax_data["PassengerAssociation"]
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
                        raise ValueError(f"DateOfExpiration is mandatory for doc type {doc_type_upper} for pax {pax_data.get('ObjectKey')}")
                    if not doc_data.get("CountryOfIssuance"):
                        raise ValueError(f"CountryOfIssuance is mandatory for doc type {doc_type_upper} for pax {pax_data.get('ObjectKey')}")
                
                if doc_type_upper == "ID" and not doc_data.get("CountryOfIssuance"):
                     raise ValueError(f"CountryOfIssuance is mandatory for doc type ID for pax {pax_data.get('ObjectKey')}")

                # Add fields if they exist in doc_data
                for field_key in ["DateOfExpiration", "CountryOfIssuance", "DateOfIssue", "CountryOfResidence"]:
                    if field_key in doc_data and doc_data[field_key] is not None:
                        doc_entry[field_key] = doc_data[field_key]
                
                formatted_documents.append(doc_entry)
            
            if formatted_documents:
                passenger_entry["PassengerIDInfo"] = {"PassengerDocument": formatted_documents}
                # AllowDocumentInd is not explicitly added as its role needs clarification from Verteil schema/usage

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
    
    order_total_before_surcharge = payment_input_info.get("OrderTotalBeforeSurcharge")
    currency_code = payment_input_info.get("Currency")

    if order_total_before_surcharge is None or currency_code is None:
        raise ValueError("OrderTotalBeforeSurcharge and Currency must be in payment_input_info.")

    surcharge_amount = 0
    surcharge_object_for_rq = None
    # Logic to extract surcharge from FlightPriceRS or payment_input_info
    # This example assumes payment_input_info might contain explicit surcharge if applicable
    if "Surcharge" in payment_input_info and payment_input_info["Surcharge"]:
         surcharge_input_details = payment_input_info["Surcharge"]
         surcharge_amount = surcharge_input_details.get("value", 0)
         surcharge_object_for_rq = {
             "Code": surcharge_input_details.get("Code", currency_code),
             "value": float(surcharge_amount) # Ensure float/number
         }
    # Add more sophisticated surcharge discovery from FlightPriceRS if needed here

    final_payment_amount_value = float(order_total_before_surcharge) + float(surcharge_amount)
    payment_amount_for_rq = {"Code": currency_code, "value": round(final_payment_amount_value, 2)}

    payment_method_object = {}
    if method_type == "CASH":
        payment_method_object = {"Cash": {"CashInd": payment_details_input.get("CashInd", True)}}
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

        payment_card_node["Amount"] = {"value": round(final_payment_amount_value, 2), "Code": currency_code}

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
        if "AccountNumber" not in ep_details or "ExpirationDate" not in ep_details:
            raise ValueError("AccountNumber and ExpirationDate are mandatory for EasyPay.")
        payment_method_object = {"EasyPay": {
            "AccountNumber": str(ep_details["AccountNumber"]),
            "ExpirationDate": ep_details["ExpirationDate"]
        }}
    elif method_type == "OTHER":
        remarks_input = payment_details_input.get("Remarks", [])
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
    if surcharge_object_for_rq and surcharge_amount > 0:
        payment_entry["Surcharge"] = surcharge_object_for_rq
    order_rq_payment_list.append(payment_entry)


def main():
    input_fprs_file = 'FlightPriceResponse.json'
    output_ocrq_file = 'OrderCreateRQ.json'
    
    try:
        with open(input_fprs_file, 'r', encoding='utf-8') as f:
            flight_price_response_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_fprs_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Input file '{input_fprs_file}' is not valid JSON.")
        return

    # --- Example Dynamic Passenger Data ---
    passengers_input = [
        {
            "ObjectKey": "T1", 
            "PTC": "ADT",
            "Name": {"Title": "Mr", "Given": ["AMONI"], "Surname": "KEVIN"},
            "Gender": "Male",
            "BirthDate": "1980-05-25",
            "Contacts": { 
                "Contact": [{
                    "PhoneContact": {"Number": [{"CountryCode": "254", "value": "0700000000"}], "Application": "Home"},
                    "EmailContact": {"Address": {"value": "kevinamoni20@example.com"}},
                    "AddressContact": {"Street": ["Nairobi, Kenya 30500"],"PostalCode": "301","CityName": "Nairobi","CountryCode": {"value": "KE"}}
                }]
            },
            "Documents": [{
                "Type": "PT", "ID": "A12345678", "DateOfExpiration": "2030-12-31", 
                "CountryOfIssuance": "KE", "DateOfIssue": "2020-01-15", "CountryOfResidence": "KE"
            }]
        },
        {
            "ObjectKey": "T2", "PTC": "ADT",
            "Name": {"Title": "Mrs", "Given": ["REBECCA"], "Surname": "MIANO"},
            "Gender": "Female", "BirthDate": "1998-05-25",
            "Documents": [{"Type": "PT", "ID": "B87654321", "DateOfExpiration": "2028-11-20", "CountryOfIssuance": "GB"}]
        },
        {
            "ObjectKey": "T3", "PTC": "CHD",
            "Name": {"Title": "Mstr", "Given": ["EGOLE"], "Surname": "DAVID"},
            "Gender": "Male", "BirthDate": "2014-05-25",
            "Documents": [{"Type": "PT", "ID": "C24681357", "DateOfExpiration": "2027-06-10", "CountryOfIssuance": "KE"}]
        },
        {
            "ObjectKey": "T1.1", "PTC": "INF",
            "Name": {"Title": "Mstr", "Given": ["EGOLE"], "Surname": "BIZZY"},
            "Gender": "Male", "BirthDate": "2024-05-25", "PassengerAssociation": "T1",
            "Documents": [{"Type": "PT", "ID": "D97531024", "DateOfExpiration": "2029-05-24", "CountryOfIssuance": "KE"}]
        }
    ]

    # --- Example Dynamic Payment Info ---
    total_order_price_from_fprs = 0
    currency_from_fprs = "INR" 
    surcharge_details_from_fprs = None

    try: # Safely extract total price and surcharge
        first_priced_offer_fprs = flight_price_response_data.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0]
        if first_priced_offer_fprs: # Check if it's not an empty dict
            # Get total price (this is usually inclusive of surcharge in FlightPriceRS.TotalPrice)
            total_price_node = first_priced_offer_fprs.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
            total_price_with_surcharge_fprs = float(total_price_node.get('value', 0))
            currency_from_fprs = total_price_node.get('Code', "INR")

            # Attempt to find explicit surcharge to deduct it for OrderTotalBeforeSurcharge
            # This logic needs to be robust based on how Verteil returns surcharge
            # For this example, we'll assume if surcharge exists, it's already in TotalPrice
            # and we might need to find the explicit surcharge value if it's itemized.
            # For now, we'll assume TotalPrice from FPRS IS the OrderTotalBeforeSurcharge for simplicity,
            # and any surcharge info will be passed separately if it needs to be *added again* explicitly
            # in OrderCreateRQ. This part is tricky without seeing an FPRS with explicit surcharge.
            
            # A more robust approach: sum base amounts and taxes of all OfferPrice items
            calculated_base_plus_tax = 0
            temp_currency = currency_from_fprs
            for op_item in first_priced_offer_fprs.get('OfferPrice', []):
                pd_item = op_item.get('RequestedDate', {}).get('PriceDetail', {})
                base_val = float(pd_item.get('BaseAmount', {}).get('value', 0))
                tax_val = float(pd_item.get('Taxes', {}).get('Total', {}).get('value', 0))
                calculated_base_plus_tax += (base_val + tax_val)
                if not temp_currency and pd_item.get('BaseAmount', {}).get('Code'):
                    temp_currency = pd_item.get('BaseAmount', {}).get('Code')
            
            order_total_before_surcharge_val = calculated_base_plus_tax
            currency_from_fprs = temp_currency

            # Example: IF a surcharge was explicitly returned and itemized in FlightPriceRS
            # surcharge_details_from_fprs = {"value": 20.00, "Code": "INR"} # Fictional
            
            # This example uses the CASH method as per your OrderCreateRQ.txt
            payment_input = {
                "OrderTotalBeforeSurcharge": order_total_before_surcharge_val,
                "Currency": currency_from_fprs,
                "MethodType": "Cash", 
                "Details": {"CashInd": True}
            }
            if surcharge_details_from_fprs: # If we had a surcharge to explicitly add
                 payment_input["Surcharge"] = surcharge_details_from_fprs

            # To test PaymentCard:
            # payment_input = {
            #     "OrderTotalBeforeSurcharge": order_total_before_surcharge_val,
            #     "Currency": currency_from_fprs,
            #     "MethodType": "PaymentCard", 
            #     "Details": {
            #         "CardCode": "VI",
            #         "CardNumberToken": "tok_simulated_token_1234", 
            #         "CardHolderName": {"value": "Amoni Kevin", "refs": []}, # refs can be passenger ObjectKey
            #         "EffectiveExpireDate": {"Expiration": "1228"}, 
            #         "CardType": "Credit",
            #         # "SeriesCode": {"value":"123"}, # Optional, usually not sent with tokens
            #         # "CardHolderBillingAddress": { ... } 
            #     }
            # }
            # if surcharge_details_from_fprs:
            #      payment_input["Surcharge"] = surcharge_details_from_fprs


    except (IndexError, KeyError, TypeError, AttributeError) as e:
        print(f"Error extracting price/surcharge details from FlightPriceRS: {e}. Using defaults.")
        payment_input = { # Fallback
            "OrderTotalBeforeSurcharge": 0, "Currency": "INR",
            "MethodType": "Cash", "Details": {"CashInd": True}
        }


    try:
        order_create_payload = generate_order_create_rq(
            flight_price_response_data, 
            passengers_input, 
            payment_input
        )
        
        with open(output_ocrq_file, 'w', encoding='utf-8') as f:
            json.dump(order_create_payload, f, indent=2, ensure_ascii=False)
        print(f"OrderCreateRQ successfully generated and saved to '{output_ocrq_file}'")
            
    except ValueError as ve:
        print(f"ValueError during OrderCreateRQ generation: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
# --- END OF FILE build_ordercreate_rq.py (Consolidated) ---