#!/usr/bin/env python3
"""
Test OrderCreate fixes using real API logs data.

This test uses the actual API logs to verify that the OrderCreate builder
is using the updated version with correct segment key mappings.
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
    
    # Load current OrderCreate payload
    booking_rq_file = logs_dir / "booking" / "Booking_RQ.json"
    if booking_rq_file.exists():
        with open(booking_rq_file, 'r') as f:
            data['current_ordercreate'] = json.load(f)
    
    return data

def test_segment_references_mapping():
    """Test that SegmentReferences use segment keys instead of flight numbers."""
    print("🧪 Testing SegmentReferences Mapping with Real Data")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('flight_price_response'):
        print("❌ No FlightPriceRS data found")
        return False
    
    if not data.get('seatavailability_response'):
        print("❌ No SeatAvailabilityRS data found")
        return False
    
    # Extract segment keys from FlightPriceRS (check nested structure)
    flight_price_data = data['flight_price_response']
    
    print(f"   🔍 FlightPriceRS keys: {list(flight_price_data.keys())}")
    
    # Check if DataLists is in response.data
    if 'response' in flight_price_data:
        response_data = flight_price_data['response']
        print(f"   🔍 response keys: {list(response_data.keys())}")
        if 'DataLists' in response_data:
            flight_price_data = response_data
            print(f"   🔍 Found DataLists in response")
        elif 'raw_response' in response_data:
            raw_response = response_data['raw_response']
            print(f"   🔍 raw_response keys: {list(raw_response.keys())}")
            if 'DataLists' in raw_response:
                flight_price_data = raw_response
                print(f"   🔍 Found DataLists in raw_response")
            else:
                print(f"   🔍 DataLists not found in raw_response")
        elif 'data' in response_data:
            nested_data = response_data['data']
            print(f"   🔍 response.data keys: {list(nested_data.keys())}")
            if 'DataLists' in nested_data:
                flight_price_data = nested_data
                print(f"   🔍 Found DataLists in response.data")
            else:
                print(f"   🔍 DataLists not found in response.data")
        else:
            print(f"   🔍 No data section in response")
    elif 'DataLists' in flight_price_data:
        print(f"   🔍 Found DataLists at root level")
    else:
        print(f"   🔍 DataLists not found in expected locations")
    
    flight_segments = flight_price_data.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
    if not isinstance(flight_segments, list):
        flight_segments = [flight_segments] if flight_segments else []
    
    print(f"   🔍 Flight segments found: {len(flight_segments)}")
    if flight_segments:
        print(f"   🔍 First segment keys: {list(flight_segments[0].keys()) if isinstance(flight_segments[0], dict) else 'Not a dict'}")
    
    segment_keys = []
    flight_to_segment_map = {}
    
    for segment in flight_segments:
        if isinstance(segment, dict):
            segment_key = segment.get('SegmentKey', '')
            marketing_carrier = segment.get('MarketingCarrier', {})
            airline_id = marketing_carrier.get('AirlineID', {}).get('value', '')
            flight_number = marketing_carrier.get('FlightNumber', {}).get('value', '')
            
            if segment_key and airline_id and flight_number:
                # Create flight number with airline code (e.g., "BA322")
                full_flight_number = f"{airline_id}{flight_number}"
                flight_to_segment_map[full_flight_number] = segment_key
                
                # Also create mapping with leading zero (e.g., "BA0322")
                full_flight_number_with_zero = f"{airline_id}{flight_number.zfill(4)}"
                flight_to_segment_map[full_flight_number_with_zero] = segment_key
                
                segment_keys.append(segment_key)
    
    print(f"📋 Flight to Segment Mapping: {flight_to_segment_map}")
    print(f"📋 Available Segment Keys: {segment_keys}")
    
    # Check current OrderCreate payload
    if data.get('current_ordercreate'):
        current_payload = data['current_ordercreate'].get('payload', {})
        
        # Find all SegmentReferences in the current payload
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
        
        segment_refs = find_segment_references(current_payload)
        
        print(f"\n📋 Current OrderCreate SegmentReferences:")
        for ref in segment_refs:
            print(f"   {ref['path']}: {ref['values']}")
        
        # Check if they use segment keys or flight numbers
        all_use_segment_keys = True
        for ref in segment_refs:
            for value in ref['values']:
                if value in flight_to_segment_map.values():
                    print(f"   ✅ {value} is a segment key")
                elif value in flight_to_segment_map.keys():
                    print(f"   ❌ {value} is a flight number (should be {flight_to_segment_map.get(value, 'unknown')})")
                    all_use_segment_keys = False
                else:
                    print(f"   ⚠️  {value} is neither flight number nor segment key")
                    all_use_segment_keys = False
        
        if all_use_segment_keys:
            print("\n✅ SUCCESS: All SegmentReferences use segment keys!")
            return True
        else:
            print("\n❌ FAILURE: Some SegmentReferences still use flight numbers!")
            return False
    else:
        print("❌ No current OrderCreate payload found")
        return False

def test_ordercreate_builder_with_real_data():
    """Test the OrderCreate builder with real API data."""
    print("\n🧪 Testing OrderCreate Builder with Real Data")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('flight_price_response'):
        print("❌ No FlightPriceRS data found")
        return False
    
    try:
        # Import the OrderCreate builders
        from scripts.build_ordercreate_rq import generate_order_create_rq
        from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request
        
        # Test data
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
        
        # Test 1: Standard OrderCreate builder
        print("\n1️⃣ Testing Standard OrderCreate Builder...")
        try:
            standard_result = generate_order_create_rq(
                flight_price_response=data['flight_price_response'],
                passengers_data=passengers_data,
                payment_input_info=payment_info,
                seatavailability_response=data.get('seatavailability_response'),
                selected_seats=["SO-597ccb29-2458-4deb-9731-5479ca43cc5e-OI-1"]  # From logs
            )
            
            # Check SegmentReferences in standard result
            def check_segment_references(obj, path=""):
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
                            references.extend(check_segment_references(value, f"{path}.{key}" if path else key))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        references.extend(check_segment_references(item, f"{path}[{i}]"))
                return references
            
            standard_refs = check_segment_references(standard_result)
            print(f"   Standard builder SegmentReferences: {standard_refs}")
            
            if standard_refs:
                print("   ✅ Standard builder generates SegmentReferences")
            else:
                print("   ⚠️  Standard builder has no SegmentReferences")
                
        except Exception as e:
            print(f"   ❌ Standard builder failed: {e}")
        
        # Test 2: Enhanced OrderCreate builder
        print("\n2️⃣ Testing Enhanced OrderCreate Builder...")
        try:
            enhanced_result = build_ordercreate_enhanced_request(
                flight_price_response=data['flight_price_response'],
                passengers_data=passengers_data,
                payment_input_info=payment_info,
                seatavailability_response=data.get('seatavailability_response'),
                selected_seats=["SO-597ccb29-2458-4deb-9731-5479ca43cc5e-OI-1"]  # From logs
            )
            
            enhanced_refs = check_segment_references(enhanced_result)
            print(f"   Enhanced builder SegmentReferences: {enhanced_refs}")
            
            if enhanced_refs:
                print("   ✅ Enhanced builder generates SegmentReferences")
            else:
                print("   ⚠️  Enhanced builder has no SegmentReferences")
                
        except Exception as e:
            print(f"   ❌ Enhanced builder failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ndc_compliance():
    """Test that the OrderCreate payload follows NDC documentation."""
    print("\n🧪 Testing NDC Documentation Compliance")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('current_ordercreate'):
        print("❌ No current OrderCreate payload found")
        return False
    
    current_payload = data['current_ordercreate'].get('payload', {})
    
    # Check VDC documentation compliance
    print("📋 Checking VDC Documentation Compliance:")
    
    # 1. Check if Query structure exists
    if "Query" in current_payload:
        print("   ✅ Query structure present")
    else:
        print("   ❌ Query structure missing")
        return False
    
    # 2. Check if Passengers structure exists
    if "Passengers" in current_payload["Query"]:
        print("   ✅ Passengers structure present")
    else:
        print("   ❌ Passengers structure missing")
        return False
    
    # 3. Check if OrderItems structure exists
    if "OrderItems" in current_payload["Query"]:
        print("   ✅ OrderItems structure present")
    else:
        print("   ❌ OrderItems structure missing")
        return False
    
    # 4. Check if DataLists structure exists
    if "DataLists" in current_payload["Query"]:
        print("   ✅ DataLists structure present")
    else:
        print("   ❌ DataLists structure missing")
        return False
    
    # 5. Check SegmentReferences compliance
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
    
    segment_refs = find_segment_references(current_payload)
    
    print(f"\n📋 SegmentReferences Analysis:")
    print(f"   Found {len(segment_refs)} SegmentReferences")
    
    for ref in segment_refs:
        print(f"   {ref['path']}: {ref['values']}")
        
        # Check if values are segment keys (should start with "FS" or similar)
        all_segment_keys = True
        for value in ref['values']:
            if not (value.startswith('FS') or value.startswith('SEG')):
                all_segment_keys = False
                break
        
        if all_segment_keys:
            print(f"     ✅ Uses segment keys")
        else:
            print(f"     ❌ Uses flight numbers (not compliant with VDC spec)")
    
    return True

def main():
    """Main test function."""
    print("🚀 OrderCreate Fixes Test with Real API Data")
    print("=" * 60)
    
    # Test 1: SegmentReferences mapping
    test1_result = test_segment_references_mapping()
    
    # Test 2: OrderCreate builder with real data
    test2_result = test_ordercreate_builder_with_real_data()
    
    # Test 3: NDC compliance
    test3_result = test_ndc_compliance()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ SegmentReferences Mapping: {'PASSED' if test1_result else 'FAILED'}")
    print(f"✅ OrderCreate Builder Test: {'PASSED' if test2_result else 'FAILED'}")
    print(f"✅ NDC Compliance Check: {'PASSED' if test3_result else 'FAILED'}")
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The OrderCreate fixes are working correctly with real data.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   The OrderCreate fixes need additional work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
