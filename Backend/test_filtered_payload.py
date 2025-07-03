#!/usr/bin/env python3
"""
Test script to validate the filtered FlightPrice payload generation.
This script tests the fix for AnonymousTravelerList contamination issue.
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
        print("Error: Test data file not found at ../postman/airshopingresponse.json")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in test data file: {e}")
        return None

def analyze_original_data(airshopping_response):
    """Analyze the original multi-airline data structure."""
    print("=== ORIGINAL MULTI-AIRLINE DATA ANALYSIS ===")
    
    data_lists = airshopping_response.get("DataLists", {})
    anonymous_travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
    
    if not isinstance(anonymous_travelers, list):
        anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
    
    print(f"Total travelers in original response: {len(anonymous_travelers)}")
    
    airline_travelers = {}
    for traveler in anonymous_travelers:
        if isinstance(traveler, dict):
            object_key = traveler.get("ObjectKey", "")
            if "-" in object_key:
                airline = object_key.split("-")[0]
                if airline not in airline_travelers:
                    airline_travelers[airline] = []
                airline_travelers[airline].append(object_key)
    
    print("Travelers by airline:")
    for airline, travelers in airline_travelers.items():
        print(f"  {airline}: {travelers}")
    
    return airline_travelers

def test_filtered_payload_generation(airshopping_response, test_offer_index=0):
    """Test the filtered payload generation for a specific offer."""
    print(f"\n=== TESTING FILTERED PAYLOAD GENERATION (Offer Index: {test_offer_index}) ===")

    # First, let's check what airline this offer belongs to
    offers_group = airshopping_response.get("OffersGroup", {})
    airline_offers = offers_group.get("AirlineOffers", [])
    if not isinstance(airline_offers, list):
        airline_offers = [airline_offers] if airline_offers else []

    # Find the offer and its airline
    global_index = 0
    found_airline = None
    for airline_offer in airline_offers:
        if isinstance(airline_offer, dict):
            offers = airline_offer.get("Offer", [])
            if not isinstance(offers, list):
                offers = [offers] if offers else []

            for offer in offers:
                if global_index == test_offer_index:
                    found_airline = airline_offer.get("Owner", "Unknown")
                    print(f"Offer {test_offer_index} belongs to airline: {found_airline}")
                    break
                global_index += 1

            if found_airline:
                break

    try:
        # Generate the FlightPrice request payload
        flight_price_payload = build_flight_price_request(
            airshopping_response,
            selected_offer_index=test_offer_index
        )
        
        # Analyze the generated payload
        data_lists = flight_price_payload.get("DataLists", {})
        anonymous_travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
        
        if not isinstance(anonymous_travelers, list):
            anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
        
        print(f"Travelers in generated payload: {len(anonymous_travelers)}")
        
        traveler_keys = []
        for traveler in anonymous_travelers:
            if isinstance(traveler, dict):
                object_key = traveler.get("ObjectKey", "")
                traveler_keys.append(object_key)
        
        print(f"Traveler keys in payload: {traveler_keys}")
        
        # Check if the payload contains only airline-specific data
        has_airline_prefixes = any("-" in key for key in traveler_keys)
        if has_airline_prefixes:
            print("❌ ERROR: Payload still contains airline-prefixed traveler keys!")
            return False
        else:
            print("✅ SUCCESS: Payload contains only standard traveler keys!")
        
        # Save the generated payload for inspection
        output_file = f"debug_filtered_payload_offer_{test_offer_index}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(flight_price_payload, f, indent=2, ensure_ascii=False)
        print(f"Generated payload saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR generating payload: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_airlines(airshopping_response):
    """Test payload generation for offers from different airlines."""
    print(f"\n=== TESTING MULTIPLE AIRLINE OFFERS ===")
    
    # Test a few different offer indices to cover different airlines
    test_indices = [0, 5, 10, 50, 100]  # QR offers appear later in the sequence
    
    success_count = 0
    for offer_index in test_indices:
        print(f"\n--- Testing Offer Index {offer_index} ---")
        if test_filtered_payload_generation(airshopping_response, offer_index):
            success_count += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Successful tests: {success_count}/{len(test_indices)}")
    
    return success_count == len(test_indices)

def main():
    """Main test function."""
    print("Testing Filtered FlightPrice Payload Generation")
    print("=" * 50)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        sys.exit(1)
    
    # Analyze original data
    analyze_original_data(airshopping_response)
    
    # Test filtered payload generation
    all_tests_passed = test_multiple_airlines(airshopping_response)
    
    if all_tests_passed:
        print("\n🎉 ALL TESTS PASSED! The filtering fix is working correctly.")
    else:
        print("\n❌ SOME TESTS FAILED! Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
