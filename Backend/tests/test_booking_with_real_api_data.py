"""
Integration Tests for Flight Booking Service Using Real API Log Data

These tests use actual response structures from api_logs to test realistic scenarios.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from services.flight.booking import FlightBookingService


def load_api_log(filename):
    """Load API log file from api_logs directory."""
    base_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'api_logs'
    )
    filepath = os.path.join(base_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('response', data)


@pytest.fixture
def real_flight_price_response():
    """Load actual FlightPrice response from logs."""
    return load_api_log('flight_price/FlightPrice_RS.json')


@pytest.fixture
def real_servicelist_response():
    """Load actual ServiceList response from logs."""
    return load_api_log('service_list/ServiceList_RS.json')


@pytest.fixture
def real_seatavailability_response():
    """Load actual SeatAvailability response from logs."""
    return load_api_log('seat_availability/SeatAvailability_RS.json')


@pytest.fixture
def real_booking_request():
    """Load actual OrderCreate request from logs."""
    return load_api_log('booking/Booking_RQ.json')


@pytest.fixture
def real_booking_response():
    """Load actual OrderCreate response from logs."""
    return load_api_log('booking/Booking_RS.json')


@pytest.fixture
def servicelist_with_priced_ind_false(real_servicelist_response):
    """
    Modify real ServiceList response to simulate PricedInd=false scenario.
    
    This simulates the case where Qatar Airways returns services without prices,
    requiring a separate pricing API call.
    """
    # Deep copy to avoid modifying the original
    import copy
    modified = copy.deepcopy(real_servicelist_response)
    
    # Select some services and remove their prices
    services = modified.get('Services', {}).get('Service', [])
    
    # Modify first 3 services to have PricedInd=false
    for i, service in enumerate(services[:3]):
        service['PricedInd'] = False
        # Remove the Price field to simulate no pricing info
        if 'Price' in service:
            del service['Price']
    
    return modified


@pytest.fixture
def ancillary_pricing_response_for_real_data(real_servicelist_response):
    """
    Mock ancillary pricing response that would provide prices for PricedInd=false items.
    Based on the structure of real ServiceList but with prices added.
    """
    import copy
    services = copy.deepcopy(real_servicelist_response.get('Services', {}).get('Service', [])[:3])
    
    # Ensure all have PricedInd=true and prices
    for service in services:
        service['PricedInd'] = True
        if 'Price' not in service:
            service['Price'] = [
                {
                    "Total": {
                        "value": 5000,
                        "Code": "INR"
                    }
                }
            ]
    
    return {
        'Services': {
            'Service': services
        }
    }


@pytest.fixture
def mock_config():
    """Mock configuration for booking service."""
    return {
        'VERTEIL_API_URL': 'https://api.test.com',
        'VERTEIL_OFFICE_ID': 'TEST-OFFICE',
        'API_BASE_URL': 'http://localhost:5000'
    }


@pytest.fixture
def real_passenger_data():
    """Extract passenger data from real booking request."""
    booking_req = load_api_log('booking/Booking_RQ.json')
    passengers_data = booking_req.get('payload', {}).get('Query', {}).get('Passengers', {}).get('Passenger', [])
    
    # Convert to the format expected by create_booking
    passengers = []
    for pax in passengers_data:
        name = pax.get('Name', {})
        age = pax.get('Age', {}).get('BirthDate', {}).get('value', '')
        contacts = pax.get('Contacts', {}).get('Contact', [{}])[0]
        doc_info = pax.get('PassengerIDInfo', {}).get('PassengerDocument', [{}])[0]
        
        # Parse birth date
        if age:
            parts = age.split('-')
            dob = {
                'year': parts[0],
                'month': parts[1],
                'day': parts[2]
            }
        else:
            dob = {'year': '1990', 'month': '01', 'day': '01'}
        
        passenger = {
            'type': pax.get('PTC', {}).get('value', 'ADT'),
            'title': name.get('Title', 'Mr'),
            'firstName': name.get('Given', [{}])[0].get('value', 'Test'),
            'lastName': name.get('Surname', {}).get('value', 'Passenger'),
            'gender': pax.get('Gender', {}).get('value', 'Male'),
            'nationality': 'US',
            'dob': dob,
            'documentType': 'Passport',
            'documentNumber': doc_info.get('ID', 'P123456'),
            'issuingCountry': doc_info.get('CountryOfIssuance', 'US'),
            'expiryDate': {
                'year': '2030',
                'month': '12',
                'day': '31'
            }
        }
        passengers.append(passenger)
    
    return passengers if passengers else [
        {
            'type': 'ADT',
            'title': 'Mr',
            'firstName': 'Kevin',
            'lastName': 'Amoni',
            'gender': 'Male',
            'nationality': 'KE',
            'dob': {'year': '1996', 'month': '03', 'day': '04'},
            'documentType': 'Passport',
            'documentNumber': 'A3293EWNIIIH',
            'issuingCountry': 'KE',
            'expiryDate': {'year': '2039', 'month': '06', 'day': '05'}
        }
    ]


class TestRealAPIDataIntegration:
    """Test booking flow with real API response structures."""
    
    def test_can_load_all_api_logs(
        self,
        real_flight_price_response,
        real_servicelist_response,
        real_seatavailability_response,
        real_booking_request,
        real_booking_response
    ):
        """Verify all API log files can be loaded successfully."""
        assert real_flight_price_response is not None
        assert real_servicelist_response is not None
        assert real_seatavailability_response is not None
        assert real_booking_request is not None
        assert real_booking_response is not None
    
    def test_real_servicelist_structure(self, real_servicelist_response):
        """Test that real ServiceList response has expected structure."""
        assert 'Services' in real_servicelist_response
        assert 'Service' in real_servicelist_response['Services']
        
        services = real_servicelist_response['Services']['Service']
        assert len(services) > 0
        
        # Check first service structure
        first_service = services[0]
        assert 'ObjectKey' in first_service
        assert 'ServiceID' in first_service
        assert 'Name' in first_service
        assert 'PricedInd' in first_service
        
        # In real data, all services have PricedInd=true
        assert first_service['PricedInd'] is True
    
    def test_real_seatavailability_structure(self, real_seatavailability_response):
        """Test that real SeatAvailability response has expected structure."""
        assert 'Flights' in real_seatavailability_response or 'Services' in real_seatavailability_response
        
        # SeatAvailability may return seats as Services
        if 'Services' in real_seatavailability_response:
            assert 'Service' in real_seatavailability_response['Services']
    
    def test_extract_shopping_response_id_from_real_data(
        self,
        mock_config,
        real_servicelist_response
    ):
        """Test navigator can extract ShoppingResponseID from real data."""
        service = FlightBookingService(config=mock_config)
        
        result = service.navigator.extract_id(
            real_servicelist_response,
            'ShoppingResponseID'
        )
        
        # Real response has: "YLrRGjL-TXBSkZ-ovx6MlBk07apHhzFOWRrdjDLKI8Y-QR"
        assert result is not None
        assert len(result) > 0
        assert result == "YLrRGjL-TXBSkZ-ovx6MlBk07apHhzFOWRrdjDLKI8Y-QR"
    
    def test_extract_service_object_keys_from_real_data(self, real_servicelist_response):
        """Test extraction of service ObjectKeys from real data."""
        services = real_servicelist_response.get('Services', {}).get('Service', [])
        
        object_keys = [s.get('ObjectKey') for s in services if 'ObjectKey' in s]
        
        assert len(object_keys) > 0
        # Real data has keys like "1-ServiceIdQR-3", "1-ServiceIdQR-4", etc.
        assert all(key.startswith('1-ServiceId') for key in object_keys)
    
    @pytest.mark.asyncio
    async def test_detect_pricing_needed_for_modified_real_data(
        self,
        servicelist_with_priced_ind_false
    ):
        """Test pricing detection on modified real data with PricedInd=false."""
        from scripts.build_flightprice_ancillary_rq import detect_pricing_required
        
        # Get ObjectKeys of the first 3 services (which we modified to PricedInd=false)
        services = servicelist_with_priced_ind_false.get('Services', {}).get('Service', [])
        selected_services = [s['ObjectKey'] for s in services[:3]]
        
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_with_priced_ind_false,
            seatavailability_response=None,
            selected_services=selected_services,
            selected_seats=None
        )
        
        assert pricing_info['requires_pricing'] is True
        assert len(pricing_info['services_require_pricing']) == 3
        assert pricing_info['total_items_require_pricing'] == 3
    
    @pytest.mark.asyncio
    async def test_no_pricing_needed_for_unmodified_real_data(
        self,
        real_servicelist_response
    ):
        """Test that real data (all PricedInd=true) doesn't require pricing API."""
        from scripts.build_flightprice_ancillary_rq import detect_pricing_required
        
        # Get first 3 service ObjectKeys from real data
        services = real_servicelist_response.get('Services', {}).get('Service', [])
        selected_services = [s['ObjectKey'] for s in services[:3]]
        
        pricing_info = detect_pricing_required(
            servicelist_response=real_servicelist_response,
            seatavailability_response=None,
            selected_services=selected_services,
            selected_seats=None
        )
        
        # Real data has all services priced, so no pricing API needed
        assert pricing_info['requires_pricing'] is False
        assert len(pricing_info['services_require_pricing']) == 0
        assert pricing_info['total_items_require_pricing'] == 0
    
    @pytest.mark.asyncio
    @patch('services.flight.booking.FlightBookingService._call_ancillary_pricing_api')
    @patch('services.flight.booking.FlightBookingService._make_request')
    async def test_booking_with_real_servicelist_priced_ind_false(
        self,
        mock_make_request,
        mock_pricing_api,
        mock_config,
        real_flight_price_response,
        servicelist_with_priced_ind_false,
        ancillary_pricing_response_for_real_data,
        real_passenger_data
    ):
        """
        Test booking flow with modified real ServiceList (PricedInd=false).
        
        Simulates scenario where Qatar Airways returns services without prices.
        """
        # Mock the pricing API to return priced services
        mock_pricing_api.return_value = ancillary_pricing_response_for_real_data
        
        # Mock successful booking response
        mock_make_request.return_value = {
            'Response': {
                'DataLists': {},
                'Order': [
                    {
                        'OrderID': {'value': 'QR-ORDER-12345'},
                        'BookingReferences': {
                            'BookingReference': [
                                {'ID': 'QR-BOOKING-67890'}
                            ]
                        }
                    }
                ]
            }
        }
        
        service = FlightBookingService(config=mock_config)
        service._token_manager = Mock()
        service._token_manager.get_token.return_value = 'Bearer test-token'
        
        # Select the 3 services we modified to have PricedInd=false
        services = servicelist_with_priced_ind_false.get('Services', {}).get('Service', [])
        selected_services = [s['ObjectKey'] for s in services[:3]]
        
        # Note: FlightPrice response format in logs is transformed, not raw NDC
        # We need to use a compatible format or skip FlightPrice validation
        contact_info = {
            'email': 'kevinamoni20@gmail.com',
            'phone': '0796861525',
            'phoneCountryCode': '+254',
            'street': '190',
            'city': 'LODWAR',
            'postalCode': '30500',
            'countryCode': 'KE'
        }
        
        payment_info = {
            'payment_method': 'CREDIT_CARD',
            'currency': 'INR',
            'card_number': '4111111111111111',
            'expiry_date': '12/25',
            'cvv': '123',
            'cardholder_name': 'Kevin Amoni'
        }
        
        async with service:
            result = await service.create_booking(
                flight_price_response=real_flight_price_response,
                passengers=real_passenger_data,
                payment_info=payment_info,
                contact_info=contact_info,
                servicelist_response=servicelist_with_priced_ind_false,
                seatavailability_response=None,
                selected_services=selected_services,
                selected_seats=None
            )
        
        # Verify pricing API was called for PricedInd=false items
        assert mock_pricing_api.call_count >= 1
        
        # Verify booking completed
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_real_service_data_structure_matches_expectations(
        self,
        real_servicelist_response
    ):
        """Verify real service data has all fields our code expects."""
        services = real_servicelist_response.get('Services', {}).get('Service', [])
        
        for service in services[:5]:  # Check first 5 services
            # Required fields
            assert 'ObjectKey' in service, "Service must have ObjectKey"
            assert 'ServiceID' in service, "Service must have ServiceID"
            assert 'PricedInd' in service, "Service must have PricedInd field"
            
            # If PricedInd is true, should have Price
            if service['PricedInd']:
                assert 'Price' in service, f"Service {service['ObjectKey']} has PricedInd=true but no Price"
                assert isinstance(service['Price'], list), "Price should be a list"
                assert len(service['Price']) > 0, "Price list should not be empty"
                
                # Check price structure
                price = service['Price'][0]
                assert 'Total' in price, "Price should have Total"
                assert 'value' in price['Total'], "Total should have value"
                assert 'Code' in price['Total'], "Total should have currency Code"


class TestRealDataResponseNavigation:
    """Test navigator with real API response structures."""
    
    @pytest.mark.asyncio
    async def test_navigate_real_servicelist_structure(
        self,
        mock_config,
        real_servicelist_response
    ):
        """Test navigator can traverse real ServiceList structure."""
        service = FlightBookingService(config=mock_config)
        
        # Navigate to Services
        services = service.navigator.navigate_nested(
            real_servicelist_response,
            ['Services', 'Service']
        )
        
        assert services is not None
        assert isinstance(services, list)
        assert len(services) > 0
    
    @pytest.mark.asyncio
    async def test_extract_all_service_ids_from_real_data(
        self,
        mock_config,
        real_servicelist_response
    ):
        """Test extraction of all service IDs from real response."""
        service = FlightBookingService(config=mock_config)
        
        services = service.navigator.navigate_nested(
            real_servicelist_response,
            ['Services', 'Service']
        )
        
        service_ids = [
            svc.get('ServiceID', {}).get('value')
            for svc in services
            if isinstance(svc, dict)
        ]
        
        # Real data has service IDs like SRV3, SRV4, etc.
        assert len(service_ids) > 0
        assert all(sid.startswith('SRV') for sid in service_ids if sid)


# Helper to run async tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
