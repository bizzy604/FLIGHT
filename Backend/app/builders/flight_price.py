"""FlightPrice request builder - Single airline only."""

import logging
from typing import Dict, Any, Set, List, Optional
from app.core.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)


class FlightPriceRequestBuilder:
    """
    Builds VDC FlightPrice requests from AirShopping responses.
    
    NOTE: FlightPrice only supports single-airline requests.
    While AirShopping can return multi-airline results, FlightPrice must be
    called for a specific airline's offer.
    """
    
    def __init__(self, air_shopping_response: Dict[str, Any]):
        """
        Initialize builder with AirShopping response.
        
        Args:
            air_shopping_response: The complete AirShopping response
        """
        self.response = air_shopping_response
        self.offers_group = air_shopping_response.get("OffersGroup", {})
        self.data_lists = air_shopping_response.get("DataLists", {})
        
        logger.info("FlightPriceRequestBuilder initialized")
    
    def build(
        self, 
        offer_index: int, 
        airline_owner: str
    ) -> Dict[str, Any]:
        """
        Build FlightPrice request for selected offer from a specific airline.
        
        Args:
            offer_index: Index of the selected offer within the airline's offers
            airline_owner: Airline code (required - e.g., 'EK', 'BA', 'LH')
            
        Returns:
            FlightPrice request payload
            
        Raises:
            BusinessLogicError: If offer not found or invalid parameters
        """
        if not airline_owner:
            raise BusinessLogicError("airline_owner is required for FlightPrice requests")
        
        logger.info(f"Building FlightPrice request for airline {airline_owner}, offer {offer_index}")
        
        # Find airline-specific offers
        airline_offers_list = self.offers_group.get("AirlineOffers", [])
        
        if not airline_offers_list:
            raise BusinessLogicError("No AirlineOffers found in AirShopping response")
        
        if not isinstance(airline_offers_list, list):
            airline_offers_list = [airline_offers_list]
        
        # Try to find airline node with Owner field at group level (old format)
        airline_node = None
        for node in airline_offers_list:
            owner = node.get("Owner", {})
            owner_value = owner.get("value") if isinstance(owner, dict) else owner
            
            if owner_value == airline_owner:
                airline_node = node
                break
        
        # If not found at group level, look in individual offers (new VDC format)
        if not airline_node:
            for node in airline_offers_list:
                node_offers = node.get("AirlineOffer", [])
                if not isinstance(node_offers, list):
                    node_offers = [node_offers] if node_offers else []
                
                # Check if any offer in this node matches the airline
                for offer in node_offers:
                    offer_id = offer.get("OfferID", {})
                    if isinstance(offer_id, dict) and offer_id.get("Owner") == airline_owner:
                        airline_node = node
                        break
                
                if airline_node:
                    break
        
        if not airline_node:
            raise BusinessLogicError(f"No offers found for airline {airline_owner}")
        
        # Get offers list for this airline
        offers = airline_node.get("AirlineOffer", [])
        if not isinstance(offers, list):
            offers = [offers] if offers else []
        
        if not offers:
            raise BusinessLogicError(f"No offers available for airline {airline_owner}")
        
        if offer_index >= len(offers):
            raise BusinessLogicError(
                f"Offer index {offer_index} out of range (airline {airline_owner} has {len(offers)} offers)"
            )
        
        selected_offer = offers[offer_index]
        logger.info(f"Selected offer {offer_index} from airline {airline_owner}")
        
        # Get ShoppingResponseID from response
        shopping_response_id = self._get_shopping_response_id(airline_owner)
        
        # Build the request
        return self._build_request_payload(selected_offer, airline_owner, shopping_response_id)
    
    def _get_shopping_response_id(self, airline_owner: str) -> str:
        """
        Extract ShoppingResponseID for the airline.
        
        For multi-airline AirShopping responses, each airline has its own
        ShoppingResponseID stored in Metadata.
        
        Args:
            airline_owner: Airline code
            
        Returns:
            ShoppingResponseID value
        """
        # Try to get airline-specific ID from Metadata (multi-airline case)
        try:
            metadata = self.response.get("Metadata", {})
            other_metadata_list = metadata.get("Other", {}).get("OtherMetadata", [])
            
            if not isinstance(other_metadata_list, list):
                other_metadata_list = [other_metadata_list] if other_metadata_list else []
            
            for other_metadata in other_metadata_list:
                desc_metadatas = other_metadata.get("DescriptionMetadatas", {})
                desc_metadata_list = desc_metadatas.get("DescriptionMetadata", [])
                
                if not isinstance(desc_metadata_list, list):
                    desc_metadata_list = [desc_metadata_list] if desc_metadata_list else []
                
                for desc_metadata in desc_metadata_list:
                    if desc_metadata.get("MetadataKey") == "SHOPPING_RESPONSE_IDS":
                        aug_points = desc_metadata.get("AugmentationPoint", {}).get("AugPoint", [])
                        
                        if not isinstance(aug_points, list):
                            aug_points = [aug_points] if aug_points else []
                        
                        for aug_point in aug_points:
                            if aug_point.get("Owner") == airline_owner:
                                shopping_id = aug_point.get("Key")
                                if shopping_id:
                                    logger.info(f"Found airline-specific ShoppingResponseID for {airline_owner}: {shopping_id}")
                                    return shopping_id
        
        except (KeyError, TypeError) as e:
            logger.debug(f"Could not extract airline-specific ShoppingResponseID: {e}")
        
        # Fallback: Use standard ShoppingResponseID (single-airline case)
        try:
            shopping_response = self.response.get("ShoppingResponse", {})
            shopping_response_id = shopping_response.get("ShoppingResponseID", {})
            
            if isinstance(shopping_response_id, dict):
                response_id = shopping_response_id.get("value", "")
                logger.info(f"Using standard ShoppingResponseID: {response_id}")
                return response_id
        
        except (KeyError, TypeError) as e:
            logger.error(f"Error extracting ShoppingResponseID: {e}")
        
        logger.warning("No ShoppingResponseID found")
        return ""
    
    def _build_request_payload(
        self,
        offer: Dict[str, Any],
        airline_owner: str,
        shopping_response_id: str
    ) -> Dict[str, Any]:
        """
        Build the FlightPrice request payload.
        
        Based on VDC documentation, FlightPriceRQ contains:
        - Query: OriginDestination, Offers
        - Travelers: Anonymous traveler list
        - ShoppingResponseID: From AirShopping
        - DataLists: FareList, AnonymousTravelerList
        - Metadata: Filtered PriceMetadatas
        
        Args:
            offer: Selected offer object
            airline_owner: Airline code
            shopping_response_id: Shopping response ID
            
        Returns:
            FlightPrice request payload
        """
        logger.info(f"Building FlightPrice payload for offer {offer.get('OfferID', {}).get('value')}")
        
        # Extract all references from the offer for metadata filtering
        offer_refs = self._extract_offer_references(offer)
        
        # Build Query section
        query = self._build_query(offer, airline_owner, offer_refs)
        
        # Build DataLists section FIRST (filters travelers for use in _build_travelers)
        data_lists = self._build_data_lists(offer_refs, airline_owner)
        
        # Build Travelers section (uses filtered travelers from _build_data_lists)
        travelers = self._build_travelers()
        
        # Build Metadata section (filtered)
        metadata = self._filter_price_metadata(offer_refs)
        
        # Build ShoppingResponseID section
        shopping_id_node = {
            "Owner": airline_owner,
            "ResponseID": {"value": shopping_response_id}
        } if shopping_response_id else {}
        
        # Assemble the request
        request = {
            "Query": query,
            "Travelers": travelers,
            "ShoppingResponseID": shopping_id_node,
            "DataLists": data_lists
        }
        
        # Add metadata if available
        if metadata:
            request["Metadata"] = metadata
        
        logger.info("FlightPrice request payload built successfully")
        return request
    
    def _extract_offer_references(self, offer: Dict[str, Any]) -> Set[str]:
        """
        Extract all reference keys from the offer.
        
        This includes:
        - Top-level offer refs
        - FareComponent refs
        - Penalty refs
        - Any other linked data
        
        Args:
            offer: Offer object
            
        Returns:
            Set of all reference strings
        """
        refs = set()
        
        # Top-level refs
        top_refs = offer.get("refs", [])
        if not isinstance(top_refs, list):
            top_refs = [top_refs] if top_refs else []
        
        for ref_item in top_refs:
            if isinstance(ref_item, dict) and "Ref" in ref_item:
                refs.add(str(ref_item["Ref"]))
            elif isinstance(ref_item, str):
                refs.add(str(ref_item))
        
        # PricedOffer refs
        priced_offer = offer.get("PricedOffer", {})
        offer_prices = priced_offer.get("OfferPrice", [])
        
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        for offer_price in offer_prices:
            # FareDetail -> FareComponent -> refs
            fare_detail = offer_price.get("FareDetail", {})
            fare_components = fare_detail.get("FareComponent", [])
            
            if not isinstance(fare_components, list):
                fare_components = [fare_components] if fare_components else []
            
            for component in fare_components:
                # Component refs (FareGroup ListKey)
                comp_refs = component.get("refs", [])
                if not isinstance(comp_refs, list):
                    comp_refs = [comp_refs] if comp_refs else []
                
                for ref_val in comp_refs:
                    if isinstance(ref_val, str):
                        refs.add(ref_val)
                
                # Penalty refs
                fare_rules = component.get("FareRules", {})
                penalty = fare_rules.get("Penalty", {})
                penalty_refs = penalty.get("refs", [])
                
                if not isinstance(penalty_refs, list):
                    penalty_refs = [penalty_refs] if penalty_refs else []
                
                for ref_val in penalty_refs:
                    if isinstance(ref_val, str):
                        refs.add(ref_val)
        
        logger.debug(f"Extracted {len(refs)} references from offer")
        return refs
    
    def _build_query(
        self,
        offer: Dict[str, Any],
        airline_owner: str,
        offer_refs: Set[str]
    ) -> Dict[str, Any]:
        """
        Build the Query section of FlightPriceRQ.
        
        Contains:
        - OriginDestination: Flight segments
        - Offers: Selected offer with OfferID and OfferItemIDs
        
        Args:
            offer: Selected offer
            airline_owner: Airline code
            offer_refs: Set of all offer references
            
        Returns:
            Query object
        """
        # Build OriginDestination from flight segments
        origin_destinations = self._build_origin_destinations(offer)
        
        # Build Offer with OfferID and OfferItemIDs
        offer_id = offer.get("OfferID", {})
        query_offer = {
            "OfferID": {
                "value": offer_id.get("value", ""),
                "Owner": airline_owner,
                "Channel": offer_id.get("Channel", "NDC")  # Add Channel field (default to NDC)
            },
            "OfferItemIDs": {"OfferItemID": []}
        }
        
        # Add top-level refs if present
        top_refs = offer.get("refs", [])
        if top_refs:
            if not isinstance(top_refs, list):
                top_refs = [top_refs]
            
            query_refs = []
            for ref_item in top_refs:
                if isinstance(ref_item, dict) and "Ref" in ref_item:
                    query_refs.append({"Ref": ref_item["Ref"]})
                elif isinstance(ref_item, str):
                    query_refs.append({"Ref": ref_item})
            
            if query_refs:
                query_offer["refs"] = query_refs
        
        # Extract OfferItemIDs with passenger refs
        priced_offer = offer.get("PricedOffer", {})
        offer_prices = priced_offer.get("OfferPrice", [])
        
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        for offer_price in offer_prices:
            offer_item_id = offer_price.get("OfferItemID")
            
            if not offer_item_id:
                continue
            
            # Extract passenger refs from Associations
            pax_refs = []
            requested_date = offer_price.get("RequestedDate", {})
            associations = requested_date.get("Associations", [])
            
            if not isinstance(associations, list):
                associations = [associations] if associations else []
            
            if associations:
                assoc_traveler = associations[0].get("AssociatedTraveler", {})
                traveler_refs = assoc_traveler.get("TravelerReferences", [])
                
                if not isinstance(traveler_refs, list):
                    traveler_refs = [traveler_refs] if traveler_refs else []
                
                pax_refs = traveler_refs
            
            if offer_item_id and pax_refs:
                query_offer["OfferItemIDs"]["OfferItemID"].append({
                    "value": offer_item_id,
                    "refs": pax_refs
                })
        
        return {
            "OriginDestination": origin_destinations,
            "Offers": {
                "Offer": [query_offer]
            }
        }
    
    def _build_origin_destinations(self, offer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build OriginDestination list from offer associations.
        
        Maps flight segments to origin-destinations based on offer structure.
        
        Args:
            offer: Selected offer
            
        Returns:
            List of OriginDestination objects
        """
        # Build OD mapping from associations
        od_map = {}  # OD ref -> list of segment refs
        
        priced_offer = offer.get("PricedOffer", {})
        offer_prices = priced_offer.get("OfferPrice", [])
        
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        # Use first offer price to build OD structure (same for all passengers)
        if offer_prices:
            requested_date = offer_prices[0].get("RequestedDate", {})
            associations = requested_date.get("Associations", [])
            
            if not isinstance(associations, list):
                associations = [associations] if associations else []
            
            for assoc in associations:
                applicable_flight = assoc.get("ApplicableFlight", {})
                
                # OD refs
                od_refs = applicable_flight.get("OriginDestinationReferences", [])
                if not isinstance(od_refs, list):
                    od_refs = [od_refs] if od_refs else []
                
                # Segment refs
                seg_refs = applicable_flight.get("FlightSegmentReference", [])
                if not isinstance(seg_refs, list):
                    seg_refs = [seg_refs] if seg_refs else []
                
                # Map OD to segments
                for od_ref in od_refs:
                    if od_ref not in od_map:
                        od_map[od_ref] = []
                    
                    for seg_ref_obj in seg_refs:
                        if isinstance(seg_ref_obj, dict) and "ref" in seg_ref_obj:
                            seg_key = seg_ref_obj["ref"]
                            if seg_key not in od_map[od_ref]:
                                od_map[od_ref].append(seg_key)
        
        # Get flight segments from DataLists
        all_segments = self.data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
        if not isinstance(all_segments, list):
            all_segments = [all_segments] if all_segments else []
        
        segment_map = {seg.get("SegmentKey"): seg for seg in all_segments}
        
        # Build OriginDestination list
        origin_destinations = []
        
        for od_ref in sorted(od_map.keys()):
            segment_keys = od_map[od_ref]
            flights = []
            
            for seg_key in segment_keys:
                segment = segment_map.get(seg_key)
                if not segment:
                    continue
                
                # Process FlightDetail - exclude StopLocations, keep only StopQuantity
                flight_detail = segment.get("FlightDetail", {})
                processed_detail = {}
                
                if "FlightDuration" in flight_detail:
                    processed_detail["FlightDuration"] = flight_detail["FlightDuration"]
                
                if "Stops" in flight_detail:
                    stops = flight_detail["Stops"]
                    processed_stops = {}
                    
                    if "StopQuantity" in stops:
                        processed_stops["StopQuantity"] = stops["StopQuantity"]
                    
                    if processed_stops:
                        processed_detail["Stops"] = processed_stops
                
                # Build flight object
                flight = {
                    "SegmentKey": seg_key,
                    "Departure": segment.get("Departure", {}),
                    "Arrival": segment.get("Arrival", {}),
                    "MarketingCarrier": segment.get("MarketingCarrier", {}),
                    "OperatingCarrier": segment.get("OperatingCarrier", {}),
                    "FlightDetail": processed_detail
                }
                
                flights.append(flight)
            
            if flights:
                origin_destinations.append({"Flight": flights})
        
        logger.debug(f"Built {len(origin_destinations)} OriginDestinations")
        return origin_destinations
    
    def _build_travelers(self) -> Dict[str, Any]:
        """
        Build Travelers section from filtered AnonymousTravelerList.
        
        Uses the travelers that were filtered in _build_data_lists to ensure
        consistency - only travelers for the selected airline.
        
        Returns:
            Travelers object with anonymous traveler PTCs
        """
        # Use filtered travelers if available (set in _build_data_lists)
        if hasattr(self, '_filtered_travelers'):
            anonymous_travelers = self._filtered_travelers
        else:
            # Fallback to all travelers (shouldn't happen in normal flow)
            anonymous_travelers = self.data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
        
        if not isinstance(anonymous_travelers, list):
            anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
        
        traveler_list = []
        
        for traveler in anonymous_travelers:
            if isinstance(traveler, dict) and "PTC" in traveler:
                traveler_list.append({
                    "AnonymousTraveler": [
                        {"PTC": traveler.get("PTC")}
                    ]
                })
        
        logger.debug(f"Built {len(traveler_list)} travelers")
        
        return {"Traveler": traveler_list} if traveler_list else {}
    
    def _build_data_lists(
        self,
        offer_refs: Set[str],
        airline_owner: str
    ) -> Dict[str, Any]:
        """
        Build DataLists section with FareList and AnonymousTravelerList.
        
        Only includes FareGroups and travelers that are referenced by the selected offer.
        
        Args:
            offer_refs: Set of all offer references
            airline_owner: Airline code
            
        Returns:
            DataLists object
        """
        data_lists = {}
        
        # Build FareList - only referenced FareGroups
        all_fare_groups = self.data_lists.get("FareList", {}).get("FareGroup", [])
        if not isinstance(all_fare_groups, list):
            all_fare_groups = [all_fare_groups] if all_fare_groups else []
        
        fare_list = []
        for fare_group in all_fare_groups:
            list_key = fare_group.get("ListKey")
            
            # Only include if referenced by the offer
            if list_key and list_key in offer_refs:
                # Also collect refs from FareGroup itself
                fg_refs = fare_group.get("refs", [])
                if fg_refs:
                    if not isinstance(fg_refs, list):
                        fg_refs = [fg_refs]
                    
                    for ref_val in fg_refs:
                        if isinstance(ref_val, str):
                            offer_refs.add(ref_val)
                
                # Build simplified FareGroup
                new_fare_group = {
                    "ListKey": list_key,
                    "FareBasisCode": fare_group.get("FareBasisCode", {})
                }
                
                if fg_refs:
                    new_fare_group["refs"] = fare_group["refs"]
                
                fare_list.append(new_fare_group)
        
        if fare_list:
            data_lists["FareGroup"] = fare_list
        
        # Add AnonymousTravelerList - filter to only include travelers for this airline
        # Store filtered travelers for use in _build_travelers
        anonymous_traveler_list_full = self.data_lists.get("AnonymousTravelerList", {})
        if anonymous_traveler_list_full:
            all_travelers = anonymous_traveler_list_full.get("AnonymousTraveler", [])
            if not isinstance(all_travelers, list):
                all_travelers = [all_travelers] if all_travelers else []
            
            # Filter travelers to only those belonging to the selected airline
            # Traveler ObjectKeys are typically prefixed with airline code (e.g., "EY-PAX1")
            filtered_travelers = []
            for traveler in all_travelers:
                object_key = traveler.get("ObjectKey", "")
                # Check if this traveler belongs to the selected airline
                if object_key.startswith(f"{airline_owner}-") or object_key in offer_refs:
                    filtered_travelers.append(traveler)
            
            if filtered_travelers:
                data_lists["AnonymousTravelerList"] = {
                    "AnonymousTraveler": filtered_travelers
                }
                # Store for use in _build_travelers
                self._filtered_travelers = filtered_travelers
                logger.debug(f"Filtered to {len(filtered_travelers)} travelers for airline {airline_owner}")
        
        logger.debug(f"Built DataLists with {len(fare_list)} FareGroups")
        return data_lists
    
    def _filter_price_metadata(self, offer_refs: Set[str]) -> Dict[str, Any]:
        """
        Filter PriceMetadata to only include items referenced by the offer.
        
        Args:
            offer_refs: Set of all offer references
            
        Returns:
            Filtered metadata structure (or empty dict if none)
        """
        try:
            other_metadata_list = self.response.get("Metadata", {}).get("Other", {}).get("OtherMetadata", [])
            
            if not other_metadata_list:
                return {}
            
            if not isinstance(other_metadata_list, list):
                other_metadata_list = [other_metadata_list]
            
            if not other_metadata_list:
                return {}
            
            # Get first item (typically contains PriceMetadatas)
            first_meta = other_metadata_list[0]
            if not isinstance(first_meta, dict):
                return {}
            
            price_metadatas = first_meta.get("PriceMetadatas", {})
            if not price_metadatas:
                return {}
            
            price_metadata_list = price_metadatas.get("PriceMetadata", [])
            if not isinstance(price_metadata_list, list):
                price_metadata_list = [price_metadata_list] if price_metadata_list else []
            
            # Filter to only referenced items
            filtered = []
            seen_keys = set()
            stringified_refs = {str(ref) for ref in offer_refs}
            
            for item in price_metadata_list:
                if not isinstance(item, dict):
                    continue
                
                metadata_key = item.get("MetadataKey")
                if not metadata_key:
                    continue
                
                # Only include if referenced
                if str(metadata_key) in stringified_refs:
                    if metadata_key not in seen_keys:
                        filtered.append(item)
                        seen_keys.add(metadata_key)
            
            if filtered:
                logger.debug(f"Filtered {len(filtered)} PriceMetadata items (from {len(price_metadata_list)})")
                return {
                    "Other": {
                        "OtherMetadata": [
                            {"PriceMetadatas": {"PriceMetadata": filtered}}
                        ]
                    }
                }
            
        except (KeyError, TypeError) as e:
            logger.debug(f"Could not filter PriceMetadata: {e}")
        
        return {}
    
    def build_with_ancillaries(
        self,
        flight_price_response: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]] = None,
        servicelist_response: Optional[Dict[str, Any]] = None,
        selected_seats: List[str] = None,
        selected_services: List[str] = None,
        selected_offer_index: int = 0
    ) -> Dict[str, Any]:
        """
        Build FlightPrice request with selected ancillaries for pricing.
        
        For ancillaries with PricedInd=false, this creates a FlightPrice request
        that includes the selected seats/services to get their prices.
        
        This uses the proven logic from build_flightprice_ancillary_rq.py script.
        
        Args:
            flight_price_response: Original FlightPrice response
            seatavailability_response: SeatAvailability response (optional)
            servicelist_response: ServiceList response (optional)
            selected_seats: List of selected seat ObjectKeys (optional)
            selected_services: List of selected service ObjectKeys (optional)
            selected_offer_index: Index of selected offer (default: 0)
            
        Returns:
            FlightPrice request payload with ancillary selections
        """
        from scripts.build_flightprice_ancillary_rq import build_flightprice_ancillary_request
        
        logger.info("Building FlightPrice request with ancillaries using proven script logic")
        
        # Use the existing proven script
        request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services or [],
            selected_seats=selected_seats or [],
            selected_offer_index=selected_offer_index
        )
        
        logger.info("FlightPrice request with ancillaries built successfully using script")
        return request

