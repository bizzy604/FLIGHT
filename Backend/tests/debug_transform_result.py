#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import transform_verteil_to_frontend
from tests.test_data_transformer import SAMPLE_VERTEIL_RESPONSE

# Transform the sample response
result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)

print("Transformation result:")
print(f"Number of flight offers: {len(result)}")

if result:
    flight_offer = result[0]
    print("\nFirst flight offer:")
    print(f"ID: {flight_offer.get('id')}")
    print(f"Airline: {flight_offer.get('airline')}")
    print(f"Departure: {flight_offer.get('departure')}")
    print(f"Arrival: {flight_offer.get('arrival')}")
    print(f"Duration: {flight_offer.get('duration')}")
    print(f"Stops: {flight_offer.get('stops')}")
    print(f"Price: {flight_offer.get('price')}")
    print(f"Currency: {flight_offer.get('currency')}")
    
    # Check specific departure/arrival airports
    if 'departure' in flight_offer and 'airport' in flight_offer['departure']:
        print(f"\nDeparture airport: {flight_offer['departure']['airport']}")
    if 'arrival' in flight_offer and 'airport' in flight_offer['arrival']:
        print(f"Arrival airport: {flight_offer['arrival']['airport']}")
else:
    print("No flight offers found in result")