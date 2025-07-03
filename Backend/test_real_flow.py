#!/usr/bin/env python3
"""
Test script to validate the real flow with the actual backend logic.
"""

import json
import sys
import os

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.build_flightprice_rq import build_flight_price_request

def load_test_data():
    """Load the multi-airline air shopping response test data."""
    try:
        with open("../postman/airshopingresponse.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: Test data file not found")
        return None

def test_real_backend_flow(airshopping_response):
    """Test the real backend flow that's used in production."""
    print("=== TESTING REAL BACKEND FLOW ===")
    
    # Test with a QR offer (they appear later in the sequence)
    # Let's try offer index 1200 which should be a QR offer
    test_indices = [0, 5, 10, 50, 100, 500, 1000, 1200, 1400]
    
    for offer_index in test_indices:
        print(f"\n--- Testing Offer Index {offer_index} ---")
        
        try:
            # This is the exact call that the backend makes
            flight_price_payload = build_flight_price_request(
                airshopping_response, 
                selected_offer_index=offer_index
            )
            
            # Check the generated payload
            data_lists = flight_price_payload.get("DataLists", {})
            anonymous_travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
            
            if not isinstance(anonymous_travelers, list):
                anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
            
            # Check if we have travelers and what their keys look like
            traveler_keys = []
            for traveler in anonymous_travelers:
                if isinstance(traveler, dict):
                    object_key = traveler.get("ObjectKey", "")
                    traveler_keys.append(object_key)
            
            # Check the offer ID to see which airline this is
            query_offers = flight_price_payload.get("Query", {}).get("Offers", {}).get("Offer", [])
            airline_owner = "Unknown"
            if query_offers and len(query_offers) > 0:
                offer_id = query_offers[0].get("OfferID", {})
                airline_owner = offer_id.get("Owner", "Unknown")
            
            print(f"  Airline: {airline_owner}")
            print(f"  Travelers: {len(traveler_keys)} - {traveler_keys}")
            
            # Check if we have the contamination issue
            has_airline_prefixes = any("-" in key for key in traveler_keys)
            if has_airline_prefixes:
                print(f"  ❌ CONTAMINATION: Still has airline-prefixed keys!")
            else:
                print(f"  ✅ CLEAN: Only standard traveler keys")
            
            # Save a sample payload for inspection
            if offer_index == 1200:  # Save one for detailed inspection
                with open(f"test_real_flow_payload_{offer_index}.json", "w", encoding="utf-8") as f:
                    json.dump(flight_price_payload, f, indent=2, ensure_ascii=False)
                print(f"  Saved payload to: test_real_flow_payload_{offer_index}.json")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

def main():
    """Main test function."""
    print("Testing Real Backend Flow")
    print("=" * 50)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        sys.exit(1)
    
    # Test the real backend flow
    test_real_backend_flow(airshopping_response)

if __name__ == "__main__":
    main()
