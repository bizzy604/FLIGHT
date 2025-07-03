#!/usr/bin/env python3
"""
Debug script to understand traveler filtering in detail.
"""

import json
import sys
import os

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.build_flightprice_rq import build_flight_price_request, _filter_airline_specific_data

def load_test_data():
    """Load the multi-airline air shopping response test data."""
    try:
        with open("../postman/airshopingresponse.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: Test data file not found")
        return None

def debug_traveler_filtering(airshopping_response):
    """Debug the traveler filtering process in detail."""
    print("=== DEBUGGING TRAVELER FILTERING ===")
    
    # Check the original DataLists
    data_lists = airshopping_response.get("DataLists", {})
    anonymous_traveler_list = data_lists.get("AnonymousTravelerList", {})
    
    print(f"\n--- Original DataLists Structure ---")
    print(f"AnonymousTravelerList keys: {list(anonymous_traveler_list.keys())}")
    
    if "AnonymousTraveler" in anonymous_traveler_list:
        travelers = anonymous_traveler_list["AnonymousTraveler"]
        if isinstance(travelers, list):
            print(f"Number of travelers: {len(travelers)}")
            for i, traveler in enumerate(travelers[:5]):  # Show first 5
                object_key = traveler.get("ObjectKey", "N/A")
                print(f"  Traveler {i}: ObjectKey = {object_key}")
        else:
            print(f"Single traveler: ObjectKey = {travelers.get('ObjectKey', 'N/A')}")
    
    # Test filtering for different airlines
    test_airlines = ["KL", "LHG", "QR", "EK", "AF"]
    
    for airline in test_airlines:
        print(f"\n--- Testing Filtering for Airline: {airline} ---")
        
        try:
            filtered_data_lists, traveler_key_mapping = _filter_airline_specific_data(data_lists, airline)
            
            filtered_travelers = filtered_data_lists.get("AnonymousTravelerList", {})
            print(f"Filtered AnonymousTravelerList: {filtered_travelers}")
            print(f"Traveler key mapping: {traveler_key_mapping}")
            
            if "AnonymousTraveler" in filtered_travelers:
                travelers = filtered_travelers["AnonymousTraveler"]
                if isinstance(travelers, list):
                    print(f"Filtered travelers count: {len(travelers)}")
                    for traveler in travelers:
                        print(f"  ObjectKey: {traveler.get('ObjectKey', 'N/A')}")
                else:
                    print(f"Single filtered traveler: ObjectKey = {travelers.get('ObjectKey', 'N/A')}")
            else:
                print("No AnonymousTraveler in filtered results")
                
        except Exception as e:
            print(f"Error filtering for airline {airline}: {e}")

def test_specific_offer_index(airshopping_response, offer_index):
    """Test a specific offer index in detail."""
    print(f"\n=== TESTING OFFER INDEX {offer_index} IN DETAIL ===")
    
    try:
        # Build the flight price request
        flight_price_payload = build_flight_price_request(
            airshopping_response, 
            selected_offer_index=offer_index
        )
        
        # Extract details
        data_lists = flight_price_payload.get("DataLists", {})
        anonymous_travelers = data_lists.get("AnonymousTravelerList", {})
        travelers_section = flight_price_payload.get("Travelers", {})
        
        # Check the offer to see which airline this is
        query_offers = flight_price_payload.get("Query", {}).get("Offers", {}).get("Offer", [])
        airline_owner = "Unknown"
        if query_offers and len(query_offers) > 0:
            offer_id = query_offers[0].get("OfferID", {})
            airline_owner = offer_id.get("Owner", "Unknown")
        
        print(f"Airline: {airline_owner}")
        print(f"DataLists.AnonymousTravelerList: {anonymous_travelers}")
        print(f"Travelers section: {travelers_section}")
        
        # Save detailed payload for inspection
        with open(f"debug_payload_{offer_index}_{airline_owner}.json", "w", encoding="utf-8") as f:
            json.dump(flight_price_payload, f, indent=2, ensure_ascii=False)
        print(f"Saved detailed payload to: debug_payload_{offer_index}_{airline_owner}.json")
        
    except Exception as e:
        print(f"Error testing offer index {offer_index}: {e}")

def main():
    """Main debug function."""
    print("Debugging Traveler Filtering")
    print("=" * 50)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        sys.exit(1)
    
    # Debug the filtering process
    debug_traveler_filtering(airshopping_response)
    
    # Test specific offer indices
    test_indices = [0, 5, 1200]
    for idx in test_indices:
        test_specific_offer_index(airshopping_response, idx)

if __name__ == "__main__":
    main()
