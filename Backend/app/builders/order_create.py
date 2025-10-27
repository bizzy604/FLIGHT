"""
OrderCreate Request Builder

Builds VDC OrderCreate requests following NDC specification.
Handles both pricedInd=true and pricedInd=false scenarios for ancillaries.

Reference: documentations/vdc-api-documentation.md
"""

from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def normalize_to_list(data: Union[List, Dict, Any]) -> List:
    """
    Utility function to ensure data is always a list - DRY principle.
    
    Args:
        data: Data that might be a list, dict, or single value
        
    Returns:
        List containing the data
    """
    if not isinstance(data, list):
        return [data] if data else []
    return data


class OrderCreateRequestBuilder:
    """
    Build VDC OrderCreate requests following NDC specification.
    
    Patterns:
    - DRY: Reusable utility functions
    - Defensive: Validate at each step
    - Flexible: Handle all pricing scenarios (pricedInd=true/false/mixed)
    
    Note: No multi-airline support needed - OrderCreate is for a specific airline's offer
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_request(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]] = None,
        servicelist_response: Optional[Dict[str, Any]] = None,
        selected_seats: Optional[List[str]] = None,
        selected_services: Optional[List[str]] = None,
        ancillary_pricing_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build complete OrderCreate request.
        
        Steps:
        1. Detect pricing scenario (pricedInd=true/false/mixed)
        2. Extract base flight data from FlightPrice response
        3. Build Passengers section
        4. Build OrderItems section (Flight + Seats + Services)
        5. Build DataLists section
        6. Build Payments section
        7. Validate structure
        
        Args:
            flight_price_response: FlightPrice response (required)
            passengers: Passenger details (required)
            payment: Payment information (required)
            seatavailability_response: SeatAvailability response (optional)
            servicelist_response: ServiceList response (optional)
            selected_seats: List of selected seat ObjectKeys (optional)
            selected_services: List of selected service ObjectKeys (optional)
            ancillary_pricing_response: FlightPrice response with ancillary pricing (optional)
        
        Returns:
            OrderCreate request payload
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            self.logger.info("🔧 Building OrderCreate request")
            
            # Step 1: Detect pricing scenario
            scenario = self._detect_pricing_scenario(
                seatavailability_response=seatavailability_response,
                servicelist_response=servicelist_response,
                selected_seats=selected_seats,
                selected_services=selected_services
            )
            self.logger.info(f"📊 Pricing scenario: {scenario['scenario']}")
            
            # Step 2: Extract base flight data
            selected_offer = self._extract_selected_offer(flight_price_response)
            offer_id = selected_offer.get('OfferID', {})
            shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
            
            # Step 3: Build Passengers section
            passengers_section = self._build_passengers(passengers, flight_price_response)
            
            # Step 4: Build OrderItems section
            order_items = self._build_order_items(
                flight_price_response=flight_price_response,
                selected_offer=selected_offer,
                scenario=scenario,
                seatavailability_response=seatavailability_response,
                servicelist_response=servicelist_response,
                selected_seats=selected_seats,
                selected_services=selected_services,
                ancillary_pricing_response=ancillary_pricing_response,
                passengers=passengers
            )
            
            # Step 5: Build DataLists section
            data_lists = self._build_data_lists(
                flight_price_response=flight_price_response,
                seatavailability_response=seatavailability_response,
                servicelist_response=servicelist_response,
                selected_seats=selected_seats,
                selected_services=selected_services,
                scenario=scenario
            )
            
            # Step 6: Build Payments section
            payments = self._build_payments(
                payment=payment,
                flight_price_response=flight_price_response,
                ancillary_pricing_response=ancillary_pricing_response
            )
            
            # Build complete request (VDC spec order: Passengers → OrderItems → DataLists → Payments)
            request = {
                "Query": {
                    "Passengers": {"Passenger": passengers_section},
                    "OrderItems": order_items,
                    "DataLists": data_lists,
                    "Payments": {"Payment": payments}
                }
            }
            
            # Step 7: Validate
            self._validate_request(request)
            
            self.logger.info("✅ OrderCreate request built successfully")
            return request
            
        except Exception as e:
            self.logger.error(f"❌ Error building OrderCreate request: {e}", exc_info=True)
            raise
    
    def _detect_pricing_scenario(
        self,
        seatavailability_response: Optional[Dict[str, Any]] = None,
        servicelist_response: Optional[Dict[str, Any]] = None,
        selected_seats: Optional[List[str]] = None,
        selected_services: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect whether we're dealing with pricedInd=true, false, or mixed scenario.
        
        Returns:
            Dict containing scenario information:
            {
                "scenario": "priced_ind_true" | "priced_ind_false" | "mixed",
                "services_priced": List[str],
                "services_unpriced": List[str],
                "seats_priced": List[str],
                "seats_unpriced": List[str]
            }
        """
        result = {
            "scenario": "priced_ind_true",  # Default assumption
            "services_priced": [],
            "services_unpriced": [],
            "seats_priced": [],
            "seats_unpriced": []
        }
        
        try:
            # Check services
            if servicelist_response and selected_services:
                services = normalize_to_list(
                    servicelist_response.get('Services', {}).get('Service', [])
                )
                
                for service in services:
                    service_key = service.get('ObjectKey', '')
                    if service_key in selected_services:
                        priced_ind = service.get('PricedInd', True)
                        if priced_ind:
                            result["services_priced"].append(service_key)
                        else:
                            result["services_unpriced"].append(service_key)
            
            # Check seats
            if seatavailability_response and selected_seats:
                services = normalize_to_list(
                    seatavailability_response.get('Services', {}).get('Service', [])
                )
                
                for service in services:
                    service_key = service.get('ObjectKey', '')
                    if service_key in selected_seats:
                        priced_ind = service.get('PricedInd', True)
                        if priced_ind:
                            result["seats_priced"].append(service_key)
                        else:
                            result["seats_unpriced"].append(service_key)
            
            # Determine scenario
            has_unpriced_services = len(result["services_unpriced"]) > 0
            has_unpriced_seats = len(result["seats_unpriced"]) > 0
            has_priced_services = len(result["services_priced"]) > 0
            has_priced_seats = len(result["seats_priced"]) > 0
            
            if has_unpriced_services or has_unpriced_seats:
                if (has_priced_services or has_priced_seats) and (has_unpriced_services or has_unpriced_seats):
                    result["scenario"] = "mixed"
                else:
                    result["scenario"] = "priced_ind_false"
            else:
                result["scenario"] = "priced_ind_true"
            
            self.logger.info(f"Pricing scenario detection: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error detecting pricing scenario: {e}")
            return result
    
    def _extract_selected_offer(self, flight_price_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the selected offer from FlightPrice response (first offer by default)."""
        priced_offers = normalize_to_list(
            flight_price_response.get('PricedFlightOffers', {})
            .get('PricedFlightOffer', [])
        )
        
        if not priced_offers:
            raise ValueError("No PricedFlightOffer found in FlightPrice response")
        
        return priced_offers[0]
    
    def _build_passengers(
        self,
        passengers: List[Dict[str, Any]],
        flight_price_response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build Passengers section with ObjectKey mapping.
        
        Maps passenger index → AnonymousTraveler ObjectKey from FlightPrice response.
        
        Args:
            passengers: Passenger details from frontend
            flight_price_response: FlightPrice response containing AnonymousTravelerList
            
        Returns:
            List of passenger objects for OrderCreate
        """
        try:
            self.logger.info(f"Building Passengers section for {len(passengers)} passengers")
            
            # Extract AnonymousTraveler ObjectKeys from FlightPrice
            data_lists = flight_price_response.get('DataLists', {})
            travelers = normalize_to_list(
                data_lists.get('AnonymousTravelerList', {})
                .get('AnonymousTraveler', [])
            )
            
            available_object_keys = [
                traveler.get('ObjectKey') 
                for traveler in travelers 
                if traveler.get('ObjectKey')
            ]
            
            self.logger.info(f"Available ObjectKeys: {available_object_keys}")
            
            passengers_section = []
            
            for idx, passenger in enumerate(passengers):
                # Map passenger to ObjectKey
                if idx < len(available_object_keys):
                    object_key = available_object_keys[idx]
                else:
                    raise ValueError(f"No ObjectKey available for passenger {idx}")
                
                # Build passenger object
                passenger_obj = {
                    "ObjectKey": object_key,
                    "PTC": {
                        "value": passenger.get('passenger_type', 'ADT')
                    },
                    "Name": {
                        "Surname": {
                            "value": passenger.get('surname', passenger.get('last_name', ''))
                        },
                        "Given": [
                            {
                                "value": passenger.get('given_name', passenger.get('first_name', ''))
                            }
                        ],
                        "Title": passenger.get('title', 'Mr')
                    },
                    "Contacts": {
                        "Contact": [
                            {
                                "EmailContact": {
                                    "Address": {
                                        "value": passenger.get('email', '')
                                    }
                                },
                                "PhoneContact": {
                                    "Application": "Home",
                                    "Number": [
                                        {
                                            "value": passenger.get('phone', ''),
                                            "CountryCode": passenger.get('country_code', '1')
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                    "Gender": {
                        "value": passenger.get('gender', 'Male')
                    }
                }
                
                # Add date of birth if provided
                if passenger.get('dob') or passenger.get('date_of_birth') or passenger.get('birthdate'):
                    passenger_obj["Age"] = {
                        "BirthDate": {
                            "value": passenger.get('dob', passenger.get('date_of_birth', passenger.get('birthdate', '')))
                        }
                    }
                
                # Mark first passenger as payment contact
                if idx == 0:
                    passenger_obj["AdditionalRoles"] = {
                        "PaymentContactInd": True
                    }
                
                passengers_section.append(passenger_obj)
            
            self.logger.info(f"✅ Built {len(passengers_section)} passenger objects")
            return passengers_section
            
        except Exception as e:
            self.logger.error(f"Error building passengers section: {e}", exc_info=True)
            raise
    
    def _build_order_items(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer: Dict[str, Any],
        scenario: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]],
        servicelist_response: Optional[Dict[str, Any]],
        selected_seats: Optional[List[str]],
        selected_services: Optional[List[str]],
        ancillary_pricing_response: Optional[Dict[str, Any]],
        passengers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build OrderItems section (Flight + Seats + Services).
        
        Returns:
            OrderItems structure with ShoppingResponse and OfferItem list
        """
        try:
            self.logger.info("Building OrderItems section")
            
            # Build ShoppingResponse
            shopping_response = self._build_shopping_response(
                flight_price_response=flight_price_response,
                selected_offer=selected_offer
            )
            
            # Build OfferItem list
            offer_items = []
            
            # 1. Add flight offer item (always present)
            flight_item = self._build_flight_offer_item(
                selected_offer=selected_offer,
                flight_price_response=flight_price_response,
                passengers=passengers
            )
            offer_items.append(flight_item)
            
            # 2. Add seat offer items (if any)
            if seatavailability_response and selected_seats:
                seat_items = self._build_seat_offer_items(
                    seatavailability_response=seatavailability_response,
                    selected_seats=selected_seats,
                    scenario=scenario,
                    ancillary_pricing_response=ancillary_pricing_response,
                    passengers=passengers,
                    flight_price_response=flight_price_response
                )
                offer_items.extend(seat_items)
            
            # 3. Add service offer items (if any)
            if servicelist_response and selected_services:
                service_items = self._build_service_offer_items(
                    servicelist_response=servicelist_response,
                    selected_services=selected_services,
                    scenario=scenario,
                    ancillary_pricing_response=ancillary_pricing_response,
                    passengers=passengers,
                    flight_price_response=flight_price_response
                )
                offer_items.extend(service_items)
            
            order_items = {
                "ShoppingResponse": shopping_response,
                "OfferItem": offer_items
            }
            
            self.logger.info(f"✅ Built OrderItems with {len(offer_items)} items")
            return order_items
            
        except Exception as e:
            self.logger.error(f"Error building order items: {e}", exc_info=True)
            raise
    
    def _build_shopping_response(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build ShoppingResponse structure from FlightPrice."""
        offer_id = selected_offer.get('OfferID', {})
        shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
        
        # Extract OfferItemIDs from OfferPrice
        offer_prices = normalize_to_list(selected_offer.get('OfferPrice', []))
        offer_item_ids = []
        
        for offer_price in offer_prices:
            offer_item_id = offer_price.get('OfferItemID', '')
            if offer_item_id:
                offer_item_ids.append({
                    "OfferItemID": {
                        "value": offer_item_id,
                        "Owner": offer_id.get('Owner', ''),
                        "Channel": offer_id.get('Channel', 'NDC')
                    }
                })
        
        shopping_response = {
            "Owner": offer_id.get('Owner', ''),
            "ResponseID": {
                "value": shopping_response_id.get('ResponseID', {}).get('value', '')
            },
            "Offers": {
                "Offer": [{
                    "OfferID": {
                        "ObjectKey": offer_id.get('value', ''),
                        "value": offer_id.get('value', ''),
                        "Owner": offer_id.get('Owner', ''),
                        "Channel": offer_id.get('Channel', 'NDC')
                    },
                    "OfferItems": {
                        "OfferItem": offer_item_ids
                    }
                }]
            }
        }
        
        return shopping_response
    
    def _build_flight_offer_item(
        self,
        selected_offer: Dict[str, Any],
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build flight DetailedFlightItem."""
        offer_id = selected_offer.get('OfferID', {})
        offer_prices = normalize_to_list(selected_offer.get('OfferPrice', []))
        
        if not offer_prices:
            raise ValueError("No OfferPrice found in selected offer")
        
        first_offer_price = offer_prices[0]
        
        # Extract passenger ObjectKeys
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(
            data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        )
        passenger_refs = [traveler.get('ObjectKey') for traveler in travelers if traveler.get('ObjectKey')]
        
        flight_item = {
            "OfferItemID": {
                "value": first_offer_price.get('OfferItemID', ''),
                "Owner": offer_id.get('Owner', ''),
                "Channel": offer_id.get('Channel', 'NDC')
            },
            "OfferItemType": {
                "DetailedFlightItem": [{
                    "Price": first_offer_price.get('RequestedDate', {}).get('PriceDetail', {}),
                    "FareDetail": first_offer_price.get('FareDetail', {}),
                    "OriginDestination": self._build_origin_destination(flight_price_response),
                    "refs": passenger_refs
                }]
            }
        }
        
        return flight_item
    
    def _build_seat_offer_items(
        self,
        seatavailability_response: Dict[str, Any],
        selected_seats: List[str],
        scenario: Dict[str, Any],
        ancillary_pricing_response: Optional[Dict[str, Any]],
        passengers: List[Dict[str, Any]],
        flight_price_response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build seat offer items - handles BOTH pricing scenarios.
        
        Logic:
        - If seat in scenario['seats_priced'] → Extract price from SeatAvailability
        - If seat in scenario['seats_unpriced'] → Extract price from ancillary_pricing_response
        """
        seat_items = []
        services = normalize_to_list(
            seatavailability_response.get('Services', {}).get('Service', [])
        )
        
        # Get owner from flight price
        selected_offer = self._extract_selected_offer(flight_price_response)
        offer_id = selected_offer.get('OfferID', {})
        owner = offer_id.get('Owner', '')
        
        # Get passenger refs
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(
            data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        )
        passenger_refs = [traveler.get('ObjectKey') for traveler in travelers if traveler.get('ObjectKey')]
        
        for seat_key in selected_seats:
            # Find seat service
            seat_service = next(
                (s for s in services if s.get('ObjectKey') == seat_key),
                None
            )
            
            if not seat_service:
                self.logger.warning(f"Seat service {seat_key} not found in SeatAvailability response")
                continue
            
            # Determine price source
            if seat_key in scenario['seats_priced']:
                # pricedInd=true: Use seat service price
                price = self._extract_price_from_service(seat_service)
                self.logger.info(f"Using priced seat: {seat_key}")
            else:
                # pricedInd=false: Extract from pricing response
                if not ancillary_pricing_response:
                    raise ValueError(
                        f"Seat {seat_key} requires pricing but no ancillary_pricing_response provided"
                    )
                
                price = self._extract_price_from_pricing_response(
                    ancillary_pricing_response,
                    seat_key
                )
                self.logger.info(f"Using unpriced seat (from pricing response): {seat_key}")
            
            # Build seat offer item (VDC uses Location for seat position)
            seat_location = self._extract_seat_definition(seat_service)
            seat_item = {
                "OfferItemID": {
                    "value": seat_key,
                    "Owner": owner,
                    "Channel": "NDC"
                },
                "OfferItemType": {
                    "SeatItem": [{
                        "Price": price,
                        "Location": seat_location,  # VDC uses Location, not SeatDefinition
                        "refs": passenger_refs[:1]  # One seat per passenger typically
                    }]
                }
            }
            
            seat_items.append(seat_item)
        
        self.logger.info(f"✅ Built {len(seat_items)} seat offer items")
        return seat_items
    
    def _build_service_offer_items(
        self,
        servicelist_response: Dict[str, Any],
        selected_services: List[str],
        scenario: Dict[str, Any],
        ancillary_pricing_response: Optional[Dict[str, Any]],
        passengers: List[Dict[str, Any]],
        flight_price_response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build service offer items - handles BOTH pricing scenarios.
        
        Logic:
        - If service in scenario['services_priced'] → Extract price from ServiceList
        - If service in scenario['services_unpriced'] → Extract price from ancillary_pricing_response
        """
        service_items = []
        services = normalize_to_list(
            servicelist_response.get('Services', {}).get('Service', [])
        )
        
        # Get owner from flight price
        selected_offer = self._extract_selected_offer(flight_price_response)
        offer_id = selected_offer.get('OfferID', {})
        owner = offer_id.get('Owner', '')
        
        # Get passenger refs
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(
            data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        )
        passenger_refs = [traveler.get('ObjectKey') for traveler in travelers if traveler.get('ObjectKey')]
        
        for service_key in selected_services:
            # Find service
            service = next(
                (s for s in services if s.get('ObjectKey') == service_key),
                None
            )
            
            if not service:
                self.logger.warning(f"Service {service_key} not found in ServiceList response")
                continue
            
            # Determine price source
            if service_key in scenario['services_priced']:
                # pricedInd=true: Use service price
                price = self._extract_price_from_service(service)
                self.logger.info(f"Using priced service: {service_key}")
            else:
                # pricedInd=false: Extract from pricing response
                if not ancillary_pricing_response:
                    raise ValueError(
                        f"Service {service_key} requires pricing but no ancillary_pricing_response provided"
                    )
                
                price = self._extract_price_from_pricing_response(
                    ancillary_pricing_response,
                    service_key
                )
                self.logger.info(f"Using unpriced service (from pricing response): {service_key}")
            
            # Build service offer item (VDC uses OtherItem for services, not ServiceItem)
            service_item = {
                "OfferItemID": {
                    "value": service_key,
                    "Owner": owner,
                    "Channel": "NDC"
                },
                "OfferItemType": {
                    "OtherItem": [{
                        "refs": passenger_refs,
                        "Price": {
                            "SimpleCurrencyPrice": price.get("Total", {})  # Extract value/code from Total
                        }
                    }]
                }
            }
            
            service_items.append(service_item)
        
        self.logger.info(f"✅ Built {len(service_items)} service offer items")
        return service_items
    
    def _extract_price_from_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Extract price from service (pricedInd=true case).
        
        Uses Total amount which includes all taxes, fees, and discounts already calculated.
        """
        price = service.get('Price', {})
        total = price.get('Total', {})
        
        return {
            "Total": {
                "value": total.get('value', 0),
                "Code": total.get('Code', 'USD')
            }
        }
    
    def _extract_price_from_pricing_response(
        self,
        pricing_response: Dict[str, Any],
        item_key: str
    ) -> Dict[str, Any]:
        """Extract price from ancillary pricing FlightPrice response (pricedInd=false case).
        
        Uses TotalAmount which includes all taxes, fees, and discounts already calculated.
        Per VDC mapping:
        FlightPriceRS/.../PriceDetail/TotalAmount/SimpleCurrencyPrice/value 
        → OrderCreateRQ/.../Price/Total/value (for SeatItem)
        → OrderCreateRQ/.../Price/SimpleCurrencyPrice/value (for OtherItem)
        """
        priced_offers = normalize_to_list(
            pricing_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        )
        
        if not priced_offers:
            raise ValueError("No PricedFlightOffer found in ancillary pricing response")
        
        offer_prices = normalize_to_list(priced_offers[0].get('OfferPrice', []))
        
        # Find the OfferPrice matching this item
        for offer_price in offer_prices:
            if offer_price.get('OfferItemID') == item_key:
                price_detail = offer_price.get('RequestedDate', {}).get('PriceDetail', {})
                total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                
                if total_amount:
                    return {
                        "Total": {
                            "value": total_amount.get('value', 0),
                            "Code": total_amount.get('Code', 'USD')
                        }
                    }
        
        # If not found, return zero price (fallback)
        self.logger.warning(f"Price not found for {item_key} in pricing response, using zero")
        return {
            "Total": {"value": 0, "Code": "USD"}
        }
    
    def _extract_seat_definition(self, seat_service: Dict[str, Any]) -> Dict[str, Any]:
        """Extract seat definition from SeatAvailability service."""
        definition = seat_service.get('Definition', {})
        seat = definition.get('Seat', {})
        
        return {
            "Row": seat.get('Row', {}),
            "Column": seat.get('Column', ''),
            "Characteristics": seat.get('Characteristics', {})
        }
    
    def _build_origin_destination(self, flight_price_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build OriginDestination structure from FlightPrice response.
        
        Per VDC mapping: FlightPriceRS DataLists/FlightSegmentList → OrderCreateRQ OriginDestination/Flight
        We need to include FULL segment details (Departure, Arrival, MarketingCarrier, etc.), not just references.
        
        Structure:
        - OriginDestination.FlightReferences → FlightList.Flight.FlightKey
        - FlightList.Flight.SegmentReferences → FlightSegmentList.FlightSegment.SegmentKey
        """
        data_lists = flight_price_response.get('DataLists', {})
        
        # Get flight segments with full details
        segment_list = normalize_to_list(
            data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
        )
        
        # Get flight list (contains segment references)
        flight_list = normalize_to_list(
            data_lists.get('FlightList', {}).get('Flight', [])
        )
        
        # Get origin destination list to group segments
        origin_dest_list = normalize_to_list(
            data_lists.get('OriginDestinationList', {}).get('OriginDestination', [])
        )
        
        result = []
        for od in origin_dest_list:
            # Get the flight references for this OD (points to FlightList)
            flight_refs_obj = od.get('FlightReferences', {})
            flight_refs = flight_refs_obj.get('value', [])
            if not isinstance(flight_refs, list):
                flight_refs = [flight_refs] if flight_refs else []
            
            # Build flights with FULL segment details
            flights = []
            
            for flight_ref in flight_refs:
                # Find the flight in FlightList
                flight_obj = next(
                    (f for f in flight_list if f.get('FlightKey') == flight_ref),
                    None
                )
                
                if flight_obj:
                    # Get segment references from this flight
                    segment_refs_obj = flight_obj.get('SegmentReferences', {})
                    segment_refs = segment_refs_obj.get('value', [])
                    if not isinstance(segment_refs, list):
                        segment_refs = [segment_refs] if segment_refs else []
                    
                    # Build each segment with full details
                    for segment_ref in segment_refs:
                        segment = next(
                            (s for s in segment_list if s.get('SegmentKey') == segment_ref),
                            None
                        )
                        
                        if segment:
                            # Build flight with complete segment data per VDC spec
                            flight = {
                                "Departure": segment.get('Departure', {}),
                                "Arrival": segment.get('Arrival', {}),
                                "MarketingCarrier": segment.get('MarketingCarrier', {}),
                                "Equipment": segment.get('Equipment', {}),
                                "Details": segment.get('FlightDetail', {}),  # FlightDetail in source, Details in destination
                                "ClassOfService": segment.get('ClassOfService', {}),
                                "SegmentKey": segment.get('SegmentKey', '')
                            }
                            flights.append(flight)
            
            # Add OriginDestinationKey if present
            od_result = {"Flight": flights}
            if 'OriginDestinationKey' in od:
                od_result['OriginDestinationKey'] = od['OriginDestinationKey']
            
            result.append(od_result)
        
        return result if result else [{"Flight": []}]
    
    def _build_data_lists(
        self,
        flight_price_response: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]],
        servicelist_response: Optional[Dict[str, Any]],
        selected_seats: Optional[List[str]],
        selected_services: Optional[List[str]],
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build DataLists section.
        
        Per VDC spec, OrderCreate DataLists should ONLY contain:
        - FareList (from FlightPriceRS)
        - ServiceList (if seats/services are selected)
        
        DO NOT include AnonymousTravelerList, FlightSegmentList, etc.
        """
        # Start with ONLY FareList from FlightPrice (not all DataLists!)
        source_data_lists = flight_price_response.get('DataLists', {})
        data_lists = {}
        
        # Copy ONLY FareList
        if 'FareList' in source_data_lists:
            data_lists['FareList'] = source_data_lists['FareList']
        
        # Build ServiceList with selected items
        service_list = []
        
        # Add selected services
        if servicelist_response and selected_services:
            services = normalize_to_list(
                servicelist_response.get('Services', {}).get('Service', [])
            )
            
            for service_key in selected_services:
                service = next(
                    (s for s in services if s.get('ObjectKey') == service_key),
                    None
                )
                if service:
                    service_list.append(service)
        
        # Add selected seats
        if seatavailability_response and selected_seats:
            services = normalize_to_list(
                seatavailability_response.get('Services', {}).get('Service', [])
            )
            
            for seat_key in selected_seats:
                service = next(
                    (s for s in services if s.get('ObjectKey') == seat_key),
                    None
                )
                if service:
                    service_list.append(service)
        
        # Add ServiceList to DataLists
        if service_list:
            data_lists['ServiceList'] = {
                "Service": service_list
            }
        
        return data_lists
    
    def _build_payments(
        self,
        payment: Dict[str, Any],
        flight_price_response: Dict[str, Any],
        ancillary_pricing_response: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build Payments section.
        
        Calculates total amount from flight price + ancillaries if applicable.
        """
        # Get total price from appropriate source
        pricing_source = ancillary_pricing_response if ancillary_pricing_response else flight_price_response
        
        priced_offers = normalize_to_list(
            pricing_source.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        )
        
        if priced_offers:
            offer_prices = normalize_to_list(priced_offers[0].get('OfferPrice', []))
            
            # Calculate total using TotalAmount (includes taxes, fees, discounts)
            total_amount = 0
            currency_code = "USD"
            
            for offer_price in offer_prices:
                price_detail = offer_price.get('RequestedDate', {}).get('PriceDetail', {})
                total_price = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                
                if total_price:
                    total_amount += total_price.get('value', 0)
                    currency_code = total_price.get('Code', 'USD')
        else:
            total_amount = 0
            currency_code = "USD"
        
        # Build payment structure based on payment method
        payment_method = payment.get('method', 'CASH').upper()
        
        if payment_method == 'CASH':
            # CASH payment - with CashInd flag
            payment_structure = {
                "Method": {
                    "Cash": {
                        "CashInd": "true"
                    }
                },
                "Amount": {
                    "Code": currency_code,
                    "value": total_amount
                }
            }
        else:
            # Card payment (default)
            payment_structure = {
                "Method": {
                    "PaymentCard": {
                        "CardNumber": payment.get('card_number', ''),
                        "CardType": {
                            "value": payment.get('card_type', 'Credit')
                        },
                        "CardHolderName": payment.get('card_holder_name', ''),
                        "ExpiryDate": payment.get('expiry_date', ''),
                        "SeriesCode": payment.get('cvv', '')
                    }
                },
                "Amount": {
                    "Code": currency_code,
                    "value": total_amount
                }
            }
        
        payments = [payment_structure]
        
        return payments
    
    def _validate_request(self, request: Dict[str, Any]) -> None:
        """Validate OrderCreate request structure."""
        # Check required top-level sections
        query = request.get('Query', {})
        
        if not query.get('Passengers'):
            raise ValueError("Passengers section is required")
        
        if not query.get('OrderItems'):
            raise ValueError("OrderItems section is required")
        
        if not query.get('DataLists'):
            raise ValueError("DataLists section is required")
        
        if not query.get('Payments'):
            raise ValueError("Payments section is required")
        
        # Check OrderItems structure
        order_items = query.get('OrderItems', {})
        if not order_items.get('ShoppingResponse'):
            raise ValueError("ShoppingResponse is required in OrderItems")
        
        if not order_items.get('OfferItem'):
            raise ValueError("At least one OfferItem is required")
        
        self.logger.info("✅ OrderCreate request validation passed")
