#!/usr/bin/env python3
"""
Debug script to call Verteil API and store response in temporary file
This will help us examine the full API response structure
"""

import json
import os
import sys
from datetime import datetime

# Add the Backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.auth import TokenManager
from scripts.build_airshopping_rq import build_airshopping_request
from config import get_config
import requests

def call_api_and_store_response():
    """
    Call the Verteil API and store the full response in a temporary file
    """
    try:
        print("Loading configuration...")
        config_class = get_config()
        # Convert config class to dictionary
        config = {}
        for attr in dir(config_class):
            if not attr.startswith('_') and not callable(getattr(config_class, attr)):
                config[attr] = getattr(config_class, attr)
        print(f"Config loaded with {len(config)} settings")
        
        print("Getting authentication token...")
        try:
            token_manager = TokenManager.get_instance()
            token_manager.set_config(config)
            full_token = token_manager.get_token(config)
            print(f"Token obtained: {full_token[:20]}...")
        except Exception as e:
            print(f"Error getting token: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        if not full_token:
            print("Failed to get authentication token")
            return False
        
        print("Building AirShopping request...")
        # Build a sample request (one-way flight)
        od_segments = [{
            "Origin": "JFK",
            "Destination": "LAX",
            "DepartureDate": "2025-01-15"
        }]
        
        request_data = build_airshopping_request(
            trip_type="ONE_WAY",
            od_segments=od_segments,
            num_adults=2,
            num_children=2,
            num_infants=1
        )
        print("Request built successfully")
        
        print("Making API call...")
        headers = {
            'Authorization': full_token,  # TokenManager returns 'Bearer <token>' format
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://api.stage.verteil.com/entrygate/rest/request:airShopping',
                headers=headers,
                json=request_data,
                timeout=30
            )
            print(f"API Response Status: {response.status_code}")
        except Exception as req_error:
            print(f"Request failed: {str(req_error)}")
            import traceback
            traceback.print_exc()
            return False
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_response_{timestamp}.json"
            filepath = os.path.join(os.path.dirname(__file__), "debug", filename)
            
            # Ensure debug directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Store the full response
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            print(f"Full API response stored in: {filepath}")
            
            # Also create a summary file with key structure info
            summary_file = filepath.replace('.json', '_summary.txt')
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"API Response Summary - {timestamp}\n")
                f.write("=" * 50 + "\n\n")
                
                # Check for key structures
                f.write("Key Structure Analysis:\n")
                f.write("-" * 25 + "\n")
                
                if 'FlightSegmentList' in response_data:
                    segments = response_data['FlightSegmentList']
                    f.write(f"✓ FlightSegmentList found at root level\n")
                    f.write(f"  - Contains {len(segments.get('FlightSegment', []))} segments\n")
                else:
                    f.write("✗ FlightSegmentList NOT found at root level\n")
                
                if 'OriginDestinationList' in response_data:
                    od_list = response_data['OriginDestinationList']
                    f.write(f"✓ OriginDestinationList found at root level\n")
                    f.write(f"  - Contains {len(od_list.get('OriginDestination', []))} origin-destinations\n")
                else:
                    f.write("✗ OriginDestinationList NOT found at root level\n")
                
                if 'DataLists' in response_data:
                    data_lists = response_data['DataLists']
                    f.write(f"✓ DataLists found\n")
                    for key in data_lists.keys():
                        f.write(f"  - {key}\n")
                else:
                    f.write("✗ DataLists NOT found\n")
                
                if 'OffersGroup' in response_data:
                    offers_group = response_data['OffersGroup']
                    f.write(f"✓ OffersGroup found\n")
                    if 'AirlineOffers' in offers_group:
                        airline_offers = offers_group['AirlineOffers']
                        total_offers = sum(len(ao.get('AirlineOffer', [])) for ao in airline_offers)
                        f.write(f"  - Total offers: {total_offers}\n")
                else:
                    f.write("✗ OffersGroup NOT found\n")
            
            print(f"Summary analysis stored in: {summary_file}")
            return True
        else:
            print(f"API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error calling API: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting API debug call...")
    success = call_api_and_store_response()
    if success:
        print("\nAPI call completed successfully!")
        print("You can now examine the stored response files to debug the data transformation issue.")
    else:
        print("\nAPI call failed. Please check the error messages above.")