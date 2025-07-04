#!/usr/bin/env python3
"""
Quick test to verify the pricing output from enhanced transformer
"""

import json
import sys
import os

# Add the Backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer

def test_pricing_output():
    """Test the pricing output from enhanced transformer"""
    
    # Load test data
    with open('tests/airshopingRS.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Transform data
    transformer = EnhancedAirShoppingTransformer(data)
    result = transformer.transform_for_results()

    # Check first flight pricing
    first_flight = result['offers'][0]
    print('=== FIRST FLIGHT PRICING ===')
    print(f'flight.price: {first_flight.get("price")}')
    print(f'flight.priceBreakdown.totalPrice: {first_flight.get("priceBreakdown", {}).get("totalPrice")}')
    print(f'flight.currency: {first_flight.get("currency")}')
    print(f'flight.priceBreakdown.currency: {first_flight.get("priceBreakdown", {}).get("currency")}')
    
    # Check if they match
    price = first_flight.get("price")
    breakdown_price = first_flight.get("priceBreakdown", {}).get("totalPrice")
    
    print(f'\n=== COMPARISON ===')
    print(f'flight.price == flight.priceBreakdown.totalPrice: {price == breakdown_price}')
    
    if price == breakdown_price:
        print('✅ Both price fields match - frontend should display correct price')
    else:
        print('❌ Price fields do not match - there may be an issue')
        print(f'Difference: {abs(price - breakdown_price) if price and breakdown_price else "N/A"}')

if __name__ == "__main__":
    test_pricing_output()
