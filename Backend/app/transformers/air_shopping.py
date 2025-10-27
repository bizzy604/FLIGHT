"""AirShopping response transformer."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AirShoppingTransformer:
    """
    Transforms VDC AirShopping responses to frontend-friendly format.
    
    Based on actual VDC API response structure with support for:
    - OfferPrice array (per-passenger pricing)
    - DataLists with baggage allowances, segments, penalties
    - Trip type detection (one-way vs round-trip)
    - Discount support
    - Multiple airlines and offers
    """
    
    def transform(
        self, 
        response: Dict[str, Any],
        search_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform AirShopping response.
        
        Args:
            response: Raw VDC AirShopping response
            search_context: Optional search request context
            
        Returns:
            Transformed response with offers grouped by airline and metadata
        """
        logger.info("Transforming AirShopping response")
        
        try:
            # Extract offers from OffersGroup
            offers_group = response.get("OffersGroup", {})
            airline_offers_list = offers_group.get("AirlineOffers", [])
            
            if not isinstance(airline_offers_list, list):
                airline_offers_list = [airline_offers_list] if airline_offers_list else []
            
            if not airline_offers_list:
                logger.warning("No airline offers found in response")
                return {
                    "airlines": [],
                    "metadata": self._extract_metadata(response, search_context),
                    "raw_response": response
                }
            
            # Extract DataLists (shared across all offers)
            data_lists = response.get("DataLists", {})
            
            # Transform offers grouped by airline
            airlines = []
            total_offers_count = 0
            
            for airline_offer_group in airline_offers_list:
                owner = airline_offer_group.get("Owner", {})
                airline_code = owner.get("value", "") if isinstance(owner, dict) else str(owner)
                
                # If Owner is missing at group level, extract from first offer's OfferID
                if not airline_code or airline_code.strip() == "":
                    airline_offers_raw = airline_offer_group.get("AirlineOffer", [])
                    if not isinstance(airline_offers_raw, list):
                        airline_offers_raw = [airline_offers_raw] if airline_offers_raw else []
                    
                    if airline_offers_raw:
                        first_offer = airline_offers_raw[0]
                        offer_id = first_offer.get("OfferID", {})
                        if isinstance(offer_id, dict):
                            airline_code = offer_id.get("Owner", "")
                        
                        if airline_code:
                            logger.info(f"Extracted airline code '{airline_code}' from OfferID.Owner")
                
                total_quantity = airline_offer_group.get("TotalOfferQuantity", 0)
                
                # Get airline offers
                airline_offers = airline_offer_group.get("AirlineOffer", [])
                if not isinstance(airline_offers, list):
                    airline_offers = [airline_offers] if airline_offers else []
                
                # Transform each offer
                transformed_offers = []
                for idx, offer in enumerate(airline_offers):
                    try:
                        transformed = self._transform_single_offer(
                            offer=offer,
                            airline_code=airline_code,
                            offer_index=total_offers_count + idx,
                            data_lists=data_lists
                        )
                        transformed_offers.append(transformed)
                    except Exception as e:
                        logger.error(f"Error transforming offer {idx} for airline {airline_code}: {e}")
                        continue
                
                airlines.append({
                    "code": airline_code,
                    "total_offers": total_quantity,
                    "offers": transformed_offers
                })
                
                total_offers_count += len(transformed_offers)
            
            # Detect trip type from DataLists
            trip_type = self._detect_trip_type(data_lists)
            
            result = {
                "airlines": airlines,
                "trip_type": trip_type,
                "metadata": self._extract_metadata(response, search_context),
                "raw_response": response
            }
            
            logger.info(f"Transformed {total_offers_count} offers from {len(airlines)} airline(s), trip type: {trip_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error transforming AirShopping response: {e}", exc_info=True)
            raise
    
    def _transform_single_offer(
        self,
        offer: Dict[str, Any],
        airline_code: str,
        offer_index: int,
        data_lists: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform a single airline offer.
        
        Args:
            offer: Single AirlineOffer object
            airline_code: Airline owner code
            offer_index: Global offer index
            data_lists: Shared DataLists
            
        Returns:
            Transformed offer with all details
        """
        # Extract PricedOffer
        priced_offer = offer.get("PricedOffer", {})
        
        transformed = {
            "offer_index": offer_index,
            "offer_id": self._extract_offer_id(offer),
            "airline": airline_code,
            "pricing": self._extract_pricing(priced_offer),
            "breakdown": self._extract_price_breakdown(priced_offer),
            "flights": self._extract_flights(priced_offer, data_lists),
            "baggage": self._extract_baggage_info(priced_offer, data_lists),
            "fare_details": self._extract_fare_details(priced_offer, data_lists),
            "penalties": self._extract_penalties(priced_offer, data_lists),
            "time_limits": self._extract_time_limits(offer),
            "metadata": {
                "currency": self._extract_currency(priced_offer)
            }
        }
        
        return transformed
    
    def _extract_offer_id(self, offer: Dict[str, Any]) -> str:
        """Extract offer ID."""
        offer_id = offer.get("OfferID", {})
        if isinstance(offer_id, dict):
            return offer_id.get("value", "")
        return str(offer_id) if offer_id else ""
    
    def _extract_pricing(self, priced_offer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract main pricing summary from first OfferPrice.
        
        Args:
            priced_offer: PricedOffer object
            
        Returns:
            Pricing summary with total, base, taxes, discount
        """
        # Get first OfferPrice (contains aggregated pricing)
        offer_prices = priced_offer.get("OfferPrice", [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        if not offer_prices:
            return {
                "total": 0.0,
                "base_fare": 0.0,
                "taxes": 0.0,
                "discount": 0.0,
                "currency": "USD"
            }
        
        first_price = offer_prices[0]
        price_detail = first_price.get("RequestedDate", {}).get("PriceDetail", {})
        total_amount = price_detail.get("TotalAmount", {}).get("SimpleCurrencyPrice", {})
        base_amount = price_detail.get("BaseAmount", {})
        taxes = price_detail.get("Taxes", {}).get("Total", {})
        
        # Extract discount if present
        discounts = price_detail.get("Discount", [])
        if not isinstance(discounts, list):
            discounts = [discounts] if discounts else []
        
        discount_amount = 0.0
        discount_details = {}
        if discounts:
            first_discount = discounts[0]
            discount_amount = float(first_discount.get("DiscountAmount", {}).get("value", 0))
            discount_details = {
                "amount": discount_amount,
                "percent": first_discount.get("DiscountPercent", 0),
                "code": first_discount.get("discountCode", ""),
                "name": first_discount.get("discountName", ""),
                "pre_discount_amount": float(first_discount.get("preDiscountedAmount", {}).get("value", 0))
            }
        
        return {
            "total": float(total_amount.get("value", 0)),
            "base_fare": float(base_amount.get("value", 0)),
            "taxes": float(taxes.get("value", 0)),
            "discount": discount_amount,
            "discount_details": discount_details if discount_details else None,
            "currency": total_amount.get("Code", "USD")
        }
    
    def _extract_price_breakdown(self, priced_offer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract detailed price breakdown by OfferPrice (per passenger/traveler).
        
        Args:
            priced_offer: PricedOffer object
            
        Returns:
            List of price breakdowns per passenger
        """
        breakdown = []
        
        offer_prices = priced_offer.get("OfferPrice", [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        for idx, offer_price in enumerate(offer_prices):
            price_detail = offer_price.get("RequestedDate", {}).get("PriceDetail", {})
            total_amount = price_detail.get("TotalAmount", {}).get("SimpleCurrencyPrice", {})
            base_amount = price_detail.get("BaseAmount", {})
            taxes_obj = price_detail.get("Taxes", {})
            taxes_total = taxes_obj.get("Total", {})
            
            # Extract traveler associations
            associations = offer_price.get("RequestedDate", {}).get("Associations", [])
            if not isinstance(associations, list):
                associations = [associations] if associations else []
            
            traveler_refs = []
            flight_refs = []
            origin_dest_refs = []
            
            for assoc in associations:
                # Traveler references
                assoc_traveler = assoc.get("AssociatedTraveler", {})
                refs = assoc_traveler.get("TravelerReferences", [])
                if refs:
                    traveler_refs.extend(refs if isinstance(refs, list) else [refs])
                
                # Flight references
                applicable_flight = assoc.get("ApplicableFlight", {})
                flight_refs_obj = applicable_flight.get("FlightReferences", {})
                f_refs = flight_refs_obj.get("value", [])
                if f_refs:
                    flight_refs.extend(f_refs if isinstance(f_refs, list) else [f_refs])
                
                # Origin destination references  
                od_refs = applicable_flight.get("OriginDestinationReferences", [])
                if od_refs:
                    origin_dest_refs.extend(od_refs if isinstance(od_refs, list) else [od_refs])
            
            breakdown.append({
                "offer_item_id": offer_price.get("OfferItemID", ""),
                "traveler_refs": traveler_refs,
                "flight_refs": flight_refs,
                "origin_destination_refs": origin_dest_refs,
                "total": float(total_amount.get("value", 0)),
                "base_fare": float(base_amount.get("value", 0)),
                "taxes": float(taxes_total.get("value", 0)),
                "tax_breakdown": self._extract_tax_breakdown(taxes_obj),
                "currency": total_amount.get("Code", base_amount.get("Code", "USD"))
            })
        
        return breakdown
    
    def _extract_tax_breakdown(self, taxes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract individual tax components.
        
        Args:
            taxes: Taxes object
            
        Returns:
            List of tax details
        """
        tax_list = []
        
        breakdown = taxes.get("Breakdown", {})
        tax_items = breakdown.get("Tax", [])
        
        if not isinstance(tax_items, list):
            tax_items = [tax_items] if tax_items else []
        
        for tax in tax_items:
            tax_list.append({
                "code": tax.get("TaxCode", ""),
                "amount": float(tax.get("Amount", {}).get("value", 0)),
                "description": tax.get("Description", "")
            })
        
        return tax_list
    
    def _extract_flights(self, priced_offer: Dict[str, Any], data_lists: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract flight information with segments.
        
        Args:
            priced_offer: PricedOffer object
            data_lists: DataLists
            
        Returns:
            List of flights with segments
        """
        flights = []
        
        # Get flight references from Associations
        associations = priced_offer.get("Associations", [])
        if not isinstance(associations, list):
            associations = [associations] if associations else []
        
        for assoc in associations:
            applicable_flight = assoc.get("ApplicableFlight", {})
            
            # Flight references
            flight_refs_obj = applicable_flight.get("FlightReferences", {})
            flight_refs = flight_refs_obj.get("value", [])
            if not isinstance(flight_refs, list):
                flight_refs = [flight_refs] if flight_refs else []
            
            # OD references
            od_refs = applicable_flight.get("OriginDestinationReferences", [])
            if not isinstance(od_refs, list):
                od_refs = [od_refs] if od_refs else []
            
            # Segment references
            segment_refs_list = applicable_flight.get("FlightSegmentReference", [])
            if not isinstance(segment_refs_list, list):
                segment_refs_list = [segment_refs_list] if segment_refs_list else []
            
            # Extract segments
            segments = []
            for seg_ref in segment_refs_list:
                ref = seg_ref.get("ref", "") if isinstance(seg_ref, dict) else seg_ref
                class_of_service = seg_ref.get("ClassOfService", {}) if isinstance(seg_ref, dict) else {}
                
                # Lookup segment details in DataLists
                segment_detail = self._lookup_segment(ref, data_lists)
                if segment_detail:
                    # Add cabin/class info from association
                    if class_of_service:
                        code_obj = class_of_service.get("Code", {})
                        rbd = code_obj.get("value", "") if isinstance(code_obj, dict) else code_obj
                        
                        marketing_name = class_of_service.get("MarketingName", {})
                        cabin_designator = marketing_name.get("CabinDesignator", "Y")
                        cabin_class_name = marketing_name.get("value", "")
                        
                        segment_detail["rbd"] = rbd
                        segment_detail["cabin_type"] = self._map_cabin_type(cabin_designator)
                        segment_detail["cabin_class_name"] = cabin_class_name
                    
                    segments.append(segment_detail)
            
            if segments:
                flights.append({
                    "flight_refs": flight_refs,
                    "od_refs": od_refs,
                    "segments": segments
                })
        
        return flights
    
    def _lookup_segment(self, segment_ref: str, data_lists: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Lookup segment details in DataLists."""
        segment_list = data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
        if not isinstance(segment_list, list):
            segment_list = [segment_list] if segment_list else []
        
        for segment in segment_list:
            if segment.get("SegmentKey", "") == segment_ref:
                departure = segment.get("Departure", {})
                arrival = segment.get("Arrival", {})
                marketing_carrier = segment.get("MarketingCarrier", {})
                equipment = segment.get("Equipment", {})
                flight_detail = segment.get("FlightDetail", {})
                
                return {
                    "segment_key": segment_ref,
                    "departure": {
                        "airport": departure.get("AirportCode", {}).get("value", ""),
                        "date": departure.get("Date", ""),
                        "time": departure.get("Time", ""),
                        "terminal": departure.get("Terminal", {}).get("Name", "")
                    },
                    "arrival": {
                        "airport": arrival.get("AirportCode", {}).get("value", ""),
                        "date": arrival.get("Date", ""),
                        "time": arrival.get("Time", ""),
                        "terminal": arrival.get("Terminal", {}).get("Name", "")
                    },
                    "marketing_carrier": {
                        "airline": marketing_carrier.get("AirlineID", {}).get("value", ""),
                        "name": marketing_carrier.get("Name", ""),
                        "flight_number": marketing_carrier.get("FlightNumber", {}).get("value", "")
                    },
                    "aircraft": equipment.get("AircraftCode", {}).get("value", ""),
                    "duration": flight_detail.get("FlightDuration", {}).get("Value", "")
                }
        
        return None
    
    def _map_cabin_type(self, cabin_designator: str) -> str:
        """Map cabin designator to cabin type name."""
        cabin_map = {
            "F": "First",
            "C": "Business",
            "W": "Premium Economy",
            "Y": "Economy"
        }
        return cabin_map.get(cabin_designator, "Economy")
    
    def _extract_fare_details(self, priced_offer: Dict[str, Any], data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fare basis codes and cabin information from OfferPrice.
        
        Args:
            priced_offer: PricedOffer object
            data_lists: DataLists from response
            
        Returns:
            Consolidated fare details
        """
        # Get first OfferPrice
        offer_prices = priced_offer.get("OfferPrice", [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        if not offer_prices:
            return {}
        
        first_price = offer_prices[0]
        fare_detail = first_price.get("FareDetail", {})
        fare_components = fare_detail.get("FareComponent", [])
        
        if not isinstance(fare_components, list):
            fare_components = [fare_components] if fare_components else []
        
        if not fare_components:
            return {}
        
        # Get first fare component and look up in FareList
        first_component = fare_components[0]
        fare_refs = first_component.get("refs", [])
        if not isinstance(fare_refs, list):
            fare_refs = [fare_refs] if fare_refs else []
        
        fare_basis_code = ""
        fare_code = ""
        
        # Lookup in FareList
        if fare_refs:
            fare_list = data_lists.get("FareList", {}).get("FareGroup", [])
            if not isinstance(fare_list, list):
                fare_list = [fare_list] if fare_list else []
            
            for fare_group in fare_list:
                if fare_group.get("ListKey") in fare_refs:
                    fare_basis_obj = fare_group.get("FareBasisCode", {})
                    fare_basis_code = fare_basis_obj.get("Code", "")
                    
                    fare_obj = fare_group.get("Fare", {}).get("FareCode", {})
                    fare_code = fare_obj.get("Code", "")
                    break
        
        # Extract associations to get cabin info
        associations = priced_offer.get("Associations", [])
        if not isinstance(associations, list):
            associations = [associations] if associations else []
        
        cabin_type = "Economy"  # Default
        booking_class_code = ""
        booking_class_name = ""
        
        if associations:
            applicable_flight = associations[0].get("ApplicableFlight", {})
            segment_refs = applicable_flight.get("FlightSegmentReference", [])
            if not isinstance(segment_refs, list):
                segment_refs = [segment_refs] if segment_refs else []
            
            if segment_refs:
                class_of_service = segment_refs[0].get("ClassOfService", {})
                code_obj = class_of_service.get("Code", {})
                booking_class_code = code_obj.get("value", "") if isinstance(code_obj, dict) else code_obj
                
                marketing_name = class_of_service.get("MarketingName", {})
                cabin_designator = marketing_name.get("CabinDesignator", "Y")
                booking_class_name = marketing_name.get("value", "")
                
                cabin_type = self._map_cabin_type(cabin_designator)
        
        return {
            "fare_basis_code": fare_basis_code,
            "fare_code": fare_code,
            "rbd": booking_class_code,
            "cabin_type": cabin_type,
            "booking_class": {
                "code": booking_class_code,
                "name": booking_class_name
            }
        }
    
    def _extract_penalties(self, priced_offer: Dict[str, Any], data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract penalty and fare rules from PenaltyList (via refs).
        
        Args:
            priced_offer: PricedOffer object
            data_lists: DataLists containing PenaltyList
            
        Returns:
            Consolidated penalty information
        """
        # Get penalty references from FareComponents
        penalty_refs = []
        
        offer_prices = priced_offer.get("OfferPrice", [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        for offer_price in offer_prices:
            fare_detail = offer_price.get("FareDetail", {})
            fare_components = fare_detail.get("FareComponent", [])
            if not isinstance(fare_components, list):
                fare_components = [fare_components] if fare_components else []
            
            for component in fare_components:
                fare_rules = component.get("FareRules", {})
                penalty = fare_rules.get("Penalty", {})
                refs = penalty.get("refs", [])
                if refs:
                    penalty_refs.extend(refs if isinstance(refs, list) else [refs])
        
        # Lookup penalties in DataLists
        penalty_list = data_lists.get("PenaltyList", {}).get("Penalty", [])
        if not isinstance(penalty_list, list):
            penalty_list = [penalty_list] if penalty_list else []
        
        penalties = {
            "change": {"allowed": True, "fees": []},
            "cancel": {"allowed": True, "fees": []},
            "refundable": True
        }
        
        for pen_ref in penalty_refs:
            # Find matching penalty
            matching_penalty = next((p for p in penalty_list if p.get("ObjectKey") == pen_ref), None)
            
            if not matching_penalty:
                continue
            
            details = matching_penalty.get("Details", {}).get("Detail", [])
            if not isinstance(details, list):
                details = [details] if details else []
            
            for detail in details:
                penalty_type = detail.get("Type", "")
                amounts_obj = detail.get("Amounts", {}).get("Amount", [])
                if not isinstance(amounts_obj, list):
                    amounts_obj = [amounts_obj] if amounts_obj else []
                
                fee_info = {
                    "type": penalty_type,
                    "max_amount": 0.0,
                    "min_amount": 0.0,
                    "currency": "USD",
                    "remarks": []
                }
                
                for amount_entry in amounts_obj:
                    curr_amount = amount_entry.get("CurrencyAmountValue", {})
                    amount_val = float(curr_amount.get("value", 0))
                    currency = curr_amount.get("Code", "USD")
                    application = amount_entry.get("AmountApplication", "")
                    
                    if application == "MAX":
                        fee_info["max_amount"] = amount_val
                        fee_info["currency"] = currency
                    elif application == "MIN":
                        fee_info["min_amount"] = amount_val
                    
                    # Extract remarks
                    remarks = amount_entry.get("ApplicableFeeRemarks", {}).get("Remark", [])
                    if remarks:
                        if not isinstance(remarks, list):
                            remarks = [remarks]
                        for remark in remarks:
                            remark_val = remark.get("value", "") if isinstance(remark, dict) else remark
                            if remark_val and remark_val not in fee_info["remarks"]:
                                fee_info["remarks"].append(remark_val)
                
                # Categorize by type
                if "Change" in penalty_type:
                    penalties["change"]["fees"].append(fee_info)
                    penalties["change"]["allowed"] = matching_penalty.get("ChangeAllowedInd", True)
                elif "Cancel" in penalty_type or "Refund" in penalty_type:
                    penalties["cancel"]["fees"].append(fee_info)
                    penalties["refundable"] = matching_penalty.get("RefundableInd", True)
        
        return penalties
    
    def _extract_baggage_info(self, priced_offer: Dict[str, Any], data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract baggage allowances from DataLists (via refs).
        
        Args:
            priced_offer: PricedOffer object
            data_lists: DataLists containing baggage allowances
            
        Returns:
            Consolidated baggage information
        """
        # Get baggage references from Associations
        checked_bag_refs = []
        carry_on_refs = []
        
        offer_prices = priced_offer.get("OfferPrice", [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        for offer_price in offer_prices:
            associations = offer_price.get("RequestedDate", {}).get("Associations", [])
            if not isinstance(associations, list):
                associations = [associations] if associations else []
            
            for assoc in associations:
                applicable_flight = assoc.get("ApplicableFlight", {})
                segment_refs = applicable_flight.get("FlightSegmentReference", [])
                if not isinstance(segment_refs, list):
                    segment_refs = [segment_refs] if segment_refs else []
                
                for seg_ref in segment_refs:
                    bag_detail = seg_ref.get("BagDetailAssociation", {})
                    
                    checked_refs = bag_detail.get("CheckedBagReferences", [])
                    if checked_refs:
                        if isinstance(checked_refs, list):
                            checked_bag_refs.extend(checked_refs)
                        else:
                            checked_bag_refs.append(checked_refs)
                    
                    carry_refs = bag_detail.get("CarryOnReferences", [])
                    if carry_refs:
                        if isinstance(carry_refs, list):
                            carry_on_refs.extend(carry_refs)
                        else:
                            carry_on_refs.append(carry_refs)
        
        # Lookup in DataLists
        checked_list = data_lists.get("CheckedBagAllowanceList", {}).get("CheckedBagAllowance", [])
        if not isinstance(checked_list, list):
            checked_list = [checked_list] if checked_list else []
        
        carry_on_list = data_lists.get("CarryOnAllowanceList", {}).get("CarryOnAllowance", [])
        if not isinstance(carry_on_list, list):
            carry_on_list = [carry_on_list] if carry_on_list else []
        
        baggage = {}
        
        # Extract checked baggage
        for ref in set(checked_bag_refs):  # Deduplicate
            matching_bag = next((b for b in checked_list if b.get("ListKey") == ref), None)
            if matching_bag:
                weight_allowance = matching_bag.get("WeightAllowance", {})
                max_weights = weight_allowance.get("MaximumWeight", [])
                if not isinstance(max_weights, list):
                    max_weights = [max_weights] if max_weights else []
                
                weight_val = 0
                weight_uom = "Kilogram"
                if max_weights:
                    weight_val = max_weights[0].get("Value", 0)
                    weight_uom = max_weights[0].get("UOM", "Kilogram")
                
                baggage["checked"] = {
                    "weight": weight_val,
                    "unit": weight_uom,
                    "description": matching_bag.get("AllowanceDescription", {}).get("ApplicableParty", "Traveler")
                }
                break  # Take first matching
        
        # Extract carry-on baggage
        for ref in set(carry_on_refs):
            matching_bag = next((b for b in carry_on_list if b.get("ListKey") == ref), None)
            if matching_bag:
                piece_allowances = matching_bag.get("PieceAllowance", [])
                if not isinstance(piece_allowances, list):
                    piece_allowances = [piece_allowances] if piece_allowances else []
                
                total_qty = 0
                if piece_allowances:
                    total_qty = piece_allowances[0].get("TotalQuantity", 0)
                
                weight_allowance = matching_bag.get("WeightAllowance", {})
                max_weights = weight_allowance.get("MaximumWeight", [])
                if not isinstance(max_weights, list):
                    max_weights = [max_weights] if max_weights else []
                
                weight_val = 0
                weight_uom = "Kilogram"
                if max_weights:
                    weight_val = max_weights[0].get("Value", 0)
                    weight_uom = max_weights[0].get("UOM", "Kilogram")
                
                baggage["carry_on"] = {
                    "quantity": total_qty,
                    "weight": weight_val,
                    "unit": weight_uom
                }
                break
        
        return baggage
    
    def _detect_trip_type(self, data_lists: Dict[str, Any]) -> str:
        """
        Detect trip type based on OriginDestination count.
        
        Args:
            data_lists: DataLists containing OriginDestinationList
            
        Returns:
            "one-way", "round-trip", or "multi-city"
        """
        od_list = data_lists.get("OriginDestinationList", {}).get("OriginDestination", [])
        if not isinstance(od_list, list):
            od_list = [od_list] if od_list else []
        
        # One OD = one-way, Two ODs = round-trip, 3+ = multi-city
        od_count = len(od_list)
        if od_count >= 3:
            return "multi-city"
        elif od_count == 2:
            return "round-trip"
        else:
            return "one-way"
    
    def _extract_time_limits(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract offer expiration and payment time limits.
        
        Args:
            offer: AirlineOffer object
            
        Returns:
            Time limit information
        """
        time_limits = offer.get("TimeLimits", {})
        
        return {
            "offer_expiration": time_limits.get("OfferExpiration", {}).get("DateTime", ""),
            "payment_time_limit": time_limits.get("Payment", {}).get("DateTime", "")
        }
    
    def _extract_currency(self, priced_offer: Dict[str, Any]) -> str:
        """Extract currency code from offer."""
        offer_prices = priced_offer.get("OfferPrice", [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        if offer_prices:
            price_detail = offer_prices[0].get("RequestedDate", {}).get("PriceDetail", {})
            total = price_detail.get("TotalAmount", {}).get("SimpleCurrencyPrice", {})
            return total.get("Code", "USD")
        
        return "USD"
    
    def _extract_metadata(
        self, 
        response: Dict[str, Any],
        search_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract metadata from response.
        
        Args:
            response: Raw response
            search_context: Optional search context
            
        Returns:
            Metadata dictionary
        """
        # Extract shopping response ID
        shopping_response_id = response.get("ShoppingResponseID", {})
        response_id = shopping_response_id.get("ResponseID", {})
        response_id_value = response_id.get("value", "") if isinstance(response_id, dict) else ""
        
        # Extract document version
        document = response.get("Document", {})
        reference_version = document.get("ReferenceVersion", "")
        
        metadata = {
            "search_context": search_context,
            "response_id": response_id_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reference_version": reference_version
        }
        
        return metadata
