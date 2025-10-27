"""
OrderCreate Service - VDC API Integration for Flight Booking

Handles the final booking step in the flight booking flow:
Search → Price → Ancillaries → **OrderCreate**

Uses OrderCreateRequestBuilder to construct requests and calls VDC preOrderCreate endpoint.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from app.config import settings
from utils.auth import TokenManager
from app.builders.order_create import OrderCreateRequestBuilder

logger = logging.getLogger(__name__)


class OrderCreateService:
    """Service for creating flight bookings via VDC OrderCreate API."""
    
    def __init__(self):
        """Initialize the OrderCreate service."""
        self.base_url = settings.VDC_API_BASE_URL
        self.office_id = settings.VDC_OFFICE_ID
        self.token_manager = TokenManager.get_instance()
        self.builder = OrderCreateRequestBuilder()
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        
        logger.info("🔧 OrderCreateService initialized")
    
    async def create_booking(
        self,
        flight_price_response: Dict[str, Any],
        passengers: list[Dict[str, Any]],
        payment: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]] = None,
        servicelist_response: Optional[Dict[str, Any]] = None,
        selected_seats: Optional[list[str]] = None,
        selected_services: Optional[list[str]] = None,
        ancillary_pricing_response: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a flight booking via VDC OrderCreate API.
        
        Args:
            flight_price_response: FlightPrice response (required)
            passengers: List of passenger details (required)
            payment: Payment information (required)
            seatavailability_response: SeatAvailability response (optional)
            servicelist_response: ServiceList response (optional)
            selected_seats: List of selected seat ObjectKeys (optional)
            selected_services: List of selected service ObjectKeys (optional)
            ancillary_pricing_response: FlightPrice response for unpriced ancillaries (optional)
        
        Returns:
            Dict containing:
                - success: bool
                - booking_reference: str (if successful)
                - order_id: str (if successful)
                - raw_response: Dict (full VDC response)
                - error: str (if failed)
        
        Raises:
            ValueError: If required data is missing or invalid
            httpx.HTTPError: If API call fails
        """
        try:
            logger.info("🔥 Starting OrderCreate booking process")
            
            # Step 1: Validate required inputs
            self._validate_inputs(flight_price_response, passengers, payment)
            
            # Step 1.5: Extract airline owner from flight_price_response for ThirdpartyId header
            airline_owner = self._extract_airline_owner(flight_price_response)
            logger.info(f"🏢 Extracted airline owner: {airline_owner}")
            
            # Step 2: Build OrderCreate request using builder
            logger.info("📦 Building OrderCreate request payload")
            order_create_request = self.builder.build_request(
                flight_price_response=flight_price_response,
                passengers=passengers,
                payment=payment,
                seatavailability_response=seatavailability_response,
                servicelist_response=servicelist_response,
                selected_seats=selected_seats,
                selected_services=selected_services,
                ancillary_pricing_response=ancillary_pricing_response
            )
            
            logger.info(f"✅ OrderCreate request built successfully")
            logger.debug(f"Request payload: {order_create_request}")
            
            # Step 3: Get authentication token
            logger.info("🔐 Obtaining VDC authentication token")
            token = self.token_manager.get_token()  # Removed await - get_token is synchronous
            
            # Step 4: Build request headers (with ThirdpartyId)
            headers = self._build_headers(token, airline_owner)
            
            # Step 5: Call VDC preOrderCreate API
            logger.info("🌐 Calling VDC preOrderCreate API")
            raw_response = await self._call_vdc_api(order_create_request, headers)
            
            logger.info("✅ VDC OrderCreate API call successful")
            logger.debug(f"Raw response: {raw_response}")
            
            # Step 6: Extract booking details
            result = self._extract_booking_details(raw_response)
            
            logger.info(f"🎉 Booking created successfully - Reference: {result.get('booking_reference', 'N/A')}")
            
            return result
            
        except ValueError as e:
            logger.error(f"🔴 Validation error in OrderCreate: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "validation_error"
            }
        except httpx.HTTPError as e:
            logger.error(f"🔴 HTTP error in OrderCreate API call: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"API call failed: {str(e)}",
                "error_type": "http_error"
            }
        except Exception as e:
            logger.error(f"🔴 Unexpected error in OrderCreate: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error"
            }
    
    def _validate_inputs(
        self,
        flight_price_response: Dict[str, Any],
        passengers: list[Dict[str, Any]],
        payment: Dict[str, Any]
    ) -> None:
        """
        Validate required inputs for OrderCreate.
        
        Raises:
            ValueError: If any required input is missing or invalid
        """
        if not flight_price_response:
            raise ValueError("flight_price_response is required")
        
        if not passengers or not isinstance(passengers, list) or len(passengers) == 0:
            raise ValueError("At least one passenger is required")
        
        if not payment:
            raise ValueError("payment information is required")
        
        # Validate flight_price_response structure
        if 'PricedFlightOffers' not in flight_price_response:
            raise ValueError("Invalid flight_price_response: missing PricedFlightOffers")
        
        # Validate passengers structure
        required_passenger_fields = ['given_name', 'surname', 'email', 'phone']
        for idx, passenger in enumerate(passengers):
            for field in required_passenger_fields:
                if field not in passenger or not passenger[field]:
                    raise ValueError(f"Passenger {idx + 1}: missing required field '{field}'")
        
        # Validate payment structure
        required_payment_fields = ['card_number', 'card_type', 'card_holder_name', 'expiry_date']
        for field in required_payment_fields:
            if field not in payment or not payment[field]:
                raise ValueError(f"Payment: missing required field '{field}'")
        
        logger.info("✅ Input validation passed")
    
    def _extract_airline_owner(self, flight_price_response: Dict[str, Any]) -> str:
        """
        Extract airline owner code from FlightPrice response for ThirdpartyId header.
        
        Args:
            flight_price_response: FlightPrice response (can be transformed or raw)
            
        Returns:
            Airline owner code (e.g., "EY", "EK")
            
        Raises:
            ValueError: If airline owner cannot be extracted
        """
        try:
            # Check if this is a transformed response with raw_response field
            raw_response = flight_price_response.get("raw_response")
            if raw_response:
                logger.debug("Using raw_response from transformed FlightPrice response")
                source = raw_response
            else:
                logger.debug("Using FlightPrice response directly (assuming raw format)")
                source = flight_price_response
            
            # Try to get from PricedFlightOffers -> Owner
            priced_offers = source.get("PricedFlightOffers", {})
            if isinstance(priced_offers, dict):
                owner = priced_offers.get("Owner")
                if owner:
                    logger.debug(f"Found airline owner from PricedFlightOffers.Owner: {owner}")
                    return owner
                
                # Try to get from PricedFlightOffer list
                offer_list = priced_offers.get("PricedFlightOffer", [])
                if isinstance(offer_list, list) and len(offer_list) > 0:
                    first_offer = offer_list[0]
                    offer_id = first_offer.get("OfferID", {})
                    if isinstance(offer_id, dict):
                        owner = offer_id.get("Owner")
                        if owner:
                            logger.debug(f"Found airline owner from PricedFlightOffer[0].OfferID.Owner: {owner}")
                            return owner
            
            # If still not found, raise error
            raise ValueError("Could not extract airline owner from flight_price_response")
            
        except Exception as e:
            logger.error(f"Error extracting airline owner: {e}")
            raise ValueError(f"Failed to extract airline owner: {str(e)}")
    
    def _build_headers(self, token: str, airline_owner: str) -> Dict[str, str]:
        """
        Build request headers for VDC OrderCreate API.
        
        Args:
            token: Bearer authentication token (already includes "Bearer " prefix)
            airline_owner: Airline code for ThirdpartyId header (e.g., "EY", "EK")
        
        Returns:
            Dict of headers
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": token,  # Token already includes "Bearer " prefix
            "service": "OrderCreate",  # VDC requires this header
            "ThirdpartyId": airline_owner,  # Required by VDC API
        }
        
        # Add OfficeId if configured
        if self.office_id:
            headers["OfficeId"] = self.office_id
        
        logger.debug(f"Built headers with ThirdpartyId: {airline_owner}")
        
        return headers
    
    async def _call_vdc_api(
        self,
        request_payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Call VDC preOrderCreate API endpoint.
        
        Args:
            request_payload: OrderCreate request body
            headers: Request headers with auth token
        
        Returns:
            VDC API response as dict
        
        Raises:
            httpx.HTTPError: If API call fails
            ValueError: If response is invalid
        """
        # base_url already includes /entrygate/rest/request, just add :preOrderCreate
        endpoint = f"{self.base_url}:preOrderCreate"
        
        # Save request payload for debugging
        try:
            import json
            from pathlib import Path
            debug_dir = Path(__file__).parent.parent.parent / "tests" / "integration" / "live_test_data"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / "ordercreate_raw_request.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(request_payload, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved raw OrderCreate request to {debug_file}")
        except Exception as e:
            logger.warning(f"Failed to save debug request: {e}")
        
        logger.info(f"📡 Sending request to: {endpoint}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    endpoint,
                    json=request_payload,
                    headers=headers
                )
                
                # Log response status
                logger.info(f"📥 Response status: {response.status_code}")
                
                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()
                
                # Parse JSON response
                json_response = response.json()
                
                # Save raw response for debugging
                try:
                    import json
                    from pathlib import Path
                    debug_dir = Path(__file__).parent.parent.parent / "tests" / "integration" / "live_test_data"
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    debug_file = debug_dir / "ordercreate_raw_response.json"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        json.dump(json_response, f, indent=2, ensure_ascii=False)
                    logger.info(f"💾 Saved raw OrderCreate response to {debug_file}")
                except Exception as e:
                    logger.warning(f"Failed to save debug response: {e}")
                
                # Check for VDC errors in response
                if 'Errors' in json_response or 'Error' in json_response:
                    error_details = json_response.get('Errors') or json_response.get('Error')
                    logger.error(f"🔴 VDC API returned errors: {error_details}")
                    raise ValueError(f"VDC API error: {error_details}")
                
                return json_response
                
            except httpx.HTTPStatusError as e:
                logger.error(f"🔴 HTTP status error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.TimeoutException as e:
                logger.error(f"🔴 Request timeout: {e}")
                raise
            except httpx.RequestError as e:
                logger.error(f"🔴 Request error: {e}")
                raise
    
    def _extract_booking_details(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract booking details from VDC OrderCreate response.
        
        Args:
            raw_response: Raw VDC API response
        
        Returns:
            Dict with extracted booking details:
                - success: True
                - booking_reference: str
                - order_id: str
                - raw_response: Dict (preserved for debugging)
        """
        try:
            # VDC OrderCreate response structure varies, handle multiple formats
            
            # Try to extract booking reference (most important field)
            booking_reference = None
            order_id = None
            
            # Format 1: OrderCreateRS.Order.BookingReference
            if 'OrderCreateRS' in raw_response:
                order_create_rs = raw_response['OrderCreateRS']
                if 'Order' in order_create_rs:
                    order = order_create_rs['Order']
                    booking_reference = order.get('BookingReference', {}).get('ID', {}).get('value')
                    order_id = order.get('OrderID', {}).get('value')
            
            # Format 2: Order directly at root
            elif 'Order' in raw_response:
                order = raw_response['Order']
                booking_reference = order.get('BookingReference', {}).get('ID', {}).get('value')
                order_id = order.get('OrderID', {}).get('value')
            
            # Format 3: BookingReference directly at root
            elif 'BookingReference' in raw_response:
                booking_reference = raw_response.get('BookingReference', {}).get('ID', {}).get('value')
                order_id = raw_response.get('OrderID', {}).get('value')
            
            # If still no booking reference, try alternate paths
            if not booking_reference:
                # Some responses nest it differently
                if 'Response' in raw_response and 'Order' in raw_response['Response']:
                    order = raw_response['Response']['Order']
                    booking_reference = order.get('BookingReference', {}).get('ID', {}).get('value')
                    order_id = order.get('OrderID', {}).get('value')
            
            # Validate we got at least booking reference
            if not booking_reference:
                logger.warning("⚠️ Could not extract BookingReference from response")
                logger.debug(f"Response structure: {list(raw_response.keys())}")
            
            result = {
                "success": True,
                "booking_reference": booking_reference or "UNKNOWN",
                "order_id": order_id or "UNKNOWN",
                "raw_response": raw_response
            }
            
            logger.info(f"✅ Extracted booking details: {booking_reference}")
            
            return result
            
        except Exception as e:
            logger.error(f"🔴 Error extracting booking details: {e}", exc_info=True)
            # Return success=True anyway since API call succeeded, just extraction failed
            return {
                "success": True,
                "booking_reference": "EXTRACTION_FAILED",
                "order_id": "EXTRACTION_FAILED",
                "raw_response": raw_response,
                "extraction_error": str(e)
            }
