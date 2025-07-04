#!/usr/bin/env python3
"""
Test script to validate multi-PTC pricing aggregation in enhanced_air_shopping_transformer.py
Tests with real air shopping response data from airshopingRS.json
"""

import json
import sys
import os
from datetime import datetime

# Add the Backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer

def load_test_data():
    """Load the air shopping response test data"""
    try:
        with open('tests/airshopingRS.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: airshopingRS.json not found in tests/ directory")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

def analyze_original_pricing_structure(data):
    """Analyze the original pricing structure to understand PTC distribution"""
    print("=== ANALYZING ORIGINAL PRICING STRUCTURE ===")
    
    # Find the first PricedOffer to analyze
    airline_offers = data.get('OffersGroup', {}).get('AirlineOffers', [])
    if not airline_offers:
        print("No AirlineOffers found")
        return None, None

    # Get the first airline's offers
    first_airline_offers = airline_offers[0].get('AirlineOffer', [])
    if not first_airline_offers:
        print("No AirlineOffer found")
        return None, None

    # Get the first PricedOffer
    priced_offer = first_airline_offers[0].get('PricedOffer', {})
    if not priced_offer:
        print("No PricedOffer found")
        return None, None
    offer_prices = priced_offer.get('OfferPrice', [])
    
    print(f"Found {len(offer_prices)} OfferPrice entries in first offer:")
    
    total_manual_calculation = 0.0
    currency = None
    
    for i, op in enumerate(offer_prices):
        price_detail = op.get('RequestedDate', {}).get('PriceDetail', {})
        price_info = price_detail.get('TotalAmount', {}).get('SimpleCurrencyPrice', {})
        amount = float(price_info.get('value', 0))
        curr = price_info.get('Code', 'Unknown')
        
        if currency is None:
            currency = curr
        
        # Count UNIQUE travelers (fix for round-trip double counting)
        unique_travelers = set()
        all_traveler_refs = []
        for assoc in op.get('RequestedDate', {}).get('Associations', []):
            raw_refs = assoc.get('AssociatedTraveler', {}).get('TravelerReferences', [])
            if isinstance(raw_refs, str):
                unique_travelers.add(raw_refs)
                all_traveler_refs.append(raw_refs)
            elif isinstance(raw_refs, list):
                for ref in raw_refs:
                    if ref:
                        unique_travelers.add(ref)
                        all_traveler_refs.append(ref)

        traveler_count = len(unique_travelers)
        contribution = amount * max(1, traveler_count)
        total_manual_calculation += contribution

        print(f"  OfferPrice {i+1}: {amount:,.2f} {curr} x {max(1, traveler_count)} unique travelers = {contribution:,.2f} {curr}")
        print(f"    All TravelerRefs: {all_traveler_refs}")
        print(f"    Unique TravelerRefs: {list(unique_travelers)}")
    
    print(f"\nMANUAL TOTAL CALCULATION: {total_manual_calculation:,.2f} {currency}")
    return total_manual_calculation, currency

def test_enhanced_transformer():
    """Test the enhanced air shopping transformer with multi-PTC pricing"""
    print("\n=== TESTING ENHANCED TRANSFORMER ===")
    
    # Load test data
    data = load_test_data()
    if not data:
        return False
    
    # Analyze original structure first
    manual_total, expected_currency = analyze_original_pricing_structure(data)
    if manual_total is None:
        return False
    
    # Initialize transformer with the response data
    transformer = EnhancedAirShoppingTransformer(data)

    # Transform the data
    try:
        transformed_data = transformer.transform_for_results()
        
        if not transformed_data:
            print("ERROR: Transformation failed - no data returned")
            return False

        print(f"Transformed data keys: {list(transformed_data.keys())}")

        # Check for different possible flight keys
        flights = None
        if 'flights' in transformed_data:
            flights = transformed_data['flights']
        elif 'offers' in transformed_data:
            flights = transformed_data['offers']
        elif isinstance(transformed_data, list):
            flights = transformed_data

        if not flights:
            print("ERROR: No flights/offers found in transformed data")
            return False
        
        # flights variable is already set above
        print(f"\nTransformed {len(flights)} flights")
        
        # Analyze the first few flights
        for i, flight in enumerate(flights[:3]):
            price_breakdown = flight.get('priceBreakdown', {})
            total_price = price_breakdown.get('totalPrice', 0)
            currency = price_breakdown.get('currency', 'Unknown')
            
            print(f"\nFlight {i+1}:")
            print(f"  Total Price: {total_price:,.2f} {currency}")
            
            # Check if this matches our manual calculation for the first flight
            if i == 0:
                print(f"\nCOMPARISON FOR FIRST FLIGHT:")
                print(f"  Manual Calculation: {manual_total:,.2f} {expected_currency}")
                print(f"  Transformer Result: {total_price:,.2f} {currency}")
                
                if abs(manual_total - total_price) < 1.0:  # Allow small rounding differences
                    print("  ✅ SUCCESS: Prices match!")
                    return True
                else:
                    print("  ❌ ERROR: Prices don't match!")
                    print(f"  Difference: {abs(manual_total - total_price):,.2f}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"ERROR during transformation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 TESTING MULTI-PTC PRICING AGGREGATION")
    print("=" * 50)
    
    success = test_enhanced_transformer()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("Multi-PTC pricing aggregation is working correctly.")
    else:
        print("\n❌ TESTS FAILED!")
        print("Multi-PTC pricing aggregation needs further investigation.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
