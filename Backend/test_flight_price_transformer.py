#!/usr/bin/env python3
"""
Test script to verify the improved flight price transformer with real data
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.flight_price_transformer import transform_flight_price_response

def test_flight_price_transformer():
    """Test the flight price transformer with real AF response data"""
    
    # Load the test flight price response
    test_file = "tests/FlightPriceRS_AF.json"
    
    try:
        with open(test_file, 'r') as f:
            raw_response = json.load(f)
        
        print("✅ Loaded test flight price response")
        print(f"📄 File: {test_file}")
        
        # Transform the response
        print("\n🔄 Transforming flight price response...")
        transformed_data = transform_flight_price_response(raw_response)
        
        print(f"✅ Transformation completed")
        print(f"📊 Status: {transformed_data.get('transformation_status', 'unknown')}")
        print(f"🎫 Total offers: {transformed_data.get('total_offers', 0)}")
        
        # Examine the first offer in detail
        priced_offers = transformed_data.get('priced_offers', [])
        if priced_offers:
            first_offer = priced_offers[0]
            print(f"\n📋 First Offer Details:")
            print(f"   Offer ID: {first_offer.get('offer_id', 'N/A')}")
            print(f"   Direction: {first_offer.get('direction', 'N/A')}")
            print(f"   Total Price: {first_offer.get('total_price', {}).get('amount', 'N/A')} {first_offer.get('total_price', {}).get('currency', 'N/A')}")
            
            # Check flight segments structure
            flight_segments = first_offer.get('flight_segments', {})
            
            if isinstance(flight_segments, dict):
                # Round-trip structure
                outbound = flight_segments.get('outbound', [])
                return_segs = flight_segments.get('return', [])
                
                print(f"\n✈️ Flight Segments (Round-trip structure):")
                print(f"   Outbound segments: {len(outbound)}")
                if outbound:
                    print(f"   Outbound route: {outbound[0].get('departure_airport', 'N/A')} -> {outbound[-1].get('arrival_airport', 'N/A')}")
                    for i, seg in enumerate(outbound):
                        print(f"     {i+1}. {seg.get('departure_airport', 'N/A')} -> {seg.get('arrival_airport', 'N/A')} ({seg.get('flight_number', 'N/A')}) at {seg.get('departure_datetime', 'N/A')}")
                
                print(f"   Return segments: {len(return_segs)}")
                if return_segs:
                    print(f"   Return route: {return_segs[0].get('departure_airport', 'N/A')} -> {return_segs[-1].get('arrival_airport', 'N/A')}")
                    for i, seg in enumerate(return_segs):
                        print(f"     {i+1}. {seg.get('departure_airport', 'N/A')} -> {seg.get('arrival_airport', 'N/A')} ({seg.get('flight_number', 'N/A')}) at {seg.get('departure_datetime', 'N/A')}")
                        
            elif isinstance(flight_segments, list):
                # One-way structure
                print(f"\n✈️ Flight Segments (One-way structure):")
                print(f"   Total segments: {len(flight_segments)}")
                if flight_segments:
                    print(f"   Route: {flight_segments[0].get('departure_airport', 'N/A')} -> {flight_segments[-1].get('arrival_airport', 'N/A')}")
                    for i, seg in enumerate(flight_segments):
                        print(f"     {i+1}. {seg.get('departure_airport', 'N/A')} -> {seg.get('arrival_airport', 'N/A')} ({seg.get('flight_number', 'N/A')}) at {seg.get('departure_datetime', 'N/A')}")
            
            # Check passengers
            passengers = first_offer.get('passengers', [])
            print(f"\n👥 Passengers:")
            for pax in passengers:
                print(f"   {pax.get('type', 'N/A')}: {pax.get('count', 0)} passengers")
                baggage = pax.get('baggage', {})
                if baggage:
                    print(f"     Carry-on: {baggage.get('carryOn', 'N/A')}")
                    print(f"     Checked: {baggage.get('checked', 'N/A')}")
        
        # Save the transformed result for inspection
        output_file = "outputs/test_flight_price_transformed.json"
        with open(output_file, 'w') as f:
            json.dump(transformed_data, f, indent=2)
        
        print(f"\n💾 Transformed data saved to: {output_file}")
        
        return transformed_data
        
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file}")
        return None
    except Exception as e:
        print(f"❌ Error during transformation: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_round_trip_detection():
    """Test the round-trip segment detection with the original NBO-FRA data"""

    print("\n🔄 Testing Round-trip Segment Detection")
    print("-" * 40)

    from utils.flight_price_transformer import _detect_round_trip_segments, FlightSegment

    # Create test segments based on the original NBO-FRA round-trip data
    segments = [
        FlightSegment(
            departure_airport='NBO',
            arrival_airport='AMS',
            departure_datetime='2025-07-12T08:40:00.000',
            arrival_datetime='2025-07-12T16:40:00.000',
            airline_code='KQ',
            airline_name='Kenya Airways',
            airline_logo_url='/airlines/KQ.svg',
            flight_number='KQ116',
            duration='9h'
        ),
        FlightSegment(
            departure_airport='AMS',
            arrival_airport='FRA',
            departure_datetime='2025-07-12T20:40:00.000',
            arrival_datetime='2025-07-12T21:45:00.000',
            airline_code='KQ',
            airline_name='Kenya Airways',
            airline_logo_url='/airlines/KQ.svg',
            flight_number='KQ1773',
            duration='1h 5m'
        ),
        FlightSegment(
            departure_airport='FRA',
            arrival_airport='AMS',
            departure_datetime='2025-07-22T11:45:00.000',
            arrival_datetime='2025-07-22T13:00:00.000',
            airline_code='KQ',
            airline_name='Kenya Airways',
            airline_logo_url='/airlines/KQ.svg',
            flight_number='KQ1768',
            duration='1h 15m'
        ),
        FlightSegment(
            departure_airport='AMS',
            arrival_airport='NBO',
            departure_datetime='2025-07-22T20:35:00.000',
            arrival_datetime='2025-07-23T06:10:00.000',
            airline_code='KQ',
            airline_name='Kenya Airways',
            airline_logo_url='/airlines/KQ.svg',
            flight_number='KQ117',
            duration='8h 35m'
        )
    ]

    print('🧪 Testing round-trip segment detection...')
    outbound, return_segs = _detect_round_trip_segments(segments)

    print(f'\n✈️ Outbound segments ({len(outbound)}):')
    for i, seg in enumerate(outbound):
        print(f'   {i+1}. {seg.departure_airport} → {seg.arrival_airport} ({seg.flight_number}) at {seg.departure_datetime}')

    print(f'\n🔄 Return segments ({len(return_segs)}):')
    for i, seg in enumerate(return_segs):
        print(f'   {i+1}. {seg.departure_airport} → {seg.arrival_airport} ({seg.flight_number}) at {seg.departure_datetime}')

    print(f'\n📍 Route Summary:')
    if outbound:
        print(f'   Outbound: {outbound[0].departure_airport} → {outbound[-1].arrival_airport}')
    if return_segs:
        print(f'   Return: {return_segs[0].departure_airport} → {return_segs[-1].arrival_airport}')

    # Validate the results
    expected_outbound_route = "NBO → FRA"
    expected_return_route = "FRA → NBO"

    actual_outbound = f"{outbound[0].departure_airport} → {outbound[-1].arrival_airport}" if outbound else ""
    actual_return = f"{return_segs[0].departure_airport} → {return_segs[-1].arrival_airport}" if return_segs else ""

    if actual_outbound == expected_outbound_route and actual_return == expected_return_route:
        print(f"\n✅ Round-trip detection working correctly!")
        print(f"   Expected: {expected_outbound_route} / {expected_return_route}")
        print(f"   Actual: {actual_outbound} / {actual_return}")
        return True
    else:
        print(f"\n❌ Round-trip detection failed!")
        print(f"   Expected: {expected_outbound_route} / {expected_return_route}")
        print(f"   Actual: {actual_outbound} / {actual_return}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Flight Price Transformer")
    print("=" * 50)

    # Test 1: Real flight price transformation
    result1 = test_flight_price_transformer()

    # Test 2: Round-trip segment detection
    result2 = test_round_trip_detection()

    if result1 and result2:
        print("\n🎉 All tests completed successfully!")
        print("✅ Flight price transformation working")
        print("✅ Round-trip segment detection working")
    else:
        print("\n❌ Some tests failed!")
        if not result1:
            print("❌ Flight price transformation failed")
        if not result2:
            print("❌ Round-trip segment detection failed")
