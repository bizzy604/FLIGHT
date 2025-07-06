#!/usr/bin/env python3
"""
Simple test to verify that our operating carrier fix is working.
"""

import json
import sys
import os
from pathlib import Path

# Add the Backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer

def test_operating_carrier_extraction():
    """Test that we're now extracting operating carrier instead of offer owner."""
    
    print("🔍 Testing Operating Carrier Extraction Fix...")
    print("=" * 60)
    
    # Load the raw air shopping response
    raw_response_path = Path("Output/AirShopping_RESPONSE_20250706_040538.json")
    if not raw_response_path.exists():
        print("❌ Raw air shopping response file not found")
        return False
    
    with open(raw_response_path, 'r', encoding='utf-8') as f:
        raw_response_data = json.load(f)
    
    # Extract the actual response from the wrapper
    raw_response = raw_response_data.get('data', raw_response_data)
    
    print("📊 Analyzing first offer in raw response...")
    
    # Find the first offer and its details
    offers = []
    if 'OffersGroup' in raw_response and 'AirlineOfferGroup' in raw_response['OffersGroup']:
        for group in raw_response['OffersGroup']['AirlineOfferGroup']:
            airline_offers = group.get('AirlineOffer', [])
            if not isinstance(airline_offers, list):
                airline_offers = [airline_offers]
            offers.extend(airline_offers)
    
    if not offers:
        print("❌ No offers found in raw response")
        return False
    
    first_offer = offers[0]
    
    # Extract offer owner
    offer_owner = '??'
    if 'PricedOffer' in first_offer:
        offer_owner = first_offer['PricedOffer'].get('OfferID', {}).get('Owner', '??')
    elif 'OfferID' in first_offer:
        offer_owner = first_offer['OfferID'].get('Owner', '??')
    
    print(f"Offer Owner (old method): {offer_owner}")
    
    # Extract operating/marketing carrier from segments
    data_lists = raw_response.get('DataLists', {})
    segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
    if not isinstance(segments, list):
        segments = [segments] if segments else []
    
    operating_carrier = '??'
    marketing_carrier = '??'
    
    if segments:
        first_segment = segments[0]
        
        # Operating carrier
        op_carrier = first_segment.get('OperatingCarrier', {})
        if op_carrier:
            op_airline_id = op_carrier.get('AirlineID', {})
            if isinstance(op_airline_id, dict):
                operating_carrier = op_airline_id.get('value', '??')
            else:
                operating_carrier = op_airline_id or '??'
        
        # Marketing carrier
        mk_carrier = first_segment.get('MarketingCarrier', {})
        if mk_carrier:
            mk_airline_id = mk_carrier.get('AirlineID', {})
            if isinstance(mk_airline_id, dict):
                marketing_carrier = mk_airline_id.get('value', '??')
            else:
                marketing_carrier = mk_airline_id or '??'
    
    print(f"Operating Carrier (new method): {operating_carrier}")
    print(f"Marketing Carrier (fallback): {marketing_carrier}")
    
    # Now test our transformer
    print("\n📊 Testing Enhanced Transformer...")
    try:
        transformer = EnhancedAirShoppingTransformer(raw_response)
        transformed_response = transformer.transform_for_results()
        
        if transformed_response and 'offers' in transformed_response:
            offers = transformed_response['offers']
            if offers:
                first_transformed_offer = offers[0]
                extracted_airline = first_transformed_offer.get('airline', {}).get('code', '??')
                
                print(f"Transformer Result: {extracted_airline}")
                
                # Check if we're using operating carrier
                expected_airline = operating_carrier if operating_carrier != '??' else marketing_carrier
                
                print(f"\n🔍 ANALYSIS:")
                print(f"Expected (Operating/Marketing): {expected_airline}")
                print(f"Actual (Transformer): {extracted_airline}")
                print(f"Old Method (Offer Owner): {offer_owner}")
                
                if extracted_airline == expected_airline:
                    print("✅ SUCCESS: Transformer is using operating/marketing carrier!")
                    if extracted_airline != offer_owner:
                        print("✅ IMPROVEMENT: No longer using offer owner!")
                        return True
                    else:
                        print("⚠️  Note: Operating carrier happens to match offer owner")
                        return True
                elif extracted_airline == offer_owner:
                    print("❌ ISSUE: Still using offer owner instead of operating carrier")
                    return False
                else:
                    print("❓ UNKNOWN: Using different airline code")
                    return False
            else:
                print("❌ No offers in transformed response")
                return False
        else:
            print("❌ Transformation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during transformation: {e}")
        return False

def test_multiple_offers():
    """Test multiple offers to see the pattern."""
    
    print("\n" + "=" * 60)
    print("🔍 Testing Multiple Offers Pattern...")
    print("=" * 60)
    
    # Load the raw air shopping response
    raw_response_path = Path("Output/AirShopping_RESPONSE_20250706_040538.json")
    with open(raw_response_path, 'r', encoding='utf-8') as f:
        raw_response_data = json.load(f)
    
    raw_response = raw_response_data.get('data', raw_response_data)
    
    try:
        transformer = EnhancedAirShoppingTransformer(raw_response)
        transformed_response = transformer.transform_for_results()
        
        if transformed_response and 'offers' in transformed_response:
            offers = transformed_response['offers']
            
            print(f"Found {len(offers)} transformed offers")
            
            # Check first 10 offers
            airline_counts = {}
            for i, offer in enumerate(offers[:10]):
                airline_code = offer.get('airline', {}).get('code', '??')
                airline_name = offer.get('airline', {}).get('name', 'Unknown')
                
                if airline_code not in airline_counts:
                    airline_counts[airline_code] = 0
                airline_counts[airline_code] += 1
                
                print(f"Offer {i+1}: {airline_code} ({airline_name})")
            
            print(f"\n📊 Airline Distribution (first 10 offers):")
            for airline, count in sorted(airline_counts.items()):
                print(f"  {airline}: {count} offers")
            
            # Check if we see AF (Air France) instead of KL (KLM) for the first offers
            first_airline = offers[0].get('airline', {}).get('code', '??')
            if first_airline == 'AF':
                print("\n✅ SUCCESS: First offer shows AF (Air France) - operating carrier!")
                return True
            elif first_airline == 'KL':
                print("\n❌ ISSUE: First offer still shows KL (KLM) - offer owner")
                return False
            else:
                print(f"\n❓ UNKNOWN: First offer shows {first_airline}")
                return False
        else:
            print("❌ No offers found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Operating Carrier Fix...")
    
    # Test single offer analysis
    single_test_ok = test_operating_carrier_extraction()
    
    # Test multiple offers pattern
    multiple_test_ok = test_multiple_offers()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS:")
    print("=" * 60)
    print(f"Single Offer Test: {'✅ PASS' if single_test_ok else '❌ FAIL'}")
    print(f"Multiple Offers Test: {'✅ PASS' if multiple_test_ok else '❌ FAIL'}")
    
    if single_test_ok and multiple_test_ok:
        print("\n🎉 ALL TESTS PASSED! Operating carrier fix is working!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. The fix may need adjustment.")
        sys.exit(1)
