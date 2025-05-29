# --- START OF FILE build_flightpriceRQ.py ---

import json
# Ensure other necessary imports like sys, Path are handled if you run this standalone via main()
# For just the functions, json is the main one.

def filter_price_metadata(price_metadatas_container, all_offer_refs_set):
    """
    Filter PriceMetadatas to only include those whose MetadataKey is *exactly* present
    in the all_offer_refs_set.

    Args:
        price_metadatas_container (dict): The dict containing PriceMetadatas,
                                          e.g., {"PriceMetadatas": {"PriceMetadata": [...]}}
        all_offer_refs_set (set): A comprehensive set of all reference strings
                                  (MetadataKeys) that are expected to be linked.
                                  This set should be populated with all direct refs
                                  from the AirShoppingRS offer structure.
    Returns:
        dict: A dictionary structured as {"PriceMetadatas": {"PriceMetadata": [filtered_items...]}}
              or an empty equivalent if no matches.
    """
    if not price_metadatas_container or not all_offer_refs_set:
        return {"PriceMetadatas": {"PriceMetadata": []}} # Return valid empty structure

    price_metadata_section = price_metadatas_container.get("PriceMetadatas", {})
    if not isinstance(price_metadata_section, dict):
        price_metadata_list = []
    else:
        price_metadata_list = price_metadata_section.get("PriceMetadata", [])
    
    if not isinstance(price_metadata_list, list):
        price_metadata_list = [price_metadata_list] if price_metadata_list else []

    filtered_items = []
    
    stringified_target_refs = {str(ref) for ref in all_offer_refs_set}

    for metadata_item in price_metadata_list:
        if not isinstance(metadata_item, dict):
            continue
        
        metadata_key = metadata_item.get("MetadataKey")
        if not metadata_key: 
            continue

        if str(metadata_key) in stringified_target_refs:
            is_already_added = any(item.get("MetadataKey") == metadata_key for item in filtered_items)
            if not is_already_added:
                 filtered_items.append(metadata_item)
    
    return {"PriceMetadatas": {"PriceMetadata": filtered_items}}


def build_flight_price_request(airshopping_response, selected_offer_index=0):
    """
    Generate a complete FlightPrice request from the AirShopping response.
    
    Args:
        airshopping_response (dict): The AirShopping response
        selected_offer_index (int): Index of the selected offer in AirlineOffers
        
    Returns:
        dict: FlightPrice request payload
    """
    if not isinstance(airshopping_response, dict):
        raise ValueError("Invalid airshopping_response format")

    offers_group = airshopping_response.get("OffersGroup", {})
    data_lists = airshopping_response.get("DataLists", {})

    try:
        airline_offers_list_container = offers_group.get("AirlineOffers", [])
        if not airline_offers_list_container or not isinstance(airline_offers_list_container, list):
            raise ValueError("No AirlineOffers found or invalid format in AirShoppingRS")
        
        selected_airline_offers_node = airline_offers_list_container[0] # Assuming primary offers are in the first AirlineOffers entry
        actual_airline_offers = selected_airline_offers_node.get("AirlineOffer", [])
        
        if not actual_airline_offers or not isinstance(actual_airline_offers, list) or selected_offer_index >= len(actual_airline_offers):
            raise ValueError(f"AirlineOffer list is empty or selected_offer_index {selected_offer_index} is out of bounds.")
            
        selected_offer = actual_airline_offers[selected_offer_index]
    except (IndexError, KeyError, TypeError) as e:
        raise ValueError(f"Error accessing selected AirlineOffer in AirShoppingRS: {str(e)}")

    all_offer_refs_for_metadata_filtering = set()

    offer_top_level_refs = selected_offer.get("refs", [])
    if not isinstance(offer_top_level_refs, list):
        offer_top_level_refs = [offer_top_level_refs] if offer_top_level_refs else []
    for ref_item in offer_top_level_refs:
        if isinstance(ref_item, dict) and "Ref" in ref_item:
            all_offer_refs_for_metadata_filtering.add(str(ref_item["Ref"]))
        elif isinstance(ref_item, str):
            all_offer_refs_for_metadata_filtering.add(str(ref_item))

    priced_offer_detail = selected_offer.get("PricedOffer", {}) 
    offer_prices_from_priced_offer = priced_offer_detail.get("OfferPrice", [])
    if not isinstance(offer_prices_from_priced_offer, list):
        offer_prices_from_priced_offer = [offer_prices_from_priced_offer] if offer_prices_from_priced_offer else []

    referenced_fare_group_list_keys = set()

    for offer_price_item in offer_prices_from_priced_offer:
        fare_detail_node = offer_price_item.get("FareDetail", {})
        fare_components = fare_detail_node.get("FareComponent", [])
        if not isinstance(fare_components, list):
            fare_components = [fare_components] if fare_components else []

        for component in fare_components:
            comp_refs = component.get("refs", [])
            if not isinstance(comp_refs, list):
                comp_refs = [comp_refs] if comp_refs else []
            for ref_val_str in comp_refs:
                if isinstance(ref_val_str, str):
                    all_offer_refs_for_metadata_filtering.add(ref_val_str)
                    referenced_fare_group_list_keys.add(ref_val_str)

            fare_rules_node = component.get("FareRules", {})
            penalty_node = fare_rules_node.get("Penalty", {})
            penalty_refs_list = penalty_node.get("refs", [])
            if not isinstance(penalty_refs_list, list):
                penalty_refs_list = [penalty_refs_list] if penalty_refs_list else []
            for ref_val_str in penalty_refs_list:
                 if isinstance(ref_val_str, str):
                    all_offer_refs_for_metadata_filtering.add(ref_val_str)

    fare_list_for_rq = []
    all_fare_groups_from_airshopping_datalists = data_lists.get("FareList", {}).get("FareGroup", [])
    if not isinstance(all_fare_groups_from_airshopping_datalists, list):
        all_fare_groups_from_airshopping_datalists = \
            [all_fare_groups_from_airshopping_datalists] if all_fare_groups_from_airshopping_datalists else []

    for fare_group_item in all_fare_groups_from_airshopping_datalists:
        list_key = fare_group_item.get("ListKey")
        if list_key in referenced_fare_group_list_keys:
            all_offer_refs_for_metadata_filtering.add(list_key)

            fg_internal_refs = fare_group_item.get("refs", [])
            if not isinstance(fg_internal_refs, list):
                fg_internal_refs = [fg_internal_refs] if fg_internal_refs else []
            for fg_ref_val_str in fg_internal_refs:
                if isinstance(fg_ref_val_str, str):
                    all_offer_refs_for_metadata_filtering.add(fg_ref_val_str)
            
            new_fare_group_for_rq = {
                "ListKey": list_key,
                "FareBasisCode": fare_group_item.get("FareBasisCode", {}),
                "refs": fare_group_item.get("refs", [])
            }
            fare_list_for_rq.append(new_fare_group_for_rq)

    query_offer_id_node = selected_offer.get("OfferID", {})
    if not query_offer_id_node.get("value") or not query_offer_id_node.get("Owner"):
        raise ValueError("Selected offer is missing required OfferID fields for Query")

    query_offer = {
        "OfferID": query_offer_id_node,
        "OfferItemIDs": {"OfferItemID": []}
    }
    
    if "refs" in selected_offer:
        query_offer_refs = []
        for ref_item in offer_top_level_refs:
            if isinstance(ref_item, dict) and "Ref" in ref_item:
                query_offer_refs.append({"Ref": ref_item["Ref"]})
            elif isinstance(ref_item, str):
                query_offer_refs.append({"Ref": ref_item})
        if query_offer_refs:
            query_offer["refs"] = query_offer_refs

    for offer_price_item in offer_prices_from_priced_offer:
        offer_item_id_value = offer_price_item.get("OfferItemID")
        current_pax_refs = []
        requested_date_node = offer_price_item.get("RequestedDate", {})
        associations_list = requested_date_node.get("Associations", [])
        if not isinstance(associations_list, list):
            associations_list = [associations_list] if associations_list else []
        
        if associations_list:
            assoc_traveler_node = associations_list[0].get("AssociatedTraveler", {})
            p_refs = assoc_traveler_node.get("TravelerReferences", [])
            if not isinstance(p_refs, list):
                current_pax_refs = [p_refs] if p_refs else []
            else:
                current_pax_refs = p_refs
        
        if offer_item_id_value and current_pax_refs:
            query_offer["OfferItemIDs"]["OfferItemID"].append({
                "value": offer_item_id_value,
                "refs": current_pax_refs
            })

    origin_destinations_for_rq = []
    od_groups_map = {}

    # Populate od_groups_map only once, as the OD structure is the same across OfferPrice items for the same PricedOffer
    if offer_prices_from_priced_offer:
        first_offer_price_item = offer_prices_from_priced_offer[0]
        requested_date_node = first_offer_price_item.get("RequestedDate", {})
        associations_list = requested_date_node.get("Associations", [])
        if not isinstance(associations_list, list):
            associations_list = [associations_list] if associations_list else []

        for assoc in associations_list:
            applicable_flight_node = assoc.get("ApplicableFlight", {})
            od_refs_list = applicable_flight_node.get("OriginDestinationReferences", [])
            if not isinstance(od_refs_list, list):
                od_refs_list = [od_refs_list] if od_refs_list else []
            
            seg_refs_list = applicable_flight_node.get("FlightSegmentReference", [])
            if not isinstance(seg_refs_list, list):
                seg_refs_list = [seg_refs_list] if seg_refs_list else []

            for od_ref_str in od_refs_list:
                if od_ref_str not in od_groups_map:
                    od_groups_map[od_ref_str] = []
                for seg_ref_obj in seg_refs_list:
                    if isinstance(seg_ref_obj, dict) and "ref" in seg_ref_obj:
                        if seg_ref_obj["ref"] not in od_groups_map[od_ref_str]:
                            od_groups_map[od_ref_str].append(seg_ref_obj["ref"])
            
    all_segments_from_datalists = data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
    if not isinstance(all_segments_from_datalists, list):
        all_segments_from_datalists = [all_segments_from_datalists] if all_segments_from_datalists else []
    
    segment_details_map = {s.get("SegmentKey"): s for s in all_segments_from_datalists}

    for od_ref_key_sorted in sorted(od_groups_map.keys()): # Sort OD keys for consistent output
        segment_key_list = od_groups_map[od_ref_key_sorted]
        od_flights = []
        for seg_key in segment_key_list:
            segment_detail = segment_details_map.get(seg_key)
            if segment_detail:
                od_flights.append(segment_detail)
        if od_flights:
            origin_destinations_for_rq.append({"Flight": od_flights})

    travelers_for_rq = []
    anonymous_travelers_list_asrs = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
    if not isinstance(anonymous_travelers_list_asrs, list):
        anonymous_travelers_list_asrs = [anonymous_travelers_list_asrs] if anonymous_travelers_list_asrs else []
    for traveler in anonymous_travelers_list_asrs: # Use the list from AirShoppingRS DataLists
        if isinstance(traveler, dict) and "PTC" in traveler:
             # Construct the format expected in FlightPriceRQ.Travelers.Traveler
            travelers_for_rq.append({"AnonymousTraveler": [{"PTC": traveler.get("PTC", [])}]})


    shopping_response_id_node = airshopping_response.get("ShoppingResponseID", {}) # From top level of AirShoppingRS
    if not (isinstance(shopping_response_id_node, dict) and \
            shopping_response_id_node.get("ResponseID", {}).get("value") and \
            shopping_response_id_node.get("Owner")):
        print("Warning: Top-level ShoppingResponseID from AirShoppingRS is incomplete or missing. Attempting fallback.")
        # Fallback logic (simplified for brevity, ensure robustness in production)
        shopping_response_id_node = {} # Reset
        try:
            sr_id_val = airshopping_response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Key"]
            sr_owner_val = airshopping_response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Owner"]
            shopping_response_id_node = {"Owner": sr_owner_val, "ResponseID": {"value": sr_id_val}}
        except (KeyError, IndexError, TypeError):
            print("Critical Warning: ShoppingResponseID could not be determined for FlightPriceRQ from any source.")
            # Depending on requirements, either raise error or set to None/empty and let Verteil handle it
            shopping_response_id_node = None


    all_price_metadatas_container = {}
    try:
        other_metadata_list_meta = airshopping_response.get("Metadata", {}).get("Other", {}).get("OtherMetadata", [])
        if other_metadata_list_meta and isinstance(other_metadata_list_meta, list) and len(other_metadata_list_meta) > 0:
            first_other_meta_item = other_metadata_list_meta[0]
            if isinstance(first_other_meta_item, dict) and "PriceMetadatas" in first_other_meta_item:
                 all_price_metadatas_container = {"PriceMetadatas": first_other_meta_item["PriceMetadatas"]}
            else: # Handle case where PriceMetadatas might not be in the first item or not exist
                all_price_metadatas_container = {"PriceMetadatas": {"PriceMetadata": []}}
        else:
            all_price_metadatas_container = {"PriceMetadatas": {"PriceMetadata": []}}
    except Exception as e:
        print(f"Warning: Could not extract PriceMetadatas from AirShoppingRS for filtering: {e}")
        all_price_metadatas_container = {"PriceMetadatas": {"PriceMetadata": []}}
    
    filtered_price_metadata_section = filter_price_metadata(
        all_price_metadatas_container,
        all_offer_refs_for_metadata_filtering
    )

    flight_price_request = {
        "DataLists": {
            "FareGroup": fare_list_for_rq,
            "AnonymousTravelerList": data_lists.get("AnonymousTravelerList", {}) # From AirShoppingRS DataLists
        },
        "Query": {
            "OriginDestination": origin_destinations_for_rq,
            "Offers": {
                "Offer": [query_offer]
            }
        },
        "ShoppingResponseID": shopping_response_id_node,
        "Travelers": {"Traveler": travelers_for_rq} if travelers_for_rq else {}, # Ensure structure if empty
        "Metadata": {
            "Other": {
                "OtherMetadata": [
                    filtered_price_metadata_section 
                ]
            }
        }
    }
    
    return flight_price_request


def main():
    import sys
    from pathlib import Path

    # Determine the correct input file name based on your previous uploads
    # It seems AirShoppingRS.txt was the source for the selected offer.
    input_file_name = "airshoping_response.json" 
    input_file_path = Path(input_file_name)
    output_file_path = Path("flightprice_request_generated.json")

    if not input_file_path.exists():
        print(f"Error: Input file '{input_file_path}' not found. Please ensure it's in the same directory or provide the correct path.")
        sys.exit(1)

    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            airshopping_response_content = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file '{input_file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading input file '{input_file_path}': {e}")
        sys.exit(1)

    try:
        # Assuming you want to process the first offer (index 0)
        flight_price_rq_payload = build_flight_price_request(airshopping_response_content, selected_offer_index=0)
        
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(flight_price_rq_payload, f, indent=2, ensure_ascii=False)
        print(f"FlightPriceRQ successfully generated and saved to '{output_file_path}'")
            
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
# --- END OF FILE build_flightpriceRQ.py ---