# --- START OF FILE build_flightpriceRQ.py ---

import json
from typing import Dict, Any, List, Set, Optional, Union

def filter_price_metadata(price_metadatas_container: Dict[str, Any], all_offer_refs_set: Set[str]) -> Dict[str, Any]:
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
        return {"PriceMetadatas": {"PriceMetadata": []}}  # Return valid empty structure

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


def build_flight_price_request(airshopping_response: Dict[str, Any], selected_offer_index: int = 0) -> Dict[str, Any]:
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
        
        selected_airline_offers_node = airline_offers_list_container[0]  # Assuming primary offers are in the first AirlineOffers entry
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
            if "Fare" in fare_group_item:
                 new_fare_group_for_rq["Fare"] = fare_group_item["Fare"]
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
        for od_ref in offer_prices_from_priced_offer[0].get("OriginDestinationReferences", []):
            od_key = od_ref.get("OriginDestinationKey")
            if od_key and od_key not in od_groups_map:
                od_groups_map[od_key] = {
                    "OriginDestinationKey": od_key,
                    "FlightReferences": {"FlightRef": []}
                }
    
    # Process each offer price to collect flight references per OD
    for offer_price_item in offer_prices_from_priced_offer:
        for od_ref in offer_price_item.get("OriginDestinationReferences", []):
            od_key = od_ref.get("OriginDestinationKey")
            flight_refs = od_ref.get("FlightReferences", {}).get("FlightRef", [])
            if not isinstance(flight_refs, list):
                flight_refs = [flight_refs] if flight_refs else []
            
            if od_key in od_groups_map:
                existing_refs = {ref.get("value") for ref in od_groups_map[od_key]["FlightReferences"]["FlightRef"]}
                for flight_ref in flight_refs:
                    if isinstance(flight_ref, dict) and flight_ref.get("value") not in existing_refs:
                        od_groups_map[od_key]["FlightReferences"]["FlightRef"].append(flight_ref)
    
    # Convert the map to a list for the final request
    origin_destinations_for_rq = list(od_groups_map.values())

    # Build the final request
    flight_price_rq = {
        "FlightPriceRQ": {
            "Query": {
                "ShoppingResponseIDs": {
                    "ResponseID": airshopping_response.get("ShoppingResponseID", {})
                },
                "OriginDestinations": {
                    "OriginDestination": origin_destinations_for_rq
                },
                "Offer": query_offer
            }
        }
    }

    # Add FareList if we have fare groups
    if fare_list_for_rq:
        flight_price_rq["FlightPriceRQ"]["Query"]["DataLists"] = {
            "FareList": {
                "FareGroup": fare_list_for_rq
            }
        }

    # Add filtered PriceMetadatas if available
    price_metadatas = data_lists.get("PriceMetadatas")
    if price_metadatas and all_offer_refs_for_metadata_filtering:
        filtered_metadata = filter_price_metadata(
            {"PriceMetadatas": price_metadatas},
            all_offer_refs_for_metadata_filtering
        )
        if filtered_metadata.get("PriceMetadatas", {}).get("PriceMetadata"):
            if "DataLists" not in flight_price_rq["FlightPriceRQ"]["Query"]:
                flight_price_rq["FlightPriceRQ"]["Query"]["DataLists"] = {}
            flight_price_rq["FlightPriceRQ"]["Query"]["DataLists"]["PriceMetadatas"] = filtered_metadata["PriceMetadatas"]

    return flight_price_rq

def main():
    """Main function to test the FlightPrice request builder."""
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python build_flightprice_rq.py <airshopping_response.json> [offer_index]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    offer_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            airshopping_response = json.load(f)
        
        flight_price_rq = build_flight_price_request(airshopping_response, offer_index)
        
        # Create output directory if it doesn't exist
        output_dir = "generated_rqs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}_FlightPriceRQ_{offer_index}.json")
        
        # Save the request
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(flight_price_rq, f, indent=2, ensure_ascii=False)
        
        print(f"FlightPrice request saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
# --- END OF FILE build_flightpriceRQ.py ---
