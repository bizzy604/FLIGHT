"""FlightPrice response transformer."""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FlightPriceTransformer:
    """
    Transforms VDC FlightPrice responses to frontend-friendly format.
    
    Based on actual VDC API response structure with support for:
    - OfferPrice array (per-passenger pricing)
    - DataLists with baggage allowances
    - PenaltyList for fare rules
    - Trip type detection (one-way vs round-trip)
    """
    
    def transform(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform FlightPrice response.
        
        Args:
            response: Raw VDC FlightPrice response
            
        Returns:
            Transformed pricing data
        """
        logger.info("Transforming FlightPrice response")
        
        try:
            # Extract priced offer
            priced_offers = response.get("PricedFlightOffers", {}).get("PricedFlightOffer", [])
            
            if not isinstance(priced_offers, list):
                priced_offers = [priced_offers] if priced_offers else []
            
            if not priced_offers:
                # Log the response structure for debugging
                logger.error(f"No priced offers found. Response keys: {list(response.keys())}")
                logger.error(f"Full response: {json.dumps(response, indent=2)[:2000]}")  # First 2000 chars
                raise ValueError("No priced offers found in response")
            
            # Transform first offer (VDC returns one priced offer per FlightPrice request)
            offer = priced_offers[0]
            data_lists = response.get("DataLists", {})
            
            transformed = {
                "offer_id": self._extract_offer_id(offer),
                "pricing": self._extract_pricing(offer),
                "breakdown": self._extract_price_breakdown(offer),
                "fare_details": self._extract_fare_details(offer, data_lists),
                "penalties": self._extract_penalties(offer, data_lists),
                "baggage": self._extract_baggage_info(offer, data_lists),
                "segments": self._extract_segment_details(data_lists),
                "trip_type": self._detect_trip_type(data_lists),
                "time_limits": self._extract_time_limits(offer),
                "metadata": {
                    "currency": self._extract_currency(offer),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info(f"Transformed offer {transformed['offer_id']} with trip type: {transformed['trip_type']}")
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming FlightPrice response: {e}", exc_info=True)
            raise
    
    def _extract_offer_id(self, offer: Dict[str, Any]) -> str:
        """Extract offer ID."""
        offer_id = offer.get("OfferID", {})
        if isinstance(offer_id, dict):
            return offer_id.get("value", "")
        return str(offer_id) if offer_id else ""
    
    def _extract_pricing(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract main pricing summary from first OfferPrice.
        
        Args:
            offer: Priced offer object
            
        Returns:
            Pricing summary with total, base, taxes, discount
        """
        # Get first OfferPrice (contains aggregated pricing)
        offer_prices = offer.get("OfferPrice", [])
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
    
    def _extract_price_breakdown(self, offer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract detailed price breakdown by OfferPrice (per passenger/traveler).
        
        Args:
            offer: Priced offer object
            
        Returns:
            List of price breakdowns per passenger
        """
        breakdown = []
        
        offer_prices = offer.get("OfferPrice", [])
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
    
    def _extract_fare_details(self, offer: Dict[str, Any], data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fare basis codes and cabin information from OfferPrice.
        
        Args:
            offer: Priced offer object
            data_lists: DataLists from response
            
        Returns:
            Consolidated fare details
        """
        # Get first OfferPrice
        offer_prices = offer.get("OfferPrice", [])
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
        
        # Get first fare component (primary fare basis)
        first_component = fare_components[0]
        fare_basis_obj = first_component.get("FareBasis", {})
        
        # Extract associations to get cabin info
        associations = first_price.get("RequestedDate", {}).get("Associations", [])
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
                
                # Map cabin designator to cabin type
                cabin_map = {"F": "First", "C": "Business", "W": "Premium Economy", "Y": "Economy"}
                cabin_type = cabin_map.get(cabin_designator, "Economy")
        
        return {
            "fare_basis_code": fare_basis_obj.get("FareBasisCode", {}).get("Code", ""),
            "rbd": fare_basis_obj.get("RBD", ""),
            "cabin_type": cabin_type,
            "booking_class": {
                "code": booking_class_code,
                "name": booking_class_name
            }
        }
    
    def _extract_penalties(self, offer: Dict[str, Any], data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract penalty and fare rules from PenaltyList (via refs).
        
        Args:
            offer: Priced offer object
            data_lists: DataLists containing PenaltyList
            
        Returns:
            Consolidated penalty information
        """
        # Get penalty references from FareComponents
        penalty_refs = []
        
        offer_prices = offer.get("OfferPrice", [])
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
        if not isinstance(offer_items, list):
            offer_items = [offer_items] if offer_items else []
        
        for item in offer_items:
            penalty_info = item.get("PenaltyInformation", {})
            
            # Change penalties
            change_penalty = penalty_info.get("ChangeBeforeDeparture", {})
            if change_penalty:
                penalties["changes_allowed"] = change_penalty.get("Allowed", True)
                change_fee = change_penalty.get("Amount", {})
                if change_fee:
                    penalties["change_fee"] = float(change_fee.get("value", 0))
            
            # Refund penalties
            refund_penalty = penalty_info.get("RefundBeforeDeparture", {})
            if refund_penalty:
                penalties["refundable"] = refund_penalty.get("Allowed", True)
                refund_fee = refund_penalty.get("Amount", {})
                if refund_fee:
                    penalties["cancellation_fee"] = float(refund_fee.get("value", 0))
    
    def _extract_baggage_info(self, offer: Dict[str, Any], data_lists: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract baggage allowances from DataLists (via refs).
        
        Args:
            offer: Priced offer object
            data_lists: DataLists containing baggage allowances
            
        Returns:
            Consolidated baggage information
        """
        # Get baggage references from Associations
        checked_bag_refs = []
        carry_on_refs = []
        
        offer_prices = offer.get("OfferPrice", [])
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
    
    def _extract_segment_details(self, data_lists: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract flight segment details from DataLists.
        
        Args:
            data_lists: DataLists containing FlightSegmentList
            
        Returns:
            List of segment details
        """
        segments = []
        
        segment_list = data_lists.get("FlightSegmentList", {}).get("FlightSegment", [])
        if not isinstance(segment_list, list):
            segment_list = [segment_list] if segment_list else []
        
        for segment in segment_list:
            departure = segment.get("Departure", {})
            arrival = segment.get("Arrival", {})
            marketing_carrier = segment.get("MarketingCarrier", {})
            equipment = segment.get("Equipment", {})
            flight_detail = segment.get("FlightDetail", {})
            
            segments.append({
                "segment_key": segment.get("SegmentKey", ""),
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
            })
        
        return segments
    
    def _detect_trip_type(self, data_lists: Dict[str, Any]) -> str:
        """
        Detect trip type based on OriginDestination count.
        
        Args:
            data_lists: DataLists containing OriginDestinationList
            
        Returns:
            "one-way" or "round-trip"
        """
        od_list = data_lists.get("OriginDestinationList", {}).get("OriginDestination", [])
        if not isinstance(od_list, list):
            od_list = [od_list] if od_list else []
        
        # One OD = one-way, Two ODs = round-trip
        return "round-trip" if len(od_list) >= 2 else "one-way"
    
    def _extract_time_limits(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract offer expiration and payment time limits.
        
        Args:
            offer: Priced offer object
            
        Returns:
            Time limit information
        """
        time_limits = offer.get("TimeLimits", {})
        
        return {
            "offer_expiration": time_limits.get("OfferExpiration", {}).get("DateTime", ""),
            "payment_time_limit": time_limits.get("Payment", {}).get("DateTime", "")
        }
    
    def _extract_currency(self, offer: Dict[str, Any]) -> str:
        """Extract currency code from offer."""
        offer_prices = offer.get("OfferPrice", [])
        if not isinstance(offer_prices, list):
            offer_prices = [offer_prices] if offer_prices else []
        
        if offer_prices:
            price_detail = offer_prices[0].get("RequestedDate", {}).get("PriceDetail", {})
            total = price_detail.get("TotalAmount", {}).get("SimpleCurrencyPrice", {})
            return total.get("Code", "USD")
        
        return "USD"
