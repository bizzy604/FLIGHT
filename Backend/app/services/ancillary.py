"""
Ancillary Service

Handles SeatAvailability and ServiceList workflows.
Orchestrates VDC API calls for ancillary services (seats and services).
"""

from typing import Dict, Any, Optional
import logging

from app.services.base import BaseVDCService
from app.builders.seat_availability import SeatAvailabilityRequestBuilder
from app.builders.service_list import ServiceListRequestBuilder
from app.core.exceptions import VDCAPIError

logger = logging.getLogger(__name__)


class AncillaryService(BaseVDCService):
    """
    Ancillary service for seats and services.
    
    Provides:
    - get_seats(): Fetch seat availability
    - get_services(): Fetch ancillary services (meals, baggage, etc.)
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize ancillary service."""
        super().__init__(*args, **kwargs)
        self.seat_builder = SeatAvailabilityRequestBuilder()
        self.service_builder = ServiceListRequestBuilder()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Import pricing builder
        from app.builders.ancillary_pricing import AncillaryPricingRequestBuilder
        self.pricing_builder = AncillaryPricingRequestBuilder()
    
    async def get_seats(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer_index: int = 0,
        airline_owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get seat availability.
        
        Args:
            flight_price_response: FlightPrice response
            selected_offer_index: Index of selected offer (default: 0)
            airline_owner: Optional airline code for ThirdpartyId header
            
        Returns:
            Seat availability response with seat map data
            
        Raises:
            VDCAPIError: If API call fails
            ValueError: If input validation fails
        """
        self.logger.info(f"Fetching seat availability for offer {selected_offer_index}")
        
        try:
            # Build SeatAvailability request
            seat_request = self.seat_builder.build(
                flight_price_response=flight_price_response,
                selected_offer_index=selected_offer_index
            )
            
            # Extract airline owner if not provided
            if not airline_owner:
                priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
                if not isinstance(priced_offers, list):
                    priced_offers = [priced_offers] if priced_offers else []
                
                if priced_offers and selected_offer_index < len(priced_offers):
                    airline_owner = priced_offers[selected_offer_index].get('OfferID', {}).get('Owner')
            
            # Prepare headers
            additional_headers = {}
            if airline_owner:
                additional_headers['ThirdpartyId'] = airline_owner
            
            # Call VDC API
            response = await self._make_request(
                service_name='preSeatAvailability',
                payload=seat_request,
                headers=additional_headers
            )
            
            self.logger.info(f"Successfully retrieved seat availability for airline {airline_owner}")
            return response
            
        except ValueError as e:
            self.logger.error(f"Validation error in get_seats: {e}")
            raise
        except VDCAPIError as e:
            self.logger.error(f"VDC API error in get_seats: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in get_seats: {e}", exc_info=True)
            raise VDCAPIError(f"Failed to get seat availability: {str(e)}")
    
    async def get_services(
        self,
        flight_price_response: Dict[str, Any],
        selected_offer_index: int = 0,
        airline_owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ancillary services (meals, baggage, etc.).
        
        Args:
            flight_price_response: FlightPrice response
            selected_offer_index: Index of selected offer (default: 0)
            airline_owner: Optional airline code for ThirdpartyId header
            
        Returns:
            ServiceList response with available services
            
        Raises:
            VDCAPIError: If API call fails
            ValueError: If input validation fails
        """
        self.logger.info(f"Fetching services for offer {selected_offer_index}")
        
        try:
            # Build ServiceList request
            service_request = self.service_builder.build(
                flight_price_response=flight_price_response,
                selected_offer_index=selected_offer_index
            )
            
            # Extract airline owner if not provided
            if not airline_owner:
                priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
                if not isinstance(priced_offers, list):
                    priced_offers = [priced_offers] if priced_offers else []
                
                if priced_offers and selected_offer_index < len(priced_offers):
                    airline_owner = priced_offers[selected_offer_index].get('OfferID', {}).get('Owner')
            
            # Prepare headers
            additional_headers = {}
            if airline_owner:
                additional_headers['ThirdpartyId'] = airline_owner
            
            # Call VDC API
            response = await self._make_request(
                service_name='ServiceList',
                payload=service_request,
                headers=additional_headers
            )
            
            self.logger.info(f"Successfully retrieved services for airline {airline_owner}")
            return response
            
        except ValueError as e:
            self.logger.error(f"Validation error in get_services: {e}")
            raise
        except VDCAPIError as e:
            self.logger.error(f"VDC API error in get_services: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in get_services: {e}", exc_info=True)
            raise VDCAPIError(f"Failed to get ancillary services: {str(e)}")
    
    async def price_ancillaries(
        self,
        flight_price_response: Dict[str, Any],
        seatavailability_response: Optional[Dict[str, Any]] = None,
        servicelist_response: Optional[Dict[str, Any]] = None,
        selected_seats: list = None,
        selected_services: list = None,
        selected_offer_index: int = 0,
        airline_owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Price selected ancillaries by calling FlightPrice with selections.
        
        This is used for ancillaries with PricedInd=false that require pricing.
        Builds a FlightPrice request with OfferItemIDs including:
        - The original flight offer item
        - Selected seat items (if any)
        - Selected service items (if any)
        
        Args:
            flight_price_response: Original FlightPrice response
            seatavailability_response: SeatAvailability response (optional)
            servicelist_response: ServiceList response (optional)
            selected_seats: List of selected seat keys (optional)
            selected_services: List of selected service keys (optional)
            selected_offer_index: Index of selected offer (default: 0)
            airline_owner: Optional airline code for ThirdpartyId header
            
        Returns:
            FlightPrice response with ancillaries priced
        """
        try:
            self.logger.info("Building ancillary pricing request (FlightPrice with selections)")
            
            # Build FlightPrice request with ancillary selections using dedicated builder
            pricing_request = self.pricing_builder.build(
                flight_price_response=flight_price_response,
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services or [],
                selected_seats=selected_seats or [],
                selected_offer_index=selected_offer_index
            )
            
            # Extract airline owner if not provided
            if not airline_owner:
                priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
                if not isinstance(priced_offers, list):
                    priced_offers = [priced_offers] if priced_offers else []
                
                if priced_offers and selected_offer_index < len(priced_offers):
                    airline_owner = priced_offers[selected_offer_index].get('OfferID', {}).get('Owner')
            
            # Prepare headers
            additional_headers = {}
            if airline_owner:
                additional_headers['ThirdpartyId'] = airline_owner
            
            # Call VDC FlightPrice API
            response = await self._make_request(
                service_name='preFlightPrice',
                payload=pricing_request,
                headers=additional_headers
            )
            
            self.logger.info(f"Successfully priced ancillaries for airline {airline_owner}")
            return response
            
        except ValueError as e:
            self.logger.error(f"Validation error in price_ancillaries: {e}")
            raise
        except VDCAPIError as e:
            self.logger.error(f"VDC API error in price_ancillaries: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in price_ancillaries: {e}", exc_info=True)
            raise VDCAPIError(f"Failed to price ancillaries: {str(e)}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute ancillary workflow (abstract method implementation).
        
        Not used directly - use get_seats() or get_services() instead.
        """
        raise NotImplementedError(
            "Use get_seats() or get_services() methods instead of execute()"
        )
