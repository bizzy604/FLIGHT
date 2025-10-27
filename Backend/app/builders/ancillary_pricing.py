"""Ancillary pricing request builder.

Builds a FlightPrice request that includes selected seats and services
so ancillaries with PricedInd=false can be priced before booking.

This builder follows the structure from the repository's reference
`Shopping and booking with Seat and Ancillary where both of them requires pricing/9_FlightPriceRQ.json`.
"""
import logging
from typing import Any, Dict, List, Optional

from app.core.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)


class AncillaryPricingRequestBuilder:
    """Builds FlightPrice (ancillary pricing) requests.

    Usage:
        builder = AncillaryPricingRequestBuilder()
        rq = builder.build(...)
    """

    def __init__(self) -> None:
        logger.debug("AncillaryPricingRequestBuilder initialized")

    def _extract_flight_offer_item_id(self, priced_offer: Dict[str, Any]) -> Optional[str]:
        """Try to extract an offer item id for the flight from a priced offer.

        Looks in common places and falls back to a recursive search for the
        first OfferItemID.value encountered.
        
        Note: VDC FlightPrice responses may not contain explicit OfferItemIDs.
        In that case, we construct one from the OfferID which serves as the base reference.
        """
        # Common nested path used by some VDC responses
        try:
            offer_price = priced_offer.get("OfferPrice")
            if isinstance(offer_price, list) and offer_price:
                # Look for FareDetail -> OfferItemIDs -> OfferItemID
                first = offer_price[0]
                fare_detail = first.get("FareDetail") or {}
                offer_item_ids = fare_detail.get("OfferItemIDs", {}).get("OfferItemID")
                if offer_item_ids:
                    if isinstance(offer_item_ids, list):
                        return offer_item_ids[0].get("value")
                    elif isinstance(offer_item_ids, dict):
                        return offer_item_ids.get("value")
        except Exception:
            pass

        # Recursive fallback search
        def _search(node: Any):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "OfferItemID":
                        if isinstance(v, list) and v:
                            return v[0].get("value")
                        if isinstance(v, dict):
                            return v.get("value")
                    else:
                        res = _search(v)
                        if res:
                            return res
            elif isinstance(node, list):
                for item in node:
                    res = _search(item)
                    if res:
                        return res
            return None

        found = _search(priced_offer)
        if found:
            return found
        
        # Final fallback: use OfferID + suffix to create a default offer item reference
        # This is common when FlightPrice responses don't explicitly list OfferItemIDs
        offer_id = priced_offer.get("OfferID", {})
        if isinstance(offer_id, dict):
            offer_id_value = offer_id.get("value") or offer_id.get("ObjectKey")
            if offer_id_value:
                # Construct a default offer item ID: OfferID-1-1 (common VDC pattern)
                return f"{offer_id_value}-1-1"
        
        return None

    def _find_selected_seat_payload(self, seatavailability_response: Dict[str, Any], seat_key: str) -> Optional[Dict[str, Any]]:
        """Try to construct a SelectedSeat object from seatavailability response for a seat_key.

        The exact structure of SeatAvailability responses can vary between providers.
        We attempt to find a matching seat entry and copy Location/SeatAssociation data.
        If not found, return None and caller should fall back to using the seat_key only.
        """
        try:
            # Typical structure: data -> seat_maps / SeatMap -> rows -> seats
            data = seatavailability_response.get("data", {}) if isinstance(seatavailability_response, dict) else {}
            # try a couple of common paths
            candidates = []
            for key in ("seat_maps", "SeatMap", "SeatMaps", "SeatMapList"):
                part = data.get(key)
                if part:
                    candidates.append(part)

            # flatten lists/dicts
            def _iter_seats(node):
                if isinstance(node, dict):
                    for v in node.values():
                        yield from _iter_seats(v)
                elif isinstance(node, list):
                    for item in node:
                        yield from _iter_seats(item)
                else:
                    return

            # naive search for seat objects that have a seat_key or similar
            def _search(node):
                if isinstance(node, dict):
                    if node.get("seat_key") == seat_key or node.get("ObjectKey") == seat_key or node.get("SeatKey") == seat_key:
                        return node
                    for v in node.values():
                        res = _search(v)
                        if res:
                            return res
                elif isinstance(node, list):
                    for item in node:
                        res = _search(item)
                        if res:
                            return res
                return None

            for c in candidates:
                res = _search(c)
                if res:
                    # Build SelectedSeat payload with Location and SeatAssociation if present
                    location = res.get("Location") or res.get("location") or res.get("loc")
                    seat_assoc = res.get("SeatAssociation") or res.get("seatAssociation")
                    payload = {}
                    if location:
                        payload["Location"] = location
                    if seat_assoc:
                        payload["SeatAssociation"] = seat_assoc
                    if payload:
                        return payload
        except Exception:
            logger.debug("Failed to extract SelectedSeat payload for seat_key %s", seat_key)
        return None

    def build(
        self,
        flight_price_response: Dict[str, Any],
        servicelist_response: Optional[Dict[str, Any]] = None,
        seatavailability_response: Optional[Dict[str, Any]] = None,
        selected_services: List[str] = None,
        selected_seats: List[str] = None,
        selected_offer_index: int = 0
    ) -> Dict[str, Any]:
        """Construct the FlightPriceRQ payload including ancillary selections.

        Returns dict suitable to send to the VDC FlightPrice API.
        """
        selected_services = selected_services or []
        selected_seats = selected_seats or []

        priced_offers = flight_price_response.get("PricedFlightOffers", {}).get("PricedFlightOffer", [])
        if not isinstance(priced_offers, list):
            priced_offers = [priced_offers] if priced_offers else []

        if not priced_offers or selected_offer_index >= len(priced_offers):
            raise BusinessLogicError("Invalid selected_offer_index or no priced offers present")

        selected_offer = priced_offers[selected_offer_index]
        offer_id = selected_offer.get("OfferID", {})

        # find flight offer item id
        flight_item_id = self._extract_flight_offer_item_id(selected_offer)
        if not flight_item_id:
            raise BusinessLogicError("Could not extract flight offer item id from priced offer")

        offer_item_ids = []
        # always include original flight item
        offer_item_ids.append({"value": flight_item_id})

        # add seats: try to include SelectedSeat structure if available, otherwise send the value
        for seat_key in selected_seats:
            selected_seat_payload = self._find_selected_seat_payload(seatavailability_response or {}, seat_key)
            if selected_seat_payload:
                offer_item_ids.append({"value": seat_key, "SelectedSeat": selected_seat_payload, "Quantity": 1})
            else:
                offer_item_ids.append({"value": seat_key, "Quantity": 1})

        # add services
        for svc_key in selected_services:
            # services typically only need the value; advanced payloads may include traveler refs
            offer_item_ids.append({"value": svc_key, "Quantity": 1})

        # Build final request
        request = {
            "Query": {
                "Offers": {
                    "Offer": [
                        {
                            "OfferID": offer_id,
                            "OfferItemIDs": {"OfferItemID": offer_item_ids}
                        }
                    ]
                }
            },
            "DataLists": flight_price_response.get("DataLists", {}),
            "ShoppingResponseID": flight_price_response.get("ShoppingResponseID", {})
        }

        logger.debug("Built ancillary FlightPrice request with %d items", len(offer_item_ids))
        return request
