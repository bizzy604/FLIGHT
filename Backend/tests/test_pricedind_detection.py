"""
Test suite for PricedInd detection functionality.

This test verifies that the system correctly detects when PricedInd=false
and triggers the enhanced OrderCreate builder with ancillary pricing.
"""
import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from routes.verteil_flights import detect_pricing_required
from scripts.build_flightprice_ancillary_rq import detect_pricing_required as script_detect_pricing_required


class TestPricedIndDetection:
    """Test cases for PricedInd detection functionality."""
    
    def test_services_priced_ind_false_detection(self):
        """Test detection of services with PricedInd=false."""
        # Mock service list response with PricedInd=false services
        servicelist_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "1-ServiceIdAF-15",
                        "Name": {"value": "BAG:LUGGAGE-FIRST ADDITIONAL BAG"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 8812.0, "Code": "INR"}}]
                    },
                    {
                        "ObjectKey": "1-ServiceIdAF-27", 
                        "Name": {"value": "DISABILITY:WCHR - Wheelchair request"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    },
                    {
                        "ObjectKey": "1-ServiceIdAF-29",
                        "Name": {"value": "DISABILITY:BLND - Visual impairment"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    }
                ]
            }
        }
        
        selected_services = ["1-ServiceIdAF-15", "1-ServiceIdAF-27", "1-ServiceIdAF-29"]
        
        # Test the detection
        result = detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=selected_services
        )
        
        # Assertions
        assert result['requires_pricing'] == True
        assert len(result['services_require_pricing']) == 3
        assert "1-ServiceIdAF-15" in result['services_require_pricing']
        assert "1-ServiceIdAF-27" in result['services_require_pricing']
        assert "1-ServiceIdAF-29" in result['services_require_pricing']
        assert result['total_items_requiring_pricing'] == 3
        
    def test_services_priced_ind_true_no_pricing_required(self):
        """Test that services with PricedInd=true don't require pricing."""
        servicelist_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "1-ServiceIdAF-15",
                        "Name": {"value": "BAG:LUGGAGE-FIRST ADDITIONAL BAG"},
                        "PricedInd": True,
                        "Price": [{"Total": {"value": 8812.0, "Code": "INR"}}]
                    }
                ]
            }
        }
        
        selected_services = ["1-ServiceIdAF-15"]
        
        result = detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=selected_services
        )
        
        assert result['requires_pricing'] == False
        assert len(result['services_require_pricing']) == 0
        assert result['total_items_requiring_pricing'] == 0
        
    def test_seats_priced_ind_false_detection(self):
        """Test detection of seats with PricedInd=false using ObjectKeys."""
        # Mock seat availability response with PricedInd=false seat
        seatavailability_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "dddb827e-00fa-440d-9b82-7e00fa24001d",
                        "Name": {"value": "Seat dddb827e-00fa-440d-9b82-7e00fa24001d"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    }
                ]
            }
        }
        
        selected_seats = ["dddb827e-00fa-440d-9b82-7e00fa24001d"]
        
        result = detect_pricing_required(
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        assert result['requires_pricing'] == True
        assert len(result['seats_require_pricing']) == 1
        assert "dddb827e-00fa-440d-9b82-7e00fa24001d" in result['seats_require_pricing']
        assert result['total_items_requiring_pricing'] == 1
        
    def test_seats_priced_ind_true_no_pricing_required(self):
        """Test that seats with PricedInd=true don't require pricing."""
        seatavailability_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "dddb827e-00fa-440d-9b82-7e00fa24001d",
                        "Name": {"value": "Seat dddb827e-00fa-440d-9b82-7e00fa24001d"},
                        "PricedInd": True,
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    }
                ]
            }
        }
        
        selected_seats = ["dddb827e-00fa-440d-9b82-7e00fa24001d"]
        
        result = detect_pricing_required(
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        assert result['requires_pricing'] == False
        assert len(result['seats_require_pricing']) == 0
        assert result['total_items_requiring_pricing'] == 0
        
    def test_mixed_priced_ind_scenarios(self):
        """Test mixed scenarios with both PricedInd=true and PricedInd=false items."""
        servicelist_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "1-ServiceIdAF-15",
                        "PricedInd": False  # Requires pricing
                    },
                    {
                        "ObjectKey": "1-ServiceIdAF-30",
                        "PricedInd": True   # Doesn't require pricing
                    }
                ]
            }
        }
        
        seatavailability_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "dddb827e-00fa-440d-9b82-7e00fa24001d",
                        "PricedInd": True   # Doesn't require pricing
                    }
                ]
            }
        }
        
        selected_services = ["1-ServiceIdAF-15", "1-ServiceIdAF-30"]
        selected_seats = ["dddb827e-00fa-440d-9b82-7e00fa24001d"]
        
        result = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        # Should require pricing because of the service with PricedInd=false
        assert result['requires_pricing'] == True
        assert len(result['services_require_pricing']) == 1
        assert "1-ServiceIdAF-15" in result['services_require_pricing']
        assert len(result['seats_require_pricing']) == 0
        assert result['total_items_requiring_pricing'] == 1
        
    def test_no_selected_items(self):
        """Test when no services or seats are selected."""
        result = detect_pricing_required()
        
        assert result['requires_pricing'] == False
        assert len(result['services_require_pricing']) == 0
        assert len(result['seats_require_pricing']) == 0
        assert result['total_items_requiring_pricing'] == 0
        
    def test_script_function_consistency(self):
        """Test that the script function produces the same results as the route function."""
        servicelist_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "1-ServiceIdAF-15",
                        "PricedInd": False
                    }
                ]
            }
        }
        
        selected_services = ["1-ServiceIdAF-15"]
        
        # Test both functions
        route_result = detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=selected_services
        )
        
        script_result = script_detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=selected_services
        )
        
        # Both should produce the same result
        assert route_result['requires_pricing'] == script_result['requires_pricing']
        assert route_result['services_require_pricing'] == script_result['services_require_pricing']
        assert route_result['total_items_requiring_pricing'] == script_result['total_items_require_pricing']
        
    def test_real_world_scenario_from_logs(self):
        """Test using the actual data structure from the Booking_RQ.json logs."""
        # This test uses the actual data structure from the logs
        servicelist_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "1-ServiceIdAF-15",
                        "ServiceID": {
                            "ObjectKey": "bc346ba6-dc31-49cc-b46b-a6dc3169000f",
                            "value": "SRV14",
                            "Owner": "AF"
                        },
                        "Name": {"value": "BAG:LUGGAGE-FIRST ADDITIONAL BAG"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 8812.0, "Code": "INR"}}]
                    },
                    {
                        "ObjectKey": "1-ServiceIdAF-27",
                        "ServiceID": {
                            "ObjectKey": "bc346ba6-dc31-49cc-b46b-a6dc3169001b",
                            "value": "SRV28",
                            "Owner": "AF"
                        },
                        "Name": {"value": "DISABILITY:WCHR - Wheelchair request - Stairs OK"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    },
                    {
                        "ObjectKey": "1-ServiceIdAF-29",
                        "ServiceID": {
                            "ObjectKey": "bc346ba6-dc31-49cc-b46b-a6dc3169001d",
                            "value": "SRV30",
                            "Owner": "AF"
                        },
                        "Name": {"value": "DISABILITY:BLND - Visual impairment"},
                        "PricedInd": False,
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    }
                ]
            }
        }
        
        seatavailability_response = {
            "Services": {
                "Service": [
                    {
                        "ObjectKey": "dddb827e-00fa-440d-9b82-7e00fa24001d",
                        "ServiceID": {"value": "SERVICE-dddb827e-00fa-440d-9b82-7e00fa24001d"},
                        "Name": {"value": "Seat dddb827e-00fa-440d-9b82-7e00fa24001d"},
                        "PricedInd": True,  # This seat is already priced
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    }
                ]
            }
        }
        
        selected_services = ["1-ServiceIdAF-29", "1-ServiceIdAF-15", "1-ServiceIdAF-27"]
        selected_seats = ["dddb827e-00fa-440d-9b82-7e00fa24001d"]
        
        result = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        # Should require pricing because of the 3 services with PricedInd=false
        assert result['requires_pricing'] == True
        assert len(result['services_require_pricing']) == 3
        assert "1-ServiceIdAF-15" in result['services_require_pricing']
        assert "1-ServiceIdAF-27" in result['services_require_pricing']
        assert "1-ServiceIdAF-29" in result['services_require_pricing']
        assert len(result['seats_require_pricing']) == 0  # Seat has PricedInd=true
        assert result['total_items_requiring_pricing'] == 3
        
    def test_edge_case_empty_responses(self):
        """Test edge cases with empty or malformed responses."""
        # Test with empty service list
        result = detect_pricing_required(
            servicelist_response={"Services": {"Service": []}},
            selected_services=["1-ServiceIdAF-15"]
        )
        assert result['requires_pricing'] == False
        
        # Test with None responses
        result = detect_pricing_required(
            servicelist_response=None,
            seatavailability_response=None,
            selected_services=None,
            selected_seats=None
        )
        assert result['requires_pricing'] == False
        
        # Test with malformed service list (single service instead of list)
        result = detect_pricing_required(
            servicelist_response={
                "Services": {
                    "Service": {
                        "ObjectKey": "1-ServiceIdAF-15",
                        "PricedInd": False
                    }
                }
            },
            selected_services=["1-ServiceIdAF-15"]
        )
        assert result['requires_pricing'] == True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
