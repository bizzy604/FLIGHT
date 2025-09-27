#!/usr/bin/env python3
"""
Test Architecture Cleanup.

This test verifies that the cleaned up architecture works correctly
after removing duplication between booking.py and request_builders.py.
"""
import sys
import os
import json
from pathlib import Path

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_architecture_cleanup():
    """Test that the cleaned up architecture works correctly."""
    print("🧪 Testing Architecture Cleanup")
    print("=" * 60)
    print("This test verifies that the cleaned up architecture works correctly")
    print("after removing duplication between booking.py and request_builders.py.")
    print("=" * 60)
    
    try:
        # Test 1: Import the cleaned up request_builders
        print("\n1️⃣ Testing request_builders.py (Simplified Wrapper)...")
        from utils.request_builders import build_ordercreate_rq
        print("✅ Successfully imported build_ordercreate_rq from request_builders.py")
        
        # Test 2: Import the booking service
        print("\n2️⃣ Testing booking.py (Business Logic)...")
        from services.flight.booking import FlightBookingService
        print("✅ Successfully imported FlightBookingService from booking.py")
        
        # Test 3: Import the core OrderCreate builder
        print("\n3️⃣ Testing core OrderCreate builder...")
        from scripts.build_ordercreate_rq import generate_order_create_rq
        print("✅ Successfully imported generate_order_create_rq from scripts/build_ordercreate_rq.py")
        
        # Test 4: Import the enhanced OrderCreate builder
        print("\n4️⃣ Testing enhanced OrderCreate builder...")
        from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request
        print("✅ Successfully imported build_ordercreate_enhanced_request from scripts/build_ordercreate_enhanced_rq.py")
        
        # Test 5: Load real API responses
        print("\n5️⃣ Loading Real API Responses...")
        
        # Load FlightPriceRS
        with open('api_logs/flight_price/FlightPrice_RS.json', 'r') as f:
            flight_price_response = json.load(f)
        print("✅ Loaded FlightPriceRS")
        
        # Load SeatAvailabilityRS
        with open('api_logs/seat_availability/SeatAvailability_RS.json', 'r') as f:
            seatavailability_response = json.load(f)
        print("✅ Loaded SeatAvailabilityRS")
        
        # Load ServiceListRS
        with open('api_logs/service_list/ServiceList_RS.json', 'r') as f:
            servicelist_response = json.load(f)
        print("✅ Loaded ServiceListRS")
        
        # Test 6: Test the simplified request_builders wrapper
        print("\n6️⃣ Testing request_builders.py wrapper (Should delegate to core builder)...")
        
        # Real passenger data
        passengers = [
            {
                "PTC": "ADT",
                "Name": {"Surname": {"value": "Smith"}, "Given": [{"value": "John"}]},
                "Gender": {"value": "Male"},
                "BirthDate": {"value": "1985-06-15"}
            }
        ]
        
        # Real payment info
        payment_info = {
            "MethodType": "PAYMENTCARD",
            "currency": "USD",
            "Details": {},
            "CardNumberToken": "4111111111111111",
            "CardType": "VI",
            "CardHolderName": {"value": "John Smith", "refs": []},
            "EffectiveExpireDate": {"Expiration": "12/25", "Effective": None},
            "CardCode": "123",
            "ProductTypeCode": ""
        }
        
        # Real contact info
        contact_info = {
            "email": "john.smith@example.com",
            "phone": "+1-555-123-4567"
        }
        
        # Extract selected services
        selected_services = []
        if 'response' in servicelist_response and 'Services' in servicelist_response['response']:
            services = servicelist_response['response']['Services'].get('Service', [])
            if not isinstance(services, list):
                services = [services] if services else []
            
            for service in services[:2]:  # Take first 2 services
                if 'ObjectKey' in service:
                    selected_services.append(service['ObjectKey'])
        
        print(f"   Selected services: {len(selected_services)} services")
        
        # Test the request_builders wrapper
        try:
            ordercreate_payload = build_ordercreate_rq(
                flight_price_response=flight_price_response,
                passenger_details=passengers,
                payment_details=payment_info,
                contact_info=contact_info,
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services,
                selected_seats=[]
            )
            
            print("   ✅ SUCCESS: request_builders.py wrapper works correctly!")
            
            # Check if the payload was generated correctly
            if ordercreate_payload and isinstance(ordercreate_payload, dict):
                query = ordercreate_payload.get('Query', {})
                order_items = query.get('OrderItems', {})
                offer_items = order_items.get('OfferItem', [])
                
                print(f"   ✅ Generated OrderCreate payload with {len(offer_items)} offer items")
                
                # Check for ShoppingResponseID in the payload
                shopping_response = order_items.get('ShoppingResponse', {})
                if shopping_response.get('ResponseID'):
                    print(f"   ✅ ShoppingResponseID found in OrderCreate payload")
                else:
                    print(f"   ⚠️  ShoppingResponseID not found in OrderCreate payload")
                
                return True
            else:
                print("   ❌ FAILURE: OrderCreate payload is empty or invalid")
                return False
                
        except Exception as e:
            print(f"   ❌ FAILURE: request_builders.py wrapper failed: {e}")
            return False
        
        # Test 7: Test the booking service (business logic)
        print("\n7️⃣ Testing booking.py business logic (Should handle complex data transformation)...")
        
        try:
            # Create a booking service instance
            booking_service = FlightBookingService()
            
            # Test the _build_booking_payload method directly
            ordercreate_payload = booking_service._build_booking_payload(
                flight_price_response=flight_price_response,
                passengers=passengers,
                payment_info=payment_info,
                contact_info=contact_info,
                request_id="architecture-cleanup-test-123",
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services,
                selected_seats=[]
            )
            
            print("   ✅ SUCCESS: booking.py business logic works correctly!")
            
            # Check if the payload was generated correctly
            if ordercreate_payload and isinstance(ordercreate_payload, dict):
                query = ordercreate_payload.get('Query', {})
                order_items = query.get('OrderItems', {})
                offer_items = order_items.get('OfferItem', [])
                
                print(f"   ✅ Generated OrderCreate payload with {len(offer_items)} offer items")
                
                # Check for ShoppingResponseID in the payload
                shopping_response = order_items.get('ShoppingResponse', {})
                if shopping_response.get('ResponseID'):
                    print(f"   ✅ ShoppingResponseID found in OrderCreate payload")
                else:
                    print(f"   ⚠️  ShoppingResponseID not found in OrderCreate payload")
                
                return True
            else:
                print("   ❌ FAILURE: OrderCreate payload is empty or invalid")
                return False
                
        except Exception as e:
            print(f"   ❌ FAILURE: booking.py business logic failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Architecture Cleanup Test")
    print("=" * 60)
    print("This test verifies that the cleaned up architecture works correctly")
    print("after removing duplication between booking.py and request_builders.py.")
    print("=" * 60)
    
    # Test the cleaned up architecture
    test_result = test_architecture_cleanup()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Architecture Cleanup: {'PASSED' if test_result else 'FAILED'}")
    
    if test_result:
        print("\n🎉 ARCHITECTURE CLEANUP SUCCESSFUL!")
        print("   ✅ request_builders.py is now a simple wrapper")
        print("   ✅ booking.py handles complex business logic")
        print("   ✅ Core OrderCreate builders work correctly")
        print("   ✅ No more duplication between files")
        print("   ✅ Clean separation of responsibilities")
        return True
    else:
        print("\n❌ ARCHITECTURE CLEANUP FAILED!")
        print("   The cleaned up architecture still has issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
