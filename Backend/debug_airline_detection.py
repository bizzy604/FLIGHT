#!/usr/bin/env python3
"""
Debug script to check airline detection and traveler filtering.
"""

import json
import sys
import os

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.build_flightprice_rq import _filter_airline_specific_data

def load_test_data():
    """Load the multi-airline air shopping response test data."""
    try:
        with open("../postman/airshopingresponse.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: Test data file not found")
        return None

def test_airline_detection(airshopping_response):
    """Test airline detection logic."""
    print("=== AIRLINE DETECTION TEST ===")
    
    offers_group = airshopping_response.get("OffersGroup", {})
    airline_offers = offers_group.get("AirlineOffers", [])
    
    if not isinstance(airline_offers, list):
        airline_offers = [airline_offers] if airline_offers else []
    
    print(f"Found {len(airline_offers)} airline offer groups")
    
    global_index = 0
    for i, airline_offer in enumerate(airline_offers):
        if isinstance(airline_offer, dict):
            owner = airline_offer.get("Owner", "Unknown")
            offers = airline_offer.get("Offer", [])
            if not isinstance(offers, list):
                offers = [offers] if offers else []
            
            print(f"Airline {i}: {owner} - {len(offers)} offers (global indices {global_index}-{global_index + len(offers) - 1})")
            
            # Test a few offers from this airline
            for j, offer in enumerate(offers[:3]):  # Test first 3 offers
                print(f"  Offer {global_index + j}: {offer.get('OfferID', {}).get('value', 'No ID')}")
            
            global_index += len(offers)

def test_traveler_filtering(airshopping_response):
    """Test traveler filtering for different airlines."""
    print("\n=== TRAVELER FILTERING TEST ===")
    
    data_lists = airshopping_response.get("DataLists", {})
    
    # Test filtering for each airline
    airlines = ["KL", "QR", "AF", "EK", "KQ", "LHG", "ET"]
    
    for airline in airlines:
        print(f"\n--- Testing filtering for airline: {airline} ---")
        
        filtered_data, traveler_mapping = _filter_airline_specific_data(data_lists, airline)
        
        filtered_travelers = filtered_data.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
        if not isinstance(filtered_travelers, list):
            filtered_travelers = [filtered_travelers] if filtered_travelers else []
        
        print(f"Filtered travelers: {len(filtered_travelers)}")
        for traveler in filtered_travelers:
            if isinstance(traveler, dict):
                print(f"  - {traveler.get('ObjectKey', 'No Key')}: {traveler.get('PTC', {})}")
        
        print(f"Traveler key mapping: {traveler_mapping}")

def main():
    """Main debug function."""
    print("Debugging Airline Detection and Traveler Filtering")
    print("=" * 50)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        sys.exit(1)
    
    # Test airline detection
    test_airline_detection(airshopping_response)
    
    # Test traveler filtering
    test_traveler_filtering(airshopping_response)

if __name__ == "__main__":
    main()
