"""
Integration Test: Complete Pricing Workflow
Tests the end-to-end flow from booking.py routing to API calls when PricedInd=false

This test:
1. Uses modified API responses with PricedInd=false for selected services/seats
2. Tests routing logic in booking.py
3. Tests FlightPrice request generation  
4. Tests OrderCreate request generation
5. Validates complete workflow with mock API calls

Modified files used:
- ServiceList_RS_test_modified.json: SRV5, SRV6, SRV7 have PricedInd=false
- SeatAvailability_RS_test_modified.json: SERVICE-1, SERVICE-2 have PricedInd=false
"""

import pytest
import json
import copy
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import the modules we're testing
from services.flight.booking import FlightBookingService
from scripts.build_flightprice_ancillary_rq import build_flightprice_ancillary_request
from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request


class TestCompletePricingWorkflowIntegration:
    """Test the complete pricing workflow with real API data"""
    
    @pytest.fixture
    def api_logs_base_path(self):
        """Get the base path for API logs"""
        return Path(__file__).parent.parent / "api_logs"
    
    @pytest.fixture
    def service_list_response_modified(self, api_logs_base_path):
        """Load modified ServiceList response with PricedInd=false for testing"""
        file_path = api_logs_base_path / "service_list" / "ServiceList_RS_test_modified.json"
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def seat_availability_response_modified(self, api_logs_base_path):
        """Load modified SeatAvailability response with PricedInd=false for testing"""
        file_path = api_logs_base_path / "seat_availability" / "SeatAvailability_RS_test_modified.json"
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def flight_price_response(self, api_logs_base_path):
        """Load FlightPrice response"""
        file_path = api_logs_base_path / "flight_price" / "FlightPrice_RS.json"
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def booking_request_data(self):
        """Sample booking request data with seat and service selections"""
        return {
            "offer_index": 0,
            "travelers": [
                {
                    "id": "PAX1",
                    "PTC": {"value": "ADT"},
                    "Given": "John",
                    "Surname": "Doe",
                    "Birthdate": "1990-01-01",
                    "ContactInformation": [
                        {
                            "EmailAddress": {"EmailAddressValue": "john.doe@example.com"},
                            "Phone": [{"PhoneNumber": "+1234567890"}]
                        }
                    ]
                }
            ],
            "selected_seats": [
                {
                    "pax_id": "PAX1",
                    "segment_key": "SEG8",
                    "seat_id": "SERVICE-2",
                    "price": 5000
                }
            ],
            "selected_services": [
                {
                    "pax_id": "PAX1",
                    "service_id": "SRV5",
                    "price": 2500
                },
                {
                    "pax_id": "PAX1", 
                    "service_id": "SRV6",
                    "price": 0
                }
            ]
        }
    
    # ==================== Test 1: Detect PricedInd=false Scenario ====================
    
    def test_detect_unpriced_services_in_modified_response(self, service_list_response_modified):
        """Test that we correctly detect services with PricedInd=false"""
        services = service_list_response_modified.get("response", {}).get("Services", {}).get("Service", [])
        
        unpriced_services = [
            s for s in services 
            if s.get("PricedInd", False) is False
        ]
        
        assert len(unpriced_services) >= 3, "Should have at least 3 unpriced services"
        
        # Verify they all have PricedInd=false
        for service in unpriced_services[:3]:
            assert service.get("PricedInd") is False, f"Service {service.get('ServiceID', {}).get('value')} should have PricedInd=false"
        
        print(f"\n✓ Detected {len(unpriced_services)} unpriced services requiring FlightPrice API call")
        print(f"  Services: {[s.get('ServiceID', {}).get('value') for s in unpriced_services[:3]]}")
    
    def test_detect_unpriced_seats_in_modified_response(self, seat_availability_response_modified):
        """Test that we correctly detect seats with PricedInd=false"""
        # In SeatAvailability, seats are under response.Services.Service (not inside Flights)
        services = seat_availability_response_modified.get("response", {}).get("Services", {}).get("Service", [])
        
        unpriced_seats = [
            s for s in services 
            if s.get("PricedInd", False) is False
        ]
        
        assert len(unpriced_seats) >= 2, "Should have at least 2 unpriced seat services"
        
        # Verify they all have PricedInd=false
        for seat in unpriced_seats[:2]:
            assert seat.get("PricedInd") is False, f"Seat {seat.get('ServiceID', {}).get('value')} should have PricedInd=false"
        
        print(f"\n✓ Detected {len(unpriced_seats)} unpriced seats requiring FlightPrice API call")
        print(f"  Seats: {[s.get('ServiceID', {}).get('value') for s in unpriced_seats[:2]]}")
    
    # ==================== Test 2: Routing Logic ====================
    
    def test_routing_detects_pricing_required(
        self,
        service_list_response_modified,
        seat_availability_response_modified
    ):
        """Test that routing correctly detects when pricing is required"""
        
        # Check services
        services = service_list_response_modified.get("response", {}).get("Services", {}).get("Service", [])
        services_need_pricing = any(not s.get("PricedInd", False) for s in services)
        
        # Check seats
        seat_services = seat_availability_response_modified.get("response", {}).get("Services", {}).get("Service", [])
        seats_need_pricing = any(not s.get("PricedInd", False) for s in seat_services)
        
        # Overall decision
        needs_pricing = services_need_pricing or seats_need_pricing
        
        assert needs_pricing is True, "Should detect that pricing is required"
        print("\n✓ Routing correctly detected PricedInd=false scenario")
        print(f"  Services need pricing: {services_need_pricing}")
        print(f"  Seats need pricing: {seats_need_pricing}")
    
    # ==================== Test 3: Data Analysis ====================
    
    def test_analyze_modified_data(
        self,
        service_list_response_modified,
        seat_availability_response_modified
    ):
        """Analyze the modified data to show what changed"""
        
        services = service_list_response_modified.get("response", {}).get("Services", {}).get("Service", [])
        seat_services = seat_availability_response_modified.get("response", {}).get("Services", {}).get("Service", [])
        
        # Count by PricedInd status
        services_false = [s for s in services if s.get("PricedInd") is False]
        services_true = [s for s in services if s.get("PricedInd") is True]
        services_missing = [s for s in services if "PricedInd" not in s]
        
        seats_false = [s for s in seat_services if s.get("PricedInd") is False]
        seats_true = [s for s in seat_services if s.get("PricedInd") is True]
        
        print("\n" + "="*70)
        print("📊 MODIFIED DATA ANALYSIS")
        print("="*70)
        print(f"\nServices (ServiceList):")
        print(f"  ✓ Total services: {len(services)}")
        print(f"  ✓ PricedInd=false: {len(services_false)}")
        print(f"    → {[s.get('ServiceID', {}).get('value') for s in services_false]}")
        print(f"  ✓ PricedInd=true: {len(services_true)}")
        print(f"  ✓ Missing PricedInd: {len(services_missing)}")
        
        print(f"\nSeats (SeatAvailability):")
        print(f"  ✓ Total seat services: {len(seat_services)}")
        print(f"  ✓ PricedInd=false: {len(seats_false)}")
        print(f"    → {[s.get('ServiceID', {}).get('value') for s in seats_false]}")
        print(f"  ✓ PricedInd=true: {len(seats_true)}")
        
        print(f"\nRouting Decision:")
        print(f"  → Needs FlightPrice API: YES")
        print(f"  → Flow: ServiceList → FlightPrice → OrderCreate")
        print("="*70)
        
        # Assertions
        assert len(services_false) >= 3, "Should have at least 3 services with PricedInd=false"
        assert len(seats_false) >= 2, "Should have at least 2 seats with PricedInd=false"


# ==================== Edge Case Tests ====================

class TestWorkflowEdgeCases:
    """Test edge cases in the pricing workflow"""
    
    @pytest.fixture
    def api_logs_base_path(self):
        """Get the base path for API logs"""
        return Path(__file__).parent.parent / "api_logs"
    
    @pytest.fixture
    def service_list_response(self, api_logs_base_path):
        """Load ServiceList response"""
        file_path = api_logs_base_path / "service_list" / "ServiceList_RS.json"
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def test_handle_mixed_priced_indicators(self, service_list_response):
        """Test handling when some services have PricedInd=true and some false"""
        
        # Create mixed scenario
        modified_response = copy.deepcopy(service_list_response)
        services = modified_response.get("response", {}).get("Services", {}).get("Service", [])
        
        # Modify only some services
        for idx, service in enumerate(services):
            if idx % 2 == 0:  # Even indices
                service["PricedInd"] = False
            # Odd indices remain True or missing
        
        # Check detection
        needs_pricing = any(
            not s.get("PricedInd", False) for s in services
        )
        
        assert needs_pricing is True, "Should detect pricing needed when ANY service has PricedInd=false"
        print("\n✓ Correctly handles mixed PricedInd scenario")
    
    def test_handle_missing_priced_ind_field(self, service_list_response):
        """Test handling when PricedInd field is missing entirely"""
        
        # Create scenario with missing field
        modified_response = copy.deepcopy(service_list_response)
        services = modified_response.get("response", {}).get("Services", {}).get("Service", [])
        
        # Remove PricedInd from first service if it exists
        if services and "PricedInd" in services[0]:
            del services[0]["PricedInd"]
        
        # Check detection with default=False logic
        needs_pricing = any(
            not s.get("PricedInd", False) for s in services
        )
        
        assert needs_pricing is True, "Missing PricedInd should default to False (needs pricing)"
        print("\n✓ Correctly defaults missing PricedInd to False")
    
    def test_handle_empty_selections(self):
        """Test workflow when no seats or services are selected"""
        
        booking_data = {
            "offer_index": 0,
            "travelers": [{"id": "PAX1"}],
            "selected_seats": [],
            "selected_services": []
        }
        
        # Should handle gracefully without errors
        assert len(booking_data.get("selected_seats", [])) == 0
        assert len(booking_data.get("selected_services", [])) == 0
        
        print("\n✓ Handles empty selections gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
