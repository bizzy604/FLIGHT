"""
Flight Booking Module

This module handles flight booking operations using the Verteil NDC API.
"""
import logging
from typing import Dict, Any, Optional, List
import uuid
import json

from .core import FlightService
from .decorators import async_cache, async_rate_limited
from .exceptions import FlightServiceError, ValidationError, BookingError
from .types import BookingResponse, SearchCriteria

# Import the OrderCreate request builder
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
    from build_ordercreate_rq import generate_order_create_rq
except ImportError as e:
    logger.error(f"Failed to import build_ordercreate_rq: {e}")
    generate_order_create_rq = None

logger = logging.getLogger(__name__)

class FlightBookingService(FlightService):
    """Service for handling flight booking operations."""
    
    @async_rate_limited(limit=100, window=60)
    async def create_booking(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment_info: Dict[str, Any],
        contact_info: Dict[str, str],
        request_id: Optional[str] = None,
        offer_id: Optional[str] = None,
        shopping_response_id: Optional[str] = None,
    ) -> BookingResponse:
        """
        Create a new flight booking.
        
        Args:
            flight_price_response: The FlightPrice response
            passengers: List of passenger details
            payment_info: Payment information
            contact_info: Contact information
            request_id: Optional request ID for tracking
            offer_id: Optional OfferID extracted from frontend
            shopping_response_id: Optional ShoppingResponseID extracted from frontend
            
        Returns:
            BookingResponse containing booking confirmation or error information
            
        Raises:
            ValidationError: If the request data is invalid
            BookingError: If there's an error creating the booking
        """
        try:
            # Validate input
            self._validate_booking_request(
                flight_price_response=flight_price_response,
                passengers=passengers,
                payment_info=payment_info,
                contact_info=contact_info
            )
            
            # Generate a request ID if not provided
            request_id = request_id or str(uuid.uuid4())
            
            # Build the request payload first (this will enhance the flight_price_response)
            payload = self._build_booking_payload(
                flight_price_response=flight_price_response,
                passengers=passengers,
                payment_info=payment_info,
                contact_info=contact_info,
                request_id=request_id,
                offer_id=offer_id,
                shopping_response_id=shopping_response_id
            )
            
            # Extract airline code from the enhanced flight price response for dynamic thirdPartyId
            # Try to get it from the enhanced response first, then fallback to original
            airline_code = self._extract_airline_code_from_enhanced_payload(payload, flight_price_response)
            logger.info(f"Extracted airline code '{airline_code}' for booking (ReqID: {request_id})")
            
            # Make the API request with dynamic airline code
            response = await self._make_request(
                endpoint='/entrygate/rest/request:orderCreate',
                payload=payload,
                service_name='OrderCreate',
                airline_code=airline_code,
                request_id=request_id
            )
            
            # Process and return the response
            return {
                'status': 'success',
                'data': self._process_booking_response(response),
                'request_id': request_id
            }
            
        except ValidationError as e:
            logger.error(f"Validation error in create_booking: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'request_id': request_id
            }
        except Exception as e:
            logger.error(f"Error in create_booking: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': f"Failed to create booking: {str(e)}",
                'request_id': request_id
            }
    
    def _extract_airline_code_from_enhanced_payload(self, payload: Dict[str, Any], original_flight_price_response: Dict[str, Any]) -> Optional[str]:
        """
        Extract the airline code from the enhanced payload or original flight price response.
        
        Args:
            payload: The generated OrderCreate payload
            original_flight_price_response: The original FlightPrice response
            
        Returns:
            The airline code (e.g., 'KQ', 'WY') or None if not found
        """
        try:
            # First try to extract from the payload's ShoppingResponse Owner
            shopping_response = payload.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {})
            owner = shopping_response.get('Owner')
            if owner:
                logger.info(f"Found airline code '{owner}' in OrderCreate payload ShoppingResponse.Owner")
                return owner
            
            # Fallback to the original extraction method
            return self._extract_airline_code_from_price_response(original_flight_price_response)
            
        except Exception as e:
            logger.error(f"Error extracting airline code from enhanced payload: {str(e)}", exc_info=True)
            # Fallback to original method
            return self._extract_airline_code_from_price_response(original_flight_price_response)
    
    def _extract_airline_code_from_price_response(self, flight_price_response: Dict[str, Any]) -> Optional[str]:
        """
        Extract the airline code from the flight price response for dynamic thirdPartyId.
        
        Args:
            flight_price_response: The FlightPrice response containing offer details
            
        Returns:
            The airline code (e.g., 'KQ', 'WY') or None if not found
        """
        try:
            # DEBUG: Log the structure we're trying to extract from
            logger.info(f"[DEBUG] Attempting to extract airline code from flight_price_response with keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
            
            # Handle the actual FlightPrice response structure with PricedFlightOffers
            priced_flight_offers = flight_price_response.get('PricedFlightOffers', {})
            priced_flight_offer_list = priced_flight_offers.get('PricedFlightOffer', [])
            
            # Ensure we have a list to work with
            if not isinstance(priced_flight_offer_list, list):
                priced_flight_offer_list = [priced_flight_offer_list]
            
            # Extract airline code from the first offer's OfferID Owner field
            if priced_flight_offer_list:
                first_offer = priced_flight_offer_list[0]
                offer_id = first_offer.get('OfferID', {})
                
                # Check for Owner field in OfferID
                if isinstance(offer_id, dict):
                    airline_code = offer_id.get('Owner')
                    if airline_code:
                        logger.info(f"Found airline code '{airline_code}' in FlightPrice response OfferID.Owner")
                        return airline_code
            
            # Try to extract from top-level structure (frontend might send different format)
            if 'OfferID' in flight_price_response:
                offer_id = flight_price_response.get('OfferID', {})
                if isinstance(offer_id, dict):
                    airline_code = offer_id.get('Owner')
                    if airline_code:
                        logger.info(f"Found airline code '{airline_code}' in top-level OfferID.Owner")
                        return airline_code
            
            # Try to extract from ShoppingResponseID structure
            if 'ShoppingResponseID' in flight_price_response:
                shopping_response = flight_price_response.get('ShoppingResponseID', {})
                if isinstance(shopping_response, dict):
                    airline_code = shopping_response.get('Owner')
                    if airline_code:
                        logger.info(f"Found airline code '{airline_code}' in ShoppingResponseID.Owner")
                        return airline_code
            
            # Fallback: try the old structure for backward compatibility
            flight_price_rs = flight_price_response.get('FlightPriceRS', {})
            priced_offer = flight_price_rs.get('PricedOffer', {})
            
            # Extract airline code from Owner field
            owner = priced_offer.get('Owner', {})
            if isinstance(owner, dict):
                airline_code = owner.get('value')
                if airline_code:
                    logger.info(f"Found airline code '{airline_code}' in FlightPriceRS.PricedOffer.Owner")
                    return airline_code
            
            # DEBUG: Log what we actually found in the structure
            logger.warning(f"Could not extract airline code from FlightPrice response. Available top-level keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
            if isinstance(flight_price_response, dict) and flight_price_response:
                logger.warning(f"[DEBUG] Sample of flight_price_response structure: {json.dumps(dict(list(flight_price_response.items())[:3]), indent=2, default=str)}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting airline code from FlightPrice response: {str(e)}", exc_info=True)
            return None
    
    async def get_booking_details(
        self,
        booking_reference: str,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve details for a specific booking.
        
        Args:
            booking_reference: The booking reference number
            request_id: Optional request ID for tracking
            
        Returns:
            Dictionary containing booking details
            
        Raises:
            ValidationError: If the booking reference is invalid
            BookingError: If there's an error retrieving the booking
        """
        try:
            if not booking_reference:
                raise ValidationError("Booking reference is required")
                
            # Generate a request ID if not provided
            request_id = request_id or str(uuid.uuid4())
            
            # Build the request payload
            payload = {
                'OrderID': booking_reference,
                'RequestID': request_id
            }
            
            # Make the API request
            response = await self._make_request(
                endpoint='orderretrieve',
                payload=payload,
                service_name='OrderRetrieve',
                request_id=request_id
            )
            
            # Process and return the response
            return {
                'status': 'success',
                'data': self._process_retrieve_response(response),
                'request_id': request_id
            }
            
        except ValidationError as e:
            logger.error(f"Validation error in get_booking_details: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'request_id': request_id
            }
        except Exception as e:
            logger.error(f"Error in get_booking_details: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': f"Failed to retrieve booking: {str(e)}",
                'request_id': request_id
            }
    
    def _validate_booking_request(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment_info: Dict[str, Any],
        contact_info: Dict[str, str]
    ) -> None:
        """
        Validate the booking request data.
        
        Args:
            flight_price_response: The FlightPrice response
            passengers: List of passenger details
            payment_info: Payment information
            contact_info: Contact information
            
        Raises:
            ValidationError: If any required data is missing or invalid
        """
        if not flight_price_response:
            raise ValidationError("Flight price response is required")
            
        if not passengers:
            raise ValidationError("At least one passenger is required")
            
        # Validate each passenger's required fields
        for i, passenger in enumerate(passengers):
            self._validate_passenger_data(passenger, i + 1)
            
        if not payment_info:
            raise ValidationError("Payment information is required")
            
        if not contact_info or not contact_info.get('email'):
            raise ValidationError("Contact information with email is required")
            
        # Validate contact info fields
        self._validate_contact_info(contact_info)
    
    def _validate_passenger_data(self, passenger: Dict[str, Any], passenger_number: int) -> None:
        """
        Validate individual passenger data for completeness.
        
        Args:
            passenger: Passenger data dictionary
            passenger_number: Passenger number for error messages
            
        Raises:
            ValidationError: If required passenger data is missing or invalid
        """
        required_fields = {
            'type': 'Passenger type',
            'title': 'Title',
            'firstName': 'First name',
            'lastName': 'Last name',
            'gender': 'Gender',
            'nationality': 'Nationality'
        }
        
        missing_fields = []
        
        # Check basic required fields
        for field, field_name in required_fields.items():
            if not passenger.get(field) or str(passenger.get(field)).strip() == '':
                missing_fields.append(field_name)
        
        # Validate date of birth
        dob = passenger.get('dob', {})
        if not dob or not all([dob.get('year'), dob.get('month'), dob.get('day')]):
            missing_fields.append('Date of birth')
        else:
            # Validate date format
            try:
                year = int(dob.get('year', 0))
                month = int(dob.get('month', 0))
                day = int(dob.get('day', 0))
                
                if year < 1900 or year > 2024:
                    missing_fields.append('Valid birth year')
                if month < 1 or month > 12:
                    missing_fields.append('Valid birth month')
                if day < 1 or day > 31:
                    missing_fields.append('Valid birth day')
            except (ValueError, TypeError):
                missing_fields.append('Valid date of birth format')
        
        # Validate travel document for adults and children
        passenger_type = passenger.get('type', '').lower()
        if passenger_type in ['adult', 'child']:
            if not passenger.get('documentType'):
                missing_fields.append('Document type')
            if not passenger.get('documentNumber') or str(passenger.get('documentNumber')).strip() == '':
                missing_fields.append('Document number')
            
            # Validate document expiry date
            expiry_date = passenger.get('expiryDate', {})
            if not expiry_date or not all([expiry_date.get('year'), expiry_date.get('month'), expiry_date.get('day')]):
                missing_fields.append('Document expiry date')
            else:
                try:
                    year = int(expiry_date.get('year', 0))
                    month = int(expiry_date.get('month', 0))
                    day = int(expiry_date.get('day', 0))
                    
                    if year < 2024 or year > 2040:
                        missing_fields.append('Valid expiry year')
                    if month < 1 or month > 12:
                        missing_fields.append('Valid expiry month')
                    if day < 1 or day > 31:
                        missing_fields.append('Valid expiry day')
                except (ValueError, TypeError):
                    missing_fields.append('Valid expiry date format')
            
            if not passenger.get('issuingCountry') or str(passenger.get('issuingCountry')).strip() == '':
                missing_fields.append('Document issuing country')
        
        # Validate passenger type-specific requirements
        if passenger_type == 'infant':
            # Infants typically don't need separate documents but need valid birth date
            pass
        elif passenger_type not in ['adult', 'child', 'infant']:
            missing_fields.append('Valid passenger type (adult, child, or infant)')
        
        if missing_fields:
            error_msg = f"Passenger {passenger_number} is missing required fields: {', '.join(missing_fields)}"
            raise ValidationError(error_msg)
    
    def _validate_contact_info(self, contact_info: Dict[str, str]) -> None:
        """
        Validate contact information completeness.
        
        Args:
            contact_info: Contact information dictionary
            
        Raises:
            ValidationError: If required contact information is missing or invalid
        """
        email = contact_info.get('email', '').strip()
        phone = contact_info.get('phone', '').strip()
        phone_country_code = contact_info.get('phoneCountryCode', '').strip()
        street = contact_info.get('street', '').strip()
        postal_code = contact_info.get('postalCode', '').strip()
        city = contact_info.get('city', '').strip()
        country_code = contact_info.get('countryCode', '').strip()
        
        # Email validation
        if not email:
            raise ValidationError("Email address is required")
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValidationError("Valid email address is required")
        
        # Phone validation
        if not phone:
            raise ValidationError("Phone number is required")
        
        if not phone_country_code:
            raise ValidationError("Phone country code is required")
        
        # Basic phone validation (should contain only digits, spaces, +, -, (, ))
        import re
        if not re.match(r'^[\d\s\+\-\(\)]+$', phone):
            raise ValidationError("Valid phone number is required")
        
        # Address validation
        if not street:
            raise ValidationError("Street address is required")
        
        if not city:
            raise ValidationError("City is required")
        
        if not postal_code:
            raise ValidationError("Postal code is required")
        
        if not country_code:
            raise ValidationError("Country is required")
        
        # Validate country code format (should be 2-letter ISO code)
        if len(country_code) != 2 or not country_code.isalpha():
            raise ValidationError("Valid country code is required (2-letter ISO format)")
    
    def _build_booking_payload(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment_info: Dict[str, Any],
        contact_info: Dict[str, str],
        request_id: str,
        offer_id: Optional[str] = None,
        shopping_response_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build the OrderCreate request payload using the request builder.
        
        Args:
            flight_price_response: The FlightPrice response
            passengers: List of passenger details
            payment_info: Payment information
            contact_info: Contact information
            request_id: Request ID for tracking
            offer_id: Optional OfferID extracted from frontend
            shopping_response_id: Optional ShoppingResponseID extracted from frontend
            
        Returns:
            Dictionary containing the request payload
        """
        try:
            if generate_order_create_rq is None:
                # Fallback to manual payload construction if import failed
                logger.warning("Using fallback payload construction for OrderCreate")
                return self._build_fallback_payload(
                    flight_price_response, passengers, payment_info, contact_info, request_id
                )
            
            logger.info(
                f"Building OrderCreate payload using request builder for request {request_id}"
            )
            
            # DEBUG: Log raw input data received by booking service
            import json
            logger.info(f"[DEBUG] Raw flight_price_response received by booking service (ReqID: {request_id}): {json.dumps(flight_price_response, indent=2, default=str)}")
            logger.info(f"[DEBUG] Raw passengers received by booking service (ReqID: {request_id}): {json.dumps(passengers, indent=2, default=str)}")
            logger.info(f"[DEBUG] Raw payment_info received by booking service (ReqID: {request_id}): {json.dumps(payment_info, indent=2, default=str)}")
            logger.info(f"[DEBUG] Raw contact_info received by booking service (ReqID: {request_id}): {json.dumps(contact_info, indent=2, default=str)}")
            logger.info(f"[DEBUG] Extracted offer_id from frontend (ReqID: {request_id}): {offer_id}")
            logger.info(f"[DEBUG] Extracted shopping_response_id from frontend (ReqID: {request_id}): {shopping_response_id}")
            
            # Transform frontend passenger data to match the expected format for build_ordercreate_rq
            transformed_passengers = []
            for passenger in passengers:
                # Map frontend passenger type to expected format
                pax_type = passenger.get('type', 'adult')
                ptc_mapping = {
                    'adult': 'ADT',
                    'child': 'CHD', 
                    'infant': 'INF'
                }
                ptc = ptc_mapping.get(pax_type, 'ADT')
                
                # Format birth date from frontend dob object
                dob = passenger.get('dob', {})
                birth_date = None
                if dob and dob.get('year') and dob.get('month') and dob.get('day'):
                    birth_date = f"{dob['year']}-{dob['month'].zfill(2)}-{dob['day'].zfill(2)}"
                
                # Map title from frontend
                title_mapping = {
                    'mr': 'Mr',
                    'ms': 'Ms', 
                    'mrs': 'Mrs',
                    'miss': 'Miss',
                    'dr': 'Dr'
                }
                title = title_mapping.get(passenger.get('title', '').lower(), 
                                        "Mr" if passenger.get('gender', '').lower() == 'male' else "Ms")
                
                # Transform to the structure expected by build_ordercreate_rq
                transformed_passenger = {
                    'PTC': ptc,  # Direct value, not nested
                    'Name': {
                        'Title': title,
                        'Given': [passenger.get('firstName', '')],  # List format expected
                        'Surname': passenger.get('lastName', '')
                    },
                    'Gender': passenger.get('gender', '').capitalize(),
                    'BirthDate': birth_date
                }
                
                # Add document information if available
                if passenger.get('documentNumber'):
                    # Format expiry date from frontend expiryDate object
                    expiry = passenger.get('expiryDate', {})
                    expiry_date = None
                    if expiry and expiry.get('year') and expiry.get('month') and expiry.get('day'):
                        expiry_date = f"{expiry['year']}-{expiry['month'].zfill(2)}-{expiry['day'].zfill(2)}"
                    
                    # Map document type
                    doc_type_mapping = {
                        'passport': 'PT',
                        'national_id': 'NI',
                        'id': 'ID'
                    }
                    doc_type = doc_type_mapping.get(passenger.get('documentType', 'passport').lower(), 'PT')
                    
                    transformed_passenger['Documents'] = [{
                        'Type': doc_type,
                        'ID': passenger.get('documentNumber'),
                        'DateOfExpiration': expiry_date,
                        'CountryOfIssuance': passenger.get('issuingCountry', '')
                    }]
                
                # Add contact info to first passenger
                if len(transformed_passengers) == 0:
                    # Build comprehensive contact structure for NDC API
                    contact_entry = {}
                    
                    # Phone Contact with country code and application
                    if contact_info.get('phone') and contact_info.get('phoneCountryCode'):
                        contact_entry['PhoneContact'] = {
                            'Number': [{
                                'CountryCode': contact_info.get('phoneCountryCode'),
                                'value': contact_info.get('phone')
                            }],
                            'Application': 'Home'
                        }
                    
                    # Email Contact with proper Address structure
                    if contact_info.get('email'):
                        contact_entry['EmailContact'] = {
                            'Address': {
                                'value': contact_info.get('email')
                            }
                        }
                    
                    # Address Contact with complete address information
                    if (contact_info.get('street') and contact_info.get('city') and 
                        contact_info.get('postalCode') and contact_info.get('countryCode')):
                        contact_entry['AddressContact'] = {
                            'Street': [contact_info.get('street')],
                            'PostalCode': contact_info.get('postalCode'),
                            'CityName': contact_info.get('city'),
                            'CountryCode': {
                                'value': contact_info.get('countryCode')
                            }
                        }
                    
                    # Only add Contacts if we have at least one contact method
                    if contact_entry:
                        transformed_passenger['Contacts'] = {
                            'Contact': [contact_entry]
                        }
                
                # DEBUG: Log each transformed passenger
                logger.info(f"[DEBUG] Individual transformed passenger (ReqID: {request_id}): {json.dumps(transformed_passenger, indent=2, default=str)}")
                
                transformed_passengers.append(transformed_passenger)
            
            # Transform payment info to match expected format
            payment_method = payment_info.get('payment_method', 'PaymentCard')
            
            # Map payment method values to what build_ordercreate_rq expects
            method_type_mapping = {
                'CASH': 'CASH',
                'CREDIT_CARD': 'PAYMENTCARD',
                'PAYMENTCARD': 'PAYMENTCARD',
                'PaymentCard': 'PAYMENTCARD',
                'EASYPAY': 'EASYPAY',
                'OTHER': 'OTHER'
            }
            
            mapped_method_type = method_type_mapping.get(payment_method, 'CASH')
            
            transformed_payment = {
                'MethodType': mapped_method_type,
                'currency': payment_info.get('currency', 'USD'),
                'Details': {}
            }
            
            if mapped_method_type == 'PAYMENTCARD':
                transformed_payment['Details'].update({
                    'CardNumberToken': payment_info.get('CardNumberToken', payment_info.get('card_number')),
                    'CardType': payment_info.get('CardType', payment_info.get('card_type', 'VI')),
                    'CardHolderName': {
                        'value': payment_info.get('CardHolderName', payment_info.get('cardholder_name', '')),
                        'refs': []
                    },
                    'EffectiveExpireDate': {
                        'Expiration': payment_info.get('EffectiveExpireDate', {}).get('Expiration', payment_info.get('expiry_date', '')),
                        'Effective': payment_info.get('EffectiveExpireDate', {}).get('Effective')
                    },
                    'CardCode': payment_info.get('CardCode', payment_info.get('cvv', '')),
                    'ProductTypeCode': payment_info.get('ProductTypeCode', payment_info.get('product_type_code', ''))
                })
            elif mapped_method_type == 'CASH':
                transformed_payment['Details']['CashInd'] = payment_info.get('CashInd', True)
            elif mapped_method_type == 'EASYPAY':
                 transformed_payment['Details'].update({
                     'AccountNumber': payment_info.get('AccountNumber', payment_info.get('account_number')),
                     'ExpirationDate': payment_info.get('ExpirationDate', payment_info.get('expiration_date'))
                 })
            elif mapped_method_type == 'OTHER':
                transformed_payment['Details']['Remarks'] = payment_info.get('remarks', [])
            
            # Enhance flight_price_response with extracted IDs if available
            enhanced_flight_price_response = flight_price_response.copy()
            
            # If we have extracted IDs from frontend, inject them into the response structure
            # to ensure build_ordercreate_rq can find them reliably
            if offer_id or shopping_response_id:
                logger.info(f"[DEBUG] Enhancing flight_price_response with extracted IDs (ReqID: {request_id})")
                
                # Ensure we have the right structure for the IDs
                if offer_id:
                    # Inject OfferID into PricedFlightOffers structure
                    if 'PricedFlightOffers' not in enhanced_flight_price_response:
                        enhanced_flight_price_response['PricedFlightOffers'] = {}
                    if 'PricedFlightOffer' not in enhanced_flight_price_response['PricedFlightOffers']:
                        enhanced_flight_price_response['PricedFlightOffers']['PricedFlightOffer'] = [{}]
                    
                    enhanced_flight_price_response['PricedFlightOffers']['PricedFlightOffer'][0]['OfferID'] = {
                        'value': offer_id,
                        'Owner': enhanced_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferID', {}).get('Owner', 'Unknown'),
                        'Channel': enhanced_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferID', {}).get('Channel', 'Unknown')
                    }
                    logger.info(f"[DEBUG] Injected OfferID: {offer_id} (ReqID: {request_id})")
                
                if shopping_response_id:
                    # Inject ShoppingResponseID
                    enhanced_flight_price_response['ShoppingResponseID'] = {
                        'ResponseID': {'value': shopping_response_id}
                    }
                    logger.info(f"[DEBUG] Injected ShoppingResponseID: {shopping_response_id} (ReqID: {request_id})")
            
            # DEBUG: Log transformed data before sending to payload builder
            logger.info(f"[DEBUG] Transformed passengers data (ReqID: {request_id}): {json.dumps(transformed_passengers, indent=2, default=str)}")
            logger.info(f"[DEBUG] Transformed payment data (ReqID: {request_id}): {json.dumps(transformed_payment, indent=2, default=str)}")
            logger.info(f"[DEBUG] Enhanced flight price response being sent to payload builder (ReqID: {request_id}): {json.dumps(enhanced_flight_price_response, indent=2, default=str)}")
            
            # Use the request builder to generate the payload
            payload = generate_order_create_rq(
                flight_price_response=enhanced_flight_price_response,
                passengers_data=transformed_passengers,
                payment_input_info=transformed_payment
            )
            
            # DEBUG: Log final payload generated by request builder
            logger.info(f"[DEBUG] Final OrderCreate payload generated (ReqID: {request_id}): {json.dumps(payload, indent=2, default=str)}")
            
            logger.info(f"Successfully generated OrderCreate payload using request builder")
            return payload
            
        except Exception as e:
            logger.error(f"Error using OrderCreate request builder: {e}")
            # Fallback to manual construction
            return self._build_fallback_payload(
                flight_price_response, passengers, payment_info, contact_info, request_id
            )
    
    def _build_fallback_payload(
        self,
        flight_price_response: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment_info: Dict[str, Any],
        contact_info: Dict[str, str],
        request_id: str
    ) -> Dict[str, Any]:
        """
        Fallback method to build OrderCreate payload manually.
        
        Args:
            flight_price_response: The FlightPrice response
            passengers: List of passenger details
            payment_info: Payment information
            contact_info: Contact information
            request_id: Request ID for tracking
            
        Returns:
            Dictionary containing the request payload
        """
        # Extract ShoppingResponseID - check multiple possible paths
        shopping_response_id = None
        
        # Log the structure we're working with
        logger.info(f"[DEBUG] Flight price response structure keys: {list(flight_price_response.keys())}")
        
        # First try the deep frontend nested structure: data.raw_response.data.raw_response
        if ('data' in flight_price_response and 
            'raw_response' in flight_price_response['data'] and 
            'data' in flight_price_response['data']['raw_response'] and 
            'raw_response' in flight_price_response['data']['raw_response']['data']):
            raw_response = flight_price_response['data']['raw_response']['data']['raw_response']
            logger.info(f"[DEBUG] Found data.raw_response.data.raw_response structure, keys: {list(raw_response.keys())}")
            
            # Try direct ShoppingResponseID in deep raw_response
            if 'ShoppingResponseID' in raw_response:
                shopping_response_id_node = raw_response['ShoppingResponseID']
                if isinstance(shopping_response_id_node, dict) and 'ResponseID' in shopping_response_id_node:
                    shopping_response_id = shopping_response_id_node['ResponseID'].get('value')
                else:
                    shopping_response_id = shopping_response_id_node
                logger.info(f"[DEBUG] Found ShoppingResponseID in data.raw_response.data.raw_response: {shopping_response_id}")
        
        # Second try the frontend nested structure: data.raw_response
        elif 'data' in flight_price_response and 'raw_response' in flight_price_response['data']:
            raw_response = flight_price_response['data']['raw_response']
            logger.info(f"[DEBUG] Found data.raw_response structure, keys: {list(raw_response.keys())}")
            
            # Try direct ShoppingResponseID in raw_response
            if 'ShoppingResponseID' in raw_response:
                shopping_response_id_node = raw_response['ShoppingResponseID']
                if isinstance(shopping_response_id_node, dict) and 'ResponseID' in shopping_response_id_node:
                    shopping_response_id = shopping_response_id_node['ResponseID'].get('value')
                else:
                    shopping_response_id = shopping_response_id_node
                logger.info(f"[DEBUG] Found ShoppingResponseID in data.raw_response: {shopping_response_id}")
        
        # Third try: check if raw_response is at top level
        if not shopping_response_id and 'raw_response' in flight_price_response:
            raw_response = flight_price_response['raw_response']
            logger.info(f"[DEBUG] Found top-level raw_response structure, keys: {list(raw_response.keys())}")
            
            if 'ShoppingResponseID' in raw_response:
                shopping_response_id_node = raw_response['ShoppingResponseID']
                if isinstance(shopping_response_id_node, dict) and 'ResponseID' in shopping_response_id_node:
                    shopping_response_id = shopping_response_id_node['ResponseID'].get('value')
                else:
                    shopping_response_id = shopping_response_id_node
                logger.info(f"[DEBUG] Found ShoppingResponseID in raw_response: {shopping_response_id}")
        
        # Fourth try: direct fields sent from frontend
        if not shopping_response_id and 'ShoppingResponseID' in flight_price_response:
            shopping_response_id = flight_price_response['ShoppingResponseID']
            logger.info(f"[DEBUG] Found ShoppingResponseID in direct field: {shopping_response_id}")
        
        # Fifth try: nested FlightPriceRS structure
        if not shopping_response_id:
            shopping_response_id_node = flight_price_response.get('FlightPriceRS', {}).get('ShoppingResponseID', {})
            shopping_response_id = shopping_response_id_node.get('ResponseID', {}).get('value')
            if shopping_response_id:
                logger.info(f"[DEBUG] Found ShoppingResponseID in FlightPriceRS structure: {shopping_response_id}")
        
        # Extract OfferID - check multiple possible paths
        offer_id = None
        
        # First try the deep frontend nested structure: data.raw_response.data.raw_response
        if ('data' in flight_price_response and 
            'raw_response' in flight_price_response['data'] and 
            'data' in flight_price_response['data']['raw_response'] and 
            'raw_response' in flight_price_response['data']['raw_response']['data']):
            raw_response = flight_price_response['data']['raw_response']['data']['raw_response']
            
            # Try PricedFlightOffers in deep raw_response
            priced_offers = raw_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                offer_id_node = priced_offers[0].get('OfferID', {})
                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                    offer_id = offer_id_node['value']
                else:
                    offer_id = offer_id_node
                logger.info(f"[DEBUG] Found OfferID in data.raw_response.data.raw_response.PricedFlightOffers: {offer_id}")
        
        # Second try the frontend nested structure: data.raw_response
        elif 'data' in flight_price_response and 'raw_response' in flight_price_response['data']:
            raw_response = flight_price_response['data']['raw_response']
            
            # Try PricedFlightOffers in raw_response
            priced_offers = raw_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                offer_id_node = priced_offers[0].get('OfferID', {})
                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                    offer_id = offer_id_node['value']
                else:
                    offer_id = offer_id_node
                logger.info(f"[DEBUG] Found OfferID in data.raw_response.PricedFlightOffers: {offer_id}")
        
        # Third try: check if raw_response is at top level
        if not offer_id and 'raw_response' in flight_price_response:
            raw_response = flight_price_response['raw_response']
            
            priced_offers = raw_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                offer_id_node = priced_offers[0].get('OfferID', {})
                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                    offer_id = offer_id_node['value']
                else:
                    offer_id = offer_id_node
                logger.info(f"[DEBUG] Found OfferID in raw_response.PricedFlightOffers: {offer_id}")
        
        # Fourth try: direct field sent from frontend
        if not offer_id and 'OfferID' in flight_price_response:
            offer_id = flight_price_response['OfferID']
            logger.info(f"[DEBUG] Found OfferID in direct field: {offer_id}")
        
        # Fifth try: nested PricedFlightOffers structure
        if not offer_id:
            priced_offers = flight_price_response.get('FlightPriceRS', {}).get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                offer_id = priced_offers[0].get('OfferID', {}).get('value')
                if offer_id:
                    logger.info(f"[DEBUG] Found OfferID in PricedFlightOffers structure: {offer_id}")
        
        # Log final extracted values
        logger.info(f"[DEBUG] Final extracted ShoppingResponseID: {shopping_response_id}")
        logger.info(f"[DEBUG] Final extracted OfferID: {offer_id}")
        
        payload = {
            'ShoppingResponseID': shopping_response_id,
            'SelectedOffer': {
                'OfferID': offer_id,
                'OfferItemIDs': [item['id'] for item in flight_price_response.get('offer_items', [])]
            },
            'Passengers': [],
            'PaymentInfo': {
                'PaymentMethod': payment_info.get('payment_method', 'CREDIT_CARD'),
                'CardInfo': {
                    'CardType': payment_info.get('card_type'),
                    'CardNumber': payment_info.get('card_number'),
                    'ExpiryDate': payment_info.get('expiry_date'),
                    'CVV': payment_info.get('cvv'),
                    'CardHolderName': payment_info.get('card_holder_name')
                }
            },
            'ContactInfo': {
                'Email': contact_info.get('email'),
                'Phone': contact_info.get('phone')
            },
            'RequestID': request_id
        }
        
        # Add passenger details
        for i, passenger in enumerate(passengers, 1):
            payload['Passengers'].append({
                'PassengerID': f'PAX{i}',
                'Type': passenger.get('type', 'ADT'),
                'Title': passenger.get('title'),
                'FirstName': passenger.get('first_name'),
                'LastName': passenger.get('last_name'),
                'DateOfBirth': passenger.get('date_of_birth'),
                'Gender': passenger.get('gender'),
                'PassportNumber': passenger.get('passport_number'),
                'PassportExpiry': passenger.get('passport_expiry'),
                'Nationality': passenger.get('nationality')
            })
        
        return payload
    
    def _extract_time_from_datetime(self, datetime_str: str) -> str:
        """Extract time from datetime string."""
        if not datetime_str or datetime_str == 'N/A':
            return 'N/A'
        try:
            # Handle various datetime formats
            if 'T' in datetime_str:
                time_part = datetime_str.split('T')[1]
                if '+' in time_part:
                    time_part = time_part.split('+')[0]
                if 'Z' in time_part:
                    time_part = time_part.replace('Z', '')
                return time_part[:5]  # Return HH:MM format
            return datetime_str
        except Exception:
            return 'N/A'
    
    def _extract_date_from_datetime(self, datetime_str: str) -> str:
        """Extract date from datetime string."""
        if not datetime_str or datetime_str == 'N/A':
            return 'N/A'
        try:
            if 'T' in datetime_str:
                return datetime_str.split('T')[0]
            return datetime_str
        except Exception:
            return 'N/A'
    
    def _format_full_date(self, datetime_str: str) -> str:
        """Format full date for display."""
        if not datetime_str or datetime_str == 'N/A':
            return 'N/A'
        try:
            from datetime import datetime
            if 'T' in datetime_str:
                date_part = datetime_str.split('T')[0]
                dt = datetime.strptime(date_part, '%Y-%m-%d')
                return dt.strftime('%A, %B %d, %Y')
            return datetime_str
        except Exception:
            return datetime_str
    
    def _get_airport_name(self, airport_code: str) -> str:
        """Get full airport name from airport code."""
        # Airport data dictionary - this should be expanded with real data
        airport_names = {
            'JFK': 'John F. Kennedy International Airport',
            'LAX': 'Los Angeles International Airport', 
            'LHR': 'London Heathrow Airport',
            'CDG': 'Charles de Gaulle Airport',
            'DXB': 'Dubai International Airport',
            'SIN': 'Singapore Changi Airport',
            'NRT': 'Narita International Airport',
            'FRA': 'Frankfurt Airport',
            'AMS': 'Amsterdam Airport Schiphol',
            'MAD': 'Madrid-Barajas Airport',
            'HND': 'Tokyo Haneda Airport',
            'PEK': 'Beijing Capital International Airport',
            'ICN': 'Incheon International Airport',
            'BKK': 'Suvarnabhumi Airport',
            'SYD': 'Sydney Airport',
            'MEL': 'Melbourne Airport',
            'MUC': 'Munich Airport',
            'FCO': 'Leonardo da Vinci International Airport',
            'BCN': 'Barcelona–El Prat Airport',
            'IST': 'Istanbul Airport',
            'DOH': 'Hamad International Airport',
            'AUH': 'Abu Dhabi International Airport',
            'KUL': 'Kuala Lumpur International Airport',
            'CGK': 'Soekarno–Hatta International Airport',
            'DEL': 'Indira Gandhi International Airport',
            'BOM': 'Chhatrapati Shivaji Maharaj International Airport',
            'GRU': 'São Paulo/Guarulhos International Airport',
            'YYZ': 'Toronto Pearson International Airport',
            'YVR': 'Vancouver International Airport',
            'ORD': "Chicago O'Hare International Airport"
        }
        return airport_names.get(airport_code, airport_code)
    
    def _get_city_from_airport(self, airport_code: str) -> str:
        """Get city name from airport code."""
        # Airport to city mapping - this should be expanded with real data
        airport_cities = {
            'JFK': 'New York',
            'LAX': 'Los Angeles',
            'LHR': 'London',
            'CDG': 'Paris',
            'DXB': 'Dubai',
            'SIN': 'Singapore',
            'NRT': 'Tokyo',
            'FRA': 'Frankfurt',
            'AMS': 'Amsterdam',
            'MAD': 'Madrid'
        }
        return airport_cities.get(airport_code, airport_code)
    
    def _get_airline_logo(self, airline_code: str) -> str:
        """Get airline logo URL from airline code."""
        try:
            import sys
            import os
            # Add the Backend directory to the path
            backend_path = os.path.join(os.path.dirname(__file__), '..', '..')
            if backend_path not in sys.path:
                sys.path.append(backend_path)
            
            from utils.data_transformer import _get_airline_logo_url
            
            logo_url = _get_airline_logo_url(airline_code)
            if logo_url:
                return logo_url
        except ImportError:
            pass
        
        # Fallback to default if no logo available or import failed
        return '/images/airlines/default.png'
    
    def _calculate_duration(self, departure_datetime: str, arrival_datetime: str) -> str:
        """Calculate flight duration from departure and arrival times."""
        try:
            from datetime import datetime
            if not departure_datetime or not arrival_datetime:
                return 'N/A'
            
            # Parse datetime strings
            dep_dt = datetime.fromisoformat(departure_datetime.replace('Z', '+00:00'))
            arr_dt = datetime.fromisoformat(arrival_datetime.replace('Z', '+00:00'))
            
            # Calculate duration
            duration = arr_dt - dep_dt
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            return f'{hours}h {minutes}m'
        except Exception:
            return 'N/A'
    
    def _calculate_boarding_time(self, departure_time: str) -> str:
        """Calculate boarding time (typically 30 minutes before departure)."""
        try:
            from datetime import datetime, timedelta
            if not departure_time or departure_time == 'N/A':
                return 'N/A'
            
            # Parse time and subtract 30 minutes
            if 'T' in departure_time:
                dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
                boarding_dt = dt - timedelta(minutes=30)
                return boarding_dt.strftime('%H:%M')
            return 'N/A'
        except Exception:
            return 'N/A'
    
    def _extract_flight_segment_new_contract(self, flights: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract flight segment according to the new data contract structure."""
        if not flights:
            return None
        
        flight = flights[0]  # Take the first flight
        
        # Extract departure and arrival info
        departure_info = flight.get('Departure', {})
        arrival_info = flight.get('Arrival', {})
        
        departure_datetime = f"{departure_info.get('Date', '')}"
        if departure_info.get('Time'):
            departure_datetime += f"T{departure_info.get('Time')}"
        
        arrival_datetime = f"{arrival_info.get('Date', '')}"
        if arrival_info.get('Time'):
            arrival_datetime += f"T{arrival_info.get('Time')}"
        
        departure_airport_code = departure_info.get('AirportCode', {}).get('value', 'N/A')
        arrival_airport_code = arrival_info.get('AirportCode', {}).get('value', 'N/A')
        
        airline_info = flight.get('MarketingCarrier', {})
        airline_code = airline_info.get('AirlineID', {}).get('value', 'N/A')
        flight_number = airline_info.get('FlightNumber', {}).get('value', 'N/A')
        
        return {
            'departure': {
                'city': self._get_city_from_airport(departure_airport_code),
                'airport': f"{departure_airport_code} - {self._get_airport_name(departure_airport_code)}",
                'code': departure_airport_code,
                'time': self._extract_time_from_datetime(departure_datetime),
                'fullDate': departure_datetime,
                'terminal': departure_info.get('Terminal', {}).get('Name')
            },
            'arrival': {
                'city': self._get_city_from_airport(arrival_airport_code),
                'airport': f"{arrival_airport_code} - {self._get_airport_name(arrival_airport_code)}",
                'code': arrival_airport_code,
                'time': self._extract_time_from_datetime(arrival_datetime),
                'fullDate': arrival_datetime,
                'terminal': arrival_info.get('Terminal', {}).get('Name')
            },
            'airline': {
                'name': airline_info.get('Name', 'Unknown Airline'),
                'code': airline_code,
                'flightNumber': f"{airline_code}{flight_number}",
                'logo': self._get_airline_logo(airline_code)
            },
            'duration': self._calculate_duration(departure_datetime, arrival_datetime),
            'aircraft': {
                'type': flight.get('Equipment', {}).get('Name', 'Unknown'),
                'model': flight.get('Equipment', {}).get('Name', 'Unknown')
            }
        }
    
    def _extract_passengers_new_contract(self, passengers_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract passenger details according to the new data contract structure."""
        passengers = []
        
        for i, passenger in enumerate(passengers_data):
            name_info = passenger.get('Name', {})
            
            # Handle different name structures
            given_name = ''
            surname = ''
            
            if isinstance(name_info.get('Given'), list):
                given_name = ' '.join([g.get('value', '') for g in name_info.get('Given', [])])
            elif isinstance(name_info.get('Given'), dict):
                given_name = name_info.get('Given', {}).get('value', '')
            else:
                given_name = str(name_info.get('Given', ''))
            
            if isinstance(name_info.get('Surname'), dict):
                surname = name_info.get('Surname', {}).get('value', '')
            else:
                surname = str(name_info.get('Surname', ''))
            
            # Handle PTC (passenger type code)
            ptc = passenger.get('PTC', 'ADT')
            if isinstance(ptc, dict):
                ptc = ptc.get('value', 'ADT')
            
            # Map PTC to frontend type
            type_mapping = {'ADT': 'adult', 'CHD': 'child', 'INF': 'infant'}
            passenger_type = type_mapping.get(ptc, 'adult')
            
            # Handle birthdate
            birth_date = passenger.get('BirthDate')
            if isinstance(birth_date, dict):
                birth_date = birth_date.get('value')
            
            # Handle document information
            identity_doc = passenger.get('IdentityDocument', {})
            doc_number = identity_doc.get('IdentityDocumentNumber', '')
            doc_type = identity_doc.get('IdentityDocumentType', 'passport')
            doc_expiry = identity_doc.get('ExpiryDate')
            
            if isinstance(doc_expiry, dict):
                doc_expiry = doc_expiry.get('value')
            
            passenger_details = {
                'id': f'passenger_{i+1}',
                'firstName': given_name,
                'lastName': surname,
                'type': passenger_type,
                'dateOfBirth': birth_date,
                'documentType': doc_type.lower(),
                'documentNumber': doc_number,
                'documentExpiry': doc_expiry,
                'nationality': passenger.get('Nationality', {}).get('value') if isinstance(passenger.get('Nationality'), dict) else passenger.get('Nationality'),
                'seatNumber': None  # Will be populated if seat selection data is available
            }
            passengers.append(passenger_details)
        
        return passengers
    
    def _extract_contact_info_new_contract(self, passengers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract contact information according to the new data contract structure."""
        contact_info = {
            'email': '',
            'phone': {
                'countryCode': '',
                'number': '',
                'formatted': ''
            }
        }
        
        if passengers_data:
            first_passenger = passengers_data[0]
            contacts = first_passenger.get('Contacts', {})
            
            # Handle nested contact structure
            if 'Contact' in contacts and isinstance(contacts['Contact'], list):
                for contact in contacts['Contact']:
                    # Extract email
                    if 'EmailContact' in contact:
                        email_data = contact['EmailContact'].get('Address', {})
                        if isinstance(email_data, dict):
                            contact_info['email'] = email_data.get('value', '')
                        else:
                            contact_info['email'] = str(email_data)
                    
                    # Extract phone
                    if 'PhoneContact' in contact:
                        phone_data = contact['PhoneContact'].get('Number', {})
                        if isinstance(phone_data, list) and len(phone_data) > 0:
                            # Handle phone as list with country code
                            phone_item = phone_data[0]
                            if isinstance(phone_item, dict):
                                phone_number = phone_item.get('value', '')
                                country_code = phone_item.get('CountryCode', '')
                                contact_info['phone'] = {
                                    'countryCode': f'+{country_code}' if country_code else '',
                                    'number': phone_number,
                                    'formatted': f'+{country_code} {phone_number}' if country_code else phone_number
                                }
                            else:
                                contact_info['phone']['number'] = str(phone_item)
                                contact_info['phone']['formatted'] = str(phone_item)
                        elif isinstance(phone_data, dict):
                            phone_number = phone_data.get('value', '')
                            contact_info['phone']['number'] = phone_number
                            contact_info['phone']['formatted'] = phone_number
            
            # Fallback to direct structure
            elif 'EmailContact' in contacts:
                email_data = contacts['EmailContact'].get('Address', '')
                if isinstance(email_data, dict):
                    contact_info['email'] = email_data.get('value', '')
                else:
                    contact_info['email'] = str(email_data)
            
            if 'PhoneContact' in contacts:
                phone_data = contacts['PhoneContact'].get('Number', '')
                if isinstance(phone_data, dict):
                    phone_number = phone_data.get('value', '')
                    contact_info['phone']['number'] = phone_number
                    contact_info['phone']['formatted'] = phone_number
                else:
                    contact_info['phone']['number'] = str(phone_data)
                    contact_info['phone']['formatted'] = str(phone_data)
        
        return contact_info

    def _extract_pricing_new_contract(self, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pricing information according to the new data contract structure."""
        return {
            'baseFare': {
                'amount': pricing_data.get('baseFare', 0.0),
                'currency': pricing_data.get('currency', 'USD')
            },
            'taxes': {
                'amount': pricing_data.get('taxes', 0.0),
                'currency': pricing_data.get('currency', 'USD')
            },
            'fees': {
                'amount': pricing_data.get('fees', 0.0),
                'currency': pricing_data.get('currency', 'USD')
            },
            'total': {
                'amount': pricing_data.get('total', 0.0),
                'currency': pricing_data.get('currency', 'USD')
            }
        }
    
    def _extract_extras_new_contract(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract additional services according to the new data contract structure."""
        extras = []
        
        try:
            # Extract from Order structure if available
            order_data = response_data.get('Response', {}).get('Order', [])
            if isinstance(order_data, list) and len(order_data) > 0:
                order = order_data[0]
                
                # Look for ancillary services
                if 'OrderItems' in order and 'OrderItem' in order['OrderItems']:
                    order_items = order['OrderItems']['OrderItem']
                    if isinstance(order_items, list):
                        for item in order_items:
                            # Check for seat selections
                            if 'SeatItem' in item:
                                seat_item = item['SeatItem']
                                extras.append({
                                    'type': 'SeatSelection',
                                    'description': f"Seat {seat_item.get('SeatNumber', 'N/A')}",
                                    'price': {
                                        'amount': float(seat_item.get('Price', {}).get('value', 0)),
                                        'currency': seat_item.get('Price', {}).get('Code', 'USD')
                                    }
                                })
                            
                            # Check for baggage
                            if 'BaggageItem' in item:
                                baggage_item = item['BaggageItem']
                                extras.append({
                                    'type': 'BaggageSelection',
                                    'description': baggage_item.get('Description', 'Additional Baggage'),
                                    'price': {
                                        'amount': float(baggage_item.get('Price', {}).get('value', 0)),
                                        'currency': baggage_item.get('Price', {}).get('Code', 'USD')
                                    }
                                })
                            
                            # Check for meals
                            if 'MealItem' in item:
                                meal_item = item['MealItem']
                                extras.append({
                                    'type': 'MealSelection',
                                    'description': meal_item.get('Description', 'Special Meal'),
                                    'price': {
                                        'amount': float(meal_item.get('Price', {}).get('value', 0)),
                                        'currency': meal_item.get('Price', {}).get('Code', 'USD')
                                    }
                                })
        
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error extracting extras: {e}")
        
        return extras
    
    def _extract_payment_info(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract payment information from the response."""
        payment_info = {
            'method': 'unknown',
            'status': 'pending',
            'transactionId': '',
            'amount': {
                'amount': 0.0,
                'currency': 'USD'
            }
        }
        
        try:
            # Extract from Order structure if available
            order_data = response_data.get('Response', {}).get('Order', [])
            if isinstance(order_data, list) and len(order_data) > 0:
                order = order_data[0]
                
                # Look for payment information
                if 'Payments' in order and 'Payment' in order['Payments']:
                    payments = order['Payments']['Payment']
                    if isinstance(payments, list) and len(payments) > 0:
                        payment = payments[0]
                        
                        payment_info['method'] = payment.get('Method', {}).get('PaymentCard', {}).get('CardType', 'unknown')
                        payment_info['status'] = payment.get('Status', 'pending')
                        payment_info['transactionId'] = payment.get('TransactionID', '')
                        
                        # Extract amount
                        amount_data = payment.get('Amount', {})
                        if isinstance(amount_data, dict):
                            payment_info['amount']['amount'] = float(amount_data.get('value', 0))
                            payment_info['amount']['currency'] = amount_data.get('Code', 'USD')
                
                # Fallback to total order price
                if payment_info['amount']['amount'] == 0 and 'TotalOrderPrice' in order:
                    total_price = order['TotalOrderPrice'].get('TotalAmount', {})
                    if isinstance(total_price, dict):
                        payment_info['amount']['amount'] = float(total_price.get('value', 0))
                        payment_info['amount']['currency'] = total_price.get('Code', 'USD')
        
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error extracting payment info: {e}")
        
        return payment_info

    def _extract_pricing_details_new_format(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pricing details in the new frontend-compatible format."""
        return {
            'baseFare': pricing_data.get('baseFare', 0),
            'taxes': pricing_data.get('taxes', 0),
            'total': pricing_data.get('total', 0),
            'currency': pricing_data.get('currency', 'USD'),
            'fees': 0,  # Placeholder for future implementation
            'discount': 0  # Placeholder for future implementation
        }
    
    def _extract_booking_time(self, response: Dict[str, Any]) -> str:
        """Extract booking time from response."""
        if 'Response' in response:
            return response['Response'].get('CreationDateTime') or response['Response'].get('Timestamp') or 'N/A'
        return 'N/A'
    
    def _extract_ticket_info(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract ticket information from response."""
        tickets = []
        
        if 'Response' in response and 'TicketDocInfos' in response['Response']:
            ticket_docs = response['Response']['TicketDocInfos']
            if 'TicketDocInfo' in ticket_docs and isinstance(ticket_docs['TicketDocInfo'], list):
                for ticket_doc in ticket_docs['TicketDocInfo']:
                    if 'TicketDocument' in ticket_doc and isinstance(ticket_doc['TicketDocument'], list):
                        for ticket in ticket_doc['TicketDocument']:
                            tickets.append({
                                'ticketNumber': ticket.get('TicketDocNbr', 'N/A'),
                                'dateOfIssue': ticket.get('DateOfIssue', 'N/A'),
                                'status': 'Issued'
                            })
        
        return tickets
    
    def _process_booking_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the OrderCreate API response according to the new data contract.
        Returns standardized booking data structure that eliminates frontend transformation needs.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response data matching the new data contract structure
        """
        try:
            # Extract basic booking information
            booking_reference = response.get('Response', {}).get('Order', [{}])[0].get('BookingReferences', {}).get('BookingReference', [{}])[0].get('ID')
            order_id = response.get('Response', {}).get('Order', [{}])[0].get('OrderID', {}).get('value')
            
            # Extract creation timestamp
            created_at = response.get('Response', {}).get('CreationDateTime') or response.get('Response', {}).get('Timestamp')
            if not created_at:
                from datetime import datetime
                created_at = datetime.utcnow().isoformat() + 'Z'
            
            # Extract payment information
            payment_info = self._extract_payment_info(response)
            
            # Extract flight details and passenger data
            outbound_flights = []
            return_flights = []
            passengers_data = []
            pricing_data = {'baseFare': 0, 'taxes': 0, 'total': 0, 'currency': 'USD'}
            
            # Extract flight information from Order node
            if 'Response' in response and 'Order' in response['Response']:
                order_list = response['Response']['Order']
                
                if isinstance(order_list, list) and len(order_list) > 0:
                    order = order_list[0]
                    
                    if 'OrderItems' in order and 'OrderItem' in order['OrderItems'] and isinstance(order['OrderItems']['OrderItem'], list):
                        for order_item in order['OrderItems']['OrderItem']:
                            if 'FlightItem' in order_item:
                                flight_item = order_item['FlightItem']
                                
                                # Extract pricing information
                                if 'Price' in flight_item:
                                    price_obj = flight_item['Price']
                                    if 'BaseAmount' in price_obj:
                                        base_amount = price_obj['BaseAmount']
                                        if isinstance(base_amount, dict):
                                            pricing_data['baseFare'] = float(base_amount.get('value', 0))
                                            pricing_data['currency'] = base_amount.get('Code', 'USD')
                                    
                                    if 'Taxes' in price_obj and 'Total' in price_obj['Taxes']:
                                        taxes_total = price_obj['Taxes']['Total']
                                        if isinstance(taxes_total, dict):
                                            pricing_data['taxes'] = float(taxes_total.get('value', 0))
                                    
                                    # Calculate total
                                    pricing_data['total'] = pricing_data['baseFare'] + pricing_data['taxes']
                                
                                # Extract flight segments
                                if 'OriginDestination' in flight_item and isinstance(flight_item['OriginDestination'], list):
                                    for idx, origin_dest in enumerate(flight_item['OriginDestination']):
                                        if 'Flight' in origin_dest and isinstance(origin_dest['Flight'], list) and len(origin_dest['Flight']) > 0:
                                            flight = origin_dest['Flight'][0]
                                            
                                            # Assign to outbound or return based on index
                                            if idx == 0:
                                                outbound_flights.append(flight)
                                            elif idx == 1:
                                                return_flights.append(flight)
            
            # Extract passenger information
            if 'Response' in response and 'Passengers' in response['Response']:
                passengers = response['Response']['Passengers']
                if 'Passenger' in passengers and isinstance(passengers['Passenger'], list):
                    passengers_data = passengers['Passenger']
            
            # Build the new data contract structure
            processed = {
                'bookingReference': booking_reference,
                'status': 'confirmed',
                'createdAt': created_at,
                'flightDetails': {
                    'outbound': self._extract_flight_segment_new_contract(outbound_flights),
                    'return': self._extract_flight_segment_new_contract(return_flights) if return_flights else None
                },
                'passengers': self._extract_passengers_new_contract(passengers_data),
                'contactInfo': self._extract_contact_info_new_contract(passengers_data),
                'pricing': self._extract_pricing_new_contract(pricing_data),
                'extras': self._extract_extras_new_contract(response),
                'paymentInfo': payment_info
            }
            
            # Log successful processing
            logger.info(f"Successfully processed OrderCreate response with new data contract. Booking reference: {booking_reference}")
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing OrderCreate response: {str(e)}")
            import json
            logger.error(f"Response structure: {json.dumps(response, indent=2, default=str)[:1000]}...")
            
            # Return error response matching the new data contract
            from datetime import datetime
            return {
                'error': {
                    'code': 'BOOKING_PROCESSING_ERROR',
                    'message': f'Failed to process booking response: {str(e)}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'requestId': response.get('RequestID', 'unknown')
                }
            }
    
    def _process_retrieve_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the OrderRetrieve API response.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response data
        """
        # Extract OrderID from nested structure using correct path
        order_id = response.get('Response', {}).get('Order', [{}])[0].get('OrderID', {}).get('value')
        booking_reference = response.get('Response', {}).get('Order', [{}])[0].get('BookingReferences', {}).get('BookingReference', [{}])[0].get('ID')
        
        processed = {
            'id': order_id,
            'booking_reference': booking_reference,
            'status': response.get('OrderStatus'),
            'booking_time': response.get('CreationDateTime'),
            'passengers': [],
            'flights': [],
            'price_info': response.get('PriceInfo', {})
        }
        
        # Process passengers if available
        if 'Passengers' in response:
            for pax in response['Passengers']:
                processed['passengers'].append({
                    'passenger_id': pax.get('PassengerID'),
                    'name': f"{pax.get('FirstName', '')} {pax.get('LastName', '')}".strip(),
                    'type': pax.get('Type'),
                    'ticket_number': pax.get('TicketNumber')
                })
        
        # Process flights if available
        if 'FlightSegments' in response:
            for segment in response['FlightSegments']:
                processed['flights'].append({
                    'flight_number': f"{segment.get('MarketingAirline')}{segment.get('FlightNumber')}",
                    'departure': segment.get('Departure'),
                    'arrival': segment.get('Arrival'),
                    'status': segment.get('Status')
                })
        
        return processed


# Helper functions for backward compatibility
async def create_booking(
    flight_price_response: Dict[str, Any],
    passengers: List[Dict[str, Any]],
    payment_info: Dict[str, Any],
    contact_info: Dict[str, str],
    request_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> BookingResponse:
    """
    Create a new flight booking.
    
    This is a backward-compatible wrapper around the FlightBookingService.
    """
    # Use a single service instance to avoid creating multiple TokenManager instances
    service = FlightBookingService(config=config or {})
    try:
        return await service.create_booking(
            flight_price_response=flight_price_response,
            passengers=passengers,
            payment_info=payment_info,
            contact_info=contact_info,
            request_id=request_id
        )
    finally:
        await service.close()


async def process_order_create(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process order creation request.
    
    This is a backward-compatible wrapper around the FlightBookingService.
    """
    config = order_data.pop('config', {})
    
    # Use a single service instance to avoid creating multiple TokenManager instances
    service = FlightBookingService(config=config)
    try:
        return await service.create_booking(
            flight_price_response=order_data.get('flight_price_response', {}),
            passengers=order_data.get('passengers', []),
            payment_info=order_data.get('payment_info', {}),
            contact_info=order_data.get('contact_info', {}),
            request_id=order_data.get('request_id'),
            offer_id=order_data.get('offer_id'),
            shopping_response_id=order_data.get('shopping_response_id')
        )
    finally:
        await service.close()


async def get_booking_details(
    booking_reference: str,
    request_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Retrieve details for a specific booking.
    
    This is a backward-compatible wrapper around the FlightBookingService.
    """
    # Use a single service instance to avoid creating multiple TokenManager instances
    service = FlightBookingService(config=config or {})
    try:
        return await service.get_booking_details(
            booking_reference=booking_reference,
            request_id=request_id
        )
    finally:
        await service.close()
