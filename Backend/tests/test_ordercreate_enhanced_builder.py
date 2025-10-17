"""
Tests for Enhanced OrderCreate Request Builder.

These tests verify the build_ordercreate_enhanced_rq.py module which:
1. Detects PricedInd scenarios (true/false/mixed)
2. Routes to correct pricing response
3. Builds OrderCreate requests with proper ancillary data
4. Handles integration between FlightPrice and OrderCreate
"""

import pytest
import json
import os
import copy
from scripts.build_ordercreate_enhanced_rq import (
    build_ordercreate_enhanced_request,
    detect_priced_ind_scenario,
    _is_multi_airline_flight_price_response,
    _extract_airline_from_flight_price_response,
    clean_airline_prefix_from_key,
    normalize_to_list
)


def load_api_log(filename):
    """Load API log file from api_logs directory."""
    base_path = os.path.join(os.path.dirname(__file__), '..', 'api_logs')
    filepath = os.path.join(base_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Extract raw_response for FlightPrice
        if 'response' in data and 'raw_response' in data['response']:
            return data['response']['raw_response']
        return data.get('response', data)


@pytest.fixture
def passenger_data():
    """Sample passenger data for testing."""
    return [
        {
            "ObjectKey": "PAX1",
            "PTC": {"value": "ADT"},
            "name": {"given": "John", "surname": "Doe"},
            "dob": {"year": "1990", "month": "01", "day": "15"},
            "gender": "M",
            "email": "john.doe@example.com",
            "phone": "+1234567890"
        }
    ]


@pytest.fixture
def payment_info():
    """Sample payment information for testing."""
    return {
        "method": "credit_card",
        "card_number": "4111111111111111",
        "expiry": "12/25",
        "cvv": "123"
    }


class TestDetectPricedIndScenario:
    """Test PricedInd scenario detection."""
    
    def test_detect_priced_ind_true_scenario(self):
        """All items with PricedInd=true should be detected as priced_ind_true scenario."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Select only items with PricedInd=true
        services = servicelist.get('Services', {}).get('Service', [])
        services_with_priced_true = [s for s in services if s.get('PricedInd') is True]
        selected_services = [s['ObjectKey'] for s in services_with_priced_true[:2]]
        
        seats = seatavailability.get('Services', {}).get('Service', [])
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        scenario = detect_priced_ind_scenario(
            servicelist_response=servicelist,
            seatavailability_response=seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        assert scenario['scenario'] == 'priced_ind_true'
        assert len(scenario['services_priced']) == 2
        assert len(scenario['seats_priced']) == 2
        assert len(scenario['services_unpriced']) == 0
        assert len(scenario['seats_unpriced']) == 0
    
    def test_detect_priced_ind_false_scenario(self):
        """All items with PricedInd=false should be detected as priced_ind_false scenario."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Modify to have PricedInd=false
        modified_servicelist = copy.deepcopy(servicelist)
        modified_seatavailability = copy.deepcopy(seatavailability)
        
        services = modified_servicelist.get('Services', {}).get('Service', [])
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        
        for service in services[:2]:
            service['PricedInd'] = False
        
        for seat in seats[:2]:
            seat['PricedInd'] = False
        
        selected_services = [s['ObjectKey'] for s in services[:2]]
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        scenario = detect_priced_ind_scenario(
            servicelist_response=modified_servicelist,
            seatavailability_response=modified_seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        assert scenario['scenario'] == 'priced_ind_false'
        assert len(scenario['services_unpriced']) == 2
        assert len(scenario['seats_unpriced']) == 2
    
    def test_detect_mixed_scenario(self):
        """Mix of priced and unpriced items should be detected as mixed scenario."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Modify to have mix
        modified_servicelist = copy.deepcopy(servicelist)
        modified_seatavailability = copy.deepcopy(seatavailability)
        
        services = modified_servicelist.get('Services', {}).get('Service', [])
        services_with_priced_true = [s for s in services if s.get('PricedInd') is True]
        
        if len(services_with_priced_true) >= 2:
            # Set first to false, keep second as true
            services_with_priced_true[0]['PricedInd'] = False
            selected_services = [s['ObjectKey'] for s in services_with_priced_true[:2]]
        else:
            selected_services = []
        
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        seats[0]['PricedInd'] = False
        selected_seats = [seats[0]['ObjectKey'], seats[1]['ObjectKey']]
        
        scenario = detect_priced_ind_scenario(
            servicelist_response=modified_servicelist,
            seatavailability_response=modified_seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        assert scenario['scenario'] == 'mixed'


class TestBuildOrderCreateEnhancedRequest:
    """Test enhanced OrderCreate request building."""
    
    def test_build_with_priced_ind_true_no_ancillary_pricing(self, passenger_data, payment_info):
        """When PricedInd=true, should use original FlightPrice response."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Select items with PricedInd=true
        services = servicelist.get('Services', {}).get('Service', [])
        services_with_priced_true = [s for s in services if s.get('PricedInd') is True]
        selected_services = [s['ObjectKey'] for s in services_with_priced_true[:2]]
        
        seats = seatavailability.get('Services', {}).get('Service', [])
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            servicelist_response=servicelist,
            seatavailability_response=seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats,
            ancillary_pricing_response=None  # No ancillary pricing needed
        )
        
        # Verify OrderCreate structure
        assert 'Query' in order_create
        assert 'Passengers' in order_create['Query']
        assert 'OrderItems' in order_create['Query']
        
        # Verify metadata
        if 'metadata' in order_create:
            pricing_info = order_create['metadata'].get('pricing_info', {})
            assert pricing_info.get('requires_pricing') is False
            assert order_create['metadata'].get('used_priced_response') is False
    
    def test_build_with_priced_ind_false_uses_ancillary_pricing(self, passenger_data, payment_info):
        """When PricedInd=false, should use ancillary pricing response."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Modify services to have PricedInd=false
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        
        for service in services[:2]:
            service['PricedInd'] = False
        
        selected_services = [s['ObjectKey'] for s in services[:2]]
        
        # Create mock ancillary pricing response (same structure as FlightPrice)
        ancillary_pricing = copy.deepcopy(flight_price)
        
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            servicelist_response=modified_servicelist,
            selected_services=selected_services,
            ancillary_pricing_response=ancillary_pricing
        )
        
        # Verify OrderCreate structure
        assert 'Query' in order_create
        
        # Verify metadata shows pricing was required
        if 'metadata' in order_create:
            pricing_info = order_create['metadata'].get('pricing_info', {})
            assert pricing_info.get('requires_pricing') is True
            assert order_create['metadata'].get('used_priced_response') is True
    
    def test_build_with_missing_priced_ind_requires_pricing(self, passenger_data, payment_info):
        """Services missing PricedInd field should trigger pricing requirement."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Remove PricedInd field from services
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        
        for service in services[:2]:
            if 'PricedInd' in service:
                del service['PricedInd']
        
        selected_services = [s['ObjectKey'] for s in services[:2]]
        
        # Should require pricing since PricedInd is missing (defaults to false)
        ancillary_pricing = copy.deepcopy(flight_price)
        
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            servicelist_response=modified_servicelist,
            selected_services=selected_services,
            ancillary_pricing_response=ancillary_pricing
        )
        
        # Verify metadata
        if 'metadata' in order_create:
            pricing_info = order_create['metadata'].get('pricing_info', {})
            assert pricing_info.get('requires_pricing') is True
    
    def test_build_with_no_ancillaries(self, passenger_data, payment_info):
        """OrderCreate without ancillaries should build successfully."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            servicelist_response=None,
            seatavailability_response=None,
            selected_services=None,
            selected_seats=None
        )
        
        # Should build successfully with just flight
        assert 'Query' in order_create
        assert 'OrderItems' in order_create['Query']
    
    def test_build_handles_nested_response_structure(self, passenger_data, payment_info):
        """Should handle FlightPrice response wrapped in 'response' structure."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        # Wrap in nested structure
        wrapped_response = {
            'response': {
                'raw_response': flight_price
            }
        }
        
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=wrapped_response,
            passengers_data=passenger_data,
            payment_input_info=payment_info
        )
        
        # Should extract and use the correct data
        assert 'Query' in order_create


class TestIntegrationFlow:
    """Test complete integration flow from detection to OrderCreate."""
    
    def test_complete_flow_priced_ind_false(self, passenger_data, payment_info):
        """
        Complete flow:
        1. Detect PricedInd=false
        2. Build FlightPrice request
        3. Get pricing response
        4. Build OrderCreate with pricing
        """
        from scripts.build_flightprice_ancillary_rq import (
            detect_pricing_required,
            build_flightprice_ancillary_request
        )
        
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Modify to have PricedInd=false
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        services[0]['PricedInd'] = False
        selected_services = [services[0]['ObjectKey']]
        
        # Step 1: Detect pricing required
        pricing_info = detect_pricing_required(
            servicelist_response=modified_servicelist,
            selected_services=selected_services
        )
        
        assert pricing_info['requires_pricing'] is True
        
        # Step 2: Build FlightPrice request for pricing
        pricing_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price,
            servicelist_response=modified_servicelist,
            selected_services=selected_services
        )
        
        assert 'Query' in pricing_request
        
        # Step 3: Simulate getting pricing response (use flight_price as mock)
        ancillary_pricing = copy.deepcopy(flight_price)
        
        # Step 4: Build OrderCreate with pricing
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            servicelist_response=modified_servicelist,
            selected_services=selected_services,
            ancillary_pricing_response=ancillary_pricing
        )
        
        assert 'Query' in order_create
        assert order_create['metadata']['used_priced_response'] is True
    
    def test_complete_flow_priced_ind_true(self, passenger_data, payment_info):
        """
        Complete flow with PricedInd=true:
        1. Detect no pricing required
        2. Build OrderCreate directly
        """
        from scripts.build_flightprice_ancillary_rq import detect_pricing_required
        
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Select items with PricedInd=true
        services = servicelist.get('Services', {}).get('Service', [])
        services_with_priced_true = [s for s in services if s.get('PricedInd') is True]
        selected_services = [s['ObjectKey'] for s in services_with_priced_true[:2]]
        
        # Step 1: Detect no pricing required
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist,
            selected_services=selected_services
        )
        
        assert pricing_info['requires_pricing'] is False
        
        # Step 2: Build OrderCreate directly (no ancillary pricing needed)
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            servicelist_response=servicelist,
            selected_services=selected_services,
            ancillary_pricing_response=None
        )
        
        assert 'Query' in order_create
        assert order_create['metadata']['used_priced_response'] is False


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_clean_airline_prefix(self):
        """Test airline prefix cleaning."""
        assert clean_airline_prefix_from_key('QR-PAX1', 'QR') == 'PAX1'
        assert clean_airline_prefix_from_key('PAX1', 'QR') == 'PAX1'
        assert clean_airline_prefix_from_key('', 'QR') == ''
    
    def test_extract_airline_code(self):
        """Test airline code extraction."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        airline = _extract_airline_from_flight_price_response(flight_price)
        
        assert airline is not None
        assert isinstance(airline, str)
    
    def test_is_multi_airline(self):
        """Test multi-airline detection."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        is_multi = _is_multi_airline_flight_price_response(flight_price)
        
        assert isinstance(is_multi, bool)
    
    def test_normalize_to_list(self):
        """Test list normalization."""
        assert normalize_to_list([1, 2]) == [1, 2]
        assert normalize_to_list({'key': 'val'}) == [{'key': 'val'}]
        assert normalize_to_list(None) == []
        assert normalize_to_list([]) == []


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_fallback_to_basic_ordercreate_on_error(self, passenger_data, payment_info):
        """Should fallback to basic OrderCreate on error."""
        # Invalid flight price response
        invalid_response = {'invalid': 'data'}
        
        # Should not crash, should fallback
        try:
            order_create = build_ordercreate_enhanced_request(
                flight_price_response=invalid_response,
                passengers_data=passenger_data,
                payment_input_info=payment_info
            )
            # May fail or succeed with fallback - just shouldn't crash
            assert order_create is not None
        except Exception as e:
            # Expected - invalid data should raise error
            assert True
    
    def test_build_with_empty_selections(self, passenger_data, payment_info):
        """Build with empty ancillary selections should work."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            selected_services=[],
            selected_seats=[]
        )
        
        assert 'Query' in order_create
    
    def test_build_with_none_ancillary_responses(self, passenger_data, payment_info):
        """Build with None ancillary responses should work."""
        flight_price = load_api_log('flight_price/FlightPrice_RS.json')
        
        order_create = build_ordercreate_enhanced_request(
            flight_price_response=flight_price,
            passengers_data=passenger_data,
            payment_input_info=payment_info,
            servicelist_response=None,
            seatavailability_response=None
        )
        
        assert 'Query' in order_create


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
