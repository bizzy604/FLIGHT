"""
Tests for PricedInd field detection using REAL API log data.

These tests verify that the code correctly handles both:
1. PricedInd=true (current Qatar Airways production data)
2. PricedInd=false (simulated scenarios for other airlines)
"""

import pytest
import json
import os
import copy
from scripts.build_flightprice_ancillary_rq import detect_pricing_required


def load_api_log(filename):
    """Load API log file from api_logs directory."""
    base_path = os.path.join(os.path.dirname(__file__), '..', 'api_logs')
    filepath = os.path.join(base_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('response', data)


class TestPricedIndWithRealData:
    """Test PricedInd detection with real API response data."""
    
    def test_real_servicelist_has_priced_ind_field(self):
        """Verify real ServiceList response contains PricedInd field for SOME services."""
        response = load_api_log('service_list/ServiceList_RS.json')
        
        services = response.get('Services', {}).get('Service', [])
        assert len(services) > 0, "ServiceList should have services"
        
        # Important finding: NOT all services have PricedInd field in real data
        # Some services have it, some don't (varies by service type)
        services_with_priced_ind = [s for s in services if 'PricedInd' in s]
        services_without_priced_ind = [s for s in services if 'PricedInd' not in s]
        
        # At least some services should have the field
        assert len(services_with_priced_ind) > 0, "Some services should have PricedInd"
        
        # When PricedInd is present, it should be true in Qatar data
        for service in services_with_priced_ind:
            assert service['PricedInd'] is True, f"Service {service['ObjectKey']} has PricedInd=true"
        
        # Services without PricedInd still have Price field (implicit pricing)
        for service in services_without_priced_ind[:5]:
            assert 'Price' in service, f"Service {service['ObjectKey']} without PricedInd should have Price"
    
    def test_real_seatavailability_has_priced_ind_field(self):
        """Verify real SeatAvailability response contains PricedInd field."""
        response = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # SeatAvailability returns seats as Services
        services = response.get('Services', {}).get('Service', [])
        assert len(services) > 0, "SeatAvailability should have seat services"
        
        # Check that PricedInd field exists
        first_seat = services[0]
        assert 'PricedInd' in first_seat, "Seat service must have PricedInd field"
        assert first_seat['PricedInd'] is True, "Qatar Airways seats have PricedInd=true"
    
    def test_all_real_services_have_prices(self):
        """Verify all services in real data have Price field when PricedInd=true."""
        response = load_api_log('service_list/ServiceList_RS.json')
        services = response.get('Services', {}).get('Service', [])
        
        for idx, service in enumerate(services[:10]):  # Check first 10
            if service.get('PricedInd') is True:
                assert 'Price' in service, f"Service {idx} has PricedInd=true but no Price"
                assert isinstance(service['Price'], list), f"Service {idx} Price should be list"
                assert len(service['Price']) > 0, f"Service {idx} Price should not be empty"
    
    def test_no_pricing_required_for_real_qatar_data(self):
        """Real Qatar Airways data - services WITH PricedInd=true don't need pricing API."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Get service ObjectKeys that HAVE PricedInd=true (not missing)
        services = servicelist.get('Services', {}).get('Service', [])
        services_with_priced_ind_true = [s for s in services if s.get('PricedInd') is True]
        selected_services = [s['ObjectKey'] for s in services_with_priced_ind_true[:5]]
        
        # Get seat ObjectKeys (seats always have PricedInd in real data)
        seats = seatavailability.get('Services', {}).get('Service', [])
        selected_seats = [s['ObjectKey'] for s in seats[:3]]
        
        # Detect if pricing is required
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist,
            seatavailability_response=seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        # Should NOT require pricing for services/seats with PricedInd=true
        assert pricing_info['requires_pricing'] is False
        assert len(pricing_info['services_require_pricing']) == 0
        assert len(pricing_info['seats_require_pricing']) == 0
        assert pricing_info['total_items_require_pricing'] == 0
    
    def test_simulated_priced_ind_false_services(self):
        """Simulate services with PricedInd=false to trigger pricing API."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Deep copy to avoid modifying original
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        
        # Modify first 3 services to have PricedInd=false
        for service in services[:3]:
            service['PricedInd'] = False
            # Remove Price field to simulate unprice service
            if 'Price' in service:
                del service['Price']
        
        # Select these modified services
        selected_services = [s['ObjectKey'] for s in services[:3]]
        
        # Detect pricing requirement
        pricing_info = detect_pricing_required(
            servicelist_response=modified_servicelist,
            seatavailability_response=None,
            selected_services=selected_services,
            selected_seats=None
        )
        
        # Should require pricing API call
        assert pricing_info['requires_pricing'] is True
        assert len(pricing_info['services_require_pricing']) == 3
        assert pricing_info['total_items_require_pricing'] == 3
        
        # Verify the correct services are flagged
        for object_key in selected_services:
            assert object_key in pricing_info['services_require_pricing']
    
    def test_simulated_priced_ind_false_seats(self):
        """Simulate seats with PricedInd=false to trigger pricing API."""
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Deep copy to avoid modifying original
        modified_seatavailability = copy.deepcopy(seatavailability)
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        
        # Modify first 2 seats to have PricedInd=false
        for seat in seats[:2]:
            seat['PricedInd'] = False
            # Remove Price field
            if 'Price' in seat:
                del seat['Price']
        
        # Select these modified seats
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        # Detect pricing requirement
        pricing_info = detect_pricing_required(
            servicelist_response=None,
            seatavailability_response=modified_seatavailability,
            selected_services=None,
            selected_seats=selected_seats
        )
        
        # Should require pricing API call
        assert pricing_info['requires_pricing'] is True
        assert len(pricing_info['seats_require_pricing']) == 2
        assert pricing_info['total_items_require_pricing'] == 2
        
        # Verify the correct seats are flagged
        for object_key in selected_seats:
            assert object_key in pricing_info['seats_require_pricing']
    
    def test_mixed_priced_and_unpriced_items_real_data(self):
        """Test with mix of PricedInd=true (real) and PricedInd=false (simulated)."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        
        # Deep copy
        modified_servicelist = copy.deepcopy(servicelist)
        modified_seatavailability = copy.deepcopy(seatavailability)
        
        services = modified_servicelist.get('Services', {}).get('Service', [])
        seats = modified_seatavailability.get('Services', {}).get('Service', [])
        
        # Find services that already HAVE PricedInd=true (to keep them as priced)
        services_with_priced_true = [s for s in services if s.get('PricedInd') is True]
        
        # Select: 1 service we'll make false + 2 services that have PricedInd=true
        if len(services_with_priced_true) >= 3:
            # Use services that already have PricedInd=true
            test_services = services_with_priced_true[:3]
            # Modify only FIRST to PricedInd=false
            test_services[0]['PricedInd'] = False
            if 'Price' in test_services[0]:
                del test_services[0]['Price']
            
            selected_services = [s['ObjectKey'] for s in test_services]
        else:
            # Fallback if not enough services with PricedInd=true
            selected_services = []
        
        # Modify only FIRST seat to PricedInd=false (others stay true)
        seats[0]['PricedInd'] = False
        if 'Price' in seats[0]:
            del seats[0]['Price']
        
        # Select: 1 unpriced seat + 1 priced seat
        selected_seats = [s['ObjectKey'] for s in seats[:2]]
        
        # Detect pricing
        pricing_info = detect_pricing_required(
            servicelist_response=modified_servicelist,
            seatavailability_response=modified_seatavailability,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        # Should require pricing for the 2 unpriced items (1 service + 1 seat)
        assert pricing_info['requires_pricing'] is True
        if selected_services:  # Only check if we have services
            assert len(pricing_info['services_require_pricing']) == 1  # Only first service
        assert len(pricing_info['seats_require_pricing']) == 1  # Only first seat
        
        # Verify correct items flagged
        if selected_services:
            assert test_services[0]['ObjectKey'] in pricing_info['services_require_pricing']
        assert seats[0]['ObjectKey'] in pricing_info['seats_require_pricing']
    
    def test_real_service_structure_completeness(self):
        """Verify real services have required fields (PricedInd is optional)."""
        response = load_api_log('service_list/ServiceList_RS.json')
        services = response.get('Services', {}).get('Service', [])
        
        # PricedInd is NOT always present - this is by design
        required_fields = ['ObjectKey', 'ServiceID', 'Name']
        optional_fields = ['PricedInd', 'Price']
        
        for idx, service in enumerate(services[:10]):
            # Check required fields
            for field in required_fields:
                assert field in service, f"Service {idx} missing required field: {field}"
            
            # All services should have either PricedInd or Price (or both)
            has_pricing_info = 'PricedInd' in service or 'Price' in service
            assert has_pricing_info, f"Service {idx} must have PricedInd or Price field"
    
    def test_real_seat_structure_completeness(self):
        """Verify real seats have all required fields."""
        response = load_api_log('seat_availability/SeatAvailability_RS.json')
        seats = response.get('Services', {}).get('Service', [])
        
        required_fields = ['ObjectKey', 'ServiceID', 'Name', 'PricedInd']
        
        for idx, seat in enumerate(seats[:5]):
            for field in required_fields:
                assert field in seat, f"Seat {idx} missing {field}"
    
    def test_price_value_zero_vs_priced_ind_true(self):
        """
        Test that even with Price value of 0, if PricedInd=true, 
        no pricing API is needed (free services/seats).
        """
        seatavailability = load_api_log('seat_availability/SeatAvailability_RS.json')
        seats = seatavailability.get('Services', {}).get('Service', [])
        
        # Find seats with price value of 0 (they exist in real data)
        free_seats = [s for s in seats if s.get('Price', [{}])[0].get('Total', {}).get('value') == 0]
        
        if len(free_seats) > 0:
            # Even though price is 0, PricedInd should be true
            for seat in free_seats[:3]:
                assert seat.get('PricedInd') is True, "Free seats still have PricedInd=true"
            
            # Select these free seats
            selected_seats = [s['ObjectKey'] for s in free_seats[:2]]
            
            # Should NOT require pricing API (already priced, just free)
            pricing_info = detect_pricing_required(
                servicelist_response=None,
                seatavailability_response=seatavailability,
                selected_services=None,
                selected_seats=selected_seats
            )
            
            assert pricing_info['requires_pricing'] is False
            assert len(pricing_info['seats_require_pricing']) == 0


class TestPricedIndEdgeCases:
    """Test edge cases for PricedInd detection."""
    
    def test_missing_priced_ind_field_requires_pricing(self):
        """Services/seats missing PricedInd field should default to requiring pricing API."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        # Deep copy and remove PricedInd field from first 3 services
        modified_servicelist = copy.deepcopy(servicelist)
        services = modified_servicelist.get('Services', {}).get('Service', [])
        
        for service in services[:3]:
            # Remove PricedInd field entirely (not just set to false)
            if 'PricedInd' in service:
                del service['PricedInd']
            # Also remove Price to simulate completely unpriced service
            if 'Price' in service:
                del service['Price']
        
        # Select these services with missing PricedInd
        selected_services = [s['ObjectKey'] for s in services[:3]]
        
        # Detect pricing requirement
        pricing_info = detect_pricing_required(
            servicelist_response=modified_servicelist,
            seatavailability_response=None,
            selected_services=selected_services,
            selected_seats=None
        )
        
        # Missing PricedInd should default to False (requires pricing)
        assert pricing_info['requires_pricing'] is True, "Missing PricedInd should require pricing"
        assert len(pricing_info['services_require_pricing']) == 3
        assert pricing_info['total_items_require_pricing'] == 3
        
        # Verify the correct services are flagged
        for object_key in selected_services:
            assert object_key in pricing_info['services_require_pricing']
    
    def test_empty_selection_no_pricing_required(self):
        """When no services/seats selected, no pricing should be required."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist,
            seatavailability_response=None,
            selected_services=[],  # Empty selection
            selected_seats=None
        )
        
        assert pricing_info['requires_pricing'] is False
        assert pricing_info['total_items_require_pricing'] == 0
    
    def test_none_responses_no_pricing_required(self):
        """When responses are None, no pricing should be required."""
        pricing_info = detect_pricing_required(
            servicelist_response=None,
            seatavailability_response=None,
            selected_services=['some-key'],
            selected_seats=['some-seat']
        )
        
        assert pricing_info['requires_pricing'] is False
        assert pricing_info['total_items_require_pricing'] == 0
    
    def test_selected_service_not_found_in_response(self):
        """When selected service isn't in response, it shouldn't crash."""
        servicelist = load_api_log('service_list/ServiceList_RS.json')
        
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist,
            seatavailability_response=None,
            selected_services=['NON-EXISTENT-KEY-123'],
            selected_seats=None
        )
        
        # Should handle gracefully
        assert pricing_info is not None
        assert isinstance(pricing_info, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
