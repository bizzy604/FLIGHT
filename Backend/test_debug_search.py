#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from services.flight_service import search_flights, FlightServiceError

def create_test_app():
    """Create a test Flask app with configuration."""
    app = Flask(__name__)
    
    # Configure the app
    app.config.update(
        TESTING=True,
        VERTEIL_API_BASE_URL='https://api.stage.verteil.com',
        VERTEIL_TOKEN_ENDPOINT='/oauth2/token',
        VERTEIL_USERNAME='reatravel_apitestuser',
        VERTEIL_PASSWORD='UZrNcyxpIFn2TOdiU5uc9kZrqJwxU44KdlyFBpiDOaaNom1xSySEtQmRq9IcDq3c',
        VERTEIL_THIRD_PARTY_ID='KQ',
        VERTEIL_OFFICE_ID='OFF3746',
        REQUEST_TIMEOUT=30,
        OAUTH2_TOKEN_EXPIRY_BUFFER=60
    )
    
    return app

if __name__ == '__main__':
    app = create_test_app()
    
    search_params = {
        'origin': 'JFK',
        'destination': 'LAX',
        'departure_date': '2024-02-01',
        'return_date': '2024-02-08',
        'adults': 1,
        'children': 0,
        'infants': 0,
        'cabin_class': 'Economy',
        'trip_type': 'roundtrip'
    }
    
    with app.app_context():
        try:
            result = search_flights(
                origin=search_params['origin'],
                destination=search_params['destination'],
                departure_date=search_params['departure_date'],
                return_date=search_params['return_date'],
                adults=search_params['adults'],
                children=search_params['children'],
                infants=search_params['infants'],
                cabin_class=search_params['cabin_class'],
                trip_type=search_params['trip_type']
            )
            # Write debug output to file
            with open('debug_output.txt', 'w') as f:
                f.write(f"Result: {result}\n")
                f.write(f"Result type: {type(result)}\n")
                f.write(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}\n")
                
                if isinstance(result, dict):
                    f.write(f"\nStatus: {result.get('status')}\n")
                    f.write(f"Request ID: {result.get('request_id')}\n")
                    
                    if 'data' in result:
                        data = result['data']
                        f.write(f"\nData type: {type(data)}\n")
                        if isinstance(data, dict):
                            f.write(f"Data keys: {list(data.keys())}\n")
                            if 'offers' in data:
                                offers = data['offers']
                                f.write(f"\nOffers type: {type(offers)}\n")
                                f.write(f"Number of offers: {len(offers) if isinstance(offers, list) else 'Not a list'}\n")
                                if isinstance(offers, list) and len(offers) > 0:
                                    f.write(f"First offer keys: {list(offers[0].keys()) if isinstance(offers[0], dict) else 'First offer not a dict'}\n")
                        else:
                            f.write(f"Data content: {str(data)[:500]}...\n")
                            
                    if 'error' in result:
                        f.write(f"\nError: {result['error']}\n")
            
            print("Debug output written to debug_output.txt")
        except Exception as e:
            with open('debug_output.txt', 'w') as f:
                f.write(f"Error: {type(e).__name__}: {e}\n")
                import traceback
                f.write(traceback.format_exc())
            print(f"Error occurred, details written to debug_output.txt")