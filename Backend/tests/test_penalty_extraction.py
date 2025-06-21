#!/usr/bin/env python3
"""
Test script to verify penalty extraction functionality.
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Add Backend directory to sys.path

from utils.data_transformer import transform_verteil_to_frontend

def test_penalty_extraction():
    """Test penalty extraction with actual API response"""
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_output')
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, 'test_penalty_extraction_output.txt')

    original_stdout = sys.stdout
    with open(output_file_path, 'w', encoding='utf-8') as f_out: # Specify UTF-8 encoding
        sys.stdout = f_out

        try:
            # Load the actual API response
            script_dir = os.path.dirname(os.path.abspath(__file__))
            api_response_path = os.path.join(script_dir, '..', 'debug', 'api_response_20250607_132944.json')
            with open(api_response_path, 'r', encoding='utf-8') as f_api: # Also specify for reading, just in case
                api_response = json.load(f_api)
            
            print("=== Testing Penalty Extraction ===")
            print(f"Original API response has {len(api_response.get('OffersGroup', {}).get('AirlineOffers', []))} airline offers")
            
            # Transform the data
            transformed_data = transform_verteil_to_frontend(api_response)
            print(f"DEBUG: Type of transformed_data: {type(transformed_data)}")
            print(f"DEBUG: Value of transformed_data: {transformed_data}")
            
            flights = transformed_data.get('flights', [])
            print(f"\n✅ Transformation successful! Found {len(flights)} flights")
            
            if not flights:
                print("❌ No flights found in the transformed result.")
            else:
                first_flight = flights[0]
                print(f"\n=== First Flight Penalty Information ===")
                print(f"Flight ID: {first_flight.get('id', 'N/A')}")
                print(f"Airline: {first_flight.get('airline', {}).get('name', 'N/A')}")
                
                penalties = first_flight.get('penalties', [])
                print(f"\nPenalties found: {len(penalties)}")
                
                if penalties:
                    for i, penalty in enumerate(penalties, 1):
                        print(f"\n--- Penalty {i} ---")
                        print(f"Type: {penalty.get('type', 'N/A')}")
                        print(f"Application: {penalty.get('application', 'N/A')}")
                        print(f"Amount: {penalty.get('amount', 0)} {penalty.get('currency', 'N/A')}")
                        print(f"Refundable: {penalty.get('refundable', False)}")
                        print(f"Cancel Fee: {penalty.get('cancelFee', False)}")
                        remarks = penalty.get('remarks', [])
                        if remarks:
                            print(f"Remarks: {', '.join(remarks)}")
                        else:
                            print("Remarks: None")
                else:
                    print("❌ No penalties extracted")
                    
                    # Debug: Check if penalty references exist in the raw data
                    print("\n=== Debug: Checking Raw Data Structure ===")
                    airline_offers = api_response.get('OffersGroup', {}).get('AirlineOffers', [])
                    if airline_offers:
                        first_offer = airline_offers[0]
                        priced_offers = first_offer.get('AirlineOffer', [])
                        if priced_offers:
                            priced_offer = priced_offers[0].get('PricedOffer', {})
                            offer_prices = priced_offer.get('OfferPrice', [])
                            if offer_prices:
                                offer_price = offer_prices[0]
                                fare_detail = offer_price.get('FareDetail', {})
                                fare_components = fare_detail.get('FareComponent', [])
                                if fare_components:
                                    fare_component = fare_components[0]
                                    fare_rules = fare_component.get('FareRules', {})
                                    penalty_refs = fare_rules.get('Penalty', {}).get('refs', [])
                                    print(f"Penalty references found: {penalty_refs}")
                                    
                                    # Check if penalty data exists in DataLists
                                    data_lists = api_response.get('DataLists', {})
                                    penalty_list = data_lists.get('PenaltyList', {})
                                    penalties_data = penalty_list.get('Penalty', [])
                                    print(f"Penalties in DataLists: {len(penalties_data)}")
                                    
                                    for penalty_data in penalties_data:
                                        object_key = penalty_data.get('ObjectKey', 'N/A')
                                        print(f"  - {object_key}")
            
            print("\n✅ SUCCESS: Penalty extraction test completed!")
            
        except Exception as e:
            print(f"❌ ERROR during transformation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sys.stdout = original_stdout # Restore stdout

if __name__ == "__main__":
    test_penalty_extraction()