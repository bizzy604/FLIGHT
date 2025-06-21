#!/usr/bin/env python3
"""
Test script to verify airline name extraction from MarketingCarrier data.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.data_transformer import transform_verteil_to_frontend, _extract_reference_data

def test_airline_name_extraction():
    """Test airline name extraction from MarketingCarrier data."""
    current_dir = Path(__file__).parent
    api_response_file = current_dir / 'api_response_20250607_132944.json'
    
    try:
        with open(api_response_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=== Testing Airline Name Extraction ===")
        
        # Test reference data extraction
        reference_data = _extract_reference_data(data)
        
        print(f"\nExtracted airlines from reference data:")
        for code, info in reference_data['airlines'].items():
            print(f"  {code}: {info}")
        
        print(f"\nDefault airline: {reference_data.get('default_airline')}")
        
        # Check specific flight segments
        data_lists = data.get('DataLists', {})
        flight_segment_list = data_lists.get('FlightSegmentList', {})
        flight_segments = flight_segment_list.get('FlightSegment', [])
        
        print(f"\nFirst 5 flight segments MarketingCarrier data:")
        for i, segment in enumerate(flight_segments[:-10]):
            marketing_carrier = segment.get('MarketingCarrier', {})
            airline_id = marketing_carrier.get('AirlineID', {})
            airline_code = airline_id.get('value') if isinstance(airline_id, dict) else None
            airline_name = marketing_carrier.get('Name')
            
            print(f"  Segment {i+1}: Code={airline_code}, Name={airline_name}")
        
        # Test full transformation
        print("\n=== Testing Full Transformation ===")
        result = transform_verteil_to_frontend(data)
        offers = result.get('offers', [])
        print(f"Generated {len(offers)} offers")
        
        # Show first few offers with airline info
        print("\nFirst 3 offers:")
        for i, offer in enumerate(offers[:3]):
            print(f"  Offer {i+1}: ID={offer.get('id')}, Airline={offer.get('airline')}, Direction={offer.get('direction')}")
        
    except Exception as e:
        print(f"Error in airline name extraction test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_airline_name_extraction()