#!/usr/bin/env python3
"""
Quick test to verify PricedInd detection is working correctly.

This script tests the fix using the actual data from the logs
to ensure the system now properly detects PricedInd=false scenarios.
"""
import sys
import os
import json
from pathlib import Path

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_pricedind_detection():
    """Test the PricedInd detection using real data from logs."""
    print("🧪 Quick Test: PricedInd Detection Fix")
    print("=" * 50)
    
    try:
        # Import the detection function
        from routes.verteil_flights import detect_pricing_required
        
        # Create test data based on the actual Booking_RQ.json structure
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
                        "PricedInd": False,  # This should trigger pricing
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
                        "PricedInd": False,  # This should trigger pricing
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
                        "PricedInd": False,  # This should trigger pricing
                        "Price": [{"Total": {"value": 0.0, "Code": "INR"}}]
                    }
                ]
            }
        }
        
        # Simulate seat availability response
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
        
        # The selected services and seats from the logs
        selected_services = ["1-ServiceIdAF-29", "1-ServiceIdAF-15", "1-ServiceIdAF-27"]
        selected_seats = ["dddb827e-00fa-440d-9b82-7e00fa24001d"]
        
        print(f"📋 Test Data:")
        print(f"   - Selected services: {selected_services}")
        print(f"   - Selected seats: {selected_seats}")
        print(f"   - Services with PricedInd=false: 3")
        print(f"   - Seats with PricedInd=true: 1")
        
        # Run the detection
        print(f"\n🔍 Running detection...")
        result = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print(f"\n📊 Detection Result:")
        print(f"   - Requires pricing: {result['requires_pricing']}")
        print(f"   - Services requiring pricing: {result['services_require_pricing']}")
        print(f"   - Seats requiring pricing: {result['seats_require_pricing']}")
        print(f"   - Total items requiring pricing: {result['total_items_requiring_pricing']}")
        
        # Verify the result
        expected_services_requiring_pricing = 3  # All 3 services have PricedInd=false
        expected_seats_requiring_pricing = 0    # The seat has PricedInd=true
        
        success = (
            result['requires_pricing'] == True and
            len(result['services_require_pricing']) == expected_services_requiring_pricing and
            len(result['seats_require_pricing']) == expected_seats_requiring_pricing and
            result['total_items_requiring_pricing'] == expected_services_requiring_pricing
        )
        
        print(f"\n🎯 Expected vs Actual:")
        print(f"   - Requires pricing: True ✓" if result['requires_pricing'] else "   - Requires pricing: True ❌")
        print(f"   - Services requiring pricing: {expected_services_requiring_pricing} ✓" if len(result['services_require_pricing']) == expected_services_requiring_pricing else f"   - Services requiring pricing: {expected_services_requiring_pricing} ❌ (got {len(result['services_require_pricing'])})")
        print(f"   - Seats requiring pricing: {expected_seats_requiring_pricing} ✓" if len(result['seats_require_pricing']) == expected_seats_requiring_pricing else f"   - Seats requiring pricing: {expected_seats_requiring_pricing} ❌ (got {len(result['seats_require_pricing'])})")
        
        if success:
            print(f"\n✅ TEST PASSED!")
            print(f"   The PricedInd detection fix is working correctly.")
            print(f"   The system will now:")
            print(f"   - Detect that pricing is required for 3 services")
            print(f"   - Call the ancillary pricing API")
            print(f"   - Use the enhanced OrderCreate builder")
            print(f"   - Properly handle PricedInd=false scenarios")
        else:
            print(f"\n❌ TEST FAILED!")
            print(f"   The detection is not working as expected.")
            print(f"   Please check the implementation.")
            
        return success
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases to ensure robustness."""
    print(f"\n🔍 Testing Edge Cases:")
    print("-" * 30)
    
    try:
        from routes.verteil_flights import detect_pricing_required
        
        # Test 1: No selected items
        result = detect_pricing_required()
        assert result['requires_pricing'] == False, "No items should not require pricing"
        print("✅ No selected items: PASSED")
        
        # Test 2: All PricedInd=true
        servicelist_response = {
            "Services": {
                "Service": [{
                    "ObjectKey": "1-ServiceIdAF-15",
                    "PricedInd": True
                }]
            }
        }
        result = detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=["1-ServiceIdAF-15"]
        )
        assert result['requires_pricing'] == False, "PricedInd=true should not require pricing"
        print("✅ All PricedInd=true: PASSED")
        
        # Test 3: Mixed scenarios
        servicelist_response = {
            "Services": {
                "Service": [
                    {"ObjectKey": "1-ServiceIdAF-15", "PricedInd": False},
                    {"ObjectKey": "1-ServiceIdAF-30", "PricedInd": True}
                ]
            }
        }
        result = detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=["1-ServiceIdAF-15", "1-ServiceIdAF-30"]
        )
        assert result['requires_pricing'] == True, "Mixed scenario should require pricing"
        assert len(result['services_require_pricing']) == 1, "Only one service should require pricing"
        print("✅ Mixed scenarios: PASSED")
        
        print("✅ All edge cases passed!")
        return True
        
    except Exception as e:
        print(f"❌ Edge case test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 PricedInd Detection Quick Test")
    print("=" * 60)
    
    # Test the main scenario
    main_test_success = test_pricedind_detection()
    
    # Test edge cases
    edge_case_success = test_edge_cases()
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📋 TEST SUMMARY")
    print(f"=" * 60)
    print(f"✅ Main scenario test: {'PASSED' if main_test_success else 'FAILED'}")
    print(f"✅ Edge cases test: {'PASSED' if edge_case_success else 'FAILED'}")
    
    if main_test_success and edge_case_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   The PricedInd detection fix is working correctly.")
        print(f"   The system will now properly handle PricedInd=false scenarios.")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED!")
        print(f"   Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
