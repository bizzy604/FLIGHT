"""
Test suite for ancillary pricing sequential flow.

This test suite validates the new sequential pricing logic for seats and services,
ensuring proper NDC specification compliance.

Test Data Source: Backend/api_logs/ - Real API request/response data
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any

# Import the functions to test
from scripts.build_flightprice_ancillary_rq import (
    build_flightprice_request_for_services,
    build_flightprice_request_for_seats,
    detect_pricing_required,
    normalize_to_list
)

# Test data directory
API_LOGS_DIR = Path(__file__).parent / "api_logs"


class TestDataLoader:
    """Helper class to load test data from api_logs directory."""
    
    @staticmethod
    def load_json(service_name: str, file_type: str) -> Dict[str, Any]:
        """
        Load JSON test data from api_logs directory.
        
        Args:
            service_name: Name of the service (e.g., 'flight_price', 'service_list')
            file_type: 'RQ' for request or 'RS' for response
        
        Returns:
            Dict containing the JSON data
        """
        service_dir = service_name.replace('_', '_')
        filename = f"{service_name.replace('_', '').title().replace('Flightprice', 'FlightPrice').replace('Servicelist', 'ServiceList').replace('Seatavailability', 'SeatAvailability')}_{file_type}.json"
        
        # Construct path
        file_path = API_LOGS_DIR / service_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Test data not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def get_flight_price_raw_response() -> Dict[str, Any]:
        """Get raw FlightPrice response for testing."""
        data = TestDataLoader.load_json('flight_price', 'RS')
        return data.get('response', {}).get('raw_response', {})
    
    @staticmethod
    def get_service_list_response() -> Dict[str, Any]:
        """Get ServiceList response for testing."""
        data = TestDataLoader.load_json('service_list', 'RS')
        return data.get('response', {})
    
    @staticmethod
    def get_seat_availability_response() -> Dict[str, Any]:
        """Get SeatAvailability response for testing."""
        data = TestDataLoader.load_json('seat_availability', 'RS')
        return data.get('response', {})


@pytest.fixture
def flight_price_response():
    """Fixture for FlightPrice response."""
    return TestDataLoader.get_flight_price_raw_response()


@pytest.fixture
def service_list_response():
    """Fixture for ServiceList response."""
    return TestDataLoader.get_service_list_response()


@pytest.fixture
def seat_availability_response():
    """Fixture for SeatAvailability response."""
    return TestDataLoader.get_seat_availability_response()


class TestDetectPricingRequired:
    """Test suite for pricing requirement detection."""
    
    def test_detect_services_requiring_pricing(self, service_list_response):
        """Test detection of services that require pricing (PricedInd=false)."""
        # Select services with PricedInd=false from test data
        selected_services = ['1-ServiceIdAF-2', '1-ServiceIdAF-15', '1-ServiceIdAF-17']
        
        result = detect_pricing_required(
            servicelist_response=service_list_response,
            selected_services=selected_services
        )
        
        assert result['requires_pricing'] == True
        assert len(result['services_require_pricing']) > 0
        assert '1-ServiceIdAF-2' in result['services_require_pricing']
    
    def test_detect_seats_requiring_pricing(self, seat_availability_response):
        """Test detection of seats that require pricing (PricedInd=false)."""
        # Select a seat from test data
        selected_seats = ['e0ee9182-5616-47e1-ae91-825616070020']
        
        result = detect_pricing_required(
            seatavailability_response=seat_availability_response,
            selected_seats=selected_seats
        )
        
        # Note: This will depend on actual PricedInd values in test data
        assert 'requires_pricing' in result
        assert 'seats_require_pricing' in result
    
    def test_detect_both_services_and_seats(self, service_list_response, seat_availability_response):
        """Test detection when both services and seats are selected."""
        selected_services = ['1-ServiceIdAF-2']
        selected_seats = ['e0ee9182-5616-47e1-ae91-825616070020']
        
        result = detect_pricing_required(
            servicelist_response=service_list_response,
            seatavailability_response=seat_availability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        assert 'requires_pricing' in result
        assert 'services_require_pricing' in result
        assert 'seats_require_pricing' in result
        assert 'total_items_require_pricing' in result
    
    def test_no_pricing_required(self):
        """Test when no pricing is required."""
        result = detect_pricing_required()
        
        assert result['requires_pricing'] == False
        assert len(result['services_require_pricing']) == 0
        assert len(result['seats_require_pricing']) == 0


class TestBuildFlightPriceRequestForServices:
    """Test suite for building FlightPrice requests for services only."""
    
    def test_build_services_only_request(self, flight_price_response, service_list_response):
        """Test building FlightPrice request with services only."""
        selected_services = ['1-ServiceIdAF-2']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services,
            selected_offer_index=0
        )
        
        # Validate request structure
        assert 'Travelers' in request
        assert 'Query' in request
        assert 'DataLists' in request
        assert 'ShoppingResponseID' in request
        
        # Validate offers structure
        assert 'Offers' in request['Query']
        assert 'Offer' in request['Query']['Offers']
        assert len(request['Query']['Offers']['Offer']) > 0
        
        # Validate offer items
        offer = request['Query']['Offers']['Offer'][0]
        assert 'OfferItemIDs' in offer
        assert 'OfferItemID' in offer['OfferItemIDs']
        
        offer_items = offer['OfferItemIDs']['OfferItemID']
        assert len(offer_items) >= 2  # Flight item + at least one service
        
        # First item should be flight
        # Subsequent items should be services
        service_items = [item for item in offer_items[1:] if item['value'] in selected_services]
        assert len(service_items) > 0
        
        print(f"✅ Successfully built services-only request with {len(offer_items)} items")
    
    def test_multiple_services(self, flight_price_response, service_list_response):
        """Test building request with multiple services."""
        selected_services = ['1-ServiceIdAF-2', '1-ServiceIdAF-15', '1-ServiceIdAF-17']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services,
            selected_offer_index=0
        )
        
        offer_items = request['Query']['Offers']['Offer'][0]['OfferItemIDs']['OfferItemID']
        
        # Should have flight item + selected services
        assert len(offer_items) >= len(selected_services) + 1
        
        print(f"✅ Successfully built request with {len(selected_services)} services")
    
    def test_services_have_refs(self, flight_price_response, service_list_response):
        """Test that service items have proper refs (traveler references)."""
        selected_services = ['1-ServiceIdAF-2']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services,
            selected_offer_index=0
        )
        
        offer_items = request['Query']['Offers']['Offer'][0]['OfferItemIDs']['OfferItemID']
        
        # All items should have refs
        for item in offer_items:
            assert 'refs' in item
            assert isinstance(item['refs'], list)
            assert len(item['refs']) > 0
        
        print("✅ All items have proper traveler references")


class TestBuildFlightPriceRequestForSeats:
    """Test suite for building FlightPrice requests for seats only."""
    
    def test_build_seats_only_request(self, flight_price_response, seat_availability_response):
        """Test building FlightPrice request with seats only."""
        selected_seats = ['e0ee9182-5616-47e1-ae91-825616070020']
        
        request = build_flightprice_request_for_seats(
            flight_price_response=flight_price_response,
            seatavailability_response=seat_availability_response,
            selected_seats=selected_seats,
            selected_offer_index=0
        )
        
        # Validate request structure
        assert 'Travelers' in request
        assert 'Query' in request
        assert 'DataLists' in request
        assert 'ShoppingResponseID' in request
        
        # Validate offers structure
        offer = request['Query']['Offers']['Offer'][0]
        offer_items = offer['OfferItemIDs']['OfferItemID']
        
        # Should have flight item + seat items
        assert len(offer_items) >= 2
        
        # Check for SelectedSeat structure in seat items
        seat_items = [item for item in offer_items if 'SelectedSeat' in item]
        assert len(seat_items) > 0
        
        # Validate SelectedSeat structure
        for seat_item in seat_items:
            assert 'SelectedSeat' in seat_item
            assert isinstance(seat_item['SelectedSeat'], list)
            assert len(seat_item['SelectedSeat']) > 0
            
            seat_info = seat_item['SelectedSeat'][0]
            assert 'Location' in seat_info
            assert 'SeatAssociation' in seat_info
        
        print(f"✅ Successfully built seats-only request with {len(seat_items)} seats")
    
    def test_seat_has_location_info(self, flight_price_response, seat_availability_response):
        """Test that seat items have proper location information."""
        selected_seats = ['e0ee9182-5616-47e1-ae91-825616070020']
        
        request = build_flightprice_request_for_seats(
            flight_price_response=flight_price_response,
            seatavailability_response=seat_availability_response,
            selected_seats=selected_seats,
            selected_offer_index=0
        )
        
        offer_items = request['Query']['Offers']['Offer'][0]['OfferItemIDs']['OfferItemID']
        seat_items = [item for item in offer_items if 'SelectedSeat' in item]
        
        for seat_item in seat_items:
            location = seat_item['SelectedSeat'][0]['Location']
            
            # Location should have Row and Column (at minimum)
            # May also have Characteristics
            assert 'Column' in location or 'Row' in location
            
            print(f"✅ Seat location info present: {location}")


class TestOfferIDChaining:
    """Test suite for offer ID chaining between sequential calls."""
    
    def test_services_request_with_base_offer_id(self, flight_price_response, service_list_response):
        """Test building services request with custom base offer ID."""
        selected_services = ['1-ServiceIdAF-2']
        custom_offer_id = "custom-offer-123"
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services,
            selected_offer_index=0,
            base_offer_id=custom_offer_id
        )
        
        # Check that custom offer ID is used
        offer_id = request['Query']['Offers']['Offer'][0]['OfferID']
        assert offer_id['value'] == custom_offer_id
        assert offer_id['ObjectKey'] == custom_offer_id
        
        print(f"✅ Custom offer ID successfully applied: {custom_offer_id}")
    
    def test_seats_request_with_base_offer_id(self, flight_price_response, seat_availability_response):
        """Test building seats request with custom base offer ID."""
        selected_seats = ['e0ee9182-5616-47e1-ae91-825616070020']
        custom_offer_id = "offer-from-services-pricing"
        
        request = build_flightprice_request_for_seats(
            flight_price_response=flight_price_response,
            seatavailability_response=seat_availability_response,
            selected_seats=selected_seats,
            selected_offer_index=0,
            base_offer_id=custom_offer_id
        )
        
        # Check that custom offer ID is used
        offer_id = request['Query']['Offers']['Offer'][0]['OfferID']
        assert offer_id['value'] == custom_offer_id
        
        print(f"✅ Chained offer ID successfully applied: {custom_offer_id}")


class TestNDCCompliance:
    """Test suite for NDC specification compliance."""
    
    def test_services_request_matches_ndc_format(self, flight_price_response, service_list_response):
        """Test that generated services request matches NDC format."""
        selected_services = ['1-ServiceIdAF-2']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services
        )
        
        # Check required NDC fields
        assert 'Travelers' in request
        assert 'Traveler' in request['Travelers']
        
        assert 'Query' in request
        assert 'OriginDestination' in request['Query']
        assert 'Offers' in request['Query']
        
        assert 'DataLists' in request
        assert 'AnonymousTravelerList' in request['DataLists']
        
        assert 'ShoppingResponseID' in request
        assert 'ResponseID' in request['ShoppingResponseID']
        
        print("✅ Request structure matches NDC specification")
    
    def test_no_mixed_ancillary_types(self, flight_price_response, service_list_response):
        """Test that services request doesn't include seat items."""
        selected_services = ['1-ServiceIdAF-2']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services
        )
        
        offer_items = request['Query']['Offers']['Offer'][0]['OfferItemIDs']['OfferItemID']
        
        # Check that no items have SelectedSeat (seat items)
        seat_items = [item for item in offer_items if 'SelectedSeat' in item]
        assert len(seat_items) == 0, "Services request should not include seat items"
        
        print("✅ Services request properly excludes seat items")


class TestRequestStructureValidation:
    """Test suite for validating request structure completeness."""
    
    def test_travelers_section_complete(self, flight_price_response, service_list_response):
        """Test that Travelers section is properly populated."""
        selected_services = ['1-ServiceIdAF-2']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services
        )
        
        travelers = request['Travelers']['Traveler']
        assert len(travelers) > 0
        
        for traveler in travelers:
            assert 'AnonymousTraveler' in traveler
            assert isinstance(traveler['AnonymousTraveler'], list)
            assert 'PTC' in traveler['AnonymousTraveler'][0]
        
        print(f"✅ Travelers section validated: {len(travelers)} traveler(s)")
    
    def test_origin_destination_section_complete(self, flight_price_response, service_list_response):
        """Test that OriginDestination section is properly populated."""
        selected_services = ['1-ServiceIdAF-2']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services
        )
        
        origin_destinations = request['Query']['OriginDestination']
        assert len(origin_destinations) > 0
        
        for od in origin_destinations:
            assert 'Flight' in od
            assert len(od['Flight']) > 0
            
            flight = od['Flight'][0]
            assert 'SegmentKey' in flight
            assert 'Departure' in flight
            assert 'Arrival' in flight
            assert 'MarketingCarrier' in flight
        
        print(f"✅ OriginDestination section validated: {len(origin_destinations)} segment(s)")
    
    def test_datalists_section_complete(self, flight_price_response, service_list_response):
        """Test that DataLists section is properly populated."""
        selected_services = ['1-ServiceIdAF-2']
        
        request = build_flightprice_request_for_services(
            flight_price_response=flight_price_response,
            servicelist_response=service_list_response,
            selected_services=selected_services
        )
        
        datalists = request['DataLists']
        assert 'AnonymousTravelerList' in datalists
        assert 'AnonymousTraveler' in datalists['AnonymousTravelerList']
        
        travelers = datalists['AnonymousTravelerList']['AnonymousTraveler']
        assert len(travelers) > 0
        
        for traveler in travelers:
            assert 'ObjectKey' in traveler
            assert 'PTC' in traveler
        
        print(f"✅ DataLists section validated: {len(travelers)} traveler(s)")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
