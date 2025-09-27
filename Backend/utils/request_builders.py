"""
Request Builder Utilities

This module contains utilities for building NDC API requests.
"""
import os
import sys
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Import the request builder functions
from scripts.build_airshopping_rq import build_airshopping_request
from scripts.build_flightprice_rq import build_flight_price_request
from scripts.build_ordercreate_rq import generate_order_create_rq


def build_airshopping_rq(
    trip_type: str,
    od_segments: List[Dict[str, str]] = None,
    origin: str = None,
    destination: str = None,
    departure_date: str = None,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: str = "ECONOMY",
    fare_type: str = "PUBL"
) -> Dict[str, Any]:
    """
    Build an AirShopping request.
    
    Args:
        trip_type: Type of trip ("ONE_WAY", "ROUND_TRIP", "MULTI_CITY")
        od_segments: List of origin-destination segments with "Origin", "Destination", "DepartureDate"
        origin: Origin airport code (deprecated, use od_segments)
        destination: Destination airport code (deprecated, use od_segments)
        departure_date: Departure date in YYYY-MM-DD format (deprecated, use od_segments)
        return_date: Return date in YYYY-MM-DD format (deprecated, use od_segments)
        adults: Number of adult passengers
        children: Number of child passengers
        infants: Number of infant passengers
        cabin_class: Cabin class ("ECONOMY", "BUSINESS", "FIRST", "PREMIUM_ECONOMY")
        fare_type: Fare type code (default: "PUBL" for published fares)
        
    Returns:
        Dictionary containing the AirShopping request
    """
    # Map cabin class to IATA codes
    cabin_map = {
        "ECONOMY": "Y",
        "PREMIUM_ECONOMY": "M",
        "BUSINESS": "C",
        "FIRST": "F"
    }
    
    # Convert cabin class to IATA code, default to Economy
    cabin_code = cabin_map.get(cabin_class.upper(), "Y")
    
    # If od_segments is not provided, create it from the legacy parameters
    if od_segments is None:
        if not all([origin, destination, departure_date]):
            raise ValueError("Either od_segments or origin/destination/departure_date must be provided")
            
        od_segments = [{
            "Origin": origin,
            "Destination": destination,
            "DepartureDate": departure_date
        }]
        
        if trip_type == "ROUND_TRIP" and return_date:
            od_segments.append({
                "Origin": destination,
                "Destination": origin,
                "DepartureDate": return_date
            })
    
    # Call the actual request builder
    return build_airshopping_request(
        trip_type=trip_type.upper(),
        od_segments=od_segments,
        num_adults=adults,
        num_children=children,
        num_infants=infants,
        cabin_preference_code=cabin_code,
        fare_type_code=fare_type
    )


def build_flightprice_rq(
    airshopping_response: Dict[str, Any],
    offer_index: int = 0
) -> Dict[str, Any]:
    """
    Build a FlightPrice request from an AirShopping response.
    
    Args:
        airshopping_response: The AirShopping response
        offer_index: Index of the offer to price
        
    Returns:
        Dictionary containing the FlightPrice request
    """
    try:
        request = build_flight_price_request(
            airshopping_response=airshopping_response,
            selected_offer_index=offer_index
        )
        return request
    except Exception as e:
        raise ValueError(f"Failed to build FlightPrice request: {str(e)}")


def build_ordercreate_rq(
    flight_price_response: Dict[str, Any],
    passenger_details: List[Dict[str, Any]],
    payment_details: Dict[str, Any],
    contact_info: Dict[str, str],
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[List[str]] = None,
    selected_seats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build an OrderCreate request from a FlightPrice response.
    
    This is a simplified wrapper that delegates to the core OrderCreate builder.
    The actual complex logic is handled in scripts/build_ordercreate_rq.py
    
    Args:
        flight_price_response: The FlightPrice response
        passenger_details: List of passenger details
        payment_details: Payment information
        contact_info: Contact information
        servicelist_response: ServiceListRS response (optional)
        seatavailability_response: SeatAvailabilityRS response (optional)
        selected_services: List of selected service ObjectKeys (optional)
        selected_seats: List of selected seat ObjectKeys (optional)
        
    Returns:
        Dictionary containing the OrderCreate request
    """
    try:
        # FIXED: Extract the raw NDC response from the nested structure
        # The core OrderCreate builder expects the raw NDC response, not the frontend-transformed response
        enhanced_flight_price_response = flight_price_response.copy()
        
        # Check if we have a nested response structure (frontend format)
        if 'response' in enhanced_flight_price_response and 'raw_response' in enhanced_flight_price_response['response']:
            # Use the raw NDC response directly
            enhanced_flight_price_response = enhanced_flight_price_response['response']['raw_response']
        elif 'response' in enhanced_flight_price_response and 'data' in enhanced_flight_price_response['response']:
            # Try to get the raw response from the data section
            data_response = enhanced_flight_price_response['response']['data']
            if 'raw_response' in data_response:
                enhanced_flight_price_response = data_response['raw_response']
            else:
                # If no raw_response, use the data section
                enhanced_flight_price_response = data_response
        
        # Ensure ShoppingResponseID is available for the core builder
        if 'ShoppingResponseID' not in enhanced_flight_price_response:
            # Try to extract from the original nested structure
            if 'response' in flight_price_response and 'raw_response' in flight_price_response['response']:
                raw_response = flight_price_response['response']['raw_response']
                if 'ShoppingResponseID' in raw_response:
                    shopping_response_id = raw_response['ShoppingResponseID'].get('ResponseID', {}).get('value')
                    if shopping_response_id:
                        enhanced_flight_price_response['ShoppingResponseID'] = {
                            'ResponseID': {'value': shopping_response_id}
                        }
            elif 'response' in flight_price_response and 'data' in flight_price_response['response']:
                data_response = flight_price_response['response']['data']
                if 'ShoppingResponseID' in data_response:
                    shopping_response_id = data_response['ShoppingResponseID'].get('ResponseID', {}).get('value')
                    if shopping_response_id:
                        enhanced_flight_price_response['ShoppingResponseID'] = {
                            'ResponseID': {'value': shopping_response_id}
                        }
        
        # Delegate to the core OrderCreate builder with enhanced response
        return generate_order_create_rq(
            flight_price_response=enhanced_flight_price_response,
            passengers_data=passenger_details,
            payment_input_info=payment_details,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
    except Exception as e:
        raise ValueError(f"Failed to build OrderCreate request: {str(e)}")
