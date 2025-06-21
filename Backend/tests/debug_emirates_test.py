#!/usr/bin/env python3

import sys
import os
import json

# Add the scripts directory to the path
sys.path.append('../scripts')

from build_ordercreate_rq import create_passenger_mapping

def debug_emirates_test():
    """Debug the Emirates ObjectKey mapping"""
    
    # Load the actual Emirates response
    with open('flightpriceresponse.json', 'r') as f:
        emirates_full_response = json.load(f)
    
    # Extract the actual flight price response
    emirates_response = emirates_full_response['data']['raw_response']['data']['raw_response']
    
    # Multiple passengers but only 1 ObjectKey available from Emirates
    passengers_data = [
        {
            "PTC": "ADT",
            "Name": {
                "Title": "Mr",
                "Given": ["John"],
                "Surname": "Doe"
            },
            "Gender": "Male",
            "BirthDate": "1985-03-15"
        },
        {
            "PTC": "ADT",
            "Name": {
                "Title": "Mrs",
                "Given": ["Jane"],
                "Surname": "Doe"
            },
            "Gender": "Female",
            "BirthDate": "1987-07-22"
        },
        {
            "PTC": "CHD",
            "Name": {
                "Title": "Miss",
                "Given": ["Emily"],
                "Surname": "Doe"
            },
            "Gender": "Female",
            "BirthDate": "2015-01-01"
        }
    ]
    
    print("=== Emirates ObjectKey Debug ===")
    print(f"Number of passengers: {len(passengers_data)}")
    
    # Check what's in the Emirates response
    if 'DataLists' in emirates_response:
        if 'AnonymousTravelerList' in emirates_response['DataLists']:
            travelers = emirates_response['DataLists']['AnonymousTravelerList']
            if 'AnonymousTraveler' in travelers:
                anon_travelers = travelers['AnonymousTraveler']
                if isinstance(anon_travelers, list):
                    print(f"Found {len(anon_travelers)} AnonymousTravelers:")
                    for i, traveler in enumerate(anon_travelers):
                        print(f"  {i}: ObjectKey='{traveler.get('ObjectKey')}', PTC='{traveler.get('PTC', {}).get('value')}'")
                else:
                    print(f"Found 1 AnonymousTraveler: ObjectKey='{anon_travelers.get('ObjectKey')}', PTC='{anon_travelers.get('PTC', {}).get('value')}'")
            else:
                print("No AnonymousTraveler found in AnonymousTravelerList")
        else:
            print("No AnonymousTravelerList found in DataLists")
    else:
        print("No DataLists found in Emirates response")
    
    # Test the mapping
    mapping = create_passenger_mapping(emirates_response, passengers_data)
    
    print(f"\nMapping result: {mapping}")
    print(f"Expected: First passenger should get 'T1', others should get fallback")
    
    # Check each passenger
    for i, passenger in enumerate(passengers_data):
        mapped_key = mapping.get(i)
        print(f"Passenger {i} (PTC: {passenger['PTC']}): ObjectKey = '{mapped_key}'")

if __name__ == "__main__":
    debug_emirates_test()