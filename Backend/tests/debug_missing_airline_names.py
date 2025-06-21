#!/usr/bin/env python3
"""
Debug script to identify why KL and AF airlines show 'Missing code or name' warnings.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

def debug_missing_airline_names():
    """Debug the specific segments causing missing airline name warnings."""
    current_dir = Path(__file__).parent
    api_response_file = current_dir / 'airshoping_response.json'
    
    try:
        with open(api_response_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=== Debugging Missing Airline Names ===")
        
        # Get flight segments
        data_lists = data.get('DataLists', {})
        flight_segment_list = data_lists.get('FlightSegmentList', {})
        flight_segments = flight_segment_list.get('FlightSegment', [])
        
        print(f"Total flight segments: {len(flight_segments)}")
        
        # Track airlines found
        airlines_found = {}
        problematic_segments = []
        
        for i, segment in enumerate(flight_segments):
            segment_key = segment.get('SegmentKey')
            
            # Check both MarketingCarrier and OperatingCarrier
            for carrier_type in ['MarketingCarrier', 'OperatingCarrier']:
                carrier = segment.get(carrier_type, {})
                if not carrier:
                    continue
                
                airline_id = carrier.get('AirlineID', {})
                
                # Extract airline code
                if isinstance(airline_id, dict):
                    airline_code = airline_id.get('value')
                else:
                    airline_code = airline_id
                
                airline_name = carrier.get('Name')
                
                # Track this airline
                if airline_code:
                    if airline_code not in airlines_found:
                        airlines_found[airline_code] = []
                    airlines_found[airline_code].append({
                        'segment_index': i,
                        'segment_key': segment_key,
                        'carrier_type': carrier_type,
                        'name': airline_name,
                        'has_name': bool(airline_name)
                    })
                
                # Check for problematic cases
                if airline_code and not airline_name:
                    problematic_segments.append({
                        'segment_index': i,
                        'segment_key': segment_key,
                        'carrier_type': carrier_type,
                        'airline_code': airline_code,
                        'airline_name': airline_name,
                        'carrier_data': carrier
                    })
        
        print(f"\n=== Airlines Found Summary ===")
        for code, occurrences in airlines_found.items():
            has_name_count = sum(1 for occ in occurrences if occ['has_name'])
            no_name_count = len(occurrences) - has_name_count
            print(f"  {code}: {len(occurrences)} total, {has_name_count} with name, {no_name_count} without name")
            
            if no_name_count > 0:
                print(f"    First occurrence without name: {occurrences[0]}")
        
        print(f"\n=== Problematic Segments (Code but no Name) ===")
        print(f"Total problematic segments: {len(problematic_segments)}")
        
        # Focus on KL and AF
        kl_problems = [p for p in problematic_segments if p['airline_code'] == 'KL']
        af_problems = [p for p in problematic_segments if p['airline_code'] == 'AF']
        
        print(f"\nKL problems: {len(kl_problems)}")
        if kl_problems:
            print(f"First KL problem:")
            print(f"  Segment: {kl_problems[0]['segment_key']}")
            print(f"  Carrier Type: {kl_problems[0]['carrier_type']}")
            print(f"  Carrier Data: {json.dumps(kl_problems[0]['carrier_data'], indent=2)}")
        
        print(f"\nAF problems: {len(af_problems)}")
        if af_problems:
            print(f"First AF problem:")
            print(f"  Segment: {af_problems[0]['segment_key']}")
            print(f"  Carrier Type: {af_problems[0]['carrier_type']}")
            print(f"  Carrier Data: {json.dumps(af_problems[0]['carrier_data'], indent=2)}")
        
        # Check if there are segments with names for these airlines
        kl_with_names = [occ for occ in airlines_found.get('KL', []) if occ['has_name']]
        af_with_names = [occ for occ in airlines_found.get('AF', []) if occ['has_name']]
        
        print(f"\nKL segments with names: {len(kl_with_names)}")
        if kl_with_names:
            print(f"  Example: {kl_with_names[0]}")
        
        print(f"AF segments with names: {len(af_with_names)}")
        if af_with_names:
            print(f"  Example: {af_with_names[0]}")
        
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_missing_airline_names()