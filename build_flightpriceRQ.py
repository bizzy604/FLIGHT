import json

def filter_price_metadata(price_metadatas, offer_refs):
    """
    Filter PriceMetadatas to only include those associated with the specific offer's references.
    
    Args:
        price_metadatas (dict): The complete PriceMetadatas from AirShoppingRS
        offer_refs (set): Set of references collected from the selected offer
        
    Returns:
        dict: Filtered PriceMetadatas containing only the metadata relevant to the selected offer
    """
    if not price_metadatas or not offer_refs:
        return price_metadatas  # Return as is if there's nothing to filter
        
    filtered_metadata = {}
    price_metadata_list = price_metadatas.get("PriceMetadata", [])
    if not isinstance(price_metadata_list, list):
        price_metadata_list = [price_metadata_list] if price_metadata_list else []
    
    filtered_price_metadata_list = []
    
    # For each price metadata, check if its MetadataKey contains any reference from our offer
    for metadata_item in price_metadata_list:
        metadata_key = metadata_item.get("MetadataKey", "")
        
        # Check if this metadata is associated with any of our offer references
        is_relevant = False
        for ref in offer_refs:
            # Check if the reference is part of the metadata key
            if str(ref) in metadata_key:
                is_relevant = True
                break
                
            # Also check if there are any references within the AugmentationPoint
            aug_point = metadata_item.get("AugmentationPoint", {}).get("AugPoint", [])
            if not isinstance(aug_point, list):
                aug_point = [aug_point] if aug_point else []
                
            for aug in aug_point:
                if isinstance(aug, dict) and "any" in aug:
                    # The 'value' field often contains serialized JSON with references
                    value = aug.get("any", {}).get("value", "")
                    if str(ref) in value:
                        is_relevant = True
                        break
                        
            if is_relevant:
                break
        
        if is_relevant:
            filtered_price_metadata_list.append(metadata_item)
    
    # If we found any relevant metadata, return them, otherwise return empty structure
    if filtered_price_metadata_list:
        filtered_metadata = {"PriceMetadata": filtered_price_metadata_list}
    
    return filtered_metadata


def build_flight_price_request(airshopping_response, selected_offer_index=0):
    """
    Generate a complete FlightPrice request from the AirShopping response.
    
    Args:
        airshopping_response (dict): The AirShopping response
        selected_offer_index (int): Index of the selected offer in AirlineOffers
        
    Returns:
        dict: FlightPrice request payload with the following structure:
            {
                "DataLists": {
                    "FareList": [fare_groups],
                    "AnonymousTravelerList": [travelers]
                },
                "Query": {
                    "OriginDestination": [
                        {"Flight": [flight_segments]},
                        ...
                    ]
                },
                "Offers": {
                    "Offer": [{"OfferID": {...}, "OfferItem": [...]}]
                },
                "Travelers": {...},
                "Metadata": {...}
            }
    """
    # 1. Validate and extract basic structure
    if not isinstance(airshopping_response, dict):
        raise ValueError("Invalid airshopping_response format")

    offers_group = airshopping_response.get("OffersGroup", {})
    data_lists = airshopping_response.get("DataLists", {})
    
    # Extract all PriceMetadatas from Metadata.Other.OtherMetadata[0].PriceMetadatas
    # We will filter these later based on the selected offer's references
    all_metadata = {}
    try:
        other_metadata = airshopping_response.get("Metadata", {}).get("Other", {})
        other_metadata_list = other_metadata.get("OtherMetadata", [])
        if other_metadata_list and isinstance(other_metadata_list, list) and len(other_metadata_list) > 0:
            first_other_metadata = other_metadata_list[0]
            if "PriceMetadatas" in first_other_metadata:
                all_metadata = {"PriceMetadatas": first_other_metadata["PriceMetadatas"]}
            else:
                pass
        else:
            pass
    except Exception as e:
        print(f"=== ERROR: Failed to extract PriceMetadatas: {str(e)}")
    
    # 2. Get the selected offer
    try:
        airline_offers = offers_group.get("AirlineOffers", [{}])[0].get("AirlineOffer", [])
        if not airline_offers:
            raise ValueError("No AirlineOffers found")
        selected_offer = airline_offers[selected_offer_index]
    except (IndexError, KeyError, TypeError) as e:
        raise ValueError(f"Invalid or missing AirlineOffer in response: {str(e)}")
    
    # 3. Extract offer details
    offer_id = selected_offer.get("OfferID", {})
    if not offer_id.get("value") or not offer_id.get("Owner"):
        raise ValueError("Missing required OfferID fields")
    
    # 4. Build FareList from FareGroup references
    fare_list = []
    try:
        # Collect all references from the selected offer to filter PriceMetadatas later
        all_offer_refs = set()
        
        # Add refs from the offer itself if they exist
        if "refs" in selected_offer:
            current_offer_refs = selected_offer.get("refs")
            if isinstance(current_offer_refs, list):
                for ref_val in current_offer_refs:
                    if isinstance(ref_val, str):
                        all_offer_refs.add(ref_val)
                    elif isinstance(ref_val, dict) and "Ref" in ref_val:
                        all_offer_refs.add(ref_val["Ref"])
            elif isinstance(current_offer_refs, str): # Single string ref
                all_offer_refs.add(current_offer_refs)
            elif isinstance(current_offer_refs, dict) and "Ref" in current_offer_refs: # Single dict ref
                all_offer_refs.add(current_offer_refs["Ref"])

        # Get all FareComponent refs from the selected offer (this comment is now more of a section header)
        priced_offers = selected_offer.get("PricedOffer", {})
        if not isinstance(priced_offers, list):
            priced_offers = [priced_offers]
        
        # Get all fare groups from DataLists
        fare_groups = data_lists.get("FareList", {}).get("FareGroup", [])
        if not isinstance(fare_groups, list):
            fare_groups = [fare_groups] if fare_groups else []
        
        # First, collect all unique fare component refs from the offer
        fare_component_refs = set()
        
        for offer in priced_offers:
            # Get all offer prices from the offer
            offer_prices = offer.get("OfferPrice", [])
            if not isinstance(offer_prices, list):
                offer_prices = [offer_prices] if offer_prices else []
            
            for price in offer_prices:
                fare_detail = price.get("FareDetail", {})
                fare_components = fare_detail.get("FareComponent", [])
                if not isinstance(fare_components, list):
                    fare_components = [fare_components] if fare_components else []
            
                for component in fare_components:
                    # Get the refs from the FareComponent
                    refs = component.get("refs", [])
                    if not isinstance(refs, list):
                        refs = [refs] if refs else []
                    
                    # Add refs to our collection for PriceMetadata filtering
                    for ref in refs:
                        if isinstance(ref, str):
                            all_offer_refs.add(ref)
                        elif isinstance(ref, dict) and "Ref" in ref:
                            all_offer_refs.add(ref["Ref"])
                    
                    fare_component_refs.update(refs)
                    
                    # Also check for refs in FareRules if they exist
                    fare_rules = component.get("FareRules", {})
                    if fare_rules:
                        penalty = fare_rules.get("Penalty", {})
                        if penalty:
                            penalty_refs = penalty.get("refs", [])
                            if not isinstance(penalty_refs, list):
                                penalty_refs = [penalty_refs] if penalty_refs else []
                            
                            # Add penalty refs to our collection for PriceMetadata filtering
                            for ref in penalty_refs:
                                if isinstance(ref, str):
                                    all_offer_refs.add(ref)
                                elif isinstance(ref, dict) and "Ref" in ref:
                                    all_offer_refs.add(ref["Ref"])
                                    
                            if penalty_refs:
                                fare_component_refs.update(penalty_refs)
        
        # Now find and add the corresponding fare groups
        added_fare_groups = set()  # Track which fare groups we've already added
        
        for ref in fare_component_refs:
            for fare_group in fare_groups:
                list_key = fare_group.get("ListKey")
                if list_key:
                    # Add the ListKey as a reference for PriceMetadata filtering
                    all_offer_refs.add(list_key)
                    
                    # If this fare group has refs, add those to our collection too
                    fg_refs = fare_group.get("refs", [])
                    if not isinstance(fg_refs, list):
                        fg_refs = [fg_refs] if fg_refs else []
                        
                    for fg_ref in fg_refs:
                        if isinstance(fg_ref, str):
                            all_offer_refs.add(fg_ref)
                        elif isinstance(fg_ref, dict) and "Ref" in fg_ref:
                            all_offer_refs.add(fg_ref["Ref"])
                
                if list_key and list_key == ref and list_key not in added_fare_groups:
                    # Create a new fare group entry with required fields
                    new_fare_group = {
                        "ListKey": list_key,
                        "FareBasisCode": {
                            "Code": fare_group.get("FareBasisCode", {}).get("Code", "")
                        }
                    }
                    
                    # Add refs if they exist in the FareGroup
                    if "refs" in fare_group:
                        new_fare_group["refs"] = fare_group["refs"]
                    
                    # Add segment references if available
                    if "SegmentReferences" in fare_group:
                        new_fare_group["SegmentReferences"] = fare_group["SegmentReferences"]
                    
                    # Add other relevant fields from the fare group
                    for field in ["FareBasis", "FareRules", "PriceClassRef"]:
                        if field in fare_group:
                            new_fare_group[field] = fare_group[field]
                    
                    fare_list.append(new_fare_group)
                    added_fare_groups.add(list_key)
                    break
    except Exception as e:
        raise ValueError(f"Error processing fare groups: {str(e)}")
    
    # 5. Build flight segments with OriginDestination grouping
    origin_destinations = []
    try:
        associations = selected_offer.get("PricedOffer", {}).get("Associations", [])
        if not isinstance(associations, list):
            associations = [associations]
            
        # Group flights by OriginDestinationReferences
        od_groups = {}
        for assoc in associations:
            applicable_flight = assoc.get("ApplicableFlight", {})
            od_refs = applicable_flight.get("OriginDestinationReferences", [])
            if not isinstance(od_refs, list):
                od_refs = [od_refs]
                
            for od_ref in od_refs:
                if od_ref not in od_groups:
                    od_groups[od_ref] = []
                
                flight_refs = applicable_flight.get("FlightSegmentReference", [])
                if not isinstance(flight_refs, list):
                    flight_refs = [flight_refs]
                
                for flight_ref in flight_refs:
                    if isinstance(flight_ref, dict) and "ref" in flight_ref:
                        od_groups[od_ref].append(flight_ref["ref"])
    
        # Create OriginDestination entries
        for od_ref, segment_refs in od_groups.items():
            flights = []
            for segment_ref in segment_refs:
                # Find the flight segment by ref
                segment = next(
                    (s for s in data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
                     if s.get("SegmentKey") == segment_ref),
                    None
                )
                if segment:
                    flights.append(segment)
            
            if flights:
                origin_destinations.append({
                    "Flight": flights
                })
    
    except Exception as e:
        raise ValueError(f"Error processing flight segments: {str(e)}")
    
    # 6. Build Offer section with OfferItemIDs and refs
    offer = {
        "OfferID": offer_id
    }
    
    # Add refs from the selected offer if they exist
    if "refs" in selected_offer:
        if isinstance(selected_offer["refs"], list):
            # Handle case where refs is a list of strings
            if all(isinstance(ref, str) for ref in selected_offer["refs"]):
                offer["refs"] = [{"Ref": ref} for ref in selected_offer["refs"]]
            # Handle case where refs is a list of objects with Ref key
            elif all(isinstance(ref, dict) and "Ref" in ref for ref in selected_offer["refs"]):
                offer["refs"] = [{"Ref": ref["Ref"]} for ref in selected_offer["refs"]]
        # Handle single ref case
        else:
            ref = selected_offer["refs"]
            if isinstance(ref, dict) and "Ref" in ref:
                offer["refs"] = [{"Ref": ref["Ref"]}]
            else:
                offer["refs"] = [{"Ref": ref}]
    
    # Process OfferItemIDs from PricedOffer.OfferPrice and collect all references
    offer_item_ids = []
    # Collect all references from the selected offer to filter PriceMetadatas later
    all_offer_refs = set()
    
    # Add refs from the offer itself if they exist
    if "refs" in selected_offer:
        if isinstance(selected_offer["refs"], list):
            for ref in selected_offer["refs"]:
                if isinstance(ref, dict) and "Ref" in ref:
                    all_offer_refs.add(ref["Ref"])
                elif isinstance(ref, str):
                    all_offer_refs.add(ref)
        else:
            ref = selected_offer["refs"]
            if isinstance(ref, dict) and "Ref" in ref:
                all_offer_refs.add(ref["Ref"])
            elif isinstance(ref, str):
                all_offer_refs.add(ref)
    
    try:
        # Get all PricedOffers from the selected offer
        priced_offers = selected_offer.get("PricedOffer", {})
        if not isinstance(priced_offers, list):
            priced_offers = [priced_offers] if priced_offers else []
        
        for priced_offer in priced_offers:
            if not isinstance(priced_offer, dict):
                continue
                
            # Get all OfferPrice entries from the PricedOffer
            offer_prices = priced_offer.get("OfferPrice", [])
            if not isinstance(offer_prices, list):
                offer_prices = [offer_prices] if offer_prices else []
            
            for offer_price in offer_prices:
                if not isinstance(offer_price, dict):
                    continue
                    
                # Get the OfferItemID directly from OfferPrice
                offer_item_id = offer_price.get("OfferItemID")
                if not offer_item_id:
                    continue
                
                # Get traveler references from the exact path: 
                # PricedOffer.OfferPrice[x].RequestedDate.Associations[0].AssociatedTraveler.TravelerReferences[0]
                traveler_refs = []
                
                # Get the RequestedDate from the current OfferPrice
                requested_date = offer_price.get("RequestedDate", {})
                
                # Get the first association from RequestedDate
                associations = requested_date.get("Associations", [])
                if not isinstance(associations, list):
                    associations = [associations] if associations else []
                
                if associations:
                    # Get the first association
                    first_assoc = associations[0] if isinstance(associations, list) and len(associations) > 0 else {}
                    
                    # Get the AssociatedTraveler from the first association
                    associated_traveler = first_assoc.get("AssociatedTraveler", {}) if isinstance(first_assoc, dict) else {}
                    
                    # Get the TravelerReferences from AssociatedTraveler
                    traveler_refs = associated_traveler.get("TravelerReferences", []) if isinstance(associated_traveler, dict) else []
                    
                    # Convert to list if it's not already
                    if not isinstance(traveler_refs, list):
                        traveler_refs = [traveler_refs] if traveler_refs else []
                
                if not traveler_refs:
                    # Skip if no traveler references found
                    continue
                    
                offer_item_ids.append({
                    "refs": traveler_refs,
                    "value": offer_item_id
                })
                    
    except Exception as e:
        raise ValueError(f"Error processing OfferItemIDs: {str(e)}")
    
    # Add OfferItemIDs to the offer if we found any
    if offer_item_ids:
        offer["OfferItemIDs"] = {
            "OfferItemID": offer_item_ids
        }
    
    # 7. Build Travelers section
    # Initialize travelers list
    travelers = []
    
    try:
        # Get all anonymous travelers
        anonymous_travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
        if not isinstance(anonymous_travelers, list):
            anonymous_travelers = [anonymous_travelers]
            
    
        # Create a traveler entry for each anonymous traveler
        for traveler in anonymous_travelers:
            if not isinstance(traveler, dict):
                continue
                
            ptc = traveler.get("PTC", {})
            if isinstance(ptc, dict):
                ptc_value = ptc.get("value")
                if ptc_value:
                    travelers.append({
                        "AnonymousTraveler": [{
                            "PTC": {
                                "value": ptc_value
                            }
                        }]
                    })
            
    except Exception:
        pass

    # 8. Build the request structure
    # First, get the airline owner from the selected offer
    selected_airline_owner = None
    # Get the airline owner from the selected offer's OfferID
    offer_id = selected_offer.get('OfferID', {})
    selected_airline_owner = None
    
    if isinstance(offer_id, dict):
        selected_airline_owner = offer_id.get('Owner')
    
    if not selected_airline_owner:
        # Fallback to check AirlineOffers if Owner is not in OfferID
        airline_offers = selected_offer.get('AirlineOffers', [{}])
        if isinstance(airline_offers, list) and airline_offers and isinstance(airline_offers[0], dict):
            selected_airline_offer = airline_offers[0]
            selected_airline_owner = selected_airline_offer.get('Owner')
    
    # Extract ShoppingResponseID from the AugPoint with matching owner
    shopping_response_id = {}
    
    try:
        # Get the first OtherMetadata entry that has DescriptionMetadatas
        other_metadata = airshopping_response.get("Metadata", {}).get("Other", {})
        other_metadata_list = other_metadata.get("OtherMetadata", [])
        if not isinstance(other_metadata_list, list):
            other_metadata_list = [other_metadata_list] if other_metadata_list else []
        
        for meta in other_metadata_list:
            if not isinstance(meta, dict):
                continue
                
            desc_metadatas = meta.get("DescriptionMetadatas", {})
            if not isinstance(desc_metadatas, dict):
                continue
                
            desc_metadata_list = desc_metadatas.get("DescriptionMetadata", [])
            if not isinstance(desc_metadata_list, list):
                desc_metadata_list = [desc_metadata_list] if desc_metadata_list else []
                
            for desc_meta in desc_metadata_list:
                if not isinstance(desc_meta, dict):
                    continue
                    
                aug_point = desc_meta.get("AugmentationPoint", {})
                if not isinstance(aug_point, dict):
                    continue
                
                # Look for AugPoint with matching owner and get its Key
                for aug_value in aug_point.values():
                    if not isinstance(aug_value, (list, dict)):
                        continue
                        
                    # Handle case where AugPoint is a list of items
                    if isinstance(aug_value, list):
                        for item in aug_value:
                            if not isinstance(item, dict):
                                continue
                                
                            owner = item.get("Owner")
                            if (selected_airline_owner and owner == selected_airline_owner) or not selected_airline_owner:
                                response_id = item.get("Key")
                                if response_id:
                                    shopping_response_id = {
                                        "Owner": owner,
                                        "ResponseID": {"value": response_id}
                                    }
                                    break
                    
                    # Handle case where AugPoint is a direct object
                    elif isinstance(aug_value, dict):
                        owner = aug_value.get("Owner")
                        if (selected_airline_owner and owner == selected_airline_owner) or not selected_airline_owner:
                            response_id = aug_value.get("Key")
                            if response_id:
                                shopping_response_id = {
                                    "Owner": owner,
                                    "ResponseID": {"value": response_id}
                                }
                                break
                    
                    if shopping_response_id:
                        break
                        
                if shopping_response_id:
                    break
                    
            if shopping_response_id:
                break
    except Exception:
        # If there's an error, shopping_response_id will remain an empty dict
        pass

    # Build the final request
    flight_price_request = {
        "DataLists": {
            "FareGroup": fare_list,
            "AnonymousTravelerList": data_lists.get("AnonymousTravelerList", {})
        },
        "Query": {
            "OriginDestination": origin_destinations,
            "Offers": {
                "Offer": [offer]
            }
        },
        "ShoppingResponseID": shopping_response_id if shopping_response_id else None,
        "Travelers": {"Traveler": travelers} if travelers else {},
        "Metadata": {
            "Other": {
                "OtherMetadata": [
                    {
                        "PriceMetadatas": filter_price_metadata(all_metadata.get("PriceMetadatas", {}), all_offer_refs)
                    }
                ]
            }
        }
    }
    
    return flight_price_request


def main():
    """Main function to execute the script."""
    import json
    import sys
    from pathlib import Path

    # Load airshoping_response from the correct file
    input_file = "airshoping_response.json"
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            airshopping_response = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading input file: {e}")
        sys.exit(1)

    try:
        # Generate the flight price request
        result = build_flight_price_request(airshopping_response)
        
        # Save to a file
        output_file = "flightprice_request.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error generating flight price request: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
