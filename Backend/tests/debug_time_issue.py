#!/usr/bin/env python3
"""
Debug script to examine time extraction issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from utils.data_transformer import _extract_reference_data

def debug_time_extraction():
    """Debug the time extraction from API response."""
    
    # Load the test data
    with open('tests/airshoping_response.json', 'r') as f:
        test_data = json.load(f)
    
    print("=== Debugging Time Extraction Issue ===")
    
    # Extract reference data
    reference_data = _extract_reference_data(test_data)
    
    # Get the first segment to examine its structure
    offers_group = test_data.get('OffersGroup', {})
    airline_offers = offers_group.get('AirlineOffers', [])
    
    if airline_offers:
        first_airline = airline_offers[0]
        airline_offer = first_airline.get('AirlineOffer', [])
        
        if airline_offer:
            first_offer = airline_offer[0]
            priced_offer = first_offer.get('PricedOffer', {})
            associations = priced_offer.get('Associations', {})
            associated_flights = associations.get('AssociatedFlights', {})
            flight_references = associated_flights.get('FlightReferences', [])
            
            if flight_references:
                flight_ref = flight_references[0]
                flight_key = flight_ref.get('value', '')
                
                # Find the flight in reference data
                flight_data = reference_data['flights'].get(flight_key, {})
                segments = flight_data.get('segments', [])
                
                if segments:
                    segment_key = segments[0]
                    segment_data = reference_data['segments'].get(segment_key, {})
                    
                    print(f"\nSegment Key: {segment_key}")
                    print(f"Segment Data Structure:")
                    print(json.dumps(segment_data, indent=2))
                    
                    # Examine departure and arrival data
                    departure = segment_data.get('Departure', {})
                    arrival = segment_data.get('Arrival', {})
                    
                    print(f"\nDeparture Data:")
                    print(json.dumps(departure, indent=2))
                    
                    print(f"\nArrival Data:")
                    print(json.dumps(arrival, indent=2))
                    
                    # Check what fields are available
                    dep_date = departure.get('Date', '')
                    dep_time = departure.get('Time', '')
                    arr_date = arrival.get('Date', '')
                    arr_time = arrival.get('Time', '')
                    
                    print(f"\nExtracted Fields:")
                    print(f"  Departure Date: '{dep_date}'")
                    print(f"  Departure Time: '{dep_time}'")
                    print(f"  Arrival Date: '{arr_date}'")
                    print(f"  Arrival Time: '{arr_time}'")
                    
                    # Check if there are other time-related fields
                    print(f"\nAll Departure Keys: {list(departure.keys())}")
                    print(f"All Arrival Keys: {list(arrival.keys())}")

if __name__ == '__main__':
    debug_time_extraction()