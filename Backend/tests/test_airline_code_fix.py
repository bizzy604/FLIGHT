#!/usr/bin/env python3
"""
Test file to implement and verify the airline code extraction fix.
This addresses the "Unknown-" prefix issue in offer IDs.
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path to import utils
sys.path.append(str(Path(__file__).parent.parent))

def test_airline_code_extraction_scenarios():
    """Test various scenarios for airline code extraction."""
    print("=== Testing Airline Code Extraction Scenarios ===")
    
    # Test scenario 1: Normal structure with Owner.value
    scenario1 = {
        'Owner': {'value': 'KQ'}
    }
    
    # Test scenario 2: Owner is a string instead of dict
    scenario2 = {
        'Owner': 'AA'
    }
    
    # Test scenario 3: Owner is missing
    scenario3 = {}
    
    # Test scenario 4: Owner exists but value is missing
    scenario4 = {
        'Owner': {}
    }
    
    # Test scenario 5: Owner.value is empty string
    scenario5 = {
        'Owner': {'value': ''}
    }
    
    # Test scenario 6: Owner.value is None
    scenario6 = {
        'Owner': {'value': None}
    }
    
    scenarios = [
        ("Normal structure", scenario1),
        ("Owner as string", scenario2),
        ("Owner missing", scenario3),
        ("Owner empty dict", scenario4),
        ("Owner.value empty string", scenario5),
        ("Owner.value is None", scenario6)
    ]
    
    def extract_airline_code_robust(airline_offer_group):
        """Robust airline code extraction with multiple fallbacks."""
        owner_data = airline_offer_group.get('Owner')
        
        # Case 1: Owner is a dict with value
        if isinstance(owner_data, dict):
            value = owner_data.get('value')
            if value and isinstance(value, str) and value.strip():
                return value.strip()
        
        # Case 2: Owner is a string directly
        elif isinstance(owner_data, str) and owner_data.strip():
            return owner_data.strip()
        
        # Case 3: Try to extract from AirlineOffer if available
        airline_offers_list = airline_offer_group.get('AirlineOffer', [])
        if isinstance(airline_offers_list, list) and airline_offers_list:
            first_offer = airline_offers_list[0]
            if isinstance(first_offer, dict):
                # Check if there's an airline code in the offer structure
                priced_offer = first_offer.get('PricedOffer', {})
                if isinstance(priced_offer, dict):
                    # Look for airline code in associations or other fields
                    associations = priced_offer.get('Associations', {})
                    if isinstance(associations, dict):
                        # This might contain flight references that have airline codes
                        pass
        
        # Default fallback
        return 'Unknown'
    
    print("\nTesting extraction scenarios:")
    for name, scenario in scenarios:
        result = extract_airline_code_robust(scenario)
        print(f"{name}: {result}")
        
        # Also test the current implementation (with error handling)
        try:
            current_result = scenario.get('Owner', {}).get('value', 'Unknown')
        except AttributeError:
            # Handle case where Owner is not a dict
            current_result = 'Error: Owner not a dict'
        
        print(f"  Current implementation: {current_result}")
        print(f"  Robust implementation: {result}")
        print()

def create_improved_data_transformer_patch():
    """Create a patch for the data_transformer.py to handle airline code extraction robustly."""
    print("=== Creating Improved Data Transformer Patch ===")
    
    patch_content = '''
# Improved airline code extraction function
def extract_airline_code_robust(airline_offer_group):
    """Robust airline code extraction with multiple fallbacks and detailed logging."""
    logger.info(f"Extracting airline code from offer group with keys: {list(airline_offer_group.keys()) if isinstance(airline_offer_group, dict) else 'Not a dict'}")
    
    owner_data = airline_offer_group.get('Owner')
    logger.info(f"Owner data: {owner_data}, type: {type(owner_data)}")
    
    # Case 1: Owner is a dict with value
    if isinstance(owner_data, dict):
        value = owner_data.get('value')
        logger.info(f"Owner.value: {value}, type: {type(value)}")
        if value and isinstance(value, str) and value.strip():
            airline_code = value.strip()
            logger.info(f"Successfully extracted airline code from Owner.value: {airline_code}")
            return airline_code
        else:
            logger.warning(f"Owner.value is empty, None, or not a string: {value}")
    
    # Case 2: Owner is a string directly
    elif isinstance(owner_data, str) and owner_data.strip():
        airline_code = owner_data.strip()
        logger.info(f"Successfully extracted airline code from Owner string: {airline_code}")
        return airline_code
    
    # Case 3: Owner is missing or invalid
    else:
        logger.warning(f"Owner field is missing or invalid: {owner_data}")
    
    # Case 4: Try to extract from AirlineOffer structure as fallback
    airline_offers_list = airline_offer_group.get('AirlineOffer', [])
    logger.info(f"Attempting fallback extraction from AirlineOffer list with {len(airline_offers_list) if isinstance(airline_offers_list, list) else 'invalid'} items")
    
    if isinstance(airline_offers_list, list) and airline_offers_list:
        first_offer = airline_offers_list[0]
        if isinstance(first_offer, dict):
            # Check OfferID for airline code pattern
            offer_id = first_offer.get('OfferID')
            if isinstance(offer_id, str) and len(offer_id) >= 2:
                # Many airline codes are 2-3 characters at the start of offer IDs
                potential_code = offer_id[:2].upper()
                if potential_code.isalpha():
                    logger.info(f"Extracted potential airline code from OfferID: {potential_code}")
                    return potential_code
            
            # Check PricedOffer structure
            priced_offer = first_offer.get('PricedOffer', {})
            if isinstance(priced_offer, dict):
                # Look for any field that might contain airline code
                for key, value in priced_offer.items():
                    if isinstance(value, str) and len(value) == 2 and value.isalpha():
                        logger.info(f"Found potential airline code in PricedOffer.{key}: {value}")
                        return value.upper()
    
    # Final fallback
    logger.error("Could not extract airline code from any source, using 'Unknown'")
    return 'Unknown'
'''
    
    return patch_content

if __name__ == "__main__":
    test_airline_code_extraction_scenarios()
    
    print("\n" + "="*50)
    patch = create_improved_data_transformer_patch()
    print("Improved extraction function created.")
    print("\nNext steps:")
    print("1. Apply this robust extraction function to data_transformer.py")
    print("2. Replace the simple Owner.value extraction with the robust version")
    print("3. Test with live API data to verify the fix")
    print("4. Monitor logs to see which extraction method works for live data")