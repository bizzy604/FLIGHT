"""
Request Builder Utilities

This module contains utilities for building NDC API requests.
"""
import os
import sys
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Add parent directory to path to allow importing the request builder files
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the request builder functions
from scripts.build_airshopping_rq import build_airshopping_request
from scripts.build_flightprice_rq import build_flight_price_request
from scripts.build_ordercreate_rq import generate_order_create_rq


def build_airshopping_rq(
    trip_type: str,
    origin: str,
    destination: str,
    departure_date: str,
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
        origin: Origin airport code
        destination: Destination airport code
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (for round trips)
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
    
    cabin_code = cabin_map.get(cabin_class.upper(), "Y")
    
    # Prepare segments
    segments = [{
        "Origin": origin,
        "Destination": destination,
        "DepartureDate": departure_date
    }]
    
    # Add return segment for round trips
    if trip_type.upper() == "ROUND_TRIP" and return_date:
        segments.append({
            "Origin": destination,
            "Destination": origin,
            "DepartureDate": return_date
        })
    
    # Build the request
    request = build_airshopping_request(
        trip_type=trip_type.upper(),
        od_segments=segments,
        num_adults=adults,
        num_children=children,
        num_infants=infants,
        cabin_preference_code=cabin_code,
        fare_type_code=fare_type
    )
    
    return request


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
