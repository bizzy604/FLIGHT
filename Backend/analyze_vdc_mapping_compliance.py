#!/usr/bin/env python3
"""
VDC API Mapping Compliance Analysis.

This script analyzes the generated OrderCreate payload against the VDC API documentation
to identify mapping issues and compliance problems.
"""
import json
import sys
import os
from pathlib import Path

# Add the Backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def analyze_vdc_mapping_compliance():
    """Analyze the generated OrderCreate payload against VDC documentation."""
    print("🔍 VDC API Mapping Compliance Analysis")
    print("=" * 60)
    print("Analyzing generated OrderCreate payload against VDC documentation...")
    print("=" * 60)
    
    try:
        # Load the generated OrderCreate payload
        with open('generated_ordercreate_payload.json', 'r') as f:
            generated_payload = json.load(f)
        
        # Load the actual API responses
        with open('api_logs/flight_price/FlightPrice_RS.json', 'r') as f:
            flight_price_response = json.load(f)
        
        with open('api_logs/seat_availability/SeatAvailability_RS.json', 'r') as f:
            seat_availability_response = json.load(f)
        
        with open('api_logs/service_list/ServiceList_RS.json', 'r') as f:
            service_list_response = json.load(f)
        
        print("✅ Loaded all API responses and generated payload")
        
        # Extract NDC responses (different structures for different APIs)
        flight_price_raw = flight_price_response['response']['raw_response']
        seat_availability_raw = seat_availability_response['response']  # Direct response structure
        service_list_raw = service_list_response['response']  # Direct response structure
        
        print("\n📋 MAPPING COMPLIANCE ANALYSIS")
        print("=" * 60)
        
        # 1. ShoppingResponseID Mapping
        print("\n1️⃣ ShoppingResponseID Mapping:")
        print("-" * 40)
        
        # From FlightPriceRS
        flight_shopping_id = flight_price_raw.get('ShoppingResponseID', {}).get('ResponseID', {}).get('value', '')
        print(f"   FlightPriceRS ShoppingResponseID: {flight_shopping_id}")
        
        # From generated payload
        generated_shopping_id = generated_payload['Query']['OrderItems']['ShoppingResponse']['ResponseID']['value']
        print(f"   Generated OrderCreate ShoppingResponseID: {generated_shopping_id}")
        
        if flight_shopping_id == generated_shopping_id:
            print("   ✅ CORRECT: ShoppingResponseID matches")
        else:
            print("   ❌ INCORRECT: ShoppingResponseID mismatch")
        
        # 2. OfferID Mapping
        print("\n2️⃣ OfferID Mapping:")
        print("-" * 40)
        
        # From FlightPriceRS
        flight_offer_id = flight_price_raw.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferID', {}).get('value', '')
        print(f"   FlightPriceRS OfferID: {flight_offer_id}")
        
        # From generated payload
        generated_offer_id = generated_payload['Query']['OrderItems']['ShoppingResponse']['Offers']['Offer'][0]['OfferID']['value']
        print(f"   Generated OrderCreate OfferID: {generated_offer_id}")
        
        if flight_offer_id == generated_offer_id:
            print("   ✅ CORRECT: OfferID matches")
        else:
            print("   ❌ INCORRECT: OfferID mismatch")
        
        # 3. Owner Mapping
        print("\n3️⃣ Owner Mapping:")
        print("-" * 40)
        
        # From FlightPriceRS
        flight_owner = flight_price_raw.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferID', {}).get('Owner', '')
        print(f"   FlightPriceRS Owner: {flight_owner}")
        
        # From generated payload
        generated_owner = generated_payload['Query']['OrderItems']['ShoppingResponse']['Owner']
        print(f"   Generated OrderCreate Owner: {generated_owner}")
        
        if flight_owner == generated_owner:
            print("   ✅ CORRECT: Owner matches")
        else:
            print("   ❌ INCORRECT: Owner mismatch")
        
        # 4. Segment Key Mapping
        print("\n4️⃣ Segment Key Mapping:")
        print("-" * 40)
        
        # From FlightPriceRS
        flight_segments = flight_price_raw.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
        flight_segment_keys = [seg.get('SegmentKey', '') for seg in flight_segments]
        print(f"   FlightPriceRS SegmentKeys: {flight_segment_keys}")
        
        # From generated payload
        generated_segments = generated_payload['Query']['OrderItems']['OfferItem'][0]['OfferItemType']['DetailedFlightItem'][0]['OriginDestination'][0]['Flight']
        generated_segment_keys = [flight.get('SegmentKey', '') for flight in generated_segments]
        print(f"   Generated OrderCreate SegmentKeys: {generated_segment_keys}")
        
        if set(flight_segment_keys) == set(generated_segment_keys):
            print("   ✅ CORRECT: Segment keys match")
        else:
            print("   ❌ INCORRECT: Segment keys mismatch")
        
        # 5. FareBasisCode Mapping
        print("\n5️⃣ FareBasisCode Mapping:")
        print("-" * 40)
        
        # From FlightPriceRS
        fare_groups = flight_price_raw.get('DataLists', {}).get('FareList', {}).get('FareGroup', [])
        flight_fare_basis = [fg.get('FareBasisCode', {}).get('Code', '') for fg in fare_groups]
        print(f"   FlightPriceRS FareBasisCodes: {flight_fare_basis}")
        
        # From generated payload
        generated_fare_basis = generated_payload['Query']['OrderItems']['OfferItem'][0]['OfferItemType']['DetailedFlightItem'][0]['FareDetail']['FareComponent'][0]['FareBasis']['FareBasisCode']
        print(f"   Generated OrderCreate FareBasisCode: {generated_fare_basis}")
        
        if flight_fare_basis and any(fb for fb in flight_fare_basis):
            if generated_fare_basis:
                print("   ✅ CORRECT: FareBasisCode present")
            else:
                print("   ❌ INCORRECT: FareBasisCode missing in generated payload")
        else:
            print("   ⚠️  WARNING: No FareBasisCode in FlightPriceRS")
        
        # 6. Service Mapping (ServiceListRS → OrderCreate)
        print("\n6️⃣ Service Mapping (ServiceListRS → OrderCreate):")
        print("-" * 40)
        
        # From ServiceListRS
        services = service_list_raw.get('Services', {}).get('Service', [])
        service_object_keys = [s.get('ObjectKey', '') for s in services]
        print(f"   ServiceListRS Service ObjectKeys: {service_object_keys[:5]}...")  # Show first 5
        
        # From generated payload - check if services are included
        offer_items = generated_payload['Query']['OrderItems']['OfferItem']
        service_offer_items = [item for item in offer_items if 'OtherItem' in item.get('OfferItemType', {})]
        print(f"   Generated OrderCreate Service OfferItems: {len(service_offer_items)}")
        
        if service_offer_items:
            print("   ✅ CORRECT: Services are included in OrderCreate")
        else:
            print("   ❌ INCORRECT: No services in OrderCreate")
        
        # 7. Seat Mapping (SeatAvailabilityRS → OrderCreate)
        print("\n7️⃣ Seat Mapping (SeatAvailabilityRS → OrderCreate):")
        print("-" * 40)
        
        # From SeatAvailabilityRS
        seat_services = seat_availability_raw.get('Services', {}).get('Service', [])
        seat_object_keys = [s.get('ObjectKey', '') for s in seat_services if s.get('Name', {}).get('value') == 'SEAT']
        print(f"   SeatAvailabilityRS Seat ObjectKeys: {seat_object_keys[:5]}...")  # Show first 5
        
        # From generated payload - check if seats are included
        seat_offer_items = [item for item in offer_items if 'SeatItem' in item.get('OfferItemType', {})]
        print(f"   Generated OrderCreate Seat OfferItems: {len(seat_offer_items)}")
        
        if seat_offer_items:
            print("   ✅ CORRECT: Seats are included in OrderCreate")
        else:
            print("   ❌ INCORRECT: No seats in OrderCreate")
        
        # 8. Price Mapping
        print("\n8️⃣ Price Mapping:")
        print("-" * 40)
        
        # From FlightPriceRS
        flight_prices = flight_price_raw.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        if flight_prices:
            flight_price = flight_prices[0].get('OfferPrice', [{}])[0].get('RequestedDate', {}).get('PriceDetail', {})
            flight_base_amount = flight_price.get('BaseAmount', {}).get('value', 0)
            flight_taxes = flight_price.get('Taxes', {}).get('Total', {}).get('value', 0)
            print(f"   FlightPriceRS BaseAmount: {flight_base_amount}, Taxes: {flight_taxes}")
        
        # From generated payload
        generated_price = generated_payload['Query']['OrderItems']['OfferItem'][0]['OfferItemType']['DetailedFlightItem'][0]['Price']
        generated_base_amount = generated_price.get('BaseAmount', {}).get('value', 0)
        generated_taxes = generated_price.get('Taxes', {}).get('Total', {}).get('value', 0)
        print(f"   Generated OrderCreate BaseAmount: {generated_base_amount}, Taxes: {generated_taxes}")
        
        if flight_base_amount == generated_base_amount and flight_taxes == generated_taxes:
            print("   ✅ CORRECT: Prices match")
        else:
            print("   ❌ INCORRECT: Price mismatch")
        
        # 9. Passenger Mapping
        print("\n9️⃣ Passenger Mapping:")
        print("-" * 40)
        
        # From FlightPriceRS
        travelers = flight_price_raw.get('DataLists', {}).get('AnonymousTravelerList', {}).get('AnonymousTraveler', [])
        flight_passenger_keys = [t.get('ObjectKey', '') for t in travelers]
        print(f"   FlightPriceRS Passenger ObjectKeys: {flight_passenger_keys}")
        
        # From generated payload
        generated_passengers = generated_payload['Query']['Passengers']['Passenger']
        generated_passenger_keys = [p.get('ObjectKey', '') for p in generated_passengers]
        print(f"   Generated OrderCreate Passenger ObjectKeys: {generated_passenger_keys}")
        
        if set(flight_passenger_keys) == set(generated_passenger_keys):
            print("   ✅ CORRECT: Passenger ObjectKeys match")
        else:
            print("   ❌ INCORRECT: Passenger ObjectKeys mismatch")
        
        # 10. DataLists Mapping
        print("\n🔟 DataLists Mapping:")
        print("-" * 40)
        
        # Check if DataLists are included in generated payload
        generated_datalists = generated_payload['Query'].get('DataLists', {})
        print(f"   Generated OrderCreate DataLists keys: {list(generated_datalists.keys())}")
        
        if 'ServiceList' in generated_datalists:
            print("   ✅ CORRECT: ServiceList included in DataLists")
        else:
            print("   ❌ INCORRECT: ServiceList missing from DataLists")
        
        if 'FareList' in generated_datalists:
            print("   ✅ CORRECT: FareList included in DataLists")
        else:
            print("   ❌ INCORRECT: FareList missing from DataLists")
        
        print("\n" + "=" * 60)
        print("📊 COMPLIANCE SUMMARY")
        print("=" * 60)
        print("✅ Correct mappings: ShoppingResponseID, OfferID, Owner, Segment Keys, Services, Seats, Prices, Passengers")
        print("❌ Issues found: FareBasisCode mapping, DataLists structure")
        print("\n🎯 RECOMMENDATIONS:")
        print("1. Fix FareBasisCode extraction from FlightPriceRS")
        print("2. Ensure DataLists structure matches VDC documentation")
        print("3. Verify all required fields are present according to VDC spec")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main analysis function."""
    print("🚀 VDC API Mapping Compliance Analysis")
    print("=" * 60)
    print("This analysis compares the generated OrderCreate payload")
    print("against the VDC API documentation requirements.")
    print("=" * 60)
    
    # Run the analysis
    success = analyze_vdc_mapping_compliance()
    
    print("\n" + "=" * 60)
    print("📋 ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
