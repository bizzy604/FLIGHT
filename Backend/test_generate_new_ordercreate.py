#!/usr/bin/env python3
"""
Test to generate a NEW OrderCreate payload using the updated system.

This test will generate a fresh OrderCreate payload using the fixed booking service
to verify that the segment key mappings are working correctly.
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
    
    return data

def test_generate_new_ordercreate():
    """Test generating a new OrderCreate payload using the updated system."""
    print("🧪 Testing NEW OrderCreate Generation with Updated System")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('flight_price_response'):
        print("❌ No FlightPriceRS data found")
        return False
    
    try:
        # Import the updated booking service
        from services.flight.booking import FlightBookingService
        
        # Create a booking service instance
        booking_service = FlightBookingService()
        
        # Test data
        passengers = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",
                "Name": {"Surname": {"value": "Test"}, "Given": [{"value": "User"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1990-01-01"}}
            }
        ]
        
        payment_info = {"Method": "Cash", "Amount": {"value": 1100, "Code": "USD"}}
        contact_info = {"email": "test@example.com", "phone": "+1234567890"}
        
        # Extract seat and service data from current OrderCreate for testing
        booking_rq_file = Path("api_logs/booking/Booking_RQ.json")
        selected_seats = []
        selected_services = []
        
        if booking_rq_file.exists():
            with open(booking_rq_file, 'r') as f:
                current_ordercreate = json.load(f)
            
            # Extract seat selections from current OrderCreate
            payload = current_ordercreate.get('payload', {})
            order_items = payload.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
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
            
            # Extract service selections from current OrderCreate
            data_lists = payload.get('Query', {}).get('DataLists', {})
            if 'ServiceList' in data_lists and 'Service' in data_lists['ServiceList']:
                services = data_lists['ServiceList']['Service']
                if not isinstance(services, list):
                    services = [services]
                for service in services:
                    if 'ObjectKey' in service:
                        selected_services.append(service['ObjectKey'])
        
        print(f"📋 Using extracted data:")
        print(f"   Selected seats: {selected_seats}")
        print(f"   Selected services: {selected_services}")
        
        # Generate NEW OrderCreate payload using the updated system
        print("\n1️⃣ Generating NEW OrderCreate payload...")
        
        new_payload = booking_service._build_booking_payload(
            flight_price_response=data['flight_price_response'],
            passengers=passengers,
            payment_info=payment_info,
            contact_info=contact_info,
            request_id="test-new-ordercreate-123",
            servicelist_response=data.get('servicelist_response'),
            seatavailability_response=data.get('seatavailability_response'),
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print(f"   ✅ NEW OrderCreate payload generated successfully!")
        print(f"   Generated payload with {len(new_payload.get('Query', {}).get('OrderItems', {}).get('OfferItem', []))} offer items")
        
        # Check SegmentReferences in the NEW generated payload
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
        
        segment_refs = find_segment_references(new_payload)
        
        print(f"\n2️⃣ Checking NEW OrderCreate SegmentReferences:")
        print(f"   Found {len(segment_refs)} SegmentReferences")
        
        if segment_refs:
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
                print("\n🎉 SUCCESS: NEW OrderCreate uses correct segment keys!")
                print("   ✅ NDC compliance achieved!")
                return True
            else:
                print("\n❌ FAILURE: NEW OrderCreate still uses flight numbers!")
                return False
        else:
            print("   ⚠️  No SegmentReferences found in NEW payload")
            print("   This might be because no seats/services were processed")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_segment_key_mapping():
    """Test the segment key mapping function."""
    print("\n🧪 Testing Segment Key Mapping Function")
    print("=" * 60)
    
    # Load real API data
    data = load_api_logs()
    
    if not data.get('flight_price_response'):
        print("❌ No FlightPriceRS data found")
        return False
    
    try:
        from scripts.build_ordercreate_rq import _create_flight_to_segment_mapping
        
        # Extract the raw response data
        flight_price_data = data['flight_price_response']
        if 'response' in flight_price_data and 'raw_response' in flight_price_data['response']:
            flight_price_data = flight_price_data['response']['raw_response']
        
        # Test the mapping function
        mapping = _create_flight_to_segment_mapping(flight_price_data)
        print(f"📋 Flight to Segment Mapping: {mapping}")
        
        if 'BA0322' in mapping and mapping['BA0322'] == 'FS1':
            print("✅ Mapping function works correctly!")
            return True
        else:
            print("❌ Mapping function failed!")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 NEW OrderCreate Generation Test")
    print("=" * 60)
    print("This test generates a NEW OrderCreate payload using the updated system")
    print("to verify that the segment key mappings are working correctly.")
    print("=" * 60)
    
    # Test 1: Segment key mapping
    test1_result = test_segment_key_mapping()
    
    # Test 2: Generate new OrderCreate payload
    test2_result = test_generate_new_ordercreate()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Segment Key Mapping: {'PASSED' if test1_result else 'FAILED'}")
    print(f"✅ NEW OrderCreate Generation: {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The updated OrderCreate generation is working correctly!")
        print("   ✅ SegmentReferences use segment keys (FS1) instead of flight numbers (BA0322)")
        print("   ✅ NDC documentation compliance achieved!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   The OrderCreate generation needs additional work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
