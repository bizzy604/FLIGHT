#!/usr/bin/env python3
"""
Comprehensive test script to validate both OriginDestination and Travelers 
grouping in SeatAvailability requests.
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append('scripts')
from build_seatavailability_rq import build_seatavailability_request

def test_comprehensive_grouping():
    """Test that both OriginDestination and Travelers are properly grouped"""
    
    print("="*80)
    print("COMPREHENSIVE TEST: OriginDestination & Travelers Grouping")
    print("="*80)
    
    # Test 1: Round Trip (KQ: NBO → CDG → NBO)
    print("\n1. ROUND TRIP TEST (KQ)")
    print("-" * 30)
    
    with open('tests/FlightPriceRS_KQ.json', 'r', encoding='utf-8') as f:
        kq_data = json.load(f)
    
    kq_request = build_seatavailability_request(kq_data)
    
    # Check OriginDestination structure
    kq_ods = kq_request.get('Query', {}).get('OriginDestination', [])
    print(f"OriginDestination: Found {len(kq_ods)} object(s)")
    for i, od in enumerate(kq_ods):
        refs = od.get('FlightSegmentReference', [])
        ref_values = [ref.get('ref') for ref in refs]
        journey_type = "OUTBOUND" if i == 0 else "RETURN"
        print(f"  OD {i+1} ({journey_type}): {ref_values}")
    
    # Check Travelers structure
    kq_travelers = kq_request.get('Travelers', {}).get('Traveler', [])
    print(f"\\nTravelers: Found {len(kq_travelers)} Traveler object(s)")
    for i, traveler in enumerate(kq_travelers):
        anon_travelers = traveler.get('AnonymousTraveler', [])
        print(f"  Traveler {i+1}: {len(anon_travelers)} AnonymousTraveler(s)")
        for j, anon in enumerate(anon_travelers[:3]):  # Show first 3
            obj_key = anon.get('ObjectKey')
            ptc = anon.get('PTC', {}).get('value')
            print(f"    {obj_key} ({ptc})")
        if len(anon_travelers) > 3:
            print(f"    ... and {len(anon_travelers) - 3} more")
    
    # Validate round trip
    assert len(kq_ods) == 2, f"Round trip should have 2 OriginDestination objects, got {len(kq_ods)}"
    assert len(kq_travelers) == 1, f"Should have 1 Traveler object, got {len(kq_travelers)}"
    print("✅ PASS: Round trip structure correct")
    
    # Test 2: Connecting Flights (AF: BLR → AMS → LHR)
    print("\\n2. CONNECTING FLIGHTS TEST (AF)")
    print("-" * 35)
    
    with open('tests/FlightPriceRS_AF.json', 'r', encoding='utf-8') as f:
        af_data = json.load(f)
    
    af_request = build_seatavailability_request(af_data)
    
    # Check OriginDestination structure
    af_ods = af_request.get('Query', {}).get('OriginDestination', [])
    print(f"OriginDestination: Found {len(af_ods)} object(s)")
    for i, od in enumerate(af_ods):
        refs = od.get('FlightSegmentReference', [])
        ref_values = [ref.get('ref') for ref in refs[:3]]  # Show first 3
        if len(refs) > 3:
            ref_values.append(f"... +{len(refs) - 3} more")
        print(f"  OD {i+1} (ALL SEGMENTS): {ref_values}")
    
    # Check Travelers structure
    af_travelers = af_request.get('Travelers', {}).get('Traveler', [])
    print(f"\\nTravelers: Found {len(af_travelers)} Traveler object(s)")
    for i, traveler in enumerate(af_travelers):
        anon_travelers = traveler.get('AnonymousTraveler', [])
        print(f"  Traveler {i+1}: {len(anon_travelers)} AnonymousTraveler(s)")
        for j, anon in enumerate(anon_travelers):
            obj_key = anon.get('ObjectKey')
            ptc = anon.get('PTC', {}).get('value')
            print(f"    {obj_key} ({ptc})")
    
    # Validate connecting flights
    assert len(af_ods) == 1, f"Connecting flights should have 1 OriginDestination object, got {len(af_ods)}"
    assert len(af_ods[0].get('FlightSegmentReference', [])) > 1, "Should have multiple segment references"
    assert len(af_travelers) == 1, f"Should have 1 Traveler object, got {len(af_travelers)}"
    print("✅ PASS: Connecting flights structure correct")
    
    # Test 3: Structure Comparison
    print("\\n3. STRUCTURE COMPARISON")
    print("-" * 25)
    
    print("Round Trip Travelers Structure:")
    print(json.dumps(kq_travelers, indent=2))
    
    print("\\nConnecting Flight Travelers Structure:")
    print(json.dumps(af_travelers, indent=2))
    
    # Test 4: Validate Key Benefits
    print("\\n4. VALIDATION SUMMARY")
    print("-" * 20)
    
    # OriginDestination validation
    print("OriginDestination Grouping:")
    print(f"  ✅ Round trips: {len(kq_ods)} separate objects (outbound + return)")
    print(f"  ✅ Connecting: {len(af_ods)} object with {len(af_ods[0].get('FlightSegmentReference', []))} segments")
    
    # Travelers validation
    kq_total_travelers = len(kq_travelers[0].get('AnonymousTraveler', [])) if kq_travelers else 0
    af_total_travelers = len(af_travelers[0].get('AnonymousTraveler', [])) if af_travelers else 0
    print("\\nTravelers Grouping:")
    print(f"  ✅ Round trips: 1 Traveler object with {kq_total_travelers} AnonymousTravelers")
    print(f"  ✅ Connecting: 1 Traveler object with {af_total_travelers} AnonymousTravelers")
    
    print("\\n" + "="*80)
    print("✅ ALL TESTS PASSED: Complete SeatAvailability grouping working correctly")
    print("✅ OriginDestination: Round trips (2 objects) vs Connecting (1 object)")
    print("✅ Travelers: All scenarios group AnonymousTravelers into single Traveler object")
    print("="*80)

if __name__ == "__main__":
    test_comprehensive_grouping()
