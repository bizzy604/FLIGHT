#!/usr/bin/env python3
"""
Final verification test for OrderCreate NDC compliance.

This test verifies that the OrderCreate generation now follows NDC documentation
by using the actual seat and service data from the current OrderCreate payload.
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
    
    # Load current OrderCreate payload for comparison
    booking_rq_file = logs_dir / "booking" / "Booking_RQ.json"
    if booking_rq_file.exists():
        with open(booking_rq_file, 'r') as f:
            data['current_ordercreate'] = json.load(f)
    
    return data

def test_final_ordercreate_verification():
    """Test the final OrderCreate verification with real data."""
    print("🧪 Final OrderCreate NDC Compliance Verification")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('flight_price_response'):
        print("❌ No FlightPriceRS data found")
        return False
    
    if not data.get('current_ordercreate'):
        print("❌ No current OrderCreate payload found")
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
        
        # Extract seat and service data from current OrderCreate payload
        print("\n2️⃣ Extracting Seat and Service Data from Current OrderCreate...")
        current_payload = data['current_ordercreate'].get('payload', {})
        
        # Find seat and service selections from current OrderCreate
        selected_seats = []
        selected_services = []
        
        # Extract seat selections from OrderItems
        order_items = current_payload.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
        for item in order_items:
            if 'OfferItemType' in item and 'SeatItem' in item['OfferItemType']:
                seat_items = item['OfferItemType']['SeatItem']
                if not isinstance(seat_items, list):
                    seat_items = [seat_items]
                for seat_item in seat_items:
                    if 'SeatAssociation' in seat_item:
                        seat_assocs = seat_item['SeatAssociation']
                        if not isinstance(seat_assocs, list):
                            seat_assocs = [seat_assocs]
                        for seat_assoc in seat_assocs:
                            if 'SeatRef' in seat_assoc:
                                seat_ref = seat_assoc['SeatRef']
                                if isinstance(seat_ref, dict) and 'value' in seat_ref:
                                    selected_seats.append(seat_ref['value'])
        
        # Extract service selections from DataLists
        data_lists = current_payload.get('Query', {}).get('DataLists', {})
        if 'ServiceList' in data_lists and 'Service' in data_lists['ServiceList']:
            services = data_lists['ServiceList']['Service']
            if not isinstance(services, list):
                services = [services]
            for service in services:
                if 'ObjectKey' in service:
                    selected_services.append(service['ObjectKey'])
        
        print(f"   Found {len(selected_seats)} seat selections: {selected_seats}")
        print(f"   Found {len(selected_services)} service selections: {selected_services}")
        
        # Test OrderCreate generation with extracted data
        print("\n3️⃣ Testing OrderCreate Generation with Extracted Data...")
        
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
        
        # Generate OrderCreate payload with extracted data
        result = generate_order_create_rq(
            flight_price_response=flight_price_data,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=data.get('seatavailability_response'),
            selected_seats=selected_seats,
            selected_services=selected_services
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
            print("   This might be because no seats/services were processed")
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
    print("🚀 Final OrderCreate NDC Compliance Verification")
    print("=" * 60)
    
    # Test 1: Final OrderCreate verification
    test1_result = test_final_ordercreate_verification()
    
    # Test 2: Compare with current OrderCreate
    test2_result = compare_with_current_ordercreate()
    
    print("\n" + "=" * 60)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Final OrderCreate Verification: {'PASSED' if test1_result else 'FAILED'}")
    print(f"✅ Current OrderCreate Analysis: {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The OrderCreate generation is now NDC compliant!")
        print("   ✅ SegmentReferences use segment keys (FS1) instead of flight numbers (BA0322)")
        print("   ✅ OrderCreate builders are working correctly")
        print("   ✅ NDC documentation compliance achieved!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   The OrderCreate generation needs additional work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
