"""
Flight Service Module

This module contains the core business logic for interacting with the Verteil NDC API.
It handles the NDC workflow: AirShopping -> FlightPrice -> OrderCreate.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from json import JSONDecodeError
from typing import Dict, List, Any, Optional, Union
import requests
from flask import current_app

# Import request builders and auth
from my_flight_portal_backend.utils.request_builders import (
    build_airshopping_rq,
    build_flightprice_rq,
    build_ordercreate_rq
)
from my_flight_portal_backend.utils.auth import TokenManager, AuthError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CURRENCY = ""
DEFAULT_LANGUAGE = "en"
DEFAULT_FARE_TYPE = "PUBL"

class FlightServiceError(Exception):
    """Custom exception for flight service errors"""
    pass

def get_verteil_headers(service_name: str) -> Dict[str, str]:
    """
    Get the headers for Verteil API requests with OAuth2 token
    
    Args:
        service_name: The name of the service (AirShopping, FlightPrice, OrderCreate)
        
    Returns:
        Dict containing the necessary headers
        
    Raises:
        FlightServiceError: If authentication fails or required configuration is missing
    """
    try:
        # Log the service name for which we're getting headers
        logger.info(f"Getting headers for service: {service_name}")
        
        # Check for required configuration
        required_configs = ['VERTEIL_THIRD_PARTY_ID', 'VERTEIL_OFFICE_ID']
        missing_configs = [cfg for cfg in required_configs if not current_app.config.get(cfg)]
        
        if missing_configs:
            error_msg = f"Missing required configuration: {', '.join(missing_configs)}"
            logger.error(error_msg)
            raise FlightServiceError(error_msg)
        
        # Get the authentication token
        try:
            token_manager = TokenManager()
            auth_token = token_manager.get_token()
            
            if not auth_token:
                error_msg = "Received empty authentication token"
                logger.error(error_msg)
                raise FlightServiceError(error_msg)
                
            logger.debug("Successfully retrieved authentication token")
            
        except Exception as e:
            error_msg = f"Failed to get authentication token: {str(e)}"
            logger.error(error_msg)
            raise FlightServiceError(error_msg) from e
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "service": service_name,
            "ThirdPartyId": str(current_app.config.get('VERTEIL_THIRD_PARTY_ID', '')),
            "OfficeId": str(current_app.config.get('VERTEIL_OFFICE_ID', 'OFF3748'))
        }
        
        # Add Authorization header without duplicating 'Bearer'
        if not auth_token.startswith('Bearer '):
            auth_token = f"Bearer {auth_token}"
        headers["Authorization"] = auth_token
        
        # Log header keys (but not the token) for debugging
        logger.debug("Prepared headers with keys: %s", 
                    [k for k in headers.keys() if k.lower() != 'authorization'])
        
        return headers
        
    except FlightServiceError:
        raise  # Re-raise our custom errors
    except AuthError as e:
        error_msg = f"Authentication failed: {str(e)}"
        logger.error(error_msg)
        raise FlightServiceError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error while preparing headers: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise FlightServiceError(error_msg) from e

def make_verteil_request(endpoint: str, payload: Dict[str, Any], service_name: str) -> Dict[str, Any]:
    """
    Make a request to the Verteil NDC API
    Make a request to the Verteil NDC API with error handling and retry logic
    
    Args:
        endpoint: API endpoint (e.g., '/entrygate/rest/request:airShopping')
        payload: Request payload
        service_name: The name of the service (AirShopping, FlightPrice, OrderCreate)
        
    Returns:
        API response as a dictionary
        
    Raises:
        FlightServiceError: If the request fails after retries
    """
    import time
    import json
    import requests
    from requests.exceptions import RequestException, HTTPError
    from json import JSONDecodeError
    
    max_retries = 3
    retry_delay = 1  # seconds
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            # Get authentication headers with service-specific headers
            headers = get_verteil_headers(service_name)
            
            # Build the full URL
            base_url = current_app.config.get('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com')
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Log the request details
            logger.info(f"\n=== Making {service_name} Request ===")
            logger.info(f"URL: {url}")
            logger.info(f"Attempt: {attempt}/{max_retries}")
            logger.info("Headers:")
            for k, v in headers.items():
                if k.lower() == 'authorization':
                    logger.info(f"  {k}: [REDACTED]")
                else:
                    logger.info(f"  {k}: {v}")
            
            logger.info("Payload:")
            logger.info(json.dumps(payload, indent=2))
            
            # Make the request
            start_time = time.time()
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=current_app.config.get('REQUEST_TIMEOUT', 30)
                )
                duration = time.time() - start_time
                
                # Log the response details
                logger.info(f"\n=== {service_name} Response ===")
                logger.info(f"Status: {response.status_code}")
                logger.info(f"Time: {duration:.2f}s")
                
                # Log response headers
                logger.info("Response Headers:")
                for k, v in response.headers.items():
                    logger.info(f"  {k}: {v}")
                
                # Log raw response content for debugging
                content_type = response.headers.get('Content-Type', '').lower()
                logger.info("Response content type: %s", content_type)
                
                # Try to parse JSON response
                try:
                    if response.content:  # Only try to parse if there's content
                        response_data = response.json()
                        logger.debug("Response JSON structure: %s", list(response_data.keys()) if isinstance(response_data, dict) else f"List with {len(response_data)} items")
                        logger.debug("Response JSON (first 2000 chars):\n%s", json.dumps(response_data, indent=2, default=str)[:2000])
                        return response_data
                    else:
                        logger.warning("Empty response content")
                        return {}
                except JSONDecodeError as e:
                    logger.error("Failed to parse JSON response: %s", str(e))
                    logger.info("Raw response (first 2000 chars):\n%s", response.text[:2000])
                    
                    # Try to extract error message from non-JSON response
                    error_msg = "Invalid JSON response from server"
                    if response.text.strip():
                        error_msg = f"{error_msg}. Response: {response.text[:500]}"
                        
                        # Log the full error response for debugging
                        logger.error("Full error response:")
                        logger.error(json.dumps(response_data, indent=2))
                        
                        raise FlightServiceError(error_msg)
                        
                    # Check for empty or unexpected response
                    if not response_data:
                        error_msg = "Empty response received from API"
                        logger.error(error_msg)
                        raise FlightServiceError(error_msg)
                        
                    logger.info("Successfully parsed JSON response")
                    return response_data
                    
                except JSONDecodeError as je:
                    # If not JSON, log the raw response
                    logger.error(f"Failed to parse JSON response: {str(je)}")
                    logger.info("Raw response content type: %s", response.headers.get('Content-Type', 'unknown'))
                    logger.info("Raw response (first 2000 chars): %s", response.text[:2000])
                    
                    if not response.ok:
                        error_msg = f"HTTP {response.status_code} - {response.reason}"
                        logger.error(f"Request failed: {error_msg}")
                        
                        # Try to extract more error details from non-JSON response
                        error_detail = response.text.strip()
                        if error_detail:
                            logger.error(f"Error details: {error_detail}")
                            error_msg = f"{error_msg}: {error_detail}"
                            
                        response.raise_for_status()
                        
                    return {'status': 'success', 'data': response.text}
                    
            except requests.exceptions.SSLError as e:
                logger.error(f"SSL Error: {str(e)}")
                raise FlightServiceError(f"SSL Error: {str(e)}") from e
                
            except requests.exceptions.Timeout as e:
                logger.error(f"Request timed out: {str(e)}")
                raise FlightServiceError("Request timed out") from e
                
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {str(e)}")
                raise FlightServiceError("Connection error") from e
                
        except HTTPError as e:
            last_error = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    last_error = json.dumps(error_data, indent=2)
                    logger.error(f"HTTP error {e.response.status_code}:")
                    logger.error(last_error)
                except JSONDecodeError:
                    last_error = e.response.text
                    logger.error(f"HTTP error {e.response.status_code}: {last_error}")
            
            if attempt < max_retries:
                wait_time = retry_delay * attempt
                logger.warning(f"Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            raise FlightServiceError(f"API request failed after {max_retries} attempts: {last_error}") from e
            
        except RequestException as e:
            last_error = str(e)
            logger.error(f"Request failed: {last_error}", exc_info=True)
            
            if attempt < max_retries:
                wait_time = retry_delay * attempt
                logger.warning(f"Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            raise FlightServiceError(f"Request failed after {max_retries} attempts: {last_error}") from e
            
        except Exception as e:
            last_error = str(e)
            logger.error(f"Unexpected error: {last_error}", exc_info=True)
            
            if attempt < max_retries:
                wait_time = retry_delay * attempt
                logger.warning(f"Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            raise FlightServiceError(f"Unexpected error after {max_retries} attempts: {last_error}") from e
    
    # This should never be reached due to the raise in the loop
    raise FlightServiceError(f"Unexpected error in make_verteil_request: {last_error}")

def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: str = "ECONOMY",
    fare_type: str = DEFAULT_FARE_TYPE
) -> Dict[str, Any]:
    """
    Search for flights using AirShopping request
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (for round trips)
        adults: Number of adult passengers
        children: Number of child passengers
        infants: Number of infant passengers
        cabin_class: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        currency: Currency code (default: USD)
        non_stop: If True, only return non-stop flights
        fare_type: Fare type code (default: PUBL for published fares)
        
    Returns:
        Dictionary containing flight search results
    """
    logger.info("Starting flight search...")
    logger.info(f"Parameters: origin={origin}, destination={destination}, "
                f"departure_date={departure_date}, adults={adults}, "
                f"children={children}, infants={infants}, "
                f"cabin_class={cabin_class}, fare_type={fare_type}")
    
    try:
        # Log configuration values
        logger.debug("Current configuration:")
        for key in ['VERTEIL_API_BASE_URL', 'VERTEIL_OFFICE_ID', 'VERTEIL_THIRD_PARTY_ID']:
            logger.debug(f"  {key}: {current_app.config.get(key, 'Not set')}")
        
        # Determine trip type
        trip_type = "ROUND_TRIP" if return_date else "ONE_WAY"
        
        logger.info(f"Building AirShopping request for {origin} to {destination} on {departure_date}")
        logger.debug(f"Trip type: {trip_type}, Cabin: {cabin_class}, Fare type: {fare_type}")
        
        # Build the AirShopping request
        logger.info("Building AirShopping request...")
        airshopping_rq = build_airshopping_rq(
            trip_type=trip_type,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class,
            fare_type=fare_type
        )
        
        logger.debug("AirShopping request built successfully")
        logger.debug(f"Request payload: {json.dumps(airshopping_rq, indent=2)}")
        
        # Make the request to Verteil API
        logger.info("Sending request to Verteil API...")
        response = make_verteil_request(
            endpoint="/entrygate/rest/request:airShopping",
            payload=airshopping_rq,
            service_name="AirShopping"
        )
        
        logger.info("Received response from Verteil API")
        logger.debug("Raw API response:")
        logger.debug(json.dumps(response, indent=2))
        
        # Process the response
        if not response:
            raise FlightServiceError("Empty response from Verteil API")
            
        # Log the full response structure for debugging
        logger.debug("Response structure: %s", list(response.keys()))
        
        # Check for errors in response
        if "Error" in response:
            error_msgs = []
            if isinstance(response["Error"], list):
                error_msgs = [e.get("Message", "Unknown error") for e in response["Error"]]
            else:
                error_msgs = [response["Error"].get("Message", "Unknown error")]
            raise FlightServiceError(f"API error: {', '.join(error_msgs)}")
            
        if "errors" in response:
            error_msgs = [e.get("message", "Unknown error") for e in response.get("errors", [])]
            raise FlightServiceError(f"API error: {', '.join(error_msgs)}")
        
        # Extract flight offers
        flight_offers = []
        try:
            # Try different response structures
            if "OffersGroup" in response:
                offers_group = response.get("OffersGroup", {})
                airline_offers = offers_group.get("AirlineOffers", [{}])[0].get("AirlineOffer", [])
                flight_offers = [offer for offer in airline_offers if isinstance(offer, dict)]
            elif "AirShoppingRS" in response:
                flight_offers = response["AirShoppingRS"].get("OffersGroup", {}).get("AirlineOffers", [{}])[0].get("AirlineOffer", [])
                flight_offers = [offer for offer in flight_offers if isinstance(offer, dict)]
            else:
                logger.warning("Unexpected response structure. Available keys: %s", list(response.keys()))
                
            logger.info("Successfully extracted %d flight offers", len(flight_offers))
                
        except (KeyError, IndexError, AttributeError, TypeError) as e:
            logger.error("Error parsing flight offers: %s", str(e), exc_info=True)
            logger.error("Response that caused the error: %s", json.dumps(response, indent=2))
            flight_offers = []
        
        # Return structured response
        result = {
            "status": "success",
            "data": {
                "flightOffers": flight_offers,
                "searchParams": {
                    "origin": origin,
                    "destination": destination,
                    "departureDate": departure_date,
                    "returnDate": return_date,
                    "adults": adults,
                    "children": children,
                    "infants": infants,
                    "cabinClass": cabin_class
                }
            },
            "meta": {
                "count": len(flight_offers),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_flights: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to search flights: {str(e)}") from e

get_flight_offers = search_flights  # Alias for backward compatibility

def get_flight_price(
    airshopping_response: Dict[str, Any],
    offer_index: int = 0,
    currency: str = DEFAULT_CURRENCY
) -> Dict[str, Any]:
    """
    Get price for a specific flight offer using FlightPrice request
    
    Args:
        airshopping_response: The AirShopping response
        offer_index: Index of the offer to price (default: 0)
        currency: Currency code (default: USD)
        
    Returns:
        Dictionary containing pricing information
    """
    try:
        # Build FlightPrice request
        flightprice_rq = build_flightprice_rq(airshopping_response, offer_index, currency)
        
        # Make request to Verteil API
        logger.info("Sending FlightPrice request to Verteil API...")
        response = make_verteil_request("/entrygate/rest/request:flightPrice", flightprice_rq, "FlightPrice")
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {
                "offer_index": offer_index
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_flight_price: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to get flight price: {str(e)}") from e

def create_booking(
    flight_price_response: Dict[str, Any],
    passenger_details: List[Dict[str, Any]],
    payment_details: Dict[str, Any],
    contact_info: Dict[str, str]
) -> Dict[str, Any]:
    """
    Create a flight booking using OrderCreate request
    
    Args:
        flight_price_response: The FlightPrice response
        passenger_details: List of passenger details
        payment_details: Payment information
        contact_info: Contact information
        
    Returns:
        Dictionary containing booking confirmation
    """
    try:
        # Build OrderCreate request
        ordercreate_rq = build_ordercreate_rq(
            flight_price_response,
            passenger_details,
            payment_details,
            contact_info
        )
        
        # Make request to Verteil API
        logger.info("Sending OrderCreate request to Verteil API...")
        response = make_verteil_request("/entrygate/rest/request:orderCreate", ordercreate_rq, "OrderCreate")
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_booking: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to create booking: {str(e)}") from e

def get_booking_details(booking_reference: str) -> Dict[str, Any]:
    """
    Get details for a specific booking
    
    Args:
        booking_reference: The booking reference number (OrderID)
        
    Returns:
        Dictionary containing booking details with the following structure:
        {
            "status": "success" | "error",
            "data": {
                "booking_reference": str,
                "status": str,
                "passengers": List[Dict],
                "flights": List[Dict],
                "price": Dict,
                "contact_info": Dict
            },
            "meta": {
                "timestamp": str,
                "reference": str
            }
        }
    """
    try:
        # Build the request to retrieve booking details
        request = {
                "Query": {
                    "Filters": {
                    "OrderID": {
                        "Owner": "WY",
                        "Channel": "NDC",
                        "value": booking_reference
                    }
                    }
                }
            }
        
        # Make request to Verteil API
        response = make_verteil_request("/entrygate/rest/request:orderRetrieve", request)
        
        # Transform and return the response
        return {
            "status": "success",
            "data": {
                "booking_reference": booking_reference,
                "status": response.get("Response", {}).get("Order", {}).get("OrderStatus", "UNKNOWN"),
                "passengers": [
                    {
                        "first_name": pax.get("Individual", {}).get("GivenName", ""),
                        "last_name": pax.get("Individual", {}).get("Surname", ""),
                        "type": pax.get("PTC", "ADT"),
                        "passenger_id": pax.get("PaxID", "")
                    }
                    for pax in response.get("Response", {}).get("DataLists", {})
                        .get("PassengerList", {}).get("Passenger", [])
                ],
                "flights": [
                    {
                        "flight_number": f"{segment.get('MarketingCarrier', {}).get('AirlineID', '')}{segment.get('MarketingCarrier', {}).get('FlightNumber', '')}",
                        "origin": segment.get("OriginLocation", {}).get("AirportCode", ""),
                        "destination": segment.get("DestinationLocation", {}).get("AirportCode", ""),
                        "departure_time": segment.get("Departure", {}).get("Date", "") + "T" + segment.get("Departure", {}).get("Time", ""),
                        "arrival_time": segment.get("Arrival", {}).get("Date", "") + "T" + segment.get("Arrival", {}).get("Time", ""),
                        "cabin_class": segment.get("CabinType", {}).get("CabinTypeCode", ""),
                        "booking_class": segment.get("ClassOfService", {}).get("Code", "")
                    }
                    for segment in response.get("Response", {}).get("DataLists", {})
                        .get("FlightSegmentList", {}).get("FlightSegment", [])
                ],
                "price": {
                    "total_amount": response.get("Response", {}).get("DataLists", {})
                        .get("PriceList", [{}])[0].get("TotalAmount", 0),
                    "currency": response.get("Response", {}).get("DataLists", {})
                        .get("PriceList", [{}])[0].get("TotalAmount", {}).get("Code", "USD")
                },
                "contact_info": {
                    "email": response.get("Response", {}).get("DataLists", {})
                        .get("ContactInfoList", {}).get("ContactInformation", {})
                        .get("Contact", {}).get("EmailContact", {}).get("EmailAddress", ""),
                    "phone": next((phone.get("PhoneNumber", "") for phone in 
                        response.get("Response", {}).get("DataLists", {})
                        .get("ContactInfoList", {}).get("ContactInformation", {})
                        .get("Contact", {}).get("PhoneContact", []) 
                        if phone.get("Label") == "MOBILE"), "")
                }
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "reference": booking_reference
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_booking_details: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to retrieve booking details: {str(e)}") from e
    try:
        # Build OrderRetrieve request
        order_retrieve_rq = {
            "OrderRetrieveRQ": {
                "Query": {
                    "OrderID": booking_reference
                }
            }
        }
        
        # Make request to Verteil API
        response = make_verteil_request("/ndc/orderretrieve", order_retrieve_rq)
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {}
        }
        
    except Exception as e:
        logger.error(f"Error in get_booking_details: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to get booking details: {str(e)}") from e

def process_air_shopping(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process flight search request and return available flight offers.
    
    Args:
        search_criteria: Dictionary containing search parameters
        
    Returns:
        Dictionary containing flight offers and metadata
    """
    try:
        # Call the search_flights function
        return search_flights(
            origin=search_criteria['origin'],
            destination=search_criteria['destination'],
            departure_date=search_criteria['departure_date'],
            return_date=search_criteria.get('return_date'),
            adults=search_criteria.get('adults', 1),
            children=search_criteria.get('children', 0),
            infants=search_criteria.get('infants', 0),
            cabin_class=search_criteria.get('cabin_class', 'ECONOMY')
        )
        
    except FlightServiceError as e:
        logger.error(f"Error in process_air_shopping: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in process_air_shopping: {str(e)}")
        return {"error": "An unexpected error occurred while searching for flights"}

def process_flight_price(price_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process flight pricing request and return detailed pricing information.
    
    Args:
        price_request: Dictionary containing pricing request data
        
    Returns:
        Dictionary containing detailed pricing information
    """
    try:
        # Call the get_flight_price function
        return get_flight_price(
            airshopping_response=price_request['airshopping_response'],
            offer_index=price_request.get('offer_index', 0)
        )
        
    except FlightServiceError as e:
        logger.error(f"Error in process_flight_price: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in process_flight_price: {str(e)}")
        return {"error": "An unexpected error occurred while pricing the flight"}

def process_order_create(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process order creation request and return booking confirmation.
    
    Args:
        order_data: Dictionary containing order data with the following structure:
        {
            "flight_offer": Dict,  # Flight price response
            "passengers": List[Dict],  # List of passenger details
            "payment": Dict,  # Payment information
            "contact_info": Dict  # Contact information
        }
        
    Returns:
        Dictionary containing booking confirmation with the following structure:
        {
            "status": "success" | "error",
            "data": {
                "booking_reference": str,
                "status": str,
                "etickets": List[Dict],
                "amount_paid": float,
                "currency": str
            },
            "meta": {
                "timestamp": str,
                "reference": str
            }
        }
    """
    try:
        # Extract data from order_data
        flight_offer = order_data.get("flight_offer", {})
        passengers = order_data.get("passengers", [])
        payment = order_data.get("payment", {})
        contact_info = order_data.get("contact_info", {})
        
        # Validate required fields
        if not flight_offer:
            raise FlightServiceError("Missing required field: flight_offer")
        if not passengers:
            raise FlightServiceError("Missing required field: passengers")
        if not payment:
            raise FlightServiceError("Missing required field: payment")
        if not contact_info:
            raise FlightServiceError("Missing required field: contact_info")
        
        # Create the booking
        booking_response = create_booking(
            flight_price_response=flight_offer,
            passenger_details=passengers,
            payment_details=payment,
            contact_info=contact_info
        )
        
        # Extract relevant data from the response
        order_response = booking_response.get("data", {})
        order_id = order_response.get("Response", {}).get("Order", {}).get("OrderID", "")
        
        if not order_id:
            raise FlightServiceError("Failed to retrieve order ID from the booking response")
        
        # Transform the response
        return {
            "status": "success",
            "data": {
                "booking_reference": order_id,
                "status": order_response.get("Response", {}).get("Order", {}).get("OrderStatus", "CONFIRMED"),
                "etickets": [
                    {
                        "ticket_number": doc.get("TicketDocInfo", {}).get("TicketDocument", {})
                            .get("TicketDocNbr", ""),
                        "passenger_name": doc.get("PassengerReference", {}).get("PassengerID", ""),
                        "status": doc.get("TicketDocInfo", {}).get("Status", {})
                            .get("StatusCode", "ISSUED")
                    }
                    for doc in order_response.get("Response", {}).get("DataLists", {})
                        .get("TicketDocInfoList", {}).get("TicketDocInfo", [])
                ],
                "amount_paid": order_response.get("Response", {}).get("DataLists", {})
                    .get("PriceList", [{}])[0].get("TotalAmount", {}).get("value", 0),
                "currency": order_response.get("Response", {}).get("DataLists", {})
                    .get("PriceList", [{}])[0].get("TotalAmount", {}).get("Code", "USD")
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "reference": order_id
            }
        }
        
    except FlightServiceError as e:
        logger.error(f"Error in process_order_create: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        error_msg = f"Unexpected error in process_order_create: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise FlightServiceError(error_msg) from e

# Transformation functions for backward compatibility
def _transform_airshopping_rs(airshopping_rs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform AirShopping response for the frontend
    
    Args:
        airshopping_rs: Raw AirShopping response
        
    Returns:
        Transformed response for the frontend
    """
    # This is a placeholder - implement transformation as needed
    return airshopping_rs

def _transform_flightprice_rs(flightprice_rs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform FlightPrice response for the frontend
    
    Args:
        flightprice_rs: Raw FlightPrice response
        
    Returns:
        Transformed response for the frontend
    """
    # This is a placeholder - implement transformation as needed
    return flightprice_rs

def _transform_ordercreate_rs(ordercreate_rs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform OrderCreate response for the frontend
    
    Args:
        ordercreate_rs: Raw OrderCreate response
        
    Returns:
        Transformed response for the frontend
    """
    # This is a placeholder - implement transformation as needed
    return ordercreate_rs
