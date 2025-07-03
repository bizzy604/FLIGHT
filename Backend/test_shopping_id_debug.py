#!/usr/bin/env python3
"""
Debug script to test the _get_airline_shopping_response_id function directly.
"""

import json
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.build_flightprice_rq import _get_airline_shopping_response_id

def load_test_data():
    """Load the multi-airline air shopping response test data."""
    try:
        with open("../postman/airshopingresponse.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: Test data file not found")
        return None

def test_shopping_id_function(airshopping_response):
    """Test the _get_airline_shopping_response_id function directly."""
    print("=== TESTING _get_airline_shopping_response_id FUNCTION ===")
    
    test_airlines = ["KL", "LHG", "QR", "EK", "AF", "KQ", "ET"]
    
    for airline in test_airlines:
        print(f"\n--- Testing airline: {airline} ---")
        
        try:
            shopping_id = _get_airline_shopping_response_id(airshopping_response, airline)
            print(f"Result: {shopping_id}")
            
            if shopping_id:
                print(f"✅ SUCCESS: Got shopping ID for {airline}")
                if shopping_id.endswith(f"-{airline}"):
                    print(f"✅ CORRECT: ID ends with -{airline}")
                else:
                    print(f"⚠️  WARNING: ID doesn't end with -{airline}")
            else:
                print(f"❌ FAILED: No shopping ID returned for {airline}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

def main():
    """Main test function."""
    print("Testing _get_airline_shopping_response_id Function")
    print("=" * 60)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        sys.exit(1)
    
    # Test the function
    test_shopping_id_function(airshopping_response)

if __name__ == "__main__":
    main()
