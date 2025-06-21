#!/usr/bin/env python3
"""
Script to examine the actual API response structure for airline code extraction.
"""

import json
from pathlib import Path

def examine_api_structure():
    """Examine the actual API response structure."""
    current_dir = Path(__file__).parent
    api_response_file = current_dir / 'airshoping_response.json'
    
    try:
        with open(api_response_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=== API Response Structure Analysis ===")
        print(f"Top-level keys: {list(data.keys())}")
        
        # Examine OffersGroup
        offers_group = data.get('OffersGroup', {})
        print(f"\nOffersGroup keys: {list(offers_group.keys())}")
        
        # Examine AirlineOffers
        airline_offers = offers_group.get('AirlineOffers', [])
        print(f"Number of airline offers: {len(airline_offers)}")
        
        if airline_offers:
            first_offer = airline_offers[0]
            print(f"\nFirst airline offer keys: {list(first_offer.keys())}")
            print(f"Owner in first offer: {first_offer.get('Owner')}")
            print(f"Owner type: {type(first_offer.get('Owner'))}")
            
            # Check if Owner has value
            owner = first_offer.get('Owner')
            if isinstance(owner, dict):
                print(f"Owner.value: {owner.get('value')}")
            
            # Examine AirlineOffer structure
            airline_offer_list = first_offer.get('AirlineOffer', [])
            print(f"\nNumber of offers in first group: {len(airline_offer_list)}")
            
            if airline_offer_list:
                first_individual_offer = airline_offer_list[0]
                print(f"First individual offer keys: {list(first_individual_offer.keys())}")
                print(f"OfferID: {first_individual_offer.get('OfferID')}")
        
        # Examine DataLists for MarketingCarrier
        data_lists = data.get('DataLists', {})
        print(f"\nDataLists keys: {list(data_lists.keys())}")
        
        flight_segment_list = data_lists.get('FlightSegmentList', {})
        flight_segments = flight_segment_list.get('FlightSegment', [])
        print(f"Number of flight segments: {len(flight_segments)}")
        
        if flight_segments:
            first_segment = flight_segments[0]
            print(f"\nFirst segment keys: {list(first_segment.keys())}")
            
            marketing_carrier = first_segment.get('MarketingCarrier', {})
            print(f"MarketingCarrier: {marketing_carrier}")
            
            if marketing_carrier:
                print(f"MarketingCarrier keys: {list(marketing_carrier.keys())}")
                airline_id = marketing_carrier.get('AirlineID', {})
                print(f"AirlineID: {airline_id}")
                if isinstance(airline_id, dict):
                    print(f"AirlineID.value: {airline_id.get('value')}")
                print(f"Name: {marketing_carrier.get('Name')}")
        
    except Exception as e:
        print(f"Error examining API structure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_api_structure()