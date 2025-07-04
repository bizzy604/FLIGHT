#!/usr/bin/env python3
"""
Test script to verify the API response structure that frontend receives
"""

import json
import sys
import os

# Add the Backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer

def test_api_response_structure():
    """Test the API response structure that frontend receives"""
    
    # Load test data
    with open('tests/airshopingRS.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Transform data (this is what the backend does)
    transformer = EnhancedAirShoppingTransformer(data)
    result = transformer.transform_for_results()

    # Simulate the API response structure that frontend receives
    api_response = {
        "data": result,
        "status": "success"
    }

    print('=== API RESPONSE STRUCTURE ===')
    print(f'api_response.keys(): {list(api_response.keys())}')
    print(f'api_response.data.keys(): {list(api_response["data"].keys())}')
    
    # Check the offers structure
    offers = api_response["data"]["offers"]
    print(f'Number of offers: {len(offers)}')
    
    # Check first offer pricing
    first_offer = offers[0]
    print(f'\n=== FIRST OFFER PRICING ===')
    print(f'offer.price: {first_offer.get("price")}')
    print(f'offer.currency: {first_offer.get("currency")}')
    print(f'offer.priceBreakdown: {first_offer.get("priceBreakdown")}')
    
    # Simulate what frontend does: apiResponse.data.offers
    frontend_flights = api_response["data"]["offers"]
    frontend_first_flight = frontend_flights[0]
    
    print(f'\n=== FRONTEND RECEIVES ===')
    print(f'flight.price: {frontend_first_flight.get("price")}')
    print(f'flight.priceBreakdown?.totalPrice: {frontend_first_flight.get("priceBreakdown", {}).get("totalPrice")}')
    print(f'flight.priceBreakdown?.currency: {frontend_first_flight.get("priceBreakdown", {}).get("currency")}')
    
    # Test the exact logic from enhanced-flight-card.tsx
    price_breakdown = frontend_first_flight.get("priceBreakdown", {})
    displayed_price = price_breakdown.get("totalPrice") or frontend_first_flight.get("price")
    displayed_currency = price_breakdown.get("currency")
    
    print(f'\n=== ENHANCED CARD DISPLAYS ===')
    print(f'Displayed Price: {displayed_currency} {displayed_price}')
    print(f'Label: "for all passengers"')

if __name__ == "__main__":
    test_api_response_structure()
