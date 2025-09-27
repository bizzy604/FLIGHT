#!/usr/bin/env python3
"""
Test the complete OrderCreate flow with real data to verify NDC compliance.

This test simulates the complete OrderCreate generation process using
real API logs data to ensure the final payload follows NDC documentation.
"""
import sys
import os
import json
from pathlib import Path

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def load_api_logs():
    """Load all the API logs data."""
    logs_dir = Path("api_logs")
    
    # Load all the API responses
    data = {}
    
    # Load FlightPriceRS
    flight_price_file = logs_dir / "flight_price" / "FlightPrice_RS.json"
    if flight_price_file.exists():
        with open(flight_price_file, 'r') as f:
            data['flight_price_response'] = json.load(f)
    
    # Load SeatAvailabilityRS
    seat_availability_file = logs_dir / "seat_availability" / "SeatAvailability_RS.json"
    if seat_availability_file.exists():
        with open(seat_availability_file, 'r') as f:
            data['seatavailability_response'] = json.load(f)
    
    # Load ServiceListRS
    service_list_file = logs_dir / "service_list" / "ServiceList_RS.json"
    if service_list_file.exists():
        with open(service_list_file, 'r') as f:
            data['servicelist_response'] = json.load(f)
    
    # Load current OrderCreate payload for comparison
    booking_rq_file = logs_dir / "booking" / "Booking_RQ.json"
    if booking_rq_file.exists():
        with open(booking_rq_file, 'r') as f:
            data['current_ordercreate'] = json.load(f)
    
    return data

def test_complete_ordercreate_flow():
    """Test the complete OrderCreate flow with real data."""
    print("🧪 Testing Complete OrderCreate Flow with Real Data")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('flight_price_response'):
        print("❌ No FlightPriceRS data found")
        return False
    
    if not data.get('seatavailability_response'):
        print("❌ No SeatAvailabilityRS data found")
        return False
    
    try:
        from scripts.build_ordercreate_rq import generate_order_create_rq, _create_flight_to_segment_mapping
        
        # Extract the raw response data
        flight_price_data = data['flight_price_response']
        if 'response' in flight_price_data and 'raw_response' in flight_price_data['response']:
            flight_price_data = flight_price_data['response']['raw_response']
        
        # Test the flight to segment mapping
        print("1️⃣ Testing Flight to Segment Mapping...")
        mapping = _create_flight_to_segment_mapping(flight_price_data)
        print(f"   Flight to segment mapping: {mapping}")
        
        if 'BA0322' in mapping and mapping['BA0322'] == 'FS1':
            print("   ✅ Mapping function works correctly!")
        else:
            print("   ❌ Mapping function failed!")
            return False
        
        # Extract seat data from SeatAvailabilityRS
        print("\n2️⃣ Extracting Seat Data from SeatAvailabilityRS...")
        seat_data = data['seatavailability_response']
        
        # Find the seat service that matches the ObjectKey from the current OrderCreate
        seat_services = seat_data.get('Services', {}).get('Service', [])
        if not isinstance(seat_services, list):
            seat_services = [seat_services] if seat_services else []
        
        print(f"   Found {len(seat_services)} seat services")
        
        # Look for the specific seat service from the current OrderCreate
        target_seat_key = "SO-597ccb29-2458-4deb-9731-5479ca43cc5e-OI-1"
        matching_seat_service = None
        
        for service in seat_services:
            if service.get('ObjectKey') == target_seat_key:
                matching_seat_service = service
                break
        
        if matching_seat_service:
            print(f"   ✅ Found matching seat service: {target_seat_key}")
            print(f"   Seat service associations: {len(matching_seat_service.get('Associations', []))}")
        else:
            print(f"   ⚠️  Seat service {target_seat_key} not found in SeatAvailabilityRS")
            print(f"   Available seat services: {[s.get('ObjectKey') for s in seat_services[:3]]}")
        
        # Test OrderCreate generation with real data
        print("\n3️⃣ Testing OrderCreate Generation...")
        
        passengers_data = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",
                "Name": {"Surname": {"value": "Test"}, "Given": [{"value": "User"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1990-01-01"}}
            }
        ]
        
        payment_info = {"Method": "Cash", "Amount": {"value": 1100, "Code": "USD"}}
        
        # Generate OrderCreate payload
        result = generate_order_create_rq(
            flight_price_response=flight_price_data,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=data.get('seatavailability_response'),
            selected_seats=[target_seat_key] if matching_seat_service else []
        )
        
        print(f"   Generated OrderCreate payload with {len(result.get('Query', {}).get('OrderItems', {}).get('OfferItem', []))} offer items")
        
        # Check SegmentReferences in the generated payload
        def find_segment_references(obj, path=""):
            references = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "SegmentReferences" and isinstance(value, dict):
                        refs = value.get("value", [])
                        if refs:
                            references.append({
                                "path": path + f".{key}",
                                "values": refs
                            })
                    else:
                        references.extend(find_segment_references(value, f"{path}.{key}" if path else key))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    references.extend(find_segment_references(item, f"{path}[{i}]"))
            return references
        
        segment_refs = find_segment_references(result)
        
        print(f"\n4️⃣ Checking Generated SegmentReferences:")
        print(f"   Found {len(segment_refs)} SegmentReferences")
        
        if segment_refs:
            all_use_segment_keys = True
            for ref in segment_refs:
                print(f"   {ref['path']}: {ref['values']}")
                
                for value in ref['values']:
                    if value == 'FS1':
                        print(f"     ✅ {value} is a segment key (CORRECT!)")
                    elif value in mapping.keys():
                        print(f"     ❌ {value} is a flight number (should be {mapping[value]})")
                        all_use_segment_keys = False
                    else:
                        print(f"     ⚠️  {value} is neither flight number nor segment key")
                        all_use_segment_keys = False
            
            if all_use_segment_keys:
                print("\n✅ SUCCESS: Generated OrderCreate uses correct segment keys!")
                return True
            else:
                print("\n❌ FAILURE: Generated OrderCreate still uses flight numbers!")
                return False
        else:
            print("   ⚠️  No SegmentReferences found in generated payload")
            print("   This might be because no seats were processed")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_current_ordercreate():
    """Compare the generated OrderCreate with the current one."""
    print("\n🧪 Comparing with Current OrderCreate Payload")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('current_ordercreate'):
        print("❌ No current OrderCreate payload found")
        return False
    
    current_payload = data['current_ordercreate'].get('payload', {})
    
    # Find SegmentReferences in current payload
    def find_segment_references(obj, path=""):
        references = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "SegmentReferences" and isinstance(value, dict):
                    refs = value.get("value", [])
                    if refs:
                        references.append({
                            "path": path + f".{key}",
                            "values": refs
                        })
                else:
                    references.extend(find_segment_references(value, f"{path}.{key}" if path else key))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                references.extend(find_segment_references(item, f"{path}[{i}]"))
        return references
    
    current_refs = find_segment_references(current_payload)
    
    print(f"📋 Current OrderCreate SegmentReferences:")
    print(f"   Found {len(current_refs)} SegmentReferences")
    
    for ref in current_refs:
        print(f"   {ref['path']}: {ref['values']}")
        
        for value in ref['values']:
            if value == 'FS1':
                print(f"     ✅ {value} is a segment key (CORRECT!)")
            elif value in ['BA322', 'BA0322']:
                print(f"     ❌ {value} is a flight number (should be FS1)")
            else:
                print(f"     ⚠️  {value} is neither flight number nor segment key")
    
    return True

def main():
    """Main test function."""
    print("🚀 Complete OrderCreate Flow Test with Real Data")
    print("=" * 60)
    
    # Test 1: Complete OrderCreate flow
    test1_result = test_complete_ordercreate_flow()
    
    # Test 2: Compare with current OrderCreate
    test2_result = compare_with_current_ordercreate()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Complete OrderCreate Flow: {'PASSED' if test1_result else 'FAILED'}")
    print(f"✅ Current OrderCreate Analysis: {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The OrderCreate flow is working correctly with NDC compliance.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   The OrderCreate flow needs additional work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
