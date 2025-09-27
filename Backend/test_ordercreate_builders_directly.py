#!/usr/bin/env python3
"""
Test OrderCreate builders directly to verify the fixes are working.

This test directly calls the OrderCreate builders to see if they generate
correct SegmentReferences with segment keys instead of flight numbers.
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
    
    return data

def test_standard_ordercreate_builder():
    """Test the standard OrderCreate builder directly."""
    print("🧪 Testing Standard OrderCreate Builder Directly")
    print("=" * 60)
    
    try:
        from scripts.build_ordercreate_rq import generate_order_create_rq, _create_flight_to_segment_mapping
        
        # Load real API data
        data = load_api_logs()
        
        if not data.get('flight_price_response'):
            print("❌ No FlightPriceRS data found")
            return False
        
        # Extract the raw response data
        flight_price_data = data['flight_price_response']
        if 'response' in flight_price_data and 'raw_response' in flight_price_data['response']:
            flight_price_data = flight_price_data['response']['raw_response']
        
        # Test the flight to segment mapping function
        print("1️⃣ Testing Flight to Segment Mapping Function...")
        mapping = _create_flight_to_segment_mapping(flight_price_data)
        print(f"   Flight to segment mapping: {mapping}")
        
        if 'BA0322' in mapping and mapping['BA0322'] == 'FS1':
            print("   ✅ Mapping function works correctly!")
        else:
            print("   ❌ Mapping function failed!")
            return False
        
        # Test the OrderCreate builder
        print("\n2️⃣ Testing OrderCreate Builder...")
        
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
            selected_seats=["SO-597ccb29-2458-4deb-9731-5479ca43cc5e-OI-1"]  # From logs
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
        
        print(f"\n3️⃣ Checking Generated SegmentReferences:")
        print(f"   Found {len(segment_refs)} SegmentReferences")
        
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
            print("\n✅ SUCCESS: Standard OrderCreate builder generates correct SegmentReferences!")
            return True
        else:
            print("\n❌ FAILURE: Standard OrderCreate builder still uses flight numbers!")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_ordercreate_builder():
    """Test the enhanced OrderCreate builder directly."""
    print("\n🧪 Testing Enhanced OrderCreate Builder Directly")
    print("=" * 60)
    
    try:
        from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request
        
        # Load real API data
        data = load_api_logs()
        
        if not data.get('flight_price_response'):
            print("❌ No FlightPriceRS data found")
            return False
        
        # Extract the raw response data
        flight_price_data = data['flight_price_response']
        if 'response' in flight_price_data and 'raw_response' in flight_price_data['response']:
            flight_price_data = flight_price_data['response']['raw_response']
        
        # Test the enhanced OrderCreate builder
        print("1️⃣ Testing Enhanced OrderCreate Builder...")
        
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
        result = build_ordercreate_enhanced_request(
            flight_price_response=flight_price_data,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=data.get('seatavailability_response'),
            selected_seats=["SO-597ccb29-2458-4deb-9731-5479ca43cc5e-OI-1"]  # From logs
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
        
        print(f"\n2️⃣ Checking Generated SegmentReferences:")
        print(f"   Found {len(segment_refs)} SegmentReferences")
        
        all_use_segment_keys = True
        for ref in segment_refs:
            print(f"   {ref['path']}: {ref['values']}")
            
            for value in ref['values']:
                if value == 'FS1':
                    print(f"     ✅ {value} is a segment key (CORRECT!)")
                elif value in ['BA322', 'BA0322']:
                    print(f"     ❌ {value} is a flight number (should be FS1)")
                    all_use_segment_keys = False
                else:
                    print(f"     ⚠️  {value} is neither flight number nor segment key")
                    all_use_segment_keys = False
        
        if all_use_segment_keys:
            print("\n✅ SUCCESS: Enhanced OrderCreate builder generates correct SegmentReferences!")
            return True
        else:
            print("\n❌ FAILURE: Enhanced OrderCreate builder still uses flight numbers!")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Direct OrderCreate Builder Tests")
    print("=" * 60)
    
    # Test 1: Standard OrderCreate builder
    test1_result = test_standard_ordercreate_builder()
    
    # Test 2: Enhanced OrderCreate builder
    test2_result = test_enhanced_ordercreate_builder()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Standard OrderCreate Builder: {'PASSED' if test1_result else 'FAILED'}")
    print(f"✅ Enhanced OrderCreate Builder: {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The OrderCreate builders are working correctly with segment key mappings.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   The OrderCreate builders need additional fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
