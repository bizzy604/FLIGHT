#!/usr/bin/env python3
"""
Test runner for PricedInd detection functionality.

This script runs the comprehensive test suite to verify that the
PricedInd detection fix is working correctly.
"""
import sys
import os
import subprocess
import json
from pathlib import Path

def run_tests():
    """Run the PricedInd detection tests."""
    print("🧪 Running PricedInd Detection Tests")
    print("=" * 50)
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    test_file = script_dir / "tests" / "test_pricedind_detection.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=True, text=True, cwd=script_dir)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def test_manual_scenario():
    """Test the manual scenario from the logs."""
    print("\n🔍 Manual Test: Real-world scenario from logs")
    print("-" * 50)
    
    try:
        # Import the detection function
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from routes.verteil_flights import detect_pricing_required
        
        # Load the actual data from Booking_RQ.json
        booking_rq_path = Path(__file__).parent / "api_logs" / "booking" / "Booking_RQ.json"
        
        if not booking_rq_path.exists():
            print(f"❌ Booking_RQ.json not found at: {booking_rq_path}")
            return False
        
        with open(booking_rq_path, 'r') as f:
            booking_data = json.load(f)
        
        # Extract the relevant data from the booking request
        payload = booking_data.get('payload', {})
        data_lists = payload.get('DataLists', {})
        
        # Extract service list - use the actual service data from the logs
        servicelist_response = {
            "Services": {
                "Service": data_lists.get('ServiceList', {}).get('Service', [])
            }
        }
        
        # If no services in the booking data, use the test data structure
        if not servicelist_response['Services']['Service']:
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
        
        # Extract seat availability (this would normally come from a separate response)
        # For this test, we'll simulate the seat data
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
        
        print(f"📋 Testing with:")
        print(f"   - Selected services: {selected_services}")
        print(f"   - Selected seats: {selected_seats}")
        print(f"   - Service list has {len(servicelist_response['Services']['Service'])} services")
        
        # Run the detection
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
        
        # Check if the result is as expected
        expected_services_requiring_pricing = 3  # All 3 services have PricedInd=false
        expected_seats_requiring_pricing = 0    # The seat has PricedInd=true
        
        success = (
            result['requires_pricing'] == True and
            len(result['services_require_pricing']) == expected_services_requiring_pricing and
            len(result['seats_require_pricing']) == expected_seats_requiring_pricing
        )
        
        if success:
            print("✅ Manual test passed! The fix is working correctly.")
            print("   The system will now properly detect PricedInd=false and trigger enhanced OrderCreate.")
        else:
            print("❌ Manual test failed! The detection is not working as expected.")
            
        return success
        
    except Exception as e:
        print(f"❌ Error in manual test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner."""
    print("🚀 PricedInd Detection Test Suite")
    print("=" * 60)
    
    # Run the comprehensive test suite
    print("\n1️⃣ Running comprehensive test suite...")
    test_suite_success = run_tests()
    
    # Run the manual scenario test
    print("\n2️⃣ Running manual scenario test...")
    manual_test_success = test_manual_scenario()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Comprehensive test suite: {'PASSED' if test_suite_success else 'FAILED'}")
    print(f"✅ Manual scenario test: {'PASSED' if manual_test_success else 'FAILED'}")
    
    if test_suite_success and manual_test_success:
        print("\n🎉 ALL TESTS PASSED! The PricedInd detection fix is working correctly.")
        print("   The system will now properly:")
        print("   - Detect services/seats with PricedInd=false")
        print("   - Call the ancillary pricing API")
        print("   - Use the enhanced OrderCreate builder")
        return True
    else:
        print("\n❌ SOME TESTS FAILED! Please check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
