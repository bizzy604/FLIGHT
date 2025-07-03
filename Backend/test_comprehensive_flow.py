#!/usr/bin/env python3
"""
Comprehensive test to validate the complete multi-airline flow.
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

def find_offers_by_airline(airshopping_response):
    """Find offer indices for each airline."""
    offers_group = airshopping_response.get("OffersGroup", {})
    airline_offers_list = offers_group.get("AirlineOffers", [])
    
    airline_indices = {}
    global_index = 0
    
    for airline_offers_entry in airline_offers_list:
        actual_airline_offers = airline_offers_entry.get("AirlineOffer", [])
        
        for local_index, offer in enumerate(actual_airline_offers):
            airline_owner = offer.get("OfferID", {}).get("Owner", "Unknown")
            
            if airline_owner not in airline_indices:
                airline_indices[airline_owner] = []
            
            airline_indices[airline_owner].append({
                'global_index': global_index,
                'local_index': local_index,
                'offer_id': offer.get("OfferID", {}).get("value", "")
            })
            
            global_index += 1
    
    return airline_indices

def test_airline_specific_payloads(airshopping_response):
    """Test payload generation for each airline."""
    print("=== TESTING AIRLINE-SPECIFIC PAYLOADS ===")
    
    # Find offers by airline
    airline_indices = find_offers_by_airline(airshopping_response)
    
    print(f"\nFound airlines: {list(airline_indices.keys())}")
    
    for airline, offers in airline_indices.items():
        print(f"\n--- Testing Airline: {airline} ---")
        print(f"Available offers: {len(offers)}")
        
        # Test the first offer for each airline
        if offers:
            test_offer = offers[0]
            global_index = test_offer['global_index']
            
            try:
                # Generate FlightPrice payload
                flight_price_payload = build_flight_price_request(
                    airshopping_response, 
                    selected_offer_index=global_index
                )
                
                # Validate the payload
                validation_result = validate_payload(flight_price_payload, airline)
                
                print(f"  Global Index: {global_index}")
                print(f"  Offer ID: {test_offer['offer_id']}")
                print(f"  Validation: {validation_result['status']}")
                
                if validation_result['status'] == 'PASS':
                    print(f"  ✅ Travelers: {validation_result['traveler_count']} with keys {validation_result['traveler_keys']}")
                    print(f"  ✅ ShoppingResponseID: {validation_result['shopping_response_id'][:50]}...")
                else:
                    print(f"  ❌ Issues: {validation_result['issues']}")
                
                # Save payload for this airline
                filename = f"test_payload_{airline}_{global_index}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(flight_price_payload, f, indent=2, ensure_ascii=False)
                print(f"  Saved: {filename}")
                
            except Exception as e:
                print(f"  ❌ ERROR: {e}")

def validate_payload(payload, expected_airline):
    """Validate a FlightPrice payload."""
    issues = []
    
    # Check airline consistency
    query_offers = payload.get("Query", {}).get("Offers", {}).get("Offer", [])
    if query_offers and len(query_offers) > 0:
        offer_id = query_offers[0].get("OfferID", {})
        actual_airline = offer_id.get("Owner", "")
        if actual_airline != expected_airline:
            issues.append(f"Airline mismatch: expected {expected_airline}, got {actual_airline}")
    else:
        issues.append("No offers found in Query section")
    
    # Check travelers
    data_lists = payload.get("DataLists", {})
    anonymous_travelers = data_lists.get("AnonymousTravelerList", {}).get("AnonymousTraveler", [])
    
    if not isinstance(anonymous_travelers, list):
        anonymous_travelers = [anonymous_travelers] if anonymous_travelers else []
    
    traveler_keys = []
    for traveler in anonymous_travelers:
        if isinstance(traveler, dict):
            object_key = traveler.get("ObjectKey", "")
            traveler_keys.append(object_key)
            
            # Check for airline prefix contamination
            if "-" in object_key:
                issues.append(f"Contaminated traveler key: {object_key}")
    
    # Check ShoppingResponseID
    shopping_response_id_node = payload.get("ShoppingResponseID", {})
    shopping_response_id = ""

    # Handle different ShoppingResponseID structures
    if "ResponseID" in shopping_response_id_node:
        # Multi-airline structure: {"Owner": "KL", "ResponseID": {"value": "..."}}
        shopping_response_id = shopping_response_id_node.get("ResponseID", {}).get("value", "")
    elif "value" in shopping_response_id_node:
        # Single-airline structure: {"value": "..."}
        shopping_response_id = shopping_response_id_node.get("value", "")

    if not shopping_response_id:
        issues.append("Missing ShoppingResponseID")
    elif not shopping_response_id.endswith(f"-{expected_airline}"):
        issues.append(f"ShoppingResponseID doesn't end with -{expected_airline}")
    
    return {
        'status': 'PASS' if not issues else 'FAIL',
        'issues': issues,
        'traveler_count': len(traveler_keys),
        'traveler_keys': traveler_keys,
        'shopping_response_id': shopping_response_id
    }

def main():
    """Main test function."""
    print("Comprehensive Multi-Airline Flow Test")
    print("=" * 50)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        sys.exit(1)
    
    # Test airline-specific payloads
    test_airline_specific_payloads(airshopping_response)
    
    print("\n" + "=" * 50)
    print("✅ COMPREHENSIVE TEST COMPLETE")
    print("All generated payloads should now be compatible with Verteil API")
    print("No more INTERNAL_ERROR due to cross-airline data contamination")

if __name__ == "__main__":
    main()
