#!/usr/bin/env python3
"""
Test script to validate SeatAvailability request generation for both 
round trip and connecting flight scenarios.
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append('scripts')
from build_seatavailability_rq import build_seatavailability_request

def test_round_trip_vs_connecting_flights():
    """Test that round trips create 2 OriginDestination objects and connecting flights create 1"""
    
    print("="*70)
    print("TESTING: Round Trip vs Connecting Flights OriginDestination Structure")
    print("="*70)
    
    # Test 1: Round Trip (KQ: NBO → CDG → NBO)
    print("\n1. ROUND TRIP TEST (KQ FlightPrice)")
    print("-" * 40)
    
    with open('tests/FlightPriceRS_KQ.json', 'r', encoding='utf-8') as f:
        kq_data = json.load(f)
    
    kq_request = build_seatavailability_request(kq_data)
    kq_ods = kq_request.get('Query', {}).get('OriginDestination', [])
    
    print(f"Flight segments analysis:")
    segments = kq_data.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
    for i, seg in enumerate(segments):
        dep = seg.get('Departure', {}).get('AirportCode', {}).get('value')
        arr = seg.get('Arrival', {}).get('AirportCode', {}).get('value')
        seg_key = seg.get('SegmentKey')
        print(f"  Segment {i+1} ({seg_key}): {dep} → {arr}")
    
    print(f"\\nOriginDestination structure:")
    print(f"  Found {len(kq_ods)} OriginDestination object(s)")
    for i, od in enumerate(kq_ods):
        refs = od.get('FlightSegmentReference', [])
        ref_values = [ref.get('ref') for ref in refs]
        journey_type = "OUTBOUND" if i == 0 else "RETURN"
        print(f"  OD {i+1} ({journey_type}): {ref_values}")
    
    # Validate round trip structure
    assert len(kq_ods) == 2, f"Round trip should have 2 OriginDestination objects, got {len(kq_ods)}"
    print("✅ PASS: Round trip correctly creates 2 OriginDestination objects")
    
    # Test 2: Connecting Flights (AF: BLR → AMS → LHR)
    print("\\n2. CONNECTING FLIGHTS TEST (AF FlightPrice)")
    print("-" * 45)
    
    with open('tests/FlightPriceRS_AF.json', 'r', encoding='utf-8') as f:
        af_data = json.load(f)
    
    af_request = build_seatavailability_request(af_data)
    af_ods = af_request.get('Query', {}).get('OriginDestination', [])
    
    print(f"Flight segments analysis:")
    segments = af_data.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', [])
    route_segments = segments[:2]  # Show first 2 for clarity
    for i, seg in enumerate(route_segments):
        dep = seg.get('Departure', {}).get('AirportCode', {}).get('value')
        arr = seg.get('Arrival', {}).get('AirportCode', {}).get('value')
        seg_key = seg.get('SegmentKey')
        print(f"  Segment {i+1} ({seg_key}): {dep} → {arr}")
    print(f"  ... and {len(segments) - 2} more segments")
    
    print(f"\\nOriginDestination structure:")
    print(f"  Found {len(af_ods)} OriginDestination object(s)")
    for i, od in enumerate(af_ods):
        refs = od.get('FlightSegmentReference', [])
        ref_values = [ref.get('ref') for ref in refs]
        print(f"  OD {i+1} (ALL SEGMENTS): {ref_values}")
    
    # Validate connecting flight structure
    assert len(af_ods) == 1, f"Connecting flights should have 1 OriginDestination object, got {len(af_ods)}"
    assert len(af_ods[0].get('FlightSegmentReference', [])) > 1, "Connecting flights should have multiple segment references"
    print("✅ PASS: Connecting flights correctly create 1 OriginDestination with multiple segments")
    
    # Test 3: Structure Comparison
    print("\\n3. STRUCTURE COMPARISON")
    print("-" * 25)
    
    print("Round Trip Structure:")
    print(json.dumps(kq_ods, indent=2))
    
    print("\\nConnecting Flight Structure:")
    print(json.dumps(af_ods, indent=2))
    
    print("\\n" + "="*70)
    print("✅ ALL TESTS PASSED: SeatAvailability correctly handles both round trips and connecting flights")
    print("✅ Round trips: 2 separate OriginDestination objects (outbound + return)")
    print("✅ Connecting flights: 1 OriginDestination object with all segments")
    print("="*70)

if __name__ == "__main__":
    test_round_trip_vs_connecting_flights()
