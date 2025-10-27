"""
OrderCreate Response Transformer

Transforms VDC OrderCreate API responses into clean, frontend-friendly format.
Extracts booking reference, order ID, prices, passenger assignments, and flight details.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class OrderCreateTransformer:
    """Transformer for VDC OrderCreate responses."""
    
    def transform(self, vdc_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform VDC OrderCreate response to clean format.
        
        Args:
            vdc_response: Raw VDC OrderCreateRS response
        
        Returns:
            Dict containing:
                - success: bool
                - booking_reference: str
                - order_id: str
                - total_price: Dict with amount, currency, breakdown
                - passengers: List of passenger details with assignments
                - flights: List of flight segment details
                - ancillaries: Dict with seats and services
                - raw_response: Dict (preserved for debugging)
        """
        try:
            logger.info("🔄 Transforming OrderCreate response")
            
            # Extract Order section (handle multiple response formats)
            order = self._extract_order(vdc_response)
            
            if not order:
                logger.warning("⚠️ No Order found in response")
                return {
                    "success": False,
                    "error": "No Order found in VDC response",
                    "raw_response": vdc_response
                }
            
            # Extract core booking details
            booking_reference = self._extract_booking_reference(order)
            order_id = self._extract_order_id(order)
            
            # Extract pricing information
            total_price = self._extract_total_price(order)
            
            # Extract passenger information (needs full response for Passengers section)
            passengers = self._extract_passengers(vdc_response, order)
            
            # Extract flight information (needs full response for DataLists)
            flights = self._extract_flights(vdc_response)
            
            # Extract ancillary information (seats, services)
            ancillaries = self._extract_ancillaries(order)
            
            # Build transformed response
            result = {
                "success": True,
                "booking_reference": booking_reference,
                "order_id": order_id,
                "total_price": total_price,
                "passengers": passengers,
                "flights": flights,
                "ancillaries": ancillaries,
                "raw_response": vdc_response
            }
            
            logger.info(f"✅ OrderCreate response transformed - Booking: {booking_reference}")
            
            return result
            
        except Exception as e:
            logger.error(f"🔴 Error transforming OrderCreate response: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Transformation error: {str(e)}",
                "raw_response": vdc_response
            }
    
    def _extract_order(self, vdc_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract Order section from VDC response.
        Handles multiple response formats.
        """
        order_data = None
        
        # Format 1: OrderCreateRS.Order
        if "OrderCreateRS" in vdc_response:
            order_data = vdc_response["OrderCreateRS"].get("Order")
        
        # Format 2: Order directly at root
        elif "Order" in vdc_response:
            order_data = vdc_response["Order"]
        
        # Format 3: Response.Order
        elif "Response" in vdc_response and "Order" in vdc_response["Response"]:
            order_data = vdc_response["Response"]["Order"]
        
        # Handle Order as a list (take first element)
        if isinstance(order_data, list) and len(order_data) > 0:
            return order_data[0]
        
        return order_data
    
    def _extract_booking_reference(self, order: Dict[str, Any]) -> str:
        """Extract booking reference from Order."""
        try:
            # Format 1: BookingReferences.BookingReference[0].ID
            if "BookingReferences" in order:
                booking_refs = order["BookingReferences"].get("BookingReference", [])
                if isinstance(booking_refs, list) and len(booking_refs) > 0:
                    first_ref = booking_refs[0]
                    if isinstance(first_ref, dict):
                        # Try ID field
                        if "ID" in first_ref:
                            return str(first_ref["ID"])
                        # Try value field
                        if "value" in first_ref:
                            return str(first_ref["value"])
                        # Try OtherID.value
                        if "OtherID" in first_ref:
                            other_id = first_ref["OtherID"]
                            if isinstance(other_id, dict):
                                return other_id.get("value", "UNKNOWN")
            
            # Format 2: BookingReference.ID.value
            if "BookingReference" in order:
                booking_ref = order["BookingReference"]
                if isinstance(booking_ref, dict):
                    id_obj = booking_ref.get("ID", {})
                    if isinstance(id_obj, dict):
                        return id_obj.get("value", "UNKNOWN")
                    return str(id_obj)
                return str(booking_ref)
            
            # Format 3: BookingReferenceID.value
            if "BookingReferenceID" in order:
                ref_id = order["BookingReferenceID"]
                if isinstance(ref_id, dict):
                    return ref_id.get("value", "UNKNOWN")
                return str(ref_id)
            
            return "UNKNOWN"
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting booking reference: {e}")
            return "UNKNOWN"
    
    def _extract_order_id(self, order: Dict[str, Any]) -> str:
        """Extract order ID from Order."""
        try:
            # Format 1: OrderID.value
            if "OrderID" in order:
                order_id = order["OrderID"]
                if isinstance(order_id, dict):
                    return order_id.get("value", "UNKNOWN")
                return str(order_id)
            
            return "UNKNOWN"
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting order ID: {e}")
            return "UNKNOWN"
    
    def _extract_total_price(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract total price information from Order.
        
        Returns:
            Dict with amount, currency, base_amount, taxes, fees
        """
        try:
            price_info = {
                "amount": 0.0,
                "currency": "USD",
                "base_amount": 0.0,
                "taxes": 0.0,
                "fees": 0.0
            }
            
            # Format 1: TotalOrderPrice.SimpleCurrencyPrice (real VDC response)
            if "TotalOrderPrice" in order:
                total_order_price = order["TotalOrderPrice"]
                if "SimpleCurrencyPrice" in total_order_price:
                    simple_price = total_order_price["SimpleCurrencyPrice"]
                    if isinstance(simple_price, dict):
                        price_info["amount"] = float(simple_price.get("value", 0))
                        price_info["currency"] = simple_price.get("Code", "USD")
                
                # Try to get base amount and taxes from OrderItems
                if "OrderItems" in order:
                    order_items = order["OrderItems"]
                    if "OrderItem" in order_items:
                        items = order_items["OrderItem"]
                        if not isinstance(items, list):
                            items = [items]
                        
                        total_base = 0.0
                        total_taxes = 0.0
                        
                        for item in items:
                            # Check FlightItem.Price
                            if "FlightItem" in item and "Price" in item["FlightItem"]:
                                price = item["FlightItem"]["Price"]
                                if "BaseAmount" in price:
                                    base = price["BaseAmount"]
                                    if isinstance(base, dict):
                                        total_base += float(base.get("value", 0))
                                
                                if "Taxes" in price and "Total" in price["Taxes"]:
                                    tax_total = price["Taxes"]["Total"]
                                    if isinstance(tax_total, dict):
                                        total_taxes += float(tax_total.get("value", 0))
                        
                        price_info["base_amount"] = total_base
                        price_info["taxes"] = total_taxes
            
            # Format 2: TotalPrice.Total (legacy format)
            elif "TotalPrice" in order:
                total_price = order["TotalPrice"]
                
                # Total amount
                if "Total" in total_price:
                    total = total_price["Total"]
                    if isinstance(total, dict):
                        price_info["amount"] = float(total.get("value", 0))
                        price_info["currency"] = total.get("Code", "USD")
                
                # Base amount
                if "BaseAmount" in total_price:
                    base = total_price["BaseAmount"]
                    if isinstance(base, dict):
                        price_info["base_amount"] = float(base.get("value", 0))
                
                # Taxes
                if "Taxes" in total_price:
                    taxes = total_price["Taxes"]
                    if isinstance(taxes, dict):
                        if "Total" in taxes:
                            tax_total = taxes["Total"]
                            if isinstance(tax_total, dict):
                                price_info["taxes"] = float(tax_total.get("value", 0))
            
            return price_info
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting price: {e}")
            return {
                "amount": 0.0,
                "currency": "USD",
                "base_amount": 0.0,
                "taxes": 0.0,
                "fees": 0.0
            }
    
    def _extract_passengers(self, vdc_response: Dict[str, Any], order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract passenger information from VDC response.
        
        Args:
            vdc_response: Full VDC response (for Response.Passengers)
            order: Order section (for OrderItems associations)
        
        Returns:
            List of passenger dicts with name, type, seat assignments, services
        """
        try:
            passengers = []
            
            # First, try to get Passengers from Response.Passengers
            passengers_section = None
            
            if "Response" in vdc_response and "Passengers" in vdc_response["Response"]:
                passengers_section = vdc_response["Response"]["Passengers"]
            elif "Passengers" in vdc_response:
                passengers_section = vdc_response["Passengers"]
            elif "Passengers" in order:
                passengers_section = order["Passengers"]
            
            if passengers_section and "Passenger" in passengers_section:
                pax_list = passengers_section["Passenger"]
                if not isinstance(pax_list, list):
                    pax_list = [pax_list]
                
                for pax in pax_list:
                    passengers.append({
                        "passenger_id": pax.get("ObjectKey", "UNKNOWN"),
                        "name": self._extract_passenger_name(pax),
                        "type": pax.get("PTC", {}).get("value", "ADT"),
                        "seat_assignments": [],
                        "services": []
                    })
            
            return passengers
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting passengers: {e}")
            return []
    
    def _extract_passenger_from_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract passenger info from OrderItem."""
        try:
            # Look for passenger reference
            passenger_refs = item.get("PassengerReferences", {})
            if not passenger_refs:
                return None
            
            passenger_id = passenger_refs.get("value", "UNKNOWN")
            
            return {
                "passenger_id": passenger_id,
                "name": "Unknown",  # Name comes from DataLists
                "type": "ADT",
                "seat_assignments": [],
                "services": []
            }
            
        except Exception:
            return None
    
    def _extract_passenger_name(self, passenger: Dict[str, Any]) -> str:
        """Extract passenger name from passenger object."""
        try:
            if "Name" in passenger:
                name_obj = passenger["Name"]
                
                # Extract title (MR, MRS, etc.)
                title = name_obj.get("Title", "")
                
                # Extract given name
                given = name_obj.get("Given", [])
                if isinstance(given, list) and given:
                    given_name = given[0].get("value", "") if isinstance(given[0], dict) else str(given[0])
                else:
                    given_name = given.get("value", "") if isinstance(given, dict) else str(given)
                
                # Extract surname
                surname = name_obj.get("Surname", {})
                surname_value = surname.get("value", "") if isinstance(surname, dict) else str(surname)
                
                # Build full name with title
                parts = []
                if title:
                    parts.append(str(title))
                if given_name:
                    parts.append(given_name)
                if surname_value:
                    parts.append(surname_value)
                
                return " ".join(parts).strip() if parts else "Unknown"
            
            return "Unknown"
            
        except Exception:
            return "Unknown"
    
    def _extract_flights(self, vdc_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract flight segment information from VDC response DataLists.
        
        Args:
            vdc_response: Full VDC response (for Response.DataLists)
        
        Returns:
            List of flight segment dicts with origin, destination, times, carrier
        """
        try:
            flights = []
            
            # Try to get DataLists from different locations
            data_lists = None
            
            if "Response" in vdc_response and "DataLists" in vdc_response["Response"]:
                data_lists = vdc_response["Response"]["DataLists"]
            elif "DataLists" in vdc_response:
                data_lists = vdc_response["DataLists"]
            
            if not data_lists:
                return []
            
            # FlightSegmentList
            if "FlightSegmentList" in data_lists:
                segment_list = data_lists["FlightSegmentList"]
                if "FlightSegment" in segment_list:
                    segments = segment_list["FlightSegment"]
                    if not isinstance(segments, list):
                        segments = [segments]
                    
                    for segment in segments:
                        # Extract departure info
                        departure = segment.get("Departure", {})
                        dep_airport = departure.get("AirportCode", {})
                        if isinstance(dep_airport, dict):
                            dep_code = dep_airport.get("value", "")
                        else:
                            dep_code = str(dep_airport)
                        
                        # Extract arrival info
                        arrival = segment.get("Arrival", {})
                        arr_airport = arrival.get("AirportCode", {})
                        if isinstance(arr_airport, dict):
                            arr_code = arr_airport.get("value", "")
                        else:
                            arr_code = str(arr_airport)
                        
                        # Extract carrier info
                        marketing_carrier = segment.get("MarketingCarrier", {})
                        carrier_id = marketing_carrier.get("AirlineID", {})
                        if isinstance(carrier_id, dict):
                            carrier = carrier_id.get("value", "")
                        else:
                            carrier = str(carrier_id)
                        
                        flight_num = marketing_carrier.get("FlightNumber", {})
                        if isinstance(flight_num, dict):
                            flight_number = flight_num.get("value", "")
                        else:
                            flight_number = str(flight_num)
                        
                        flights.append({
                            "segment_key": segment.get("SegmentKey", "UNKNOWN"),
                            "origin": dep_code,
                            "destination": arr_code,
                            "departure_time": departure.get("Time", ""),
                            "arrival_time": arrival.get("Time", ""),
                            "carrier": carrier,
                            "flight_number": flight_number
                        })
            
            return flights
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting flights: {e}")
            return []
    
    def _extract_ancillaries(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract ancillary information (seats, services) from Order.
        
        Returns:
            Dict with seats and services lists
        """
        try:
            ancillaries = {
                "seats": [],
                "services": []
            }
            
            # Extract from OrderItems
            if "OrderItems" in order:
                order_items = order["OrderItems"]
                if "OrderItem" in order_items:
                    items = order_items["OrderItem"]
                    if not isinstance(items, list):
                        items = [items]
                    
                    for item in items:
                        # Real VDC format: Direct SeatItem in OrderItem
                        if "SeatItem" in item:
                            seat_item = item["SeatItem"]
                            
                            # Extract location info
                            location = seat_item.get("Location", {})
                            row = location.get("Row", {}).get("Number", {}).get("value", "")
                            column = location.get("Column", "")
                            seat_number = f"{row}{column}" if row and column else "UNKNOWN"
                            
                            # Extract associations
                            seat_assoc = seat_item.get("SeatAssociation", [])
                            if not isinstance(seat_assoc, list):
                                seat_assoc = [seat_assoc]
                            
                            segment_refs = []
                            passenger_id = ""
                            for assoc in seat_assoc:
                                if "SegmentReferences" in assoc:
                                    seg_refs = assoc["SegmentReferences"]
                                    if isinstance(seg_refs, dict):
                                        segment_refs = seg_refs.get("value", [])
                                if "TravelerReference" in assoc:
                                    passenger_id = assoc["TravelerReference"]
                            
                            # Extract price
                            price = self._extract_item_price(item)
                            
                            ancillaries["seats"].append({
                                "seat_number": seat_number,
                                "passenger_id": passenger_id,
                                "segment_refs": segment_refs,
                                "service_id": location.get("Associations", {}).get("Services", {}).get("ServiceID", [{}])[0].get("ObjectKey", "") if "Associations" in location else "",
                                "price": price
                            })
                        
                        # Real VDC format: Services array in OrderItem
                        if "Services" in item:
                            services_list = item["Services"]
                            if not isinstance(services_list, list):
                                services_list = [services_list]
                            
                            for service in services_list:
                                service_id_obj = service.get("ServiceID", {})
                                if isinstance(service_id_obj, dict):
                                    service_id = service_id_obj.get("ObjectKey", "")
                                else:
                                    service_id = str(service_id_obj)
                                
                                passenger_refs = service.get("PassengerReferences", "")
                                segment_refs = service.get("SegmentRefs", "")
                                if not isinstance(segment_refs, list):
                                    segment_refs = [segment_refs] if segment_refs else []
                                
                                # Extract price
                                price = self._extract_item_price(item)
                                
                                ancillaries["services"].append({
                                    "service_id": service_id,
                                    "passenger_id": passenger_refs,
                                    "segment_refs": segment_refs,
                                    "service_definition_refs": service.get("ServiceDefinitionRefs", ""),
                                    "price": price
                                })
                        
                        # Legacy format: OfferItemType (keep for backward compatibility)
                        if "OfferItemType" in item:
                            offer_type = item["OfferItemType"]
                            
                            # Seat items
                            if "SeatItem" in offer_type:
                                seat_items = offer_type["SeatItem"]
                                if not isinstance(seat_items, list):
                                    seat_items = [seat_items]
                                
                                for seat_item in seat_items:
                                    ancillaries["seats"].append({
                                        "seat_number": self._extract_seat_number(seat_item),
                                        "segment": seat_item.get("SegmentRef", ""),
                                        "passenger_ref": self._extract_refs(item, "PassengerReferences"),
                                        "price": self._extract_item_price(item)
                                    })
                            
                            # Service items
                            if "ServiceItem" in offer_type:
                                service_items = offer_type["ServiceItem"]
                                if not isinstance(service_items, list):
                                    service_items = [service_items]
                                
                                for service_item in service_items:
                                    ancillaries["services"].append({
                                        "service_code": service_item.get("ServiceDefinitionRef", ""),
                                        "name": service_item.get("Name", ""),
                                        "passenger_ref": self._extract_refs(item, "PassengerReferences"),
                                        "price": self._extract_item_price(item)
                                    })
            
            return ancillaries
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting ancillaries: {e}")
            return {"seats": [], "services": []}
    
    def _extract_seat_number(self, seat_item: Dict[str, Any]) -> str:
        """Extract seat number from SeatItem."""
        try:
            if "SeatReference" in seat_item:
                seat_ref = seat_item["SeatReference"]
                row = seat_ref.get("Row", {}).get("Number", {}).get("value", "")
                column = seat_ref.get("Column", "")
                return f"{row}{column}"
            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"
    
    def _extract_refs(self, item: Dict[str, Any], key: str) -> str:
        """Extract reference value from item."""
        try:
            refs = item.get(key, {})
            if isinstance(refs, dict):
                return refs.get("value", "")
            return str(refs)
        except Exception:
            return ""
    
    def _extract_item_price(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract price from OrderItem."""
        try:
            # Format 1: Direct Price.Total
            if "Price" in item:
                price = item["Price"]
                if "Total" in price:
                    total = price["Total"]
                    if isinstance(total, dict):
                        return {
                            "amount": float(total.get("value", 0)),
                            "currency": total.get("Code", "USD")
                        }
            
            # Format 2: SeatItem.Price.Total (real VDC format)
            if "SeatItem" in item and "Price" in item["SeatItem"]:
                price = item["SeatItem"]["Price"]
                if "Total" in price:
                    total = price["Total"]
                    if isinstance(total, dict):
                        return {
                            "amount": float(total.get("value", 0)),
                            "currency": total.get("Code", "USD")
                        }
            
            return {"amount": 0.0, "currency": "USD"}
        except Exception:
            return {"amount": 0.0, "currency": "USD"}
