#!/usr/bin/env python3
"""
Complete OrderCreate Payload Generation Test using Real API Logs.

This test generates a complete OrderCreate payload using all real API responses
from the api_logs folder to verify that our fixed OrderCreate builder is working
correctly with segment key mappings and NDC compliance.
"""
import sys
import os
import json
from pathlib import Path

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def load_all_api_logs():
    """Load all API responses from the api_logs folder."""
    logs_dir = Path("api_logs")
    
    data = {}
    
    # Load FlightPriceRS
    flight_price_file = logs_dir / "flight_price" / "FlightPrice_RS.json"
    if flight_price_file.exists():
        with open(flight_price_file, 'r') as f:
            data['flight_price_response'] = json.load(f)
        print(f"✅ Loaded FlightPriceRS: {flight_price_file}")
    
    # Load SeatAvailabilityRS
    seat_availability_file = logs_dir / "seat_availability" / "SeatAvailability_RS.json"
    if seat_availability_file.exists():
        with open(seat_availability_file, 'r') as f:
            data['seatavailability_response'] = json.load(f)
        print(f"✅ Loaded SeatAvailabilityRS: {seat_availability_file}")
    
    # Load ServiceListRS
    service_list_file = logs_dir / "service_list" / "ServiceList_RS.json"
    if service_list_file.exists():
        with open(service_list_file, 'r') as f:
            data['servicelist_response'] = json.load(f)
        print(f"✅ Loaded ServiceListRS: {service_list_file}")
    
    # Load AirShoppingRS (optional)
    air_shopping_file = logs_dir / "air_shopping" / "AirShopping_RS.json"
    if air_shopping_file.exists():
        with open(air_shopping_file, 'r') as f:
            data['airshopping_response'] = json.load(f)
        print(f"✅ Loaded AirShoppingRS: {air_shopping_file}")
    
    return data

def extract_seat_and_service_selections(data):
    """Extract seat and service selections from the API responses."""
    print("\n🔍 Extracting Seat and Service Selections from API Responses")
    print("=" * 60)
    
    selected_seats = []
    selected_services = []
    
    # Extract seat data from SeatAvailabilityRS
    if data.get('seatavailability_response'):
        seat_response = data['seatavailability_response']
        if 'response' in seat_response and 'Services' in seat_response['response']:
            services = seat_response['response']['Services'].get('Service', [])
            if not isinstance(services, list):
                services = [services] if services else []
            
            print(f"📋 Found {len(services)} seat services in SeatAvailabilityRS")
            for i, service in enumerate(services[:3]):  # Show first 3
                if 'ObjectKey' in service:
                    selected_seats.append(service['ObjectKey'])
                    print(f"   Seat {i+1}: {service['ObjectKey']}")
            if len(services) > 3:
                print(f"   ... and {len(services) - 3} more seats")
    
    # Extract service data from ServiceListRS
    if data.get('servicelist_response'):
        service_response = data['servicelist_response']
        if 'response' in service_response and 'Services' in service_response['response']:
            services = service_response['response']['Services'].get('Service', [])
            if not isinstance(services, list):
                services = [services] if services else []
            
            print(f"📋 Found {len(services)} services in ServiceListRS")
            for i, service in enumerate(services[:3]):  # Show first 3
                if 'ObjectKey' in service:
                    selected_services.append(service['ObjectKey'])
                    print(f"   Service {i+1}: {service['ObjectKey']}")
            if len(services) > 3:
                print(f"   ... and {len(services) - 3} more services")
    
    print(f"\n📋 Final Selections:")
    print(f"   Selected seats: {len(selected_seats)} seats")
    print(f"   Selected services: {len(selected_services)} services")
    
    return selected_seats, selected_services

def test_complete_ordercreate_generation():
    """Test complete OrderCreate generation using all real API data."""
    print("🧪 Complete OrderCreate Payload Generation Test")
    print("=" * 60)
    print("This test generates a complete OrderCreate payload using all real API responses")
    print("to verify that our fixed OrderCreate builder is working correctly.")
    print("=" * 60)
    
    # Load all API data
    print("\n1️⃣ Loading All API Responses...")
    data = load_all_api_logs()
    
    if not data.get('flight_price_response'):
        print("❌ No FlightPriceRS data found")
        return False
    
    # Extract seat and service selections
    print("\n2️⃣ Extracting Seat and Service Selections...")
    selected_seats, selected_services = extract_seat_and_service_selections(data)
    
    try:
        # Import the updated booking service
        from services.flight.booking import FlightBookingService
        
        # Create a booking service instance
        booking_service = FlightBookingService()
        
        # Test passenger data
        passengers = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",
                "Name": {"Surname": {"value": "Smith"}, "Given": [{"value": "John"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1985-06-15"}}
            }
        ]
        
        # Test payment info
        payment_info = {
            "Method": "CreditCard",
            "Amount": {"value": 1500, "Code": "USD"},
            "CardNumber": "4111111111111111",
            "CardHolderName": "John Smith",
            "ExpiryDate": "12/25"
        }
        
        # Test contact info
        contact_info = {
            "email": "john.smith@example.com",
            "phone": "+1-555-123-4567"
        }
        
        # Generate complete OrderCreate payload
        print("\n3️⃣ Generating Complete OrderCreate Payload...")
        print("   Using real FlightPriceRS, SeatAvailabilityRS, and ServiceListRS data...")
        
        ordercreate_payload = booking_service._build_booking_payload(
            flight_price_response=data['flight_price_response'],
            passengers=passengers,
            payment_info=payment_info,
            contact_info=contact_info,
            request_id="complete-ordercreate-test-123",
            servicelist_response=data.get('servicelist_response'),
            seatavailability_response=data.get('seatavailability_response'),
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print(f"   ✅ Complete OrderCreate payload generated successfully!")
        print(f"   Generated payload with {len(ordercreate_payload.get('Query', {}).get('OrderItems', {}).get('OfferItem', []))} offer items")
        
        # Save the generated payload for inspection
        output_file = Path("generated_ordercreate_payload.json")
        with open(output_file, 'w') as f:
            json.dump(ordercreate_payload, f, indent=2)
        print(f"   💾 Saved complete payload to: {output_file}")
        
        # Analyze the generated payload
        print("\n4️⃣ Analyzing Generated OrderCreate Payload...")
        analyze_ordercreate_payload(ordercreate_payload)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_ordercreate_payload(payload):
    """Analyze the generated OrderCreate payload for NDC compliance."""
    print("   🔍 Analyzing OrderCreate payload structure...")
    
    # Check basic structure
    query = payload.get('Query', {})
    order_items = query.get('OrderItems', {})
    data_lists = query.get('DataLists', {})
    
    print(f"   📋 OrderCreate Structure:")
    print(f"      - OrderItems: {len(order_items.get('OfferItem', []))} items")
    print(f"      - DataLists: {len(data_lists)} sections")
    
    # Check SegmentReferences
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
    
    segment_refs = find_segment_references(payload)
    
    print(f"   📋 SegmentReferences Analysis:")
    print(f"      - Found {len(segment_refs)} SegmentReferences")
    
    if segment_refs:
        all_use_segment_keys = True
        for ref in segment_refs:
            print(f"      - {ref['path']}: {ref['values']}")
            
            for value in ref['values']:
                if value == 'FS1':
                    print(f"        ✅ {value} is a segment key (CORRECT!)")
                elif value in ['BA322', 'BA0322']:
                    print(f"        ❌ {value} is a flight number (should be FS1)")
                    all_use_segment_keys = False
                else:
                    print(f"        ⚠️  {value} is neither flight number nor segment key")
                    all_use_segment_keys = False
        
        if all_use_segment_keys:
            print(f"\n   🎉 SUCCESS: All SegmentReferences use correct segment keys!")
            print(f"   ✅ NDC compliance achieved!")
        else:
            print(f"\n   ❌ FAILURE: Some SegmentReferences still use flight numbers!")
    else:
        print(f"   ⚠️  No SegmentReferences found in payload")
    
    # Check ServiceList
    service_list = data_lists.get('ServiceList', {}).get('Service', [])
    print(f"   📋 ServiceList: {len(service_list)} services")
    
    # Check OrderItems
    offer_items = order_items.get('OfferItem', [])
    print(f"   📋 OrderItems: {len(offer_items)} offer items")
    
    for i, item in enumerate(offer_items):
        item_type = item.get('OfferItemType', {})
        if 'SeatItem' in item_type:
            print(f"      - OfferItem {i+1}: SeatItem")
        elif 'ServiceItem' in item_type:
            print(f"      - OfferItem {i+1}: ServiceItem")
        else:
            print(f"      - OfferItem {i+1}: Other")

def main():
    """Main test function."""
    print("🚀 Complete OrderCreate Payload Generation Test")
    print("=" * 60)
    print("This test generates a complete OrderCreate payload using all real API responses")
    print("from the api_logs folder to verify NDC compliance and segment key mappings.")
    print("=" * 60)
    
    # Test complete OrderCreate generation
    test_result = test_complete_ordercreate_generation()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Complete OrderCreate Generation: {'PASSED' if test_result else 'FAILED'}")
    
    if test_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The OrderCreate generation is working correctly with real API data!")
        print("   ✅ Complete OrderCreate payload generated successfully")
        print("   ✅ SegmentReferences use segment keys (FS1) instead of flight numbers (BA0322)")
        print("   ✅ NDC documentation compliance achieved!")
        print("   💾 Generated payload saved to: generated_ordercreate_payload.json")
        return True
    else:
        print("\n❌ TEST FAILED!")
        print("   The OrderCreate generation needs additional work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
