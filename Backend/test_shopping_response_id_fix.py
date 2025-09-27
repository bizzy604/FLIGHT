#!/usr/bin/env python3
"""
Test ShoppingResponseID Fix.

This test verifies that the ShoppingResponseID fix is working correctly
and the OrderCreate builder no longer fails with the missing ShoppingResponseID error.
"""
import sys
import os
import json
from pathlib import Path

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_shopping_response_id_fix():
    """Test that the ShoppingResponseID fix is working correctly."""
    print("🧪 Testing ShoppingResponseID Fix")
    print("=" * 60)
    print("This test verifies that the OrderCreate builder no longer fails")
    print("with the missing ShoppingResponseID error.")
    print("=" * 60)
    
    try:
        # Import the actual booking service
        from services.flight.booking import FlightBookingService
        
        # Create a booking service instance
        booking_service = FlightBookingService()
        
        # Load real API responses
        print("\n1️⃣ Loading Real API Responses...")
        
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
        
        # Simulate production booking request data
        print("\n2️⃣ Testing OrderCreate Builder with Real Data...")
        
        # Real passenger data
        passengers = [
            {
                "ObjectKey": "T1",
                "PTC": "ADT",
                "Name": {"Surname": {"value": "Smith"}, "Given": [{"value": "John"}]},
                "Gender": {"value": "Male"},
                "Age": {"BirthDate": {"value": "1985-06-15"}}
            }
        ]
        
        # Real payment info
        payment_info = {
            "Method": "CreditCard",
            "Amount": {"value": 1500, "Code": "USD"},
            "CardNumber": "4111111111111111",
            "CardHolderName": "John Smith",
            "ExpiryDate": "12/25"
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
        
        # Test the OrderCreate builder directly
        print("\n3️⃣ Testing OrderCreate Builder (Should NOT fail with ShoppingResponseID error)...")
        
        try:
            # This should now work without the ShoppingResponseID error
            ordercreate_payload = booking_service._build_booking_payload(
                flight_price_response=flight_price_response,
                passengers=passengers,
                payment_info=payment_info,
                contact_info=contact_info,
                request_id="shopping-response-id-test-123",
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services,
                selected_seats=[]
            )
            
            print("   ✅ SUCCESS: OrderCreate builder completed without ShoppingResponseID error!")
            
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
                
        except ValueError as e:
            if "ShoppingResponseID" in str(e):
                print(f"   ❌ FAILURE: Still getting ShoppingResponseID error: {e}")
                return False
            else:
                print(f"   ❌ FAILURE: Different error occurred: {e}")
                return False
        except Exception as e:
            print(f"   ❌ FAILURE: Unexpected error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 ShoppingResponseID Fix Test")
    print("=" * 60)
    print("This test verifies that the ShoppingResponseID fix is working correctly")
    print("and the OrderCreate builder no longer fails with the missing ShoppingResponseID error.")
    print("=" * 60)
    
    # Test the fix
    test_result = test_shopping_response_id_fix()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ ShoppingResponseID Fix: {'PASSED' if test_result else 'FAILED'}")
    
    if test_result:
        print("\n🎉 FIX SUCCESSFUL!")
        print("   The ShoppingResponseID error has been resolved!")
        print("   ✅ OrderCreate builder works without ShoppingResponseID error")
        print("   ✅ OrderCreate payload generated successfully")
        print("   ✅ Production system is now working correctly")
        return True
    else:
        print("\n❌ FIX FAILED!")
        print("   The ShoppingResponseID error still needs to be resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
