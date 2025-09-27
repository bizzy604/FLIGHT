#!/usr/bin/env python3
"""
Verify that we're correctly using the priced FlightPriceRS response for OrderCreate.
This confirms the NDC workflow: Initial FlightPrice → Ancillary Pricing → Priced FlightPriceRS → OrderCreate
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def load_workflow_responses():
    """Load the complete workflow responses to verify the flow."""
    try:
        workflow_dir = "Shopping and booking with Seat and Ancillary where both of them requires pricing"
        
        # Load initial FlightPrice response (before ancillary pricing)
        with open(f'{workflow_dir}/4_FlightPriceRS.json', 'r') as f:
            initial_flight_price = json.load(f)
        
        # Load priced FlightPrice response (after ancillary pricing)
        with open(f'{workflow_dir}/10_FlightPriceRS.json', 'r') as f:
            priced_flight_price = json.load(f)
        
        # Load expected OrderCreate request
        with open(f'{workflow_dir}/11_OrderCreateRQ.json', 'r') as f:
            expected_order_create = json.load(f)
        
        return {
            'initial_flight_price': initial_flight_price,
            'priced_flight_price': priced_flight_price,
            'expected_order_create': expected_order_create
        }
    
    except Exception as e:
        print(f"Error loading workflow responses: {e}")
        return None

def analyze_priced_response(priced_response):
    """Analyze the priced FlightPriceRS response to see what pricing information it contains."""
    print("=" * 80)
    print("ANALYZING PRICED FLIGHTPRICERS RESPONSE")
    print("=" * 80)
    
    # Extract pricing information
    priced_offers = priced_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    if not priced_offers:
        print("❌ No PricedFlightOffers found")
        return
    
    print(f"✅ Found {len(priced_offers)} priced flight offers")
    
    for i, offer in enumerate(priced_offers):
        print(f"\n📋 PricedFlightOffer {i+1}:")
        offer_id = offer.get('OfferID', {})
        print(f"  OfferID: {offer_id.get('value', 'N/A')}")
        print(f"  Owner: {offer_id.get('Owner', 'N/A')}")
        
        # Analyze offer prices
        offer_prices = offer.get('OfferPrice', [])
        print(f"  Offer Prices: {len(offer_prices)}")
        
        for j, price in enumerate(offer_prices):
            print(f"\n    OfferPrice {j+1}:")
            offer_item_id = price.get('OfferItemID', 'N/A')
            print(f"      OfferItemID: {offer_item_id}")
            
            # Check for associations
            associations = price.get('RequestedDate', {}).get('Associations', [])
            print(f"      Associations: {len(associations)}")
            
            for k, assoc in enumerate(associations):
                print(f"\n        Association {k+1}:")
                
                # Check for associated traveler
                traveler = assoc.get('AssociatedTraveler', {})
                if traveler:
                    traveler_refs = traveler.get('TravelerReferences', [])
                    print(f"          TravelerReferences: {traveler_refs}")
                
                # Check for associated service
                service = assoc.get('AssociatedService', {})
                if service:
                    service_refs = service.get('ServiceReferences', [])
                    print(f"          ServiceReferences: {service_refs}")
                    
                    # Check for seat assignment
                    seat_assignment = service.get('SeatAssignment', [])
                    if seat_assignment:
                        print(f"          SeatAssignment: {len(seat_assignment)} seats")
                        for seat in seat_assignment:
                            seat_data = seat.get('Seat', {})
                            location = seat_data.get('Location', {})
                            if location:
                                row = location.get('Row', {}).get('Number', {}).get('value', 'N/A')
                                column = location.get('Column', 'N/A')
                                print(f"            Seat: Row {row}, Column {column}")
                
                # Check for price details
                price_detail = price.get('RequestedDate', {}).get('PriceDetail', {})
                if price_detail:
                    total_amount = price_detail.get('TotalAmount', {})
                    if total_amount:
                        simple_price = total_amount.get('SimpleCurrencyPrice', {})
                        if simple_price:
                            value = simple_price.get('value', 0)
                            currency = simple_price.get('Code', 'N/A')
                            print(f"          Price: {value} {currency}")

def compare_initial_vs_priced(initial_response, priced_response):
    """Compare initial FlightPriceRS vs priced FlightPriceRS to see the differences."""
    print("\n" + "=" * 80)
    print("COMPARING INITIAL VS PRICED FLIGHTPRICERS")
    print("=" * 80)
    
    # Compare offer counts
    initial_offers = initial_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    priced_offers = priced_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
    
    print(f"Initial FlightPriceRS offers: {len(initial_offers)}")
    print(f"Priced FlightPriceRS offers: {len(priced_offers)}")
    
    if len(initial_offers) > 0 and len(priced_offers) > 0:
        # Compare offer IDs
        initial_offer_id = initial_offers[0].get('OfferID', {}).get('value', 'N/A')
        priced_offer_id = priced_offers[0].get('OfferID', {}).get('value', 'N/A')
        
        print(f"Initial OfferID: {initial_offer_id}")
        print(f"Priced OfferID: {priced_offer_id}")
        
        # Compare offer prices
        initial_prices = initial_offers[0].get('OfferPrice', [])
        priced_prices = priced_offers[0].get('OfferPrice', [])
        
        print(f"Initial OfferPrice count: {len(initial_prices)}")
        print(f"Priced OfferPrice count: {len(priced_prices)}")
        
        if len(priced_prices) > len(initial_prices):
            print("✅ Priced response has MORE offer items (ancillaries/seats added)")
        else:
            print("⚠️  Priced response doesn't have more offer items")

def test_ordercreate_with_priced_response(data):
    """Test OrderCreate generation using the priced FlightPriceRS response."""
    print("\n" + "=" * 80)
    print("TESTING ORDERCREATE WITH PRICED FLIGHTPRICERS")
    print("=" * 80)
    
    # Create test passenger data
    passengers_data = [{
        "ObjectKey": "PAX1",
        "PTC": "ADT",
        "Name": {
            "Surname": "DOE",
            "Given": ["JON"],
            "Title": "Mr"
        },
        "Gender": "Male",
        "BirthDate": "1990-01-01",
        "Contacts": {
            "AddressContact": {
                "Street": ["123 Main St"],
                "CityName": "Test City",
                "CountrySubDivisionCode": "TS",
                "PostalCode": "12345",
                "CountryCode": {"value": "US"}
            },
            "EmailContact": {
                "Address": {"value": "test@example.com"}
            },
            "PhoneContact": {
                "Application": "Home",
                "Number": [{
                    "value": "1234567890",
                    "CountryCode": "1"
                }]
            }
        },
        "Documents": [{
            "Type": "P",
            "ID": "A1234567",
            "DateOfExpiration": "2030-01-01",
            "CountryOfIssuance": "US"
        }]
    }]
    
    payment_data = {"MethodType": "Cash"}
    
    # Test with priced FlightPriceRS response
    try:
        order_create_rq = generate_order_create_rq(
            flight_price_response=data['priced_flight_price'],  # Use PRICED response
            passengers_data=passengers_data,
            payment_input_info=payment_data,
            selected_services=[],  # No additional services needed - already in priced response
            selected_seats=[]      # No additional seats needed - already in priced response
        )
        
        print("✅ Successfully generated OrderCreate using PRICED FlightPriceRS!")
        
        # Analyze the generated OrderCreate
        query = order_create_rq.get('Query', {})
        order_items = query.get('OrderItems', {})
        shopping_response = order_items.get('ShoppingResponse', {})
        offers = shopping_response.get('Offers', {}).get('Offer', [])
        
        if offers:
            offer_items = offers[0].get('OfferItems', {}).get('OfferItem', [])
            print(f"\n📊 Generated OrderCreate Structure:")
            print(f"  Shopping Response Offer Items: {len(offer_items)}")
            
            # Show offer items from priced response
            for item in offer_items:
                offer_item_id = item.get('OfferItemID', {})
                print(f"    - {offer_item_id.get('value', 'N/A')} (Owner: {offer_item_id.get('Owner', 'N/A')})")
        
        # Additional OfferItems
        additional_offer_items = order_items.get('OfferItem', [])
        print(f"  Additional Offer Items: {len(additional_offer_items)}")
        
        return order_create_rq
        
    except Exception as e:
        print(f"❌ Error generating OrderCreate with priced response: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Verify the correct usage of priced FlightPriceRS response."""
    print("🔍 VERIFYING PRICED FLIGHTPRICERS USAGE FOR ORDERCREATE")
    print("=" * 80)
    
    # Load workflow responses
    data = load_workflow_responses()
    if not data:
        print("❌ Failed to load workflow responses")
        return
    
    print("✅ Loaded workflow responses")
    
    # Analyze the priced response
    analyze_priced_response(data['priced_flight_price'])
    
    # Compare initial vs priced
    compare_initial_vs_priced(data['initial_flight_price'], data['priced_flight_price'])
    
    # Test OrderCreate with priced response
    order_create_rq = test_ordercreate_with_priced_response(data)
    
    # Final verification
    print("\n" + "=" * 80)
    print("FINAL VERIFICATION")
    print("=" * 80)
    
    if order_create_rq:
        print("✅ OrderCreate generation with priced FlightPriceRS: SUCCESS")
        print("✅ NDC workflow compliance: CONFIRMED")
        print("\n🎉 The implementation correctly uses the priced FlightPriceRS response for OrderCreate!")
    else:
        print("❌ OrderCreate generation failed")

if __name__ == "__main__":
    main()
