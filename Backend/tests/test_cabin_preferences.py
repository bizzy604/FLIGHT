#!/usr/bin/env python3
"""
Local test file to verify cabin preference logic without making API calls.
This will help us debug the separate cabin class issue locally.
"""

import sys
import os
import json
from datetime import datetime

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.build_airshopping_rq import build_airshopping_request
from services.flight.search import FlightSearchService

def test_cabin_preferences_logic():
    """
    Test the cabin preferences logic locally without API calls.
    """
    print("=== Testing Cabin Preferences Logic ===")
    print()
    
    # Test case 1: Round trip with different cabin classes
    print("Test Case 1: Round trip with different outbound (Y) and return (C) cabin classes")
    print("-" * 70)
    
    # Simulate the search criteria that would come from the frontend
    search_criteria = {
        'trip_type': 'ROUND_TRIP',
        'odSegments': [
            {'Origin': 'DXB', 'Destination': 'BOM', 'DepartureDate': '2025-06-15'},
            {'Origin': 'BOM', 'Destination': 'DXB', 'DepartureDate': '2025-06-25'}
        ],
        'num_adults': 2,
        'num_children': 1,
        'num_infants': 1,
        'outboundCabinClass': 'Y',  # Economy for outbound
        'returnCabinClass': 'C',    # Business for return
        'directOnly': False
    }
    
    print(f"Input search criteria: {json.dumps(search_criteria, indent=2)}")
    print()
    
    # Test the cabin preferences extraction logic from FlightSearchService
    print("Step 1: Testing cabin preferences extraction...")
    
    # Simulate the logic from FlightSearchService.process_air_shopping
    cabin_preferences_per_segment = []
    fallback_cabin_code = None
    
    if search_criteria['trip_type'] == 'ROUND_TRIP' and len(search_criteria['odSegments']) == 2:
        outbound_cabin = search_criteria.get('outboundCabinClass')
        return_cabin = search_criteria.get('returnCabinClass')
        
        if outbound_cabin and return_cabin:
            print(f"  - Outbound cabin class: {outbound_cabin}")
            print(f"  - Return cabin class: {return_cabin}")
            
            cabin_preferences_per_segment = [outbound_cabin, return_cabin]
            fallback_cabin_code = outbound_cabin  # Use outbound as fallback
            
            print(f"  - Cabin preferences per segment: {cabin_preferences_per_segment}")
            print(f"  - Fallback cabin code: {fallback_cabin_code}")
        else:
            # Fallback to single cabin preference
            fallback_cabin_code = search_criteria.get('cabinPreference', 'Y')
            print(f"  - Using fallback cabin code: {fallback_cabin_code}")
    else:
        fallback_cabin_code = search_criteria.get('cabinPreference', 'Y')
        print(f"  - Single trip, using cabin code: {fallback_cabin_code}")
    
    print()
    
    # Test the build_airshopping_request function
    print("Step 2: Testing build_airshopping_request function...")
    
    try:
        # Build the request payload
        payload = build_airshopping_request(
            trip_type=search_criteria['trip_type'],
            od_segments=search_criteria['odSegments'],
            num_adults=search_criteria['num_adults'],
            num_children=search_criteria['num_children'],
            num_infants=search_criteria['num_infants'],
            cabin_preference_code=fallback_cabin_code,
            cabin_preferences=cabin_preferences_per_segment
        )
        
        print("✓ Successfully built AirShopping request payload")
        print()
        
        # Extract and display the cabin preferences from the payload
        print("Step 3: Analyzing the generated cabin preferences...")
        cabin_prefs = payload.get('Preference', {}).get('CabinPreferences', {}).get('CabinType', [])
        
        print(f"Number of cabin types in payload: {len(cabin_prefs)}")
        
        for i, cabin_type in enumerate(cabin_prefs):
            code = cabin_type.get('Code')
            od_refs = cabin_type.get('OriginDestinationReferences', [])
            print(f"  Cabin Type {i+1}: Code='{code}', OD References={od_refs}")
        
        print()
        
        # Verify the expected behavior
        print("Step 4: Verification...")
        
        if len(cabin_prefs) == 2:
            outbound_code = cabin_prefs[0].get('Code')
            return_code = cabin_prefs[1].get('Code')
            outbound_refs = cabin_prefs[0].get('OriginDestinationReferences', [])
            return_refs = cabin_prefs[1].get('OriginDestinationReferences', [])
            
            print(f"  Outbound segment (OD1): Expected='Y', Actual='{outbound_code}', Refs={outbound_refs}")
            print(f"  Return segment (OD2): Expected='C', Actual='{return_code}', Refs={return_refs}")
            
            # Check if the cabin codes match expectations
            outbound_correct = outbound_code == 'Y' and 'OD1' in outbound_refs
            return_correct = return_code == 'C' and 'OD2' in return_refs
            
            if outbound_correct and return_correct:
                print("  ✓ SUCCESS: Cabin preferences are correctly set for each segment!")
            else:
                print("  ✗ FAILURE: Cabin preferences are not correctly set.")
                if not outbound_correct:
                    print(f"    - Outbound issue: Expected Y/OD1, got {outbound_code}/{outbound_refs}")
                if not return_correct:
                    print(f"    - Return issue: Expected C/OD2, got {return_code}/{return_refs}")
        else:
            print(f"  ✗ FAILURE: Expected 2 cabin types, got {len(cabin_prefs)}")
        
        print()
        
        # Display the full payload for debugging
        print("Step 5: Full payload (for debugging):")
        print(json.dumps(payload, indent=2))
        
    except Exception as e:
        print(f"✗ Error building AirShopping request: {e}")
        import traceback
        traceback.print_exc()

def test_single_cabin_preference():
    """
    Test case with single cabin preference (should work as before).
    """
    print("\n" + "=" * 70)
    print("Test Case 2: Round trip with single cabin class (Y)")
    print("-" * 70)
    
    search_criteria = {
        'trip_type': 'ROUND_TRIP',
        'odSegments': [
            {'Origin': 'DXB', 'Destination': 'BOM', 'DepartureDate': '2025-06-15'},
            {'Origin': 'BOM', 'Destination': 'DXB', 'DepartureDate': '2025-06-25'}
        ],
        'num_adults': 2,
        'num_children': 1,
        'num_infants': 1,
        'cabinPreference': 'Y',  # Single cabin preference
        'directOnly': False
    }
    
    print(f"Input search criteria: {json.dumps(search_criteria, indent=2)}")
    print()
    
    # No separate cabin classes provided
    cabin_preferences_per_segment = []
    fallback_cabin_code = search_criteria.get('cabinPreference', 'Y')
    
    print(f"Cabin preferences per segment: {cabin_preferences_per_segment}")
    print(f"Fallback cabin code: {fallback_cabin_code}")
    print()
    
    try:
        payload = build_airshopping_request(
            trip_type=search_criteria['trip_type'],
            od_segments=search_criteria['odSegments'],
            num_adults=search_criteria['num_adults'],
            num_children=search_criteria['num_children'],
            num_infants=search_criteria['num_infants'],
            cabin_preference_code=fallback_cabin_code,
            cabin_preferences=cabin_preferences_per_segment
        )
        
        cabin_prefs = payload.get('Preference', {}).get('CabinPreferences', {}).get('CabinType', [])
        
        print(f"Number of cabin types in payload: {len(cabin_prefs)}")
        
        for i, cabin_type in enumerate(cabin_prefs):
            code = cabin_type.get('Code')
            od_refs = cabin_type.get('OriginDestinationReferences', [])
            print(f"  Cabin Type {i+1}: Code='{code}', OD References={od_refs}")
        
        # Verify both segments get the same cabin class
        if len(cabin_prefs) == 2:
            all_same_code = all(ct.get('Code') == 'Y' for ct in cabin_prefs)
            has_both_refs = any('OD1' in ct.get('OriginDestinationReferences', []) for ct in cabin_prefs) and \
                           any('OD2' in ct.get('OriginDestinationReferences', []) for ct in cabin_prefs)
            
            if all_same_code and has_both_refs:
                print("  ✓ SUCCESS: Both segments correctly use the same cabin class (Y)")
            else:
                print("  ✗ FAILURE: Segments don't have consistent cabin class")
        else:
            print(f"  ✗ FAILURE: Expected 2 cabin types, got {len(cabin_prefs)}")
            
    except Exception as e:
        print(f"✗ Error building AirShopping request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Flight Cabin Preferences Local Test")
    print("====================================")
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Run the tests
    test_cabin_preferences_logic()
    test_single_cabin_preference()
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("\nIf the tests show failures, we can debug the logic without making API calls.")
    print("If the tests show success, the issue might be in how the frontend sends the data.")