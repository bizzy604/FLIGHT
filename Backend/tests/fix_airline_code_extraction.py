#!/usr/bin/env python3
"""
Fix for airline code extraction issue causing 'Unknown-' prefix in offer IDs.

This script identifies and fixes the issue where airline codes are not being properly
extracted from the API response, leading to offer IDs starting with 'Unknown-' and
causing flight selection failures.
"""

import json
import sys
import os
from typing import Dict, Any

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_airline_code_extraction_issue():
    """
    Analyze the airline code extraction issue in the current data transformer.
    """
    print("=== Airline Code Extraction Issue Analysis ===")
    print()
    
    # Load a sample API response to analyze
    try:
        with open('c:/Users/User/Desktop/FLIGHT/Backend/tests/airshoping_response.json', 'r') as f:
            api_response = json.load(f)
    except FileNotFoundError:
        print("Error: Could not find airshoping_response.json file")
        return
    
    print("1. Analyzing API response structure...")
    
    # Navigate to airline offers
    offers_group = api_response.get('OffersGroup', {})
    airline_offers = offers_group.get('AirlineOffers', [])
    
    print(f"   - Found {len(airline_offers)} airline offer groups")
    
    # Analyze the first few airline offer groups
    for i, airline_offer_group in enumerate(airline_offers[:3]):
        print(f"\n2. Analyzing airline offer group {i + 1}:")
        print(f"   - Keys: {list(airline_offer_group.keys())}")
        
        # Check for Owner at group level
        owner_data = airline_offer_group.get('Owner')
        print(f"   - Owner at group level: {owner_data}")
        
        # Check individual offers
        airline_offers_list = airline_offer_group.get('AirlineOffer', [])
        if airline_offers_list:
            first_offer = airline_offers_list[0]
            print(f"   - First offer keys: {list(first_offer.keys())}")
            
            # Check OfferID structure
            offer_id_data = first_offer.get('OfferID')
            print(f"   - OfferID: {offer_id_data}")
            print(f"   - OfferID type: {type(offer_id_data)}")
            
            if isinstance(offer_id_data, dict):
                owner = offer_id_data.get('Owner')
                print(f"   - OfferID.Owner: {owner}")
            elif isinstance(offer_id_data, str):
                print(f"   - OfferID is string, potential code: {offer_id_data[:3]}")
    
    print("\n3. Issue Analysis:")
    print("   The 'Unknown-' prefix in offer IDs indicates that the airline code")
    print("   extraction is failing. This happens when:")
    print("   - OfferID.Owner is missing or empty")
    print("   - The extraction logic doesn't handle the API response structure properly")
    print("   - Fallback methods also fail to extract a valid airline code")
    
    print("\n4. Impact:")
    print("   - Offer IDs start with 'Unknown-' instead of proper airline codes")
    print("   - Flight selection fails because the frontend can't match offer IDs")
    print("   - Users cannot proceed with booking")

def create_improved_extraction_function():
    """
    Create an improved airline code extraction function.
    """
    print("\n=== Creating Improved Extraction Function ===")
    
    improved_function = '''
def _extract_airline_code_robust(airline_offer_group: Dict[str, Any]) -> str:
    """Improved airline code extraction with better fallback logic."""
    logger.info(f"Extracting airline code from offer group with keys: {list(airline_offer_group.keys()) if isinstance(airline_offer_group, dict) else 'Not a dict'}")
    
    # Method 1: Extract from OfferID.Owner in individual offers
    airline_offers_list = airline_offer_group.get('AirlineOffer', [])
    logger.info(f"Found {len(airline_offers_list) if isinstance(airline_offers_list, list) else 'invalid'} airline offers")
    
    if isinstance(airline_offers_list, list) and airline_offers_list:
        first_offer = airline_offers_list[0]
        if isinstance(first_offer, dict):
            offer_id_data = first_offer.get('OfferID')
            logger.info(f"OfferID data: {offer_id_data}, type: {type(offer_id_data)}")
            
            if isinstance(offer_id_data, dict):
                owner = offer_id_data.get('Owner')
                logger.info(f"OfferID.Owner: {owner}, type: {type(owner)}")
                
                if owner and isinstance(owner, str) and owner.strip():
                    airline_code = owner.strip()
                    logger.info(f"Successfully extracted airline code from OfferID.Owner: {airline_code}")
                    return airline_code
            
            # Method 2: Extract from OfferID string pattern
            elif isinstance(offer_id_data, str) and len(offer_id_data) >= 2:
                # Try to extract airline code from the beginning of the string
                potential_code = offer_id_data[:2].upper()
                if potential_code.isalpha():
                    logger.info(f"Extracted airline code from OfferID string: {potential_code}")
                    return potential_code
                
                # Try 3-character code
                if len(offer_id_data) >= 3:
                    potential_code = offer_id_data[:3].upper()
                    if potential_code.isalpha():
                        logger.info(f"Extracted 3-char airline code from OfferID string: {potential_code}")
                        return potential_code
    
    # Method 3: Check Owner at airline_offer_group level
    owner_data = airline_offer_group.get('Owner')
    logger.info(f"Checking group-level Owner data: {owner_data}, type: {type(owner_data)}")
    
    if isinstance(owner_data, dict):
        value = owner_data.get('value')
        if value and isinstance(value, str) and value.strip():
            airline_code = value.strip()
            logger.info(f"Successfully extracted airline code from group Owner.value: {airline_code}")
            return airline_code
    elif isinstance(owner_data, str) and owner_data.strip():
        airline_code = owner_data.strip()
        logger.info(f"Successfully extracted airline code from group Owner string: {airline_code}")
        return airline_code
    
    # Method 4: Extract from PricedOffer structure
    if isinstance(airline_offers_list, list) and airline_offers_list:
        first_offer = airline_offers_list[0]
        priced_offer = first_offer.get('PricedOffer', {})
        
        # Check if there's airline info in the priced offer
        if isinstance(priced_offer, dict):
            # Look for airline references in associations
            associations = priced_offer.get('Associations', {})
            if isinstance(associations, dict):
                applicable_flight = associations.get('ApplicableFlight', {})
                if isinstance(applicable_flight, dict):
                    # Try to extract from flight references
                    flight_refs = applicable_flight.get('FlightSegmentReference', [])
                    if flight_refs and isinstance(flight_refs, list) and flight_refs:
                        # This would require reference data lookup, but we can try pattern matching
                        first_ref = flight_refs[0]
                        if isinstance(first_ref, dict):
                            ref_value = first_ref.get('ref', '')
                            if isinstance(ref_value, str) and len(ref_value) >= 2:
                                # Extract potential airline code from reference
                                potential_code = ref_value[:2].upper()
                                if potential_code.isalpha():
                                    logger.info(f"Extracted airline code from flight reference: {potential_code}")
                                    return potential_code
    
    # Method 5: Try to extract from any string field that might contain airline code
    def extract_from_nested_dict(data, path=""):
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, str) and len(value) == 2 and value.isalpha() and value.isupper():
                    logger.info(f"Found potential 2-char airline code '{value}' at {current_path}")
                    return value
                elif isinstance(value, str) and len(value) == 3 and value.isalpha() and value.isupper():
                    logger.info(f"Found potential 3-char airline code '{value}' at {current_path}")
                    return value
                elif isinstance(value, (dict, list)):
                    result = extract_from_nested_dict(value, current_path)
                    if result:
                        return result
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                result = extract_from_nested_dict(item, current_path)
                if result:
                    return result
        return None
    
    # Try the nested extraction as a last resort
    nested_result = extract_from_nested_dict(airline_offer_group)
    if nested_result:
        logger.info(f"Extracted airline code from nested search: {nested_result}")
        return nested_result
    
    # Final fallback - this should be avoided
    logger.error("Could not extract airline code from any source, using 'Unknown'")
    return 'Unknown'
'''
    
    print("Improved extraction function created with the following enhancements:")
    print("1. Better handling of OfferID string patterns")
    print("2. Additional fallback to PricedOffer structure")
    print("3. Nested dictionary search for airline codes")
    print("4. More robust pattern matching")
    print("5. Enhanced logging for debugging")
    
    return improved_function

def provide_fix_recommendations():
    """
    Provide recommendations for fixing the issue.
    """
    print("\n=== Fix Recommendations ===")
    print()
    print("1. IMMEDIATE FIX:")
    print("   - Update the _extract_airline_code_robust function in data_transformer.py")
    print("   - Add better fallback logic for airline code extraction")
    print("   - Improve pattern matching for OfferID strings")
    print()
    print("2. TESTING:")
    print("   - Test with the current API response data")
    print("   - Verify that offer IDs no longer start with 'Unknown-'")
    print("   - Ensure flight selection works properly")
    print()
    print("3. MONITORING:")
    print("   - Add more detailed logging to track extraction success")
    print("   - Monitor for any remaining 'Unknown' airline codes")
    print("   - Set up alerts for extraction failures")
    print()
    print("4. LONG-TERM:")
    print("   - Work with API provider to ensure consistent OfferID.Owner format")
    print("   - Consider caching airline code mappings")
    print("   - Implement validation for extracted airline codes")

if __name__ == "__main__":
    print("Flight Selection Issue Analysis and Fix")
    print("=" * 50)
    
    analyze_airline_code_extraction_issue()
    improved_function = create_improved_extraction_function()
    provide_fix_recommendations()
    
    print("\n=== Next Steps ===")
    print("1. Apply the improved extraction function to data_transformer.py")
    print("2. Test the fix with current API data")
    print("3. Verify that flight selection works properly")
    print("4. Monitor for any remaining issues")