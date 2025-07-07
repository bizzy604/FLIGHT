# --- START OF FILE build_flightpriceRQ.py ---

import json
import logging
# Ensure other necessary imports like sys, Path are handled if you run this standalone via main()
# For just the functions, json is the main one.

# Import Phase 1 core infrastructure for multi-airline support
try:
    from utils.multi_airline_detector import MultiAirlineDetector
    from utils.reference_extractor import EnhancedReferenceExtractor
except ImportError:
    # Fallback for standalone execution
    MultiAirlineDetector = None
    EnhancedReferenceExtractor = None

logger = logging.getLogger(__name__)

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


def build_flight_price_request(airshopping_response, selected_offer_index=0, selected_airline_owner=None):
    """
    Enhanced FlightPrice request builder with multi-airline support.

    Args:
        airshopping_response (dict): The AirShopping response
        selected_offer_index (int): Index of the selected offer (for multi-airline: global index)
        selected_airline_owner (str, optional): The airline owner code (e.g., 'KQ', 'BA').
                                               If not provided, will be auto-detected.

    Returns:
        dict: FlightPrice request payload
    """
    if not isinstance(airshopping_response, dict):
        raise ValueError("Invalid airshopping_response format")

    logger.info(f"Building flight price request for offer index {selected_offer_index}")

    # Detect response type and extract airline context
    is_multi_airline = False
    if MultiAirlineDetector:
        is_multi_airline = MultiAirlineDetector.is_multi_airline_response(airshopping_response)
        logger.info(f"Response type: {'multi-airline' if is_multi_airline else 'single-airline'}")

    if is_multi_airline:
        return _build_multi_airline_flight_price_request(
            airshopping_response, selected_offer_index, selected_airline_owner
        )
    else:
        return _build_single_airline_flight_price_request(
            airshopping_response, selected_offer_index, selected_airline_owner
        )


def _build_multi_airline_flight_price_request(airshopping_response, selected_offer_index, selected_airline_owner=None):
    """
    Build FlightPrice request for multi-airline response.

    Args:
        airshopping_response (dict): The multi-airline AirShopping response
        selected_offer_index (int): Global index of the selected offer
        selected_airline_owner (str, optional): The airline owner code

    Returns:
        dict: FlightPrice request payload
    """
    logger.info(f"Building multi-airline flight price request for global offer index {selected_offer_index}")

    offers_group = airshopping_response.get("OffersGroup", {})
    data_lists = airshopping_response.get("DataLists", {})

    try:
        # Recreate the flattened offers array (matching transformer logic)
        airline_offers_list = offers_group.get("AirlineOffers", [])
        all_offers = []
        airline_mapping = {}  # Maps global index to (airline_offers_node, local_index)

        global_index = 0
        for airline_offers_node in airline_offers_list:
            airline_offers = airline_offers_node.get("AirlineOffer", [])
            if not isinstance(airline_offers, list):
                airline_offers = [airline_offers]

            for local_index, offer in enumerate(airline_offers):
                if offer.get("PricedOffer"):  # Only include priced offers
                    all_offers.append(offer)
                    airline_mapping[global_index] = (airline_offers_node, local_index)
                    global_index += 1

        # Validate the selected index
        if selected_offer_index >= len(all_offers):
            raise ValueError(f"Multi-airline offer index {selected_offer_index} out of range (total: {len(all_offers)})")

        # Get the selected offer and its airline context
        selected_offer = all_offers[selected_offer_index]
        selected_airline_offers_node, local_offer_index = airline_mapping[selected_offer_index]

        # Extract airline owner from the selected offer's OfferID
        airline_owner = selected_offer.get("OfferID", {}).get("Owner", "")
        if not airline_owner:
            # Fallback: try to get from AirlineOffers node (legacy structure)
            airline_owner = selected_airline_offers_node.get("Owner", {}).get("value", "")
        logger.info(f"Selected multi-airline offer from airline {airline_owner} at local index {local_offer_index}")

        # Get airline-specific ShoppingResponseID
        shopping_response_id = _get_airline_shopping_response_id(airshopping_response, airline_owner)

    except (IndexError, KeyError, TypeError) as e:
        raise ValueError(f"Error accessing multi-airline offer at index {selected_offer_index}: {str(e)}")

    # Continue with common offer processing logic
    return _build_common_flight_price_request(
        airshopping_response, selected_offer, airline_owner, shopping_response_id, data_lists
    )


def _build_single_airline_flight_price_request(airshopping_response, selected_offer_index, selected_airline_owner=None):
    """
    Build FlightPrice request for single-airline response (legacy logic).

    Args:
        airshopping_response (dict): The single-airline AirShopping response
        selected_offer_index (int): Index of the selected offer in AirlineOffers
        selected_airline_owner (str, optional): The airline owner code

    Returns:
        dict: FlightPrice request payload
    """
    logger.info(f"Building single-airline flight price request for offer index {selected_offer_index}")

    offers_group = airshopping_response.get("OffersGroup", {})
    data_lists = airshopping_response.get("DataLists", {})

    try:
        airline_offers_list_container = offers_group.get("AirlineOffers", [])
        if not airline_offers_list_container or not isinstance(airline_offers_list_container, list):
            raise ValueError("No AirlineOffers found or invalid format in AirShoppingRS")

        # Find the correct AirlineOffers entry based on selected_airline_owner
        selected_airline_offers_node = None
        if selected_airline_owner:
            for airline_offers_entry in airline_offers_list_container:
                if isinstance(airline_offers_entry, dict):
                    owner_info = airline_offers_entry.get("Owner", {})
                    if isinstance(owner_info, dict) and owner_info.get("value") == selected_airline_owner:
                        selected_airline_offers_node = airline_offers_entry
                        break
            if not selected_airline_offers_node:
                raise ValueError(f"No AirlineOffers found for airline owner: {selected_airline_owner}")
        else:
            # Default to first entry if no specific airline owner is provided
            selected_airline_offers_node = airline_offers_list_container[0]

        actual_airline_offers = selected_airline_offers_node.get("AirlineOffer", [])

        if not actual_airline_offers or not isinstance(actual_airline_offers, list) or selected_offer_index >= len(actual_airline_offers):
            raise ValueError(f"AirlineOffer list is empty or selected_offer_index {selected_offer_index} is out of bounds.")

        selected_offer = actual_airline_offers[selected_offer_index]

        # Extract the airline owner from the selected offer's OfferID
        airline_owner = selected_offer.get("OfferID", {}).get("Owner", "")
        if not airline_owner:
            # Fallback: try to get from AirlineOffers node (legacy structure)
            airline_owner = selected_airline_offers_node.get("Owner", {}).get("value", "")

        # Get standard ShoppingResponseID
        shopping_response = airshopping_response.get("ShoppingResponse", {})
        shopping_response_id = shopping_response.get("ShoppingResponseID", {}).get("value", "")

    except (IndexError, KeyError, TypeError) as e:
        raise ValueError(f"Error accessing selected AirlineOffer in AirShoppingRS: {str(e)}")

    # Continue with common offer processing logic
    return _build_common_flight_price_request(
        airshopping_response, selected_offer, airline_owner, shopping_response_id, data_lists
    )


def _get_airline_shopping_response_id(airshopping_response, airline_code):
    """
    Get airline-specific ShoppingResponseID for multi-airline responses.

    Args:
        airshopping_response (dict): The AirShopping response
        airline_code (str): The airline code

    Returns:
        str: The airline-specific ShoppingResponseID
    """
    try:
        if EnhancedReferenceExtractor:
            extractor = EnhancedReferenceExtractor(airshopping_response)
            refs = extractor.extract_references()
            shopping_ids = refs.get('shopping_response_ids', {})

            airline_shopping_id = shopping_ids.get(airline_code)
            if airline_shopping_id:
                logger.info(f"Found airline-specific ShoppingResponseID for {airline_code}: {airline_shopping_id}")
                return airline_shopping_id
            else:
                # Fallback to first available ShoppingResponseID
                if shopping_ids:
                    fallback_id = next(iter(shopping_ids.values()))
                    logger.info(f"Using fallback ShoppingResponseID: {fallback_id}")
                    return fallback_id

        # Final fallback to standard ShoppingResponseID
        shopping_response = airshopping_response.get("ShoppingResponse", {})
        shopping_response_id = shopping_response.get("ShoppingResponseID", {}).get("value", "")
        logger.info(f"Using standard ShoppingResponseID: {shopping_response_id}")
        return shopping_response_id

    except Exception as e:
        logger.error(f"Error getting ShoppingResponseID for airline {airline_code}: {e}")
        return ""


def _filter_airline_specific_data(data_lists, airline_owner):
    """
    Filter DataLists to only include data relevant to the selected airline.

    Args:
        data_lists (dict): The DataLists from the AirShopping response
        airline_owner (str): The airline owner code (e.g., 'QR', 'KL')

    Returns:
        tuple: (filtered_data_lists, traveler_key_mapping)
    """
    logger.info(f"Filtering DataLists for airline: {airline_owner}")

    filtered_data_lists = {}

    # Filter AnonymousTravelerList to only include airline-specific travelers
    anonymous_travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
    if not isinstance(anonymous_travelers, list):
        anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []

    filtered_travelers = []
    traveler_key_mapping = {}  # Maps airline-prefixed keys to standard keys

    for i, traveler in enumerate(anonymous_travelers):
        if isinstance(traveler, dict):
            object_key = traveler.get("ObjectKey", "")

            # Check if this traveler belongs to the selected airline
            if object_key.startswith(f"{airline_owner}-"):
                # Transform airline-prefixed key to standard key
                standard_key = object_key.replace(f"{airline_owner}-", "")
                traveler_key_mapping[object_key] = standard_key

                # Create filtered traveler with standard key
                filtered_traveler = traveler.copy()
                filtered_traveler["ObjectKey"] = standard_key
                filtered_travelers.append(filtered_traveler)

                logger.debug(f"Included traveler: {object_key} -> {standard_key}")

    if filtered_travelers:
        filtered_data_lists["AnonymousTravelerList"] = {
            "AnonymousTraveler": filtered_travelers
        }
        logger.info(f"Filtered {len(filtered_travelers)} travelers for airline {airline_owner}")
    else:
        logger.warning(f"No travelers found for airline {airline_owner}")
        filtered_data_lists["AnonymousTravelerList"] = {}

    # Filter CarryOnAllowanceList
    carry_on_allowances = data_lists.get("CarryOnAllowanceList", {}).get("CarryOnAllowance", [])
    if not isinstance(carry_on_allowances, list):
        carry_on_allowances = [carry_on_allowances] if carry_on_allowances else []

    filtered_carry_on = []
    for allowance in carry_on_allowances:
        if isinstance(allowance, dict):
            list_key = allowance.get("ListKey", "")
            # Check if this allowance belongs to the selected airline
            if list_key.startswith(f"{airline_owner}-"):
                filtered_carry_on.append(allowance)
                logger.debug(f"Included carry-on allowance: {list_key}")

    if filtered_carry_on:
        filtered_data_lists["CarryOnAllowanceList"] = {
            "CarryOnAllowance": filtered_carry_on
        }
        logger.info(f"Filtered {len(filtered_carry_on)} carry-on allowances for airline {airline_owner}")

    # Filter CheckedBagAllowanceList
    checked_bag_allowances = data_lists.get("CheckedBagAllowanceList", {}).get("CheckedBagAllowance", [])
    if not isinstance(checked_bag_allowances, list):
        checked_bag_allowances = [checked_bag_allowances] if checked_bag_allowances else []

    filtered_checked_bag = []
    for allowance in checked_bag_allowances:
        if isinstance(allowance, dict):
            list_key = allowance.get("ListKey", "")
            # Check if this allowance belongs to the selected airline
            if list_key.startswith(f"{airline_owner}-"):
                filtered_checked_bag.append(allowance)
                logger.debug(f"Included checked bag allowance: {list_key}")

    if filtered_checked_bag:
        filtered_data_lists["CheckedBagAllowanceList"] = {
            "CheckedBagAllowance": filtered_checked_bag
        }
        logger.info(f"Filtered {len(filtered_checked_bag)} checked bag allowances for airline {airline_owner}")

    # Filter FareList
    fare_groups = data_lists.get("FareList", {}).get("FareGroup", [])
    if not isinstance(fare_groups, list):
        fare_groups = [fare_groups] if fare_groups else []

    filtered_fare_groups = []
    for fare_group in fare_groups:
        if isinstance(fare_group, dict):
            list_key = fare_group.get("ListKey", "")
            # Check if this fare group belongs to the selected airline
            if list_key.startswith(f"{airline_owner}-"):
                filtered_fare_groups.append(fare_group)
                logger.debug(f"Included fare group: {list_key}")

    if filtered_fare_groups:
        filtered_data_lists["FareList"] = {
            "FareGroup": filtered_fare_groups
        }
        logger.info(f"Filtered {len(filtered_fare_groups)} fare groups for airline {airline_owner}")

    # Filter other DataLists sections if they contain airline-specific data
    # Check for FlightSegmentList filtering
    flight_segments = data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
    if not isinstance(flight_segments, list):
        flight_segments = [flight_segments] if flight_segments else []

    filtered_segments = []
    for segment in flight_segments:
        if isinstance(segment, dict):
            segment_key = segment.get("SegmentKey", "")
            # Check if this segment belongs to the selected airline
            if segment_key.startswith(f"{airline_owner}-"):
                filtered_segments.append(segment)
                logger.debug(f"Included segment: {segment_key}")

    if filtered_segments:
        filtered_data_lists["FlightSegmentList"] = {
            "FlightSegment": filtered_segments
        }
        logger.info(f"Filtered {len(filtered_segments)} flight segments for airline {airline_owner}")

    # Check for FlightList filtering
    flights = data_lists.get("FlightList", {}).get("Flight", [])
    if not isinstance(flights, list):
        flights = [flights] if flights else []

    filtered_flights = []
    for flight in flights:
        if isinstance(flight, dict):
            flight_key = flight.get("FlightKey", "")
            # Check if this flight belongs to the selected airline
            if flight_key.startswith(f"{airline_owner}-"):
                filtered_flights.append(flight)
                logger.debug(f"Included flight: {flight_key}")

    if filtered_flights:
        filtered_data_lists["FlightList"] = {
            "Flight": filtered_flights
        }
        logger.info(f"Filtered {len(filtered_flights)} flights for airline {airline_owner}")

    # Filter OriginDestinationList
    origin_destinations = data_lists.get("OriginDestinationList", {}).get("OriginDestination", [])
    if not isinstance(origin_destinations, list):
        origin_destinations = [origin_destinations] if origin_destinations else []

    filtered_origin_destinations = []
    for od in origin_destinations:
        if isinstance(od, dict):
            od_key = od.get("OriginDestinationKey", "")

            # Check if this OriginDestination belongs to the selected airline
            if od_key.startswith(f"{airline_owner}-"):
                filtered_origin_destinations.append(od)
                logger.debug(f"Included OriginDestination: {od_key}")

    if filtered_origin_destinations:
        filtered_data_lists["OriginDestinationList"] = {
            "OriginDestination": filtered_origin_destinations
        }
        logger.info(f"Filtered {len(filtered_origin_destinations)} OriginDestinations for airline {airline_owner}")

    return filtered_data_lists, traveler_key_mapping


def _build_common_flight_price_request(airshopping_response, selected_offer, airline_owner, shopping_response_id, data_lists):
    """
    Build the common parts of the FlightPrice request payload.

    Args:
        airshopping_response (dict): The AirShopping response
        selected_offer (dict): The selected offer
        airline_owner (str): The airline owner code
        shopping_response_id (str): The ShoppingResponseID to use
        data_lists (dict): The DataLists from the response

    Returns:
        dict: FlightPrice request payload
    """
    logger.info(f"Building common flight price request for airline {airline_owner}")

    # Filter DataLists to only include airline-specific data
    filtered_data_lists, traveler_key_mapping = _filter_airline_specific_data(data_lists, airline_owner)
    logger.info(f"Traveler key mapping: {traveler_key_mapping}")

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
    # Use filtered fare groups instead of all fare groups from original data_lists
    all_fare_groups_from_airshopping_datalists = filtered_data_lists.get("FareList", {}).get("FareGroup", [])
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
                **({"refs": fare_group_item["refs"]} if "refs" in fare_group_item and fare_group_item["refs"] else {})
            }
            fare_list_for_rq.append(new_fare_group_for_rq)

    query_offer_id_node = selected_offer.get("OfferID", {})
    logger.info(f"Selected offer OfferID node: {query_offer_id_node}")

    if not query_offer_id_node.get("value") or not query_offer_id_node.get("Owner"):
        raise ValueError("Selected offer is missing required OfferID fields for Query")

    logger.info(f"Using OfferID for airline API: {query_offer_id_node.get('value')} (Owner: {query_offer_id_node.get('Owner')})")

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
            
    # Use filtered flight segments instead of all segments from original data_lists
    all_segments_from_datalists = filtered_data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
    if not isinstance(all_segments_from_datalists, list):
        all_segments_from_datalists = [all_segments_from_datalists] if all_segments_from_datalists else []

    segment_details_map = {s.get("SegmentKey"): s for s in all_segments_from_datalists}

    for od_ref_key_sorted in sorted(od_groups_map.keys()): # Sort OD keys for consistent output
        segment_key_list = od_groups_map[od_ref_key_sorted]
        od_flights = []
        for seg_key in segment_key_list:
            segment_detail = segment_details_map.get(seg_key)
            if segment_detail:
                # Build the flight object with SegmentKey and full flight details
                flight_obj = {
                    "SegmentKey": seg_key,
                    "Departure": segment_detail.get("Departure", {}),
                    "Arrival": segment_detail.get("Arrival", {}),
                    "MarketingCarrier": segment_detail.get("MarketingCarrier", {}),
                    "OperatingCarrier": segment_detail.get("OperatingCarrier", {}),
                    "FlightDetail": segment_detail.get("FlightDetail", {})
                }
                od_flights.append(flight_obj)
                logger.debug(f"Added flight segment {seg_key} to OriginDestination {od_ref_key_sorted}")

        if od_flights:
            # Build OriginDestination with Flight array containing full flight details
            origin_destinations_for_rq.append({
                "Flight": od_flights
            })
            logger.info(f"Built OriginDestination with {len(od_flights)} flight segments for OD {od_ref_key_sorted}")

    travelers_for_rq = []
    # Use filtered travelers instead of all travelers from original response
    filtered_travelers_list = filtered_data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
    if not isinstance(filtered_travelers_list, list):
        filtered_travelers_list = [filtered_travelers_list] if filtered_travelers_list else []

    for traveler in filtered_travelers_list: # Use the filtered list for the specific airline
        if isinstance(traveler, dict) and "PTC" in traveler:
             # Construct the format expected in FlightPriceRQ.Travelers.Traveler
            travelers_for_rq.append({"AnonymousTraveler": [{"PTC": traveler.get("PTC", [])}]})

    logger.info(f"Built {len(travelers_for_rq)} travelers for FlightPrice request")


    # Use the provided shopping_response_id (airline-specific or standard)
    shopping_response_id_node = {"value": shopping_response_id} if shopping_response_id else {}

    try:
        # Find the shopping response ID for the specific airline owner
        metadata_section = airshopping_response.get("Metadata", {})
        other_metadata_list = metadata_section.get("Other", {}).get("OtherMetadata", [])

        sr_id_val = None
        sr_owner_val = None
        
        if isinstance(other_metadata_list, list):
            for other_metadata in other_metadata_list:
                if isinstance(other_metadata, dict):
                    desc_metadatas = other_metadata.get("DescriptionMetadatas", {})
                    desc_metadata_list = desc_metadatas.get("DescriptionMetadata", [])
                    
                    if isinstance(desc_metadata_list, list):
                        for desc_metadata in desc_metadata_list:
                            if isinstance(desc_metadata, dict) and desc_metadata.get("MetadataKey") == "SHOPPING_RESPONSE_IDS":
                                aug_points = desc_metadata.get("AugmentationPoint", {}).get("AugPoint", [])
                                if isinstance(aug_points, list):
                                    for aug_point in aug_points:
                                        if isinstance(aug_point, dict) and aug_point.get("Owner") == airline_owner:
                                            sr_id_val = aug_point.get("Key")
                                            sr_owner_val = aug_point.get("Owner")
                                            break
                                    if sr_id_val and sr_owner_val:
                                        break
                            if sr_id_val and sr_owner_val:
                                break
                if sr_id_val and sr_owner_val:
                    break
        
        if sr_id_val and sr_owner_val:
            shopping_response_id_node = {"Owner": sr_owner_val, "ResponseID": {"value": sr_id_val}}
            logger.info(f"Found ShoppingResponseID for airline {sr_owner_val}: {sr_id_val}")
        else:
            logger.warning(f"ShoppingResponseID could not be found for airline owner: {airline_owner}")
            # Use the provided shopping_response_id if available
            if shopping_response_id:
                shopping_response_id_node = {"value": shopping_response_id}
                logger.info(f"Using provided ShoppingResponseID: {shopping_response_id}")
            else:
                # Fallback to the original logic for backward compatibility
                try:
                    sr_id_val = airshopping_response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Key"]
                    sr_owner_val = airshopping_response["Metadata"]["Other"]["OtherMetadata"][0]["DescriptionMetadatas"]["DescriptionMetadata"][0]["AugmentationPoint"]["AugPoint"][0]["Owner"]
                    shopping_response_id_node = {"Owner": sr_owner_val, "ResponseID": {"value": sr_id_val}}
                    logger.info(f"Fallback: Using first available ShoppingResponseID for owner: {sr_owner_val}")
                except (KeyError, IndexError, TypeError):
                    logger.warning("ShoppingResponseID could not be determined for FlightPriceRQ from any source.")
                    shopping_response_id_node = None

    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error extracting ShoppingResponseID: {str(e)}")
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

    # Build DataLists with only mandatory sections for FlightPrice requests
    data_lists_for_rq = {
        "FareGroup": fare_list_for_rq,
        "AnonymousTravelerList": filtered_data_lists.get("AnonymousTravelerList", {})
    }

    flight_price_request = {
        "DataLists": data_lists_for_rq,
        "Query": {
            "OriginDestination": origin_destinations_for_rq,
            "Offers": {
                "Offer": [query_offer]
            }
        },
        "ShoppingResponseID": shopping_response_id_node,
        "Travelers": {"Traveler": travelers_for_rq} if travelers_for_rq else {}, # Ensure structure if empty
        **({"Metadata": {
            "Other": {
                "OtherMetadata": [filtered_price_metadata_section]
            }
        }} if filtered_price_metadata_section else {})
    }

    logger.info(f"Successfully built flight price request for airline {airline_owner}")
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

# --- USAGE EXAMPLES ---
"""
Enhanced Usage Examples for Multi-Airline Support:

1. Multi-airline response with global offer index (recommended):
   result = build_flight_price_request(airshopping_response, selected_offer_index=5)
   # Automatically detects multi-airline response and handles global indexing

2. Single-airline response (legacy compatibility):
   result = build_flight_price_request(airshopping_response, selected_offer_index=0)
   # Uses traditional single-airline logic

3. Specify a particular airline for single-airline response:
   result = build_flight_price_request(
       airshopping_response,
       selected_offer_index=0,
       selected_airline_owner='KQ'
   )

The enhanced function will automatically:
- Detect whether the response is multi-airline or single-airline
- For multi-airline: Use global offer indexing and extract airline-specific ShoppingResponseID
- For single-airline: Use traditional airline-specific logic
- Extract the appropriate ShoppingResponseID for the selected airline
- Build the FlightPriceRQ with the correct airline-specific information

Multi-airline features:
- Global offer indexing across all airlines
- Automatic airline detection from selected offer
- Airline-specific ShoppingResponseID extraction
- Backward compatibility with single-airline responses

Note: For multi-airline responses, the selected_offer_index represents the global index
across all flattened offers from all airlines.
"""

# --- END OF FILE build_flightpriceRQ.py ---
