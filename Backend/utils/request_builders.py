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
    contact_info: Dict[str, str]
) -> Dict[str, Any]:
    """
    Build an OrderCreate request from a FlightPrice response.
    
    Args:
        flight_price_response: The FlightPrice response
        passenger_details: List of passenger details
        payment_details: Payment information
        contact_info: Contact information
        
    Returns:
        Dictionary containing the OrderCreate request
    """
    try:
        # First generate the base request
        request = generate_order_create_rq(flight_price_response)
        
        # Update with passenger details
        if passenger_details:
            if 'Query' not in request:
                request['Query'] = {}
            if 'DataLists' not in request['Query']:
                request['Query']['DataLists'] = {}
            
            # Add passenger details
            passengers = []
            for idx, pax in enumerate(passenger_details, 1):
                passenger = {
                    "PaxID": f"PAX{idx}",
                    "PTC": pax.get('type', 'ADT'),
                    "CitizenshipCountryCode": pax.get('nationality', ''),
                    "Individual": {
                        "GivenName": pax.get('first_name', ''),
                        "Surname": pax.get('last_name', ''),
                        "Birthdate": pax.get('birth_date', ''),
                        "Gender": pax.get('gender', 'U')
                    }
                }
                
                # Add passport info if available
                if 'passport_number' in pax:
                    passenger['IdentityDocument'] = {
                        "IdentityDocumentNumber": pax['passport_number'],
                        "ExpiryDate": pax.get('passport_expiry', ''),
                        "IssuingCountryCode": pax.get('passport_country', '')
                    }
                
                passengers.append(passenger)
            
            request['Query']['DataLists']['PassengerList'] = {"Passenger": passengers}
        
        # Update with contact information
        if contact_info:
            if 'ContactInfoList' not in request['Query']:
                request['Query']['ContactInfoList'] = {}
            
            request['Query']['ContactInfoList']['ContactInformation'] = {
                "Contact": {
                    "EmailContact": {
                        "EmailAddress": contact_info.get('email', '')
                    },
                    "PhoneContact": [
                        {
                            "PhoneNumber": contact_info.get('phone', ''),
                            "Label": "MOBILE"
                        }
                    ]
                }
            }
        
        # Update with payment information
        if payment_details:
            if 'Payments' not in request['Query']:
                request['Query']['Payments'] = {}
            
            request['Query']['Payments']['Payment'] = {
                "Type": payment_details.get('type', 'CARD'),
                "Amount": {
                    "value": payment_details.get('amount', '0'),
                    "Code": payment_details.get('currency', 'USD')
                },
                "Method": {
                    "PaymentCard": {
                        "CardType": payment_details.get('card_type', ''),
                        "CardCode": payment_details.get('card_code', ''),
                        "CardNumber": payment_details.get('card_number', ''),
                        "ExpiryDate": payment_details.get('card_expiry', ''),
                        "CardHolderName": payment_details.get('card_holder_name', '')
                    }
                }
            }
        
        return request
        
    except Exception as e:
        raise ValueError(f"Failed to build OrderCreate request: {str(e)}")
