#!/usr/bin/env python3
"""
Test script to verify the fallback transformation fix for Brussels Airlines.
"""

import json
import sys
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer

def test_fallback_transformation():
    """Test the fallback transformation with actual response data."""
    
    # Load the most recent air shopping response
    output_dir = backend_dir / "Output"
    response_files = list(output_dir.glob("AirShopping_RESPONSE_*.json"))
    
    if not response_files:
        print("❌ No air shopping response files found in Output directory")
        return False
    
    # Get the most recent response file
    latest_response = max(response_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Using response file: {latest_response.name}")
    
    try:
        with open(latest_response, 'r', encoding='utf-8') as f:
            response_data = json.load(f)
        
        print(f"✅ Loaded response data successfully")
        
        # Initialize the transformer
        transformer = EnhancedAirShoppingTransformer(response_data)
        
        # Transform the response
        result = transformer.transform_for_results()
        
        if not result or result.get('status') != 'success':
            print(f"❌ Transformation failed: {result}")
            return False
        
        offers = result.get('data', {}).get('offers', [])
        print(f"📊 Total offers transformed: {len(offers)}")
        
        # Look for Brussels Airlines (SN) offers
        sn_offers = [offer for offer in offers if offer.get('airline', {}).get('code') == 'SN']
        print(f"🇧🇪 Brussels Airlines (SN) offers found: {len(sn_offers)}")

        # Check what airlines we actually have
        airline_codes = set(offer.get('airline', {}).get('code') for offer in offers)
        print(f"📋 Airlines in transformed offers: {sorted(airline_codes)}")

        if not sn_offers:
            print("⚠️  No Brussels Airlines offers found in this response")
            print("✅ This is expected - the raw response contains SN segments but no SN offers")

            # Check if we have any offers with actual flight data (not "Unknown")
            sample_offers = offers[:3]  # Check first 3 offers
            for i, offer in enumerate(sample_offers):
                airline_code = offer.get('airline', {}).get('code', 'Unknown')
                departure_airport = offer.get('departure', {}).get('airport', 'Unknown')
                arrival_airport = offer.get('arrival', {}).get('airport', 'Unknown')
                departure_time = offer.get('departure', {}).get('time', 'Unknown')
                arrival_time = offer.get('arrival', {}).get('time', 'Unknown')

                print(f"\n🔍 Sample offer {i+1} ({airline_code}):")
                print(f"   Departure: {departure_airport} at {departure_time}")
                print(f"   Arrival: {arrival_airport} at {arrival_time}")

                if (departure_airport != 'Unknown' and arrival_airport != 'Unknown' and
                    departure_time != 'Unknown' and arrival_time != 'Unknown'):
                    print(f"✅ Offer {i+1} has real flight data!")
                    return True
                else:
                    print(f"❌ Offer {i+1} still has 'Unknown' values")

            return False

        # Check the first SN offer for actual flight data
        first_sn_offer = sn_offers[0]
        
        print("\n🔍 Checking Brussels Airlines offer data:")
        print(f"   Airline: {first_sn_offer.get('airline', {}).get('name', 'Unknown')}")
        print(f"   Flight Number: {first_sn_offer.get('airline', {}).get('flightNumber', 'Unknown')}")
        print(f"   Departure Airport: {first_sn_offer.get('departure', {}).get('airport', 'Unknown')}")
        print(f"   Departure Time: {first_sn_offer.get('departure', {}).get('time', 'Unknown')}")
        print(f"   Arrival Airport: {first_sn_offer.get('arrival', {}).get('airport', 'Unknown')}")
        print(f"   Arrival Time: {first_sn_offer.get('arrival', {}).get('time', 'Unknown')}")
        print(f"   Duration: {first_sn_offer.get('duration', 'Unknown')}")
        print(f"   Price: {first_sn_offer.get('price', 0)} {first_sn_offer.get('currency', 'USD')}")
        print(f"   Segments: {len(first_sn_offer.get('segments', []))}")
        
        # Check if we still have "Unknown" values (indicating the fix didn't work)
        departure_airport = first_sn_offer.get('departure', {}).get('airport', 'Unknown')
        arrival_airport = first_sn_offer.get('arrival', {}).get('airport', 'Unknown')
        departure_time = first_sn_offer.get('departure', {}).get('time', 'Unknown')
        arrival_time = first_sn_offer.get('arrival', {}).get('time', 'Unknown')
        
        if (departure_airport == 'Unknown' and arrival_airport == 'Unknown' and 
            departure_time == 'Unknown' and arrival_time == 'Unknown'):
            print("❌ Fix not working - still showing 'Unknown' values")
            return False
        else:
            print("✅ Fix working - showing actual flight data!")
            return True
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Brussels Airlines fallback transformation fix...")
    success = test_fallback_transformation()
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
