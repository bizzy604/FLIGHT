#!/usr/bin/env python3
"""
Integration test for round trip transformation in the main data_transformer module.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import transform_verteil_to_frontend
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE

def test_original_transformation():
    """Test the original transformation (default behavior)."""
    print("Testing Original Transformation (enable_roundtrip=False)")
    print("=" * 60)
    
    result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE, enable_roundtrip=False)
    
    print(f"Number of offers: {len(result)}")
    
    if result:
        first_offer = result[0]
        print(f"First offer:")
        print(f"  Route: {first_offer['departure']['airport']} -> {first_offer['arrival']['airport']}")
        print(f"  Segments: {len(first_offer.get('segments', []))}")
        print(f"  Trip Type: {first_offer.get('tripType', 'Not specified')}")
        print(f"  Direction: {first_offer.get('direction', 'Not specified')}")
        
        # Show segment details
        segments = first_offer.get('segments', [])
        for i, segment in enumerate(segments):
            print(f"  Segment {i+1}: {segment['departure']['airport']} -> {segment['arrival']['airport']}")

def test_roundtrip_transformation():
    """Test the enhanced round trip transformation."""
    print("\n\nTesting Round Trip Transformation (enable_roundtrip=True)")
    print("=" * 60)
    
    result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE, enable_roundtrip=True)
    
    print(f"Number of offers: {len(result)}")
    
    if result:
        # Show first few offers
        print(f"\nFirst 6 offers:")
        for i, offer in enumerate(result[:6]):
            print(f"  {i+1}: {offer['departure']['airport']} -> {offer['arrival']['airport']} ({offer.get('direction', 'unknown')}) - {offer.get('tripType', 'unknown')}")
        
        # Count outbound vs return
        outbound_count = sum(1 for offer in result if offer.get('direction') == 'outbound')
        return_count = sum(1 for offer in result if offer.get('direction') == 'return')
        
        print(f"\nBreakdown:")
        print(f"  Outbound offers: {outbound_count}")
        print(f"  Return offers: {return_count}")
        print(f"  Total: {len(result)}")

def test_backward_compatibility():
    """Test that the default behavior remains unchanged."""
    print("\n\nTesting Backward Compatibility")
    print("=" * 60)
    
    # Test default parameter (should be same as enable_roundtrip=False)
    default_result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)
    explicit_false = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE, enable_roundtrip=False)
    
    print(f"Default call result: {len(default_result)} offers")
    print(f"Explicit False result: {len(explicit_false)} offers")
    print(f"Results match: {len(default_result) == len(explicit_false)}")
    
    if default_result and explicit_false:
        first_default = default_result[0]
        first_explicit = explicit_false[0]
        
        routes_match = (first_default['departure']['airport'] == first_explicit['departure']['airport'] and
                       first_default['arrival']['airport'] == first_explicit['arrival']['airport'])
        
        print(f"First offer routes match: {routes_match}")

if __name__ == "__main__":
    test_original_transformation()
    test_roundtrip_transformation()
    test_backward_compatibility()