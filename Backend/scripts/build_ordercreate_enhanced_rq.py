# --- START OF FILE build_ordercreate_enhanced_rq.py ---

"""
⚠️ DEPRECATION NOTICE ⚠️

This file is DEPRECATED and should NOT be used for new implementations.

Reason: This builder uses fallback logic that doesn't align with NDC specification.
According to reference examples (9_FlightPriceRQ, 10_FlightPriceRS, 11_OrderCreateRQ),
ancillary items must be priced separately via sequential FlightPrice calls, and
OrderCreate must use offer items from the ancillary pricing response.

Use instead:
- build_ordercreate_rq.py - Standard OrderCreate builder with proper ancillary pricing support
- build_flightprice_ancillary_rq.py - Separate pricing for services and seats

This file will be removed in a future version.
Last Updated: October 17, 2025
"""

import json
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Log deprecation warning on import
logger.warning("⚠️ DEPRECATION WARNING: build_ordercreate_enhanced_rq.py is deprecated. Use build_ordercreate_rq.py instead.")

def normalize_to_list(data: Union[List, Dict, Any]) -> List:
    """Utility function to ensure data is always a list - DRY principle"""
    if not isinstance(data, list):
        return [data] if data else []
    return data

def _is_multi_airline_flight_price_response(flight_price_response: Dict[str, Any]) -> bool:
    """Check if the flight price response is from a multi-airline context."""
    try:
        data_lists = flight_price_response.get('DataLists', {})
        travelers = normalize_to_list(data_lists.get('AnonymousTravelerList', {}).get('AnonymousTraveler', []))

        for traveler in travelers:
            object_key = traveler.get('ObjectKey', '')
            if re.match(r'^[A-Z0-9]{2,3}-', object_key):
                return True

        shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
        if isinstance(shopping_response_id, dict):
            response_id_value = shopping_response_id.get('ResponseID', {}).get('value', '')
            if '-' in response_id_value and len(response_id_value.split('-')[-1]) <= 3:
                return True

        return False

    except Exception as e:
        logger.error(f"Error detecting multi-airline flight price response: {e}")
        return False

def _extract_airline_from_flight_price_response(flight_price_response: Dict[str, Any]) -> Optional[str]:
    """Extract airline code from flight price response."""
    try:
        # Method 1: Extract from ShoppingResponseID
        shopping_response_id = flight_price_response.get('ShoppingResponseID', {})
        if isinstance(shopping_response_id, dict):
            owner = shopping_response_id.get('Owner')
            if owner:
                return owner

            response_id_value = shopping_response_id.get('ResponseID', {}).get('value', '')
            if '-' in response_id_value:
                airline_code = response_id_value.split('-')[-1]
                if len(airline_code) <= 3:
                    return airline_code

        # Method 2: Extract from PricedFlightOffers
        priced_offers = normalize_to_list(flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
        if priced_offers:
            first_offer = priced_offers[0]
            offer_id = first_offer.get('OfferID', {})
            owner = offer_id.get('Owner')
            if owner:
                return owner

        return None

    except Exception as e:
        logger.error(f"Error extracting airline from flight price response: {e}")
        return None

def clean_airline_prefix_from_key(key: str, airline_code: str) -> str:
    """Remove airline prefix from a key."""
    if not key or not airline_code:
        return key
    
    prefix = f"{airline_code}-"
    if key.startswith(prefix):
        return key[len(prefix):]
    
    return key

def detect_priced_ind_scenario(
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Detect whether we're dealing with PricedInd=true or PricedInd=false scenario.
    
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
            services = normalize_to_list(servicelist_response.get('Services', {}).get('Service', []))
            
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
            services = normalize_to_list(seatavailability_response.get('Services', {}).get('Service', []))
            
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
        
        logger.info(f"PricedInd scenario detection: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error detecting PricedInd scenario: {e}")
        return result

def build_ordercreate_enhanced_request(
    flight_price_response: Dict[str, Any],
    passengers_data: List[Dict[str, Any]],
    payment_input_info: Dict[str, Any],
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None,
    ancillary_pricing_response: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build enhanced OrderCreate request that handles both PricedInd=true and PricedInd=false scenarios.
    
    Args:
        flight_price_response: Original FlightPrice response
        passengers_data: Passenger information
        payment_input_info: Payment details
        servicelist_response: ServiceList response (optional)
        seatavailability_response: SeatAvailability response (optional)
        selected_services: List of selected service ObjectKeys (optional)
        selected_seats: List of selected seat ObjectKeys (optional)
        ancillary_pricing_response: Additional FlightPrice response for unpriced items (optional)
    
    Returns:
        Dict containing the OrderCreate request
    """
    try:
        logger.info("Building enhanced OrderCreate request")
        
        # If ancillary_pricing_response is provided, it means we're in PricedInd=false scenario
        # Override scenario detection in this case
        if ancillary_pricing_response:
            logger.info("Ancillary pricing response provided - forcing PricedInd=false scenario")
            scenario_info = {
                "scenario": "priced_ind_false",
                "services_priced": [],
                "services_unpriced": selected_services or [],
                "seats_priced": [],
                "seats_unpriced": selected_seats or []
            }
        else:
            # Detect PricedInd scenario from original responses
            scenario_info = detect_priced_ind_scenario(
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services,
                selected_seats=selected_seats
            )
        
        # Determine which response to use for pricing data
        pricing_response = ancillary_pricing_response if ancillary_pricing_response else flight_price_response
        
        # Detect multi-airline context
        is_multi_airline = _is_multi_airline_flight_price_response(flight_price_response)
        airline_code = _extract_airline_from_flight_price_response(flight_price_response)
        
        logger.info(f"Scenario: {scenario_info['scenario']}, Multi-airline: {is_multi_airline}, Airline: {airline_code}")
        
        # Build base request structure
        request = {
            "Query": {
                "Passengers": {
                    "Passenger": []
                },
                "OrderItems": {
                    "ShoppingResponse": {},
                    "OfferItem": []
                },
                "DataLists": {
                    "ServiceList": {
                        "Service": []
                    }
                }
            }
        }
        
        # Build passenger information
        for i, pax in enumerate(passengers_data):
            passenger_obj = {
                "ObjectKey": pax.get('ObjectKey', f'PAX{i+1}'),
                "PTC": {"value": pax.get('PTC', 'ADT')},
                "Name": {
                    "Surname": {"value": pax.get('surname', 'DOE')},
                    "Given": [{"value": pax.get('givenName', 'JON')}],
                    "Title": pax.get('title', 'Mr')
                },
                "AdditionalRoles": {
                    "PaymentContactInd": i == 0  # First passenger is payment contact
                },
                "Contacts": {
                    "Contact": [{
                        "AddressContact": {
                            "Street": pax.get('address', {}).get('street', ['123 Main St']),
                            "CityName": pax.get('address', {}).get('city', 'City'),
                            "CountrySubDivisionCode": pax.get('address', {}).get('state', ''),
                            "PostalCode": pax.get('address', {}).get('postalCode', '12345'),
                            "CountryCode": {"value": pax.get('address', {}).get('country', 'US')}
                        },
                        "EmailContact": {
                            "Address": {"value": pax.get('email', 'user@example.com')}
                        },
                        "PhoneContact": {
                            "Application": "Home",
                            "Number": [{
                                "value": pax.get('phone', '1234567890'),
                                "CountryCode": pax.get('phoneCountryCode', '1')
                            }]
                        }
                    }]
                },
                "Age": {
                    "BirthDate": {"value": pax.get('birthDate', '1990-01-01')}
                },
                "Gender": {"value": pax.get('gender', 'Male')}
            }
            request["Query"]["Passengers"]["Passenger"].append(passenger_obj)
        
        # Extract offer information from pricing response
        priced_offers = normalize_to_list(pricing_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
        if not priced_offers:
            raise ValueError("No priced offers found in response")
        
        selected_offer = priced_offers[0]  # Use first offer
        offer_id = selected_offer.get('OfferID', {})
        
        # Build ShoppingResponse
        shopping_response = {
            "Owner": offer_id.get('Owner', ''),
            "Offers": {
                "Offer": [{
                    "OfferID": {
                        "ObjectKey": offer_id.get('value', ''),
                        "value": offer_id.get('value', ''),
                        "Owner": offer_id.get('Owner', ''),
                        "Channel": offer_id.get('Channel', 'NDC')
                    },
                    "OfferItems": {
                        "OfferItem": [{
                            "OfferItemID": {
                                "value": normalize_to_list(selected_offer.get('OfferPrice', []))[0].get('OfferItemID', '') if normalize_to_list(selected_offer.get('OfferPrice', [])) else '',
                                "Owner": offer_id.get('Owner', '')
                            }
                        }]
                    }
                }]
            },
            "ResponseID": {
                "value": pricing_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
            }
        }
        
        request["Query"]["OrderItems"]["ShoppingResponse"] = shopping_response
        
        # Build OfferItems based on scenario
        offer_items = []
        
        # Add flight item (always present)
        flight_offer_item = {
            "OfferItemID": {
                "value": normalize_to_list(selected_offer.get('OfferPrice', []))[0].get('OfferItemID', '') if normalize_to_list(selected_offer.get('OfferPrice', [])) else '',
                "Owner": offer_id.get('Owner', ''),
                "Channel": "NDC"
            },
            "OfferItemType": {
                "DetailedFlightItem": [{
                    "Price": normalize_to_list(selected_offer.get('OfferPrice', []))[0].get('RequestedDate', {}).get('PriceDetail', {}) if normalize_to_list(selected_offer.get('OfferPrice', [])) else {},
                    "OriginDestination": _build_origin_destination(pricing_response),
                    "refs": [pax.get('ObjectKey', f'PAX{i+1}') for i, pax in enumerate(passengers_data)]
                }]
            }
        }
        offer_items.append(flight_offer_item)
        
        # Add services and seats based on scenario
        if scenario_info["scenario"] == "priced_ind_true":
            # Use PRICED results from FlightPriceRS (after pricing seat and ancillary)
            offer_items.extend(_build_priced_ind_true_items(
                servicelist_response, seatavailability_response, 
                selected_services, selected_seats, passengers_data, airline_code,
                ancillary_pricing_response  # Pass the pricing response
            ))
        elif scenario_info["scenario"] == "priced_ind_false":
            # Use ancillary pricing response
            logger.info("Building offer items for PricedInd=false scenario")
            priced_ind_false_items = _build_priced_ind_false_items(
                pricing_response, passengers_data, airline_code
            )
            logger.info(f"Built {len(priced_ind_false_items)} items from PricedInd=false builder")
            for i, item in enumerate(priced_ind_false_items):
                logger.info(f"PricedInd=false item {i}: OfferItemID={item.get('OfferItemID', {}).get('value', 'N/A')}")
            offer_items.extend(priced_ind_false_items)
        else:  # mixed scenario
            # Combine both approaches
            offer_items.extend(_build_mixed_scenario_items(
                servicelist_response, seatavailability_response,
                pricing_response, selected_services, selected_seats,
                passengers_data, airline_code, scenario_info
            ))
        
        request["Query"]["OrderItems"]["OfferItem"] = offer_items
        
        # Build ServiceList in DataLists
        service_list = []
        
        if scenario_info["scenario"] == "priced_ind_true":
            service_list.extend(_build_service_list_from_responses(
                servicelist_response, seatavailability_response,
                selected_services, selected_seats
            ))
        elif scenario_info["scenario"] == "priced_ind_false":
            # CRITICAL FIX: For PricedInd=false, use ServiceList from ANCILLARY PRICING RESPONSE (FlightPriceRS)
            # NOT from original ServiceListRS/SeatAvailabilityRS to avoid duplicates
            logger.info("Using ServiceList from ancillary pricing response (FlightPriceRS)")
            data_lists = ancillary_pricing_response.get('DataLists', {})
            logger.info(f"DataLists keys: {list(data_lists.keys())}")
            
            service_list_obj = data_lists.get('ServiceList', {})
            logger.info(f"ServiceList object type: {type(service_list_obj)}, keys: {list(service_list_obj.keys()) if isinstance(service_list_obj, dict) else 'N/A'}")
            
            ancillary_services = service_list_obj.get('Service', []) if isinstance(service_list_obj, dict) else []
            logger.info(f"Service array type: {type(ancillary_services)}, length: {len(ancillary_services) if isinstance(ancillary_services, (list, dict)) else 0}")
            
            # Normalize to list
            ancillary_services = normalize_to_list(ancillary_services)
            logger.info(f"After normalization: {len(ancillary_services)} services")
            
            service_list.extend(ancillary_services)
            logger.info(f"Added {len(service_list)} services from ancillary pricing response to OrderCreate DataLists")
            
            # Log each service for debugging
            for idx, svc in enumerate(service_list):
                logger.info(f"Service {idx}: ObjectKey={svc.get('ObjectKey')}, ServiceID={svc.get('ServiceID', {}).get('value')}, PricedInd={svc.get('PricedInd')}")
        else:  # mixed scenario
            service_list.extend(_build_mixed_service_list(
                servicelist_response, seatavailability_response,
                pricing_response, selected_services, selected_seats,
                scenario_info
            ))
        
        request["Query"]["DataLists"]["ServiceList"]["Service"] = service_list
        
        logger.info(f"Built enhanced OrderCreate request with {len(offer_items)} offer items")
        return request
        
    except Exception as e:
        logger.error(f"Error building enhanced OrderCreate request: {e}")
        raise

def _build_origin_destination(pricing_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build OriginDestination structure from pricing response."""
    try:
        data_lists = pricing_response.get('DataLists', {})
        flight_segment_list = data_lists.get('FlightSegmentList', {})
        flight_segments = normalize_to_list(flight_segment_list.get('FlightSegment', []) if isinstance(flight_segment_list, dict) else flight_segment_list)
        
        origin_destinations = []
        for segment in flight_segments:
            origin_dest = {
                "Flight": [{
                    "Departure": {
                        "Time": segment.get('Departure', {}).get('Time', ''),
                        "AirportCode": segment.get('Departure', {}).get('AirportCode', {}),
                        "Date": segment.get('Departure', {}).get('Date', ''),
                        "Terminal": segment.get('Departure', {}).get('Terminal', {})
                    },
                    "Arrival": {
                        "Time": segment.get('Arrival', {}).get('Time', ''),
                        "AirportCode": segment.get('Arrival', {}).get('AirportCode', {}),
                        "Date": segment.get('Arrival', {}).get('Date', ''),
                        "Terminal": segment.get('Arrival', {}).get('Terminal', {})
                    },
                    "MarketingCarrier": segment.get('MarketingCarrier', {}),
                    "Equipment": segment.get('Equipment', {}),
                    "Details": segment.get('Details', {}),
                    "ClassOfService": segment.get('ClassOfService', {}),
                    "SegmentKey": segment.get('SegmentKey', '')
                }],
                "OriginDestinationKey": f"OD{len(origin_destinations) + 1}"
            }
            origin_destinations.append(origin_dest)
        
        return origin_destinations
        
    except Exception as e:
        logger.error(f"Error building origin destination: {e}")
        return []

def _build_priced_ind_true_items(
    servicelist_response: Optional[Dict[str, Any]],
    seatavailability_response: Optional[Dict[str, Any]],
    selected_services: Optional[List[str]],
    selected_seats: Optional[List[str]],
    passengers_data: List[Dict[str, Any]],
    airline_code: Optional[str],
    pricing_response: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Build offer items for PricedInd=true scenario using priced results from FlightPriceRS."""
    items = []
    
    try:
        # For PricedInd=true scenario, we should use the PRICED results from FlightPriceRS
        # not the original ServiceListRS/SeatAvailabilityRS data
        
        if pricing_response:
            # Extract priced offers from the final FlightPriceRS (after pricing seat and ancillary)
            priced_offers = normalize_to_list(pricing_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
            
            for offer in priced_offers:
                offer_id = offer.get('OfferID', {})
                offer_id_value = offer_id.get('value', '')
                offer_id_owner = offer_id.get('Owner', '')
                shopping_response_id = pricing_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                
                # Process each priced offer item
                offer_prices = normalize_to_list(offer.get('OfferPrice', []))
                
                for price in offer_prices:
                    offer_item_id = price.get('OfferItemID', '')
                    if not offer_item_id:
                        continue
                    
                    # Check if this is a service or seat item by looking at associations
                    associations = price.get('RequestedDate', {}).get('Associations', [])
                    
                    # Build refs array: OfferID first, then ShoppingResponseID
                    offer_item_refs = []
                    if offer_id_value:
                        offer_item_refs.append(offer_id_value)
                    if shopping_response_id:
                        offer_item_refs.append(shopping_response_id)
                    
                    # Determine if this is a service or seat item
                    is_seat_item = False
                    is_service_item = False
                    
                    for assoc in associations:
                        if 'AssociatedService' in assoc and 'SeatAssignment' in assoc.get('AssociatedService', {}):
                            is_seat_item = True
                            break
                        elif 'AssociatedService' in assoc and 'ServiceReferences' in assoc.get('AssociatedService', {}):
                            is_service_item = True
                            break
                    
                    if is_seat_item:
                        # Build seat item
                        seat_item = _build_seat_item_from_pricing(price, offer_item_id, offer_item_refs, offer_id_owner, passengers_data)
                        if seat_item:
                            items.append(seat_item)
                    
                    elif is_service_item:
                        # Build service item
                        service_item = _build_service_item_from_pricing(price, offer_item_id, offer_item_refs, offer_id_owner, passengers_data)
                        if service_item:
                            items.append(service_item)
        
        # Fallback to original logic if no pricing response provided
        else:
            logger.warning("No pricing response provided for PricedInd=true scenario, using original ServiceList/SeatAvailability data")
            # Add services from ServiceList response (fallback)
            if servicelist_response and selected_services:
                services = normalize_to_list(servicelist_response.get('Services', {}).get('Service', []))
                
                # Get OfferExpiration and ShoppingResponseID from ServiceList response
                offer_expiration_key = servicelist_response.get('OfferExpiration', {}).get('ObjectKey', '')
                shopping_response_id = servicelist_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                
                for service in services:
                    service_key = service.get('ObjectKey', '')
                    if service_key in selected_services:
                        # Get ServiceID.ObjectKey for the value
                        service_id_object_key = service.get('ServiceID', {}).get('ObjectKey', '')
                        
                        # Build refs array: OfferExpiration.ObjectKey first, then ShoppingResponseID
                        offer_item_refs = []
                        if offer_expiration_key:
                            offer_item_refs.append(offer_expiration_key)
                        if shopping_response_id:
                            offer_item_refs.append(shopping_response_id)
                        
                        # Build OfferItemType refs: Passenger refs first, then Service.ObjectKey
                        offer_item_type_refs = [pax.get('ObjectKey', f'PAX{i+1}') for i, pax in enumerate(passengers_data)]
                        if service_key:
                            offer_item_type_refs.append(service_key)
                        
                        service_item = {
                            "OfferItemID": {
                                "value": service_id_object_key,  # Use ServiceID.ObjectKey as value
                                "Owner": service.get('ServiceID', {}).get('Owner', ''),
                                "refs": offer_item_refs,  # OfferExpiration.ObjectKey first, then ShoppingResponseID
                                "Channel": "NDC"
                            },
                            "OfferItemType": {
                                "OtherItem": [{
                                    "refs": offer_item_type_refs,  # Passenger refs first, then Service.ObjectKey
                                    "Price": {
                                        "SimpleCurrencyPrice": service.get('Price', [{}])[0].get('Total', {}) if service.get('Price') else {
                                            "value": 0,
                                            "Code": "USD"
                                        }
                                    }
                                }]
                            }
                        }
                        items.append(service_item)
        
        # Add seats
        if seatavailability_response and selected_seats:
            services = normalize_to_list(seatavailability_response.get('Services', {}).get('Service', []))
            
            for service in services:
                service_key = service.get('ObjectKey', '')
                if service_key in selected_seats:
                    # Find corresponding seat details
                    seat_list = seatavailability_response.get('DataLists', {}).get('SeatList', {}).get('Seats', [])
                    seat_list = normalize_to_list(seat_list)
                    
                    selected_seat = None
                    for seat in seat_list:
                        if seat.get('ObjectKey') == service_key:
                            selected_seat = seat
                            break
                    
                    if selected_seat:
                        seat_item = {
                            "OfferItemID": {
                                "value": service_key,
                                "refs": [pax.get('ObjectKey', f'PAX{i+1}') for i, pax in enumerate(passengers_data)],
                                "Channel": "NDC"
                            },
                            "OfferItemType": {
                                "SeatItem": [{
                                    "Price": {
                                        "Total": service.get('Price', [{}])[0].get('Total', {}) if service.get('Price') else {
                                            "value": 0,
                                            "Code": "USD"
                                        }
                                    },
                                    "Descriptions": service.get('Descriptions', {}),
                                    "Location": selected_seat.get('Location', {}),
                                    "SeatAssociation": selected_seat.get('SeatAssociation', [])
                                }]
                            }
                        }
                        items.append(seat_item)
        
        return items
        
    except Exception as e:
        logger.error(f"Error building PricedInd=true items: {e}")
        return []

def _build_seat_item_from_pricing(
    price: Dict[str, Any],
    offer_item_id: str,
    offer_item_refs: List[str],
    owner: str,
    passengers_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Build seat item from pricing response."""
    try:
        associations = price.get('RequestedDate', {}).get('Associations', [])
        
        # Extract seat details from associations
        seat_details = None
        traveler_refs = []
        segment_refs = []
        
        for assoc in associations:
            if 'AssociatedTraveler' in assoc:
                traveler_refs.extend(assoc['AssociatedTraveler'].get('TravelerReferences', []))
            
            if 'AssociatedService' in assoc and 'SeatAssignment' in assoc['AssociatedService']:
                seat_assignment = assoc['AssociatedService']['SeatAssignment']
                seat_details = seat_assignment.get('Seat', {})
                
                # Extract segment references
                if 'ApplicableFlight' in assoc:
                    flight_refs = assoc['ApplicableFlight'].get('FlightSegmentReference', [])
                    segment_refs = [ref.get('ref', '') for ref in flight_refs if ref.get('ref')]
        
        if not seat_details:
            return None
        
        # Build seat item
        seat_item = {
            "OfferItemID": {
                "value": offer_item_id,
                "refs": offer_item_refs,
                "Owner": owner,
                "Channel": "NDC"
            },
            "OfferItemType": {
                "SeatItem": [{
                    "Price": {
                        "Total": price.get('RequestedDate', {}).get('PriceDetail', {}).get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                    },
                    "Location": seat_details.get('Location', {}),
                    "Characteristics": seat_details.get('Location', {}).get('Characteristics', {}),
                    "SeatAssociation": [{
                        "SegmentReferences": {
                            "value": segment_refs
                        },
                        "TravelerReference": traveler_refs[0] if traveler_refs else "PAX1"
                    }]
                }]
            }
        }
        
        return seat_item
        
    except Exception as e:
        logger.error(f"Error building seat item from pricing: {e}")
        return None

def _build_service_item_from_pricing(
    price: Dict[str, Any],
    offer_item_id: str,
    offer_item_refs: List[str],
    owner: str,
    passengers_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Build service item from pricing response."""
    try:
        associations = price.get('RequestedDate', {}).get('Associations', [])
        
        # Extract service details from associations
        traveler_refs = []
        segment_refs = []
        service_refs = []
        
        for assoc in associations:
            if 'AssociatedTraveler' in assoc:
                traveler_refs.extend(assoc['AssociatedTraveler'].get('TravelerReferences', []))
            
            if 'AssociatedService' in assoc:
                service_refs.extend(assoc['AssociatedService'].get('ServiceReferences', []))
                
                # Extract segment references
                if 'ApplicableFlight' in assoc:
                    flight_refs = assoc['ApplicableFlight'].get('FlightSegmentReference', [])
                    segment_refs = [ref.get('ref', '') for ref in flight_refs if ref.get('ref')]
        
        # Build OfferItemType refs: Passenger refs first, then segment refs, then service refs
        offer_item_type_refs = []
        if traveler_refs:
            offer_item_type_refs.extend(traveler_refs)
        if segment_refs:
            offer_item_type_refs.extend(segment_refs)
        if service_refs:
            offer_item_type_refs.extend(service_refs)
        
        # Build service item
        service_item = {
            "OfferItemID": {
                "value": offer_item_id,
                "refs": offer_item_refs,
                "Owner": owner,
                "Channel": "NDC"
            },
            "OfferItemType": {
                "OtherItem": [{
                    "refs": offer_item_type_refs,
                    "Price": {
                        "SimpleCurrencyPrice": price.get('RequestedDate', {}).get('PriceDetail', {}).get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                    }
                }]
            }
        }
        
        return service_item
        
    except Exception as e:
        logger.error(f"Error building service item from pricing: {e}")
        return None

def _build_priced_ind_false_items(
    pricing_response: Dict[str, Any],
    passengers_data: List[Dict[str, Any]],
    airline_code: Optional[str]
) -> List[Dict[str, Any]]:
    """Build offer items for PricedInd=false scenario using pricing response."""
    items = []
    
    try:
        logger.info("Building PricedInd=false items from pricing response")
        # Extract offer items from pricing response
        priced_offers = normalize_to_list(pricing_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
        logger.info(f"Found {len(priced_offers)} priced offers")
        
        for offer in priced_offers:
            offer_prices = normalize_to_list(offer.get('OfferPrice', []))
            logger.info(f"Processing offer with {len(offer_prices)} prices")
            
            for price in offer_prices:
                offer_item_id = price.get('OfferItemID', '')
                logger.info(f"Processing price with OfferItemID: {offer_item_id}")
                if not offer_item_id:
                    continue
                
                # Determine item type based on associations
                associations = price.get('RequestedDate', {}).get('Associations', [])
                associations = normalize_to_list(associations)
                logger.info(f"Associations keys: {list(associations[0].keys()) if associations else 'None'}")
                
                if associations and 'AssociatedService' in associations[0]:
                    # This is a service or seat item
                    associated_service = associations[0].get('AssociatedService', {})
                    logger.info(f"AssociatedService keys: {list(associated_service.keys()) if associated_service else 'None'}")
                    
                    if 'SeatAssignment' in associated_service:
                        # This is a seat item - build per VDC spec
                        seat_assignments = normalize_to_list(associated_service.get('SeatAssignment', []))
                        if seat_assignments:
                            seat_assignment = seat_assignments[0]
                            seat = seat_assignment.get('Seat', {})
                        else:
                            seat = {}
                        
                        # Get price total
                        price_detail = price.get('RequestedDate', {}).get('PriceDetail', {})
                        total_amount = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                        
                        # Get traveler reference
                        traveler_ref = associations[0].get('AssociatedTraveler', {}).get('TravelerReferences', ['PAX1'])
                        if isinstance(traveler_ref, list):
                            traveler_ref = traveler_ref[0] if traveler_ref else 'PAX1'
                        
                        # Build SeatItem per VDC specification
                        seat_item = {
                            "OfferItemID": {
                                "value": offer_item_id,
                                "Owner": offer.get('OfferID', {}).get('Owner', ''),
                                "refs": [
                                    offer.get('OfferID', {}).get('value', ''),
                                    pricing_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                                ],
                                "Channel": "NDC"
                            },
                            "OfferItemType": {
                                "SeatItem": [{
                                    "Price": {
                                        "Total": total_amount
                                    },
                                    "Descriptions": seat.get('Descriptions', {}),
                                    "Location": seat.get('Location', {}),
                                    "SeatAssociation": [{
                                        "SegmentReferences": {
                                            "value": [associations[0].get('ApplicableFlight', {}).get('FlightSegmentReference', '')]
                                        },
                                        "TravelerReference": traveler_ref
                                    }]
                                }]
                            }
                        }
                        items.append(seat_item)
                        logger.info(f"Built SeatItem for OfferItemID: {offer_item_id}")
                    else:
                        # This is a service item (baggage, meal, etc.)
                        logger.info(f"Building service item for OfferItemID: {offer_item_id}")
                        service_item = {
                            "OfferItemID": {
                                "value": offer_item_id,
                                "Owner": offer.get('OfferID', {}).get('Owner', ''),
                                "refs": [
                                    offer.get('OfferID', {}).get('value', ''),
                                    pricing_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                                ],
                                "Channel": "NDC"
                            },
                            "OfferItemType": {
                                "OtherItem": [{
                                    "refs": [pax.get('ObjectKey', f'PAX{i+1}') for i, pax in enumerate(passengers_data)],
                                    "Price": {
                                        "SimpleCurrencyPrice": price.get('RequestedDate', {}).get('PriceDetail', {}).get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
                                    }
                                }]
                            }
                        }
                        items.append(service_item)
                        logger.info(f"Built OtherItem for OfferItemID: {offer_item_id}")
        
        return items
        
    except Exception as e:
        logger.error(f"Error building PricedInd=false items: {e}")
        return []

def _build_mixed_scenario_items(
    servicelist_response: Optional[Dict[str, Any]],
    seatavailability_response: Optional[Dict[str, Any]],
    pricing_response: Dict[str, Any],
    selected_services: Optional[List[str]],
    selected_seats: Optional[List[str]],
    passengers_data: List[Dict[str, Any]],
    airline_code: Optional[str],
    scenario_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Build offer items for mixed scenario (some PricedInd=true, some PricedInd=false)."""
    items = []
    
    try:
        # Add priced services and seats
        if scenario_info["services_priced"]:
            items.extend(_build_priced_ind_true_items(
                servicelist_response, None, scenario_info["services_priced"], None,
                passengers_data, airline_code
            ))
        
        if scenario_info["seats_priced"]:
            items.extend(_build_priced_ind_true_items(
                None, seatavailability_response, None, scenario_info["seats_priced"],
                passengers_data, airline_code
            ))
        
        # Add unpriced services and seats from pricing response
        if scenario_info["services_unpriced"] or scenario_info["seats_unpriced"]:
            items.extend(_build_priced_ind_false_items(
                pricing_response, passengers_data, airline_code
            ))
        
        return items
        
    except Exception as e:
        logger.error(f"Error building mixed scenario items: {e}")
        return []

def _build_service_list_from_responses(
    servicelist_response: Optional[Dict[str, Any]],
    seatavailability_response: Optional[Dict[str, Any]],
    selected_services: Optional[List[str]],
    selected_seats: Optional[List[str]]
) -> List[Dict[str, Any]]:
    """Build ServiceList from ServiceList and SeatAvailability responses."""
    service_list = []
    
    try:
        # Add services
        if servicelist_response and selected_services:
            services = normalize_to_list(servicelist_response.get('Services', {}).get('Service', []))
            
            for service in services:
                service_key = service.get('ObjectKey', '')
                if service_key in selected_services:
                    service_entry = {
                        "ObjectKey": service_key,
                        "ServiceID": service.get('ServiceID', {}),
                        "Name": service.get('Name', {}),
                        "Descriptions": service.get('Descriptions', {}),
                        "Price": service.get('Price', []),
                        "Associations": service.get('Associations', []),
                        "PricedInd": service.get('PricedInd', True)
                    }
                    service_list.append(service_entry)
        
        # Add seats
        if seatavailability_response and selected_seats:
            services = normalize_to_list(seatavailability_response.get('Services', {}).get('Service', []))
            
            for service in services:
                service_key = service.get('ObjectKey', '')
                if service_key in selected_seats:
                    service_entry = {
                        "ObjectKey": service_key,
                        "ServiceID": service.get('ServiceID', {}),
                        "Name": service.get('Name', {}),
                        "Descriptions": service.get('Descriptions', {}),
                        "Price": service.get('Price', []),
                        "Associations": service.get('Associations', []),
                        "PricedInd": service.get('PricedInd', True)
                    }
                    service_list.append(service_entry)
        
        return service_list
        
    except Exception as e:
        logger.error(f"Error building service list from responses: {e}")
        return []

def _build_service_list_from_pricing(
    pricing_response: Dict[str, Any],
    selected_services: Optional[List[str]],
    selected_seats: Optional[List[str]]
) -> List[Dict[str, Any]]:
    """Build ServiceList from pricing response."""
    service_list = []
    
    try:
        # Extract services from pricing response DataLists
        data_lists = pricing_response.get('DataLists', {})
        services = normalize_to_list(data_lists.get('ServiceList', {}).get('Service', []))
        
        for service in services:
            service_key = service.get('ObjectKey', '')
            if (selected_services and service_key in selected_services) or \
               (selected_seats and service_key in selected_seats):
                service_entry = {
                    "ObjectKey": service_key,
                    "ServiceID": service.get('ServiceID', {}),
                    "Name": service.get('Name', {}),
                    "Descriptions": service.get('Descriptions', {}),
                    "Price": service.get('Price', []),
                    "Associations": service.get('Associations', []),
                    "PricedInd": service.get('PricedInd', False)
                }
                service_list.append(service_entry)
        
        return service_list
        
    except Exception as e:
        logger.error(f"Error building service list from pricing: {e}")
        return []

def _build_mixed_service_list(
    servicelist_response: Optional[Dict[str, Any]],
    seatavailability_response: Optional[Dict[str, Any]],
    pricing_response: Dict[str, Any],
    selected_services: Optional[List[str]],
    selected_seats: Optional[List[str]],
    scenario_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Build ServiceList for mixed scenario."""
    service_list = []
    
    try:
        # Add priced items from responses
        if scenario_info["services_priced"]:
            service_list.extend(_build_service_list_from_responses(
                servicelist_response, None, scenario_info["services_priced"], None
            ))
        
        if scenario_info["seats_priced"]:
            service_list.extend(_build_service_list_from_responses(
                None, seatavailability_response, None, scenario_info["seats_priced"]
            ))
        
        # Add unpriced items from pricing response
        if scenario_info["services_unpriced"] or scenario_info["seats_unpriced"]:
            service_list.extend(_build_service_list_from_pricing(
                pricing_response, scenario_info["services_unpriced"], scenario_info["seats_unpriced"]
            ))
        
        return service_list
        
    except Exception as e:
        logger.error(f"Error building mixed service list: {e}")
        return []

def build_ordercreate_enhanced_request(
    flight_price_response: Dict[str, Any],
    passengers_data: List[Dict[str, Any]],
    payment_input_info: Dict[str, Any],
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None,
    selected_offer_index: int = 0,
    ancillary_pricing_response: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Enhanced OrderCreate request builder that automatically handles PricedInd=false scenarios.
    
    This function:
    1. Detects if pricing is required for selected services/seats
    2. Uses the provided ancillary pricing response if available
    3. Falls back to original response if no pricing needed
    
    Args:
        flight_price_response: Original FlightPriceRS response
        passengers_data: Passenger information
        payment_input_info: Payment information
        servicelist_response: ServiceListRS response (optional)
        seatavailability_response: SeatAvailabilityRS response (optional)
        selected_services: List of selected service ObjectKeys (optional)
        selected_seats: List of selected seat ObjectKeys (optional)
        selected_offer_index: Index of selected offer (default: 0)
        ancillary_pricing_response: Priced FlightPriceRS response (optional)
        
    Returns:
        OrderCreateRQ payload
    """
    try:
        logger.info("Building enhanced OrderCreate request")
        
        # Step 1: Detect if pricing is required
        from scripts.build_flightprice_ancillary_rq import detect_pricing_required
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        logger.info(f"Pricing requirements: {pricing_info}")
        
        # Step 2: Determine which FlightPriceRS response to use
        final_flight_price_response = flight_price_response
        
        # CRITICAL: If ancillary_pricing_response is provided, we're in PricedInd=false scenario
        # Use the ancillary pricing response as the source for OrderCreate
        if ancillary_pricing_response:
            logger.info("Ancillary pricing response provided - using it as source for OrderCreate (PricedInd=false scenario)")
            # Check if it's wrapped in response structure
            if 'response' in ancillary_pricing_response and 'raw_response' in ancillary_pricing_response['response']:
                final_flight_price_response = ancillary_pricing_response['response']['raw_response']
            else:
                final_flight_price_response = ancillary_pricing_response
            
            logger.info(f"Using ancillary FlightPriceRS with {len(final_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))} offers")
        # FIXED: Ensure we use the correct FlightPriceRS data structure
        elif 'response' in flight_price_response and 'raw_response' in flight_price_response['response']:
            final_flight_price_response = flight_price_response['response']['raw_response']
            logger.info("Using raw FlightPriceRS response for proper segment key mapping")
            
            # FIXED: Ensure ShoppingResponseID is available
            if 'ShoppingResponseID' not in final_flight_price_response:
                if 'response' in flight_price_response and 'data' in flight_price_response['response']:
                    shopping_id = flight_price_response['response']['data'].get('ShoppingResponseID')
                    if shopping_id:
                        final_flight_price_response['ShoppingResponseID'] = shopping_id
                        logger.info(f"Added ShoppingResponseID to FlightPriceRS: {shopping_id}")
                else:
                    final_flight_price_response['ShoppingResponseID'] = {"value": "test-shopping-id"}
                    logger.warning("Using default ShoppingResponseID for OrderCreate generation")
        
        if pricing_info['requires_pricing']:
            if ancillary_pricing_response:
                logger.info("Using provided ancillary pricing response for PricedInd=false items")
                # Also ensure ancillary response has correct structure
                if 'response' in ancillary_pricing_response and 'raw_response' in ancillary_pricing_response['response']:
                    final_flight_price_response = ancillary_pricing_response['response']['raw_response']
                else:
                    final_flight_price_response = ancillary_pricing_response
            else:
                logger.warning("Pricing required but no ancillary pricing response provided")
                logger.warning("Using original FlightPriceRS response (may be incomplete)")
        else:
            logger.info("No pricing required - using original FlightPriceRS response")
        
        # Step 3: Generate OrderCreate request using the appropriate method
        if ancillary_pricing_response:
            # Use NEW builder that correctly handles SeatItem from ancillary pricing response
            logger.info("Using NEW builder for PricedInd=false scenario (builds SeatItem correctly)")
            
            # Call the internal builder function (the one at line 158) that builds SeatItem correctly
            # This is the CORRECT implementation for ancillary pricing
            scenario_info = {
                "scenario": "priced_ind_false",
                "services_priced": [],
                "services_unpriced": selected_services or [],
                "seats_priced": [],
                "seats_unpriced": selected_seats or []
            }
            
            # Build using the same logic as the function starting at line 158
            # which correctly builds SeatItems from PricedFlightOffers
            order_create_rq = {
                "Query": {
                    "Passengers": {"Passenger": []},
                    "OrderItems": {
                        "ShoppingResponse": {},
                        "OfferItem": []
                    },
                    "DataLists": {
                        "ServiceList": {"Service": []}
                    },
                    "Metadata": {},
                    "Payments": {"Payment": []}
                }
            }
            
            # Build passengers (use generate_order_create_rq approach)
            from scripts.build_ordercreate_rq import generate_order_create_rq as build_passengers_helper
            temp_order = build_passengers_helper(
                flight_price_response=final_flight_price_response,
                passengers_data=passengers_data,
                payment_input_info=payment_input_info,
                servicelist_response=None,
                seatavailability_response=None,
                selected_services=[],
                selected_seats=[]
            )
            
            # Copy passengers from temp order
            order_create_rq["Query"]["Passengers"] = temp_order["Query"]["Passengers"]
            order_create_rq["Query"]["Metadata"] = temp_order["Query"]["Metadata"]
            order_create_rq["Query"]["Payments"] = temp_order["Query"]["Payments"]
            
            # Build ShoppingResponse
            priced_offers = normalize_to_list(final_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))
            if priced_offers:
                selected_offer = priced_offers[0]
                offer_id = selected_offer.get('OfferID', {})
                
                order_create_rq["Query"]["OrderItems"]["ShoppingResponse"] = {
                    "Owner": offer_id.get('Owner', ''),
                    "ResponseID": {
                        "value": final_flight_price_response.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
                    },
                    "Offers": {
                        "Offer": [{
                            "OfferID": {
                                "ObjectKey": offer_id.get('value', ''),
                                "value": offer_id.get('value', ''),
                                "Owner": offer_id.get('Owner', ''),
                                "Channel": offer_id.get('Channel', 'NDC')
                            },
                            "OfferItems": {"OfferItem": []}
                        }]
                    }
                }
            
            # Build OfferItems using _build_priced_ind_false_items
            airline_code = _extract_airline_from_flight_price_response(final_flight_price_response)
            offer_items = _build_priced_ind_false_items(
                final_flight_price_response, 
                passengers_data, 
                airline_code
            )
            order_create_rq["Query"]["OrderItems"]["OfferItem"] = offer_items
            
            # Build ServiceList from ancillary pricing response
            data_lists = final_flight_price_response.get('DataLists', {})
            service_list_obj = data_lists.get('ServiceList', {})
            services = normalize_to_list(service_list_obj.get('Service', []) if isinstance(service_list_obj, dict) else [])
            order_create_rq["Query"]["DataLists"]["ServiceList"]["Service"] = services
            
            logger.info(f"NEW builder: Generated {len(offer_items)} OfferItems, {len(services)} services")
            
        else:
            # Use OLD builder for backward compatibility (PricedInd=true scenario)
            logger.info("Using OLD builder (generate_order_create_rq) for PricedInd=true scenario")
            from scripts.build_ordercreate_rq import generate_order_create_rq
            order_create_rq = generate_order_create_rq(
                flight_price_response=final_flight_price_response,
                passengers_data=passengers_data,
                payment_input_info=payment_input_info,
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services,
                selected_seats=selected_seats
            )
        
        # Add metadata about the pricing process
        if 'metadata' not in order_create_rq:
            order_create_rq['metadata'] = {}
        
        order_create_rq['metadata']['pricing_info'] = pricing_info
        order_create_rq['metadata']['used_priced_response'] = pricing_info['requires_pricing'] and ancillary_pricing_response is not None
        
        logger.info("Enhanced OrderCreate request built successfully")
        return order_create_rq
        
    except Exception as e:
        logger.error(f"Error building enhanced OrderCreate request: {e}")
        # Fallback to basic OrderCreate
        logger.info("Falling back to basic OrderCreate request")
        from scripts.build_ordercreate_rq import generate_order_create_rq
        return generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_input_info,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )

# --- END OF FILE build_ordercreate_enhanced_rq.py ---
