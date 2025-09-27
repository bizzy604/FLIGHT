#!/usr/bin/env python3
"""
Test Real VDC Mapping with Actual API Data.

This test uses the actual API responses from @api_logs/ to generate
an OrderCreate payload and verify VDC mapping compliance.
"""
import sys
import os
import json
from pathlib import Path

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_real_vdc_mapping():
    """Test VDC mapping with real API data."""
    print("🧪 Testing Real VDC Mapping with Actual API Data")
    print("=" * 60)
    print("Using actual API responses from @api_logs/ to generate OrderCreate payload")
    print("=" * 60)
    
    try:
        # Load actual API responses
        print("\n1️⃣ Loading Real API Responses...")
        
        # Load FlightPriceRS
        with open('api_logs/flight_price/FlightPrice_RS.json', 'r') as f:
            flight_price_response = json.load(f)
        print("   ✅ Loaded FlightPriceRS")
        
        # Load SeatAvailabilityRS
        with open('api_logs/seat_availability/SeatAvailability_RS.json', 'r') as f:
            seatavailability_response = json.load(f)
        print("   ✅ Loaded SeatAvailabilityRS")
        
        # Load ServiceListRS
        with open('api_logs/service_list/ServiceList_RS.json', 'r') as f:
            servicelist_response = json.load(f)
        print("   ✅ Loaded ServiceListRS")
        
        # Extract the raw NDC responses
        flight_price_raw = flight_price_response['response']['raw_response']
        seat_availability_raw = seatavailability_response['response']
        service_list_raw = servicelist_response['response']
        
        print("\n2️⃣ Analyzing Real API Data Structure...")
        
        # Analyze FlightPriceRS structure
        print("   FlightPriceRS Analysis:")
        print(f"     - ShoppingResponseID: {flight_price_raw.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'MISSING')}")
        print(f"     - PricedFlightOffers count: {len(flight_price_raw.get('PricedFlightOffers', {}).get('PricedFlightOffer', []))}")
        
        if flight_price_raw.get('PricedFlightOffers', {}).get('PricedFlightOffer'):
            offer = flight_price_raw['PricedFlightOffers']['PricedFlightOffer'][0]
            print(f"     - OfferID: {offer.get('OfferID', {}).get('value', 'MISSING')}")
            print(f"     - Owner: {offer.get('OfferID', {}).get('Owner', 'MISSING')}")
        
        # Analyze segment data
        segments = flight_price_raw.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
        print(f"     - Flight Segments: {len(segments)}")
        for i, seg in enumerate(segments):
            print(f"       Segment {i+1}: {seg.get('SegmentKey', 'MISSING')} - {seg.get('MarketingCarrier', {}).get('AirlineID', {}).get('value', 'MISSING')}{seg.get('MarketingCarrier', {}).get('FlightNumber', {}).get('value', 'MISSING')}")
        
        # Analyze fare data
        fare_groups = flight_price_raw.get('DataLists', {}).get('FareList', {}).get('FareGroup', [])
        print(f"     - Fare Groups: {len(fare_groups)}")
        for i, fg in enumerate(fare_groups):
            print(f"       Fare {i+1}: {fg.get('FareBasisCode', {}).get('Code', 'MISSING')}")
        
        # Analyze passenger data
        travelers = flight_price_raw.get('DataLists', {}).get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        print(f"     - Travelers: {len(travelers)}")
        for i, traveler in enumerate(travelers):
            print(f"       Traveler {i+1}: {traveler.get('ObjectKey', 'MISSING')} - {traveler.get('PTC', {}).get('value', 'MISSING')}")
        
        # Analyze ServiceListRS structure
        print("\n   ServiceListRS Analysis:")
        services = service_list_raw.get('Services', {}).get('Service', [])
        print(f"     - Services count: {len(services)}")
        print(f"     - OfferExpiration: {service_list_raw.get('OfferExpiration', {}).get('ObjectKey', 'MISSING')}")
        print(f"     - ShoppingResponseID: {service_list_raw.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'MISSING')}")
        
        # Analyze SeatAvailabilityRS structure
        print("\n   SeatAvailabilityRS Analysis:")
        seat_services = seat_availability_raw.get('Services', {}).get('Service', [])
        seat_services_filtered = [s for s in seat_services if s.get('Name', {}).get('value') == 'SEAT']
        print(f"     - Seat Services count: {len(seat_services_filtered)}")
        print(f"     - ShoppingResponseID: {seat_availability_raw.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', 'MISSING')}")
        
        print("\n3️⃣ Testing OrderCreate Generation with Real Data...")
        
        # Import the OrderCreate builder
        from scripts.build_ordercreate_rq import generate_order_create_rq
        
        # Prepare passenger data (using real structure from FlightPriceRS)
        passengers_data = []
        for traveler in travelers:
            passenger = {
                "PTC": traveler.get('PTC', {}).get('value', 'ADT'),
                "Name": {
                    "Surname": {"value": "Test"},
                    "Given": [{"value": "User"}]
                },
                "Gender": {"value": "Male"},
                "BirthDate": {"value": "1990-01-01"}
            }
            passengers_data.append(passenger)
        
        # Prepare payment info
        payment_input_info = {
            "MethodType": "PAYMENTCARD",
            "currency": "INR",
            "Details": {},
            "CardNumberToken": "4111111111111111",
            "CardType": "VI",
            "CardHolderName": {"value": "Test User", "refs": []},
            "EffectiveExpireDate": {"Expiration": "12/25", "Effective": None},
            "CardCode": "123",
            "ProductTypeCode": ""
        }
        
        # Select some services for testing
        selected_services = []
        for service in services[:3]:  # Take first 3 services
            if 'ObjectKey' in service:
                selected_services.append(service['ObjectKey'])
        
        print(f"   Selected services: {selected_services}")
        
        # Generate OrderCreate payload using real data
        ordercreate_payload = generate_order_create_rq(
            flight_price_response=flight_price_raw,  # Use raw NDC response
            passengers_data=passengers_data,
            payment_input_info=payment_input_info,
            servicelist_response=service_list_raw,  # Use raw NDC response
            seatavailability_response=seat_availability_raw,  # Use raw NDC response
            selected_services=selected_services,
            selected_seats=[]
        )
        
        print("   ✅ Generated OrderCreate payload with real data")
        
        # Save the generated payload
        with open('generated_ordercreate_real_data.json', 'w') as f:
            json.dump(ordercreate_payload, f, indent=2)
        print("   ✅ Saved generated payload to generated_ordercreate_real_data.json")
        
        print("\n4️⃣ Verifying VDC Mapping Compliance...")
        
        # Check ShoppingResponseID
        generated_shopping_id = ordercreate_payload['Query']['OrderItems']['ShoppingResponse']['ResponseID']['value']
        expected_shopping_id = flight_price_raw.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
        
        print(f"   ShoppingResponseID:")
        print(f"     Expected: {expected_shopping_id}")
        print(f"     Generated: {generated_shopping_id}")
        print(f"     Status: {'✅ CORRECT' if expected_shopping_id == generated_shopping_id else '❌ INCORRECT'}")
        
        # Check OfferID
        generated_offer_id = ordercreate_payload['Query']['OrderItems']['ShoppingResponse']['Offers']['Offer'][0]['OfferID']['value']
        expected_offer_id = flight_price_raw.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferID', {}).get('value', '')
        
        print(f"   OfferID:")
        print(f"     Expected: {expected_offer_id}")
        print(f"     Generated: {generated_offer_id}")
        print(f"     Status: {'✅ CORRECT' if expected_offer_id == generated_offer_id else '❌ INCORRECT'}")
        
        # Check Owner
        generated_owner = ordercreate_payload['Query']['OrderItems']['ShoppingResponse']['Owner']
        expected_owner = flight_price_raw.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferID', {}).get('Owner', '')
        
        print(f"   Owner:")
        print(f"     Expected: {expected_owner}")
        print(f"     Generated: {generated_owner}")
        print(f"     Status: {'✅ CORRECT' if expected_owner == generated_owner else '❌ INCORRECT'}")
        
        # Check Segment Keys
        generated_segments = ordercreate_payload['Query']['OrderItems']['OfferItem'][0]['OfferItemType']['DetailedFlightItem'][0]['OriginDestination'][0]['Flight']
        generated_segment_keys = [flight.get('SegmentKey', '') for flight in generated_segments]
        expected_segment_keys = [seg.get('SegmentKey', '') for seg in segments]
        
        print(f"   Segment Keys:")
        print(f"     Expected: {expected_segment_keys}")
        print(f"     Generated: {generated_segment_keys}")
        print(f"     Status: {'✅ CORRECT' if set(expected_segment_keys) == set(generated_segment_keys) else '❌ INCORRECT'}")
        
        # Check FareBasisCode
        generated_fare_basis = ordercreate_payload['Query']['OrderItems']['OfferItem'][0]['OfferItemType']['DetailedFlightItem'][0]['FareDetail']['FareComponent'][0]['FareBasis']['FareBasisCode']
        expected_fare_basis = fare_groups[0].get('FareBasisCode', {}).get('Code', '') if fare_groups else ''
        
        print(f"   FareBasisCode:")
        print(f"     Expected: {expected_fare_basis}")
        print(f"     Generated: {generated_fare_basis}")
        print(f"     Status: {'✅ CORRECT' if expected_fare_basis == generated_fare_basis.get('Code', '') else '❌ INCORRECT'}")
        
        # Check Passenger ObjectKeys
        generated_passengers = ordercreate_payload['Query']['Passengers']['Passenger']
        generated_passenger_keys = [p.get('ObjectKey', '') for p in generated_passengers]
        expected_passenger_keys = [t.get('ObjectKey', '') for t in travelers]
        
        print(f"   Passenger ObjectKeys:")
        print(f"     Expected: {expected_passenger_keys}")
        print(f"     Generated: {generated_passenger_keys}")
        print(f"     Status: {'✅ CORRECT' if set(expected_passenger_keys) == set(generated_passenger_keys) else '❌ INCORRECT'}")
        
        print("\n" + "=" * 60)
        print("📊 REAL VDC MAPPING TEST RESULTS")
        print("=" * 60)
        print("This test used actual API responses from @api_logs/ to generate OrderCreate payload")
        print("and verified VDC mapping compliance against the real source data.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Real VDC Mapping Test")
    print("=" * 60)
    print("This test uses actual API responses from @api_logs/ to generate")
    print("OrderCreate payload and verify VDC mapping compliance.")
    print("=" * 60)
    
    # Run the test
    success = test_real_vdc_mapping()
    
    print("\n" + "=" * 60)
    print("📋 TEST COMPLETE")
    print("=" * 60)
    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
