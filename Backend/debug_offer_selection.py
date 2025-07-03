#!/usr/bin/env python3
"""
Debug script to compare offer selection logic between runtime extraction and payload building
"""

import json
import sys
from pathlib import Path

# Add the Backend directory to the Python path
sys.path.append('.')

def debug_runtime_extraction_logic(test_data, offer_index):
    """Simulate the runtime extraction logic from pricing.py"""
    print(f"\n=== RUNTIME EXTRACTION LOGIC (offer_index={offer_index}) ===")
    
    # Recreate the flattened offers array (matching transformer logic)
    offers_group = test_data.get('OffersGroup', {})
    airline_offers_list = offers_group.get('AirlineOffers', [])

    print(f"OffersGroup keys: {list(offers_group.keys())}")
    print(f"AirlineOffers type: {type(airline_offers_list)}, length: {len(airline_offers_list) if isinstance(airline_offers_list, list) else 'N/A'}")

    all_offers = []
    for i, airline_offer_group in enumerate(airline_offers_list):
        print(f"AirlineOffer group {i} keys: {list(airline_offer_group.keys()) if isinstance(airline_offer_group, dict) else 'Not a dict'}")
        airline_offers = airline_offer_group.get('AirlineOffer', [])
        print(f"AirlineOffer group {i} has {len(airline_offers) if isinstance(airline_offers, list) else 'N/A'} offers")

        for j, offer in enumerate(airline_offers):
            if offer.get('PricedOffer'):
                all_offers.append(offer)
                if j < 3:  # Log first 3 offers
                    offer_id_info = offer.get('OfferID', {})
                    print(f"Offer {len(all_offers)-1}: OfferID Owner = {offer_id_info.get('Owner', 'N/A')}, Value = {offer_id_info.get('value', 'N/A')[:20]}...")

    # Get the offer at the specified index
    print(f"Total offers found: {len(all_offers)}, requested index: {offer_index}")

    if 0 <= offer_index < len(all_offers):
        selected_offer = all_offers[offer_index]
        offer_id_data = selected_offer.get('OfferID', {})
        airline_code = offer_id_data.get('Owner')

        print(f"RUNTIME RESULT:")
        print(f"  - Selected offer OfferID: {offer_id_data.get('value')}")
        print(f"  - Owner: {airline_code}")
        return selected_offer, airline_code
    else:
        print(f"ERROR: Offer index {offer_index} out of range")
        return None, None

def debug_payload_builder_logic(test_data, offer_index):
    """Simulate the payload builder logic from build_flightprice_rq.py"""
    print(f"\n=== PAYLOAD BUILDER LOGIC (offer_index={offer_index}) ===")
    
    offers_group = test_data.get("OffersGroup", {})
    
    # Recreate the flattened offers array (matching transformer logic)
    airline_offers_list = offers_group.get("AirlineOffers", [])
    all_offers = []
    airline_mapping = {}  # Maps global index to (airline_offers_node, local_index)

    global_index = 0
    for airline_offers_node in airline_offers_list:
        airline_offers = airline_offers_node.get("AirlineOffer", [])
        if not isinstance(airline_offers, list):
            airline_offers = [airline_offers]

        print(f"Processing airline offers node: Owner = {airline_offers_node.get('Owner', {}).get('value', 'N/A')}")
        print(f"  - Number of offers: {len(airline_offers)}")

        for local_index, offer in enumerate(airline_offers):
            if offer.get("PricedOffer"):  # Only include priced offers
                all_offers.append(offer)
                airline_mapping[global_index] = (airline_offers_node, local_index)
                
                if global_index < 5:  # Log first 5 offers
                    offer_id_info = offer.get('OfferID', {})
                    print(f"  - Global index {global_index}: OfferID Owner = {offer_id_info.get('Owner', 'N/A')}, Value = {offer_id_info.get('value', 'N/A')[:20]}...")
                
                global_index += 1

    # Validate the selected index
    print(f"Total offers found: {len(all_offers)}, requested index: {offer_index}")
    
    if offer_index >= len(all_offers):
        print(f"ERROR: Multi-airline offer index {offer_index} out of range")
        return None, None

    # Get the selected offer and its airline context
    selected_offer = all_offers[offer_index]
    selected_airline_offers_node, local_offer_index = airline_mapping[offer_index]

    # Extract airline owner
    airline_owner = selected_airline_offers_node.get("Owner", {}).get("value", "")
    
    print(f"PAYLOAD BUILDER RESULT:")
    print(f"  - Selected offer OfferID: {selected_offer.get('OfferID', {}).get('value')}")
    print(f"  - Owner from offer: {selected_offer.get('OfferID', {}).get('Owner')}")
    print(f"  - Owner from airline node: {airline_owner}")
    print(f"  - Local offer index: {local_offer_index}")
    
    return selected_offer, airline_owner

def main():
    # Load the test data
    test_file = Path('../postman/airshopingresponse.json')
    
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return 1
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    # Test with offer index 0 (the one causing issues)
    offer_index = 0
    
    print("DEBUGGING OFFER SELECTION LOGIC MISMATCH")
    print("=" * 60)
    
    # Run both logics
    runtime_offer, runtime_airline = debug_runtime_extraction_logic(test_data, offer_index)
    payload_offer, payload_airline = debug_payload_builder_logic(test_data, offer_index)
    
    # Compare results
    print(f"\n=== COMPARISON ===")
    if runtime_offer and payload_offer:
        runtime_offer_id = runtime_offer.get('OfferID', {}).get('value')
        payload_offer_id = payload_offer.get('OfferID', {}).get('value')
        
        print(f"Runtime OfferID:     {runtime_offer_id}")
        print(f"Payload OfferID:     {payload_offer_id}")
        print(f"OfferIDs match:      {runtime_offer_id == payload_offer_id}")
        print(f"Runtime airline:     {runtime_airline}")
        print(f"Payload airline:     {payload_airline}")
        print(f"Airlines match:      {runtime_airline == payload_airline}")
        
        if runtime_offer_id != payload_offer_id:
            print("\n❌ MISMATCH DETECTED!")
            print("The runtime extraction and payload builder are selecting different offers!")
        else:
            print("\n✅ LOGIC MATCHES!")
    else:
        print("❌ One or both logics failed to select an offer")
    
    return 0

if __name__ == "__main__":
    exit(main())
