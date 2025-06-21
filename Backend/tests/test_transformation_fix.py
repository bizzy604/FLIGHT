#!/usr/bin/env python3

import json
import sys
import os

# Add the Backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import transform_verteil_to_frontend

def test_transformation():
    """Test the transformation with the saved API response"""
    
    # Load the saved API response
    response_file = 'debug/api_response_20250607_132944.json'
    
    try:
        with open(response_file, 'r') as f:
            api_response = json.load(f)
        
        print(f"Loaded API response with keys: {list(api_response.keys())}")
        
        # Test the transformation
        print("\n=== Testing Transformation ===")
        transformed_offers = transform_verteil_to_frontend(api_response)
        
        print(f"\nTransformation Result:")
        print(f"Number of offers transformed: {len(transformed_offers)}")
        
        if transformed_offers:
            print("\n=== First Offer Details ===")
            first_offer = transformed_offers[0]
            print(json.dumps(first_offer, indent=2))
        else:
            print("No offers were successfully transformed")
            
            # Debug: Check if segments are being found
            data_lists = api_response.get('DataLists', {})
            flight_segment_list = data_lists.get('FlightSegmentList', {})
            segments = flight_segment_list.get('FlightSegment', [])
            print(f"\nDebug: Found {len(segments)} segments in DataLists.FlightSegmentList")
            
            if segments:
                print("Sample segment keys:")
                for i, segment in enumerate(segments[:3]):
                    print(f"  Segment {i}: {segment.get('SegmentKey', 'No key')}")
        
    except FileNotFoundError:
        print(f"Error: Could not find response file: {response_file}")
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON: {e}")
    except Exception as e:
        print(f"Error during transformation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transformation()