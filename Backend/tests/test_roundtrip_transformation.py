#!/usr/bin/env python3
"""
Test script for round trip transformation logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer_roundtrip import (
    transform_verteil_to_frontend_with_roundtrip,
    _detect_round_trip_segments
)
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE
import json

def test_round_trip_detection():
    """Test the round trip detection logic."""
    print("Testing Round Trip Detection")
    print("=" * 50)
    
    # First, let's get the segments from the original transformation
    from utils.data_transformer import transform_verteil_to_frontend
    
    original_result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)
    if original_result:
        segments = original_result[0].get('segments', [])
        print(f"Original segments count: {len(segments)}")
        
        for i, segment in enumerate(segments):
            print(f"  Segment {i+1}: {segment['departure']['airport']} -> {segment['arrival']['airport']} at {segment['departure']['datetime']}")
        
        # Test round trip detection
        outbound, return_segments = _detect_round_trip_segments(segments)
        
        print(f"\nRound trip detection results:")
        print(f"  Outbound segments: {len(outbound)}")
        print(f"  Return segments: {len(return_segments)}")
        
        if outbound:
            print(f"  Outbound route: {outbound[0]['departure']['airport']} -> {outbound[-1]['arrival']['airport']}")
        
        if return_segments:
            print(f"  Return route: {return_segments[0]['departure']['airport']} -> {return_segments[-1]['arrival']['airport']}")
        else:
            print("  No return segments detected (one-way trip)")

def test_enhanced_transformation():
    """Test the enhanced transformation with round trip support."""
    print("\n\nTesting Enhanced Transformation")
    print("=" * 50)
    
    # Transform using the enhanced function
    enhanced_result = transform_verteil_to_frontend_with_roundtrip(SAMPLE_VERTEIL_RESPONSE)
    
    print(f"Enhanced transformation result:")
    print(f"  Number of flight offers: {len(enhanced_result)}")
    
    for i, offer in enumerate(enhanced_result):
        print(f"\n  Offer {i+1}:")
        print(f"    ID: {offer.get('id')}")
        print(f"    Trip Type: {offer.get('tripType', 'N/A')}")
        print(f"    Direction: {offer.get('direction', 'N/A')}")
        print(f"    Route: {offer['departure']['airport']} -> {offer['arrival']['airport']}")
        print(f"    Departure: {offer['departure']['datetime']}")
        print(f"    Arrival: {offer['arrival']['datetime']}")
        print(f"    Segments: {len(offer.get('segments', []))}")
        print(f"    Stops: {offer.get('stops', 0)}")
        print(f"    Price: {offer.get('price')} {offer.get('currency')}")

def compare_transformations():
    """Compare original vs enhanced transformation."""
    print("\n\nComparing Transformations")
    print("=" * 50)
    
    # Original transformation
    from utils.data_transformer import transform_verteil_to_frontend
    original_result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)
    
    # Enhanced transformation
    enhanced_result = transform_verteil_to_frontend_with_roundtrip(SAMPLE_VERTEIL_RESPONSE)
    
    print(f"Original transformation: {len(original_result)} offers")
    print(f"Enhanced transformation: {len(enhanced_result)} offers")
    
    if original_result:
        original_offer = original_result[0]
        print(f"\nOriginal offer:")
        print(f"  Route: {original_offer['departure']['airport']} -> {original_offer['arrival']['airport']}")
        print(f"  Segments: {len(original_offer.get('segments', []))}")
    
    if enhanced_result:
        print(f"\nEnhanced offers:")
        for i, offer in enumerate(enhanced_result):
            print(f"  Offer {i+1}: {offer['departure']['airport']} -> {offer['arrival']['airport']} ({offer.get('direction', 'unknown')})")

if __name__ == "__main__":
    test_round_trip_detection()
    test_enhanced_transformation()
    compare_transformations()