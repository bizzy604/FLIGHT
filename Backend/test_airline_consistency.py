#!/usr/bin/env python3
"""
Test script to verify airline consistency between air shopping and flight pricing.
"""

import json
import sys
import os
from pathlib import Path

# Add the Backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer
from utils.flight_price_transformer import build_flight_segment
from services.flight.pricing import FlightPricingService

def test_airline_consistency():
    """Test that airline information is consistent between air shopping and flight pricing."""

    print("🔍 Testing Airline Consistency...")
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

    # Transform using enhanced transformer
    print("📊 Transforming air shopping response...")
    try:
        transformer = EnhancedAirShoppingTransformer(raw_response)
        transformed_response = transformer.transform_for_results()

        if not transformed_response:
            print("❌ Failed to transform air shopping response")
            return False

        print(f"✅ Transformed response keys: {list(transformed_response.keys())}")

        # Check for different possible keys
        flights = []
        if 'flights' in transformed_response:
            flights = transformed_response['flights']
        elif 'offers' in transformed_response:
            flights = transformed_response['offers']
        elif 'data' in transformed_response:
            flights = transformed_response['data']
        else:
            print("❌ No flight data found in transformed response")
            return False

        print(f"✅ Found {len(flights)} flights in transformed response")
    except Exception as e:
        print(f"❌ Error transforming response: {e}")
        return False
    
    # Test the first few flights for consistency
    test_count = min(5, len(flights))
    print(f"\n🧪 Testing first {test_count} flights for airline consistency...")
    
    consistent_count = 0
    
    for i in range(test_count):
        flight = flights[i]
        airline_code = flight.get('airline', {}).get('code', '??')
        airline_name = flight.get('airline', {}).get('name', 'Unknown')
        
        print(f"\n--- Flight {i+1} ---")
        print(f"Display Airline: {airline_code} ({airline_name})")
        
        # Get the original offer from raw response
        try:
            # Find the corresponding offer in raw response
            offers = []
            if 'AirlineOfferGroup' in raw_response.get('AirShoppingRS', {}):
                for group in raw_response['AirShoppingRS']['AirlineOfferGroup']:
                    airline_offers = group.get('AirlineOffer', [])
                    if not isinstance(airline_offers, list):
                        airline_offers = [airline_offers]
                    offers.extend(airline_offers)
            elif 'PricedFlightOffer' in raw_response.get('AirShoppingRS', {}):
                offers = raw_response['AirShoppingRS']['PricedFlightOffer']
                if not isinstance(offers, list):
                    offers = [offers]
            
            if i < len(offers):
                offer = offers[i]
                
                # Extract offer owner
                offer_owner = '??'
                if 'PricedOffer' in offer:
                    offer_owner = offer['PricedOffer'].get('OfferID', {}).get('Owner', '??')
                elif 'OfferID' in offer:
                    offer_owner = offer['OfferID'].get('Owner', '??')
                
                print(f"Offer Owner: {offer_owner}")
                
                # Extract operating carrier from segments
                operating_carriers = set()
                marketing_carriers = set()
                
                # Look for segments in DataLists
                data_lists = raw_response.get('AirShoppingRS', {}).get('DataLists', {})
                segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
                if not isinstance(segments, list):
                    segments = [segments] if segments else []
                
                # Get first few segments for this offer
                for seg in segments[:2]:  # Check first 2 segments
                    operating_carrier = seg.get('OperatingCarrier', {})
                    marketing_carrier = seg.get('MarketingCarrier', {})
                    
                    if operating_carrier:
                        op_airline_id = operating_carrier.get('AirlineID', {})
                        if isinstance(op_airline_id, dict):
                            op_code = op_airline_id.get('value')
                        else:
                            op_code = op_airline_id
                        if op_code:
                            operating_carriers.add(op_code)
                    
                    if marketing_carrier:
                        mk_airline_id = marketing_carrier.get('AirlineID', {})
                        if isinstance(mk_airline_id, dict):
                            mk_code = mk_airline_id.get('value')
                        else:
                            mk_code = mk_airline_id
                        if mk_code:
                            marketing_carriers.add(mk_code)
                
                print(f"Operating Carriers: {list(operating_carriers)}")
                print(f"Marketing Carriers: {list(marketing_carriers)}")
                
                # Check consistency
                expected_airline = list(operating_carriers)[0] if operating_carriers else list(marketing_carriers)[0] if marketing_carriers else offer_owner
                
                if airline_code == expected_airline:
                    print("✅ CONSISTENT - Display matches operating/marketing carrier")
                    consistent_count += 1
                elif airline_code == offer_owner:
                    print("⚠️  USING OFFER OWNER - May not match actual operating airline")
                else:
                    print("❌ INCONSISTENT - Display doesn't match any carrier")
                
            else:
                print("❌ Could not find corresponding offer in raw response")
                
        except Exception as e:
            print(f"❌ Error analyzing flight {i+1}: {e}")
    
    print(f"\n📊 SUMMARY:")
    print(f"Consistent flights: {consistent_count}/{test_count}")
    print(f"Consistency rate: {(consistent_count/test_count)*100:.1f}%")
    
    if consistent_count == test_count:
        print("🎉 ALL FLIGHTS ARE CONSISTENT!")
        return True
    else:
        print("⚠️  Some flights may have inconsistent airline information")
        return consistent_count > 0

def test_flight_price_consistency():
    """Test flight price transformer consistency."""
    
    print("\n" + "=" * 60)
    print("🔍 Testing Flight Price Transformer Consistency...")
    print("=" * 60)
    
    # Load flight price response
    price_response_path = Path("Output/FlightPrice_RESPONSE_20250706_040942.json")
    if not price_response_path.exists():
        print("❌ Flight price response file not found")
        return False
    
    with open(price_response_path, 'r', encoding='utf-8') as f:
        price_response = json.load(f)
    
    # Extract segments and test airline extraction
    data_lists = price_response.get('FlightPriceRS', {}).get('DataLists', {})
    segments = data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
    if not isinstance(segments, list):
        segments = [segments] if segments else []
    
    print(f"✅ Found {len(segments)} segments in flight price response")
    
    consistent_count = 0
    test_count = min(3, len(segments))
    
    for i, segment in enumerate(segments[:test_count]):
        print(f"\n--- Segment {i+1} ---")
        
        # Test our updated flight segment builder
        try:
            flight_segment = build_flight_segment(segment)
            
            # Extract carriers manually for comparison
            operating_carrier = segment.get('OperatingCarrier', {})
            marketing_carrier = segment.get('MarketingCarrier', {})
            
            op_code = '??'
            mk_code = '??'
            
            if operating_carrier:
                op_airline_id = operating_carrier.get('AirlineID', {})
                if isinstance(op_airline_id, dict):
                    op_code = op_airline_id.get('value', '??')
                else:
                    op_code = op_airline_id or '??'
            
            if marketing_carrier:
                mk_airline_id = marketing_carrier.get('AirlineID', {})
                if isinstance(mk_airline_id, dict):
                    mk_code = mk_airline_id.get('value', '??')
                else:
                    mk_code = mk_airline_id or '??'
            
            print(f"Operating Carrier: {op_code}")
            print(f"Marketing Carrier: {mk_code}")
            print(f"Flight Segment Airline: {flight_segment.airline_code}")
            
            # Check if our transformer prioritizes operating carrier
            expected_code = op_code if op_code != '??' else mk_code
            
            if flight_segment.airline_code == expected_code:
                print("✅ CONSISTENT - Using operating carrier priority")
                consistent_count += 1
            else:
                print("❌ INCONSISTENT - Not using expected carrier")
                
        except Exception as e:
            print(f"❌ Error processing segment {i+1}: {e}")
    
    print(f"\n📊 FLIGHT PRICE SUMMARY:")
    print(f"Consistent segments: {consistent_count}/{test_count}")
    if test_count > 0:
        print(f"Consistency rate: {(consistent_count/test_count)*100:.1f}%")
        return consistent_count == test_count
    else:
        print("No segments to test")
        return True

if __name__ == "__main__":
    print("🚀 Starting Airline Consistency Tests...")
    
    # Test air shopping consistency
    air_shopping_ok = test_airline_consistency()
    
    # Test flight price consistency  
    flight_price_ok = test_flight_price_consistency()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS:")
    print("=" * 60)
    print(f"Air Shopping Consistency: {'✅ PASS' if air_shopping_ok else '❌ FAIL'}")
    print(f"Flight Price Consistency: {'✅ PASS' if flight_price_ok else '❌ FAIL'}")
    
    if air_shopping_ok and flight_price_ok:
        print("\n🎉 ALL TESTS PASSED! Airline information is consistent.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Review the output above for details.")
        sys.exit(1)
