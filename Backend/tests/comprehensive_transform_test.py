#!/usr/bin/env python3
"""
Comprehensive Test for transform_verteil_to_frontend

This test validates the transformation function with real API data and writes
detailed results to a file for manual cross-checking and validation.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add Backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.data_transformer import transform_verteil_to_frontend

def load_api_response(filename: str) -> Dict:
    """Load API response from JSON file"""
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_offer_details(offer: Dict) -> str:
    """Format offer details for readable output"""
    details = []
    details.append(f"  ID: {offer.get('id', 'N/A')}")
    details.append(f"  Direction: {offer.get('direction', 'N/A')}")
    
    # Airline information
    airline = offer.get('airline', {})
    details.append(f"  Airline Code: {airline.get('code', 'N/A')}")
    details.append(f"  Airline Name: {airline.get('name', 'N/A')}")
    details.append(f"  Airline Logo: {airline.get('logo', 'N/A')}")
    
    # Flight information
    flight = offer.get('flight', {})
    details.append(f"  Flight Number: {flight.get('number', 'N/A')}")
    details.append(f"  Aircraft: {flight.get('aircraft', 'N/A')}")
    
    # Route information
    route = offer.get('route', {})
    details.append(f"  Origin: {route.get('origin', 'N/A')}")
    details.append(f"  Destination: {route.get('destination', 'N/A')}")
    
    # Timing information
    timing = offer.get('timing', {})
    details.append(f"  Departure: {timing.get('departure', 'N/A')}")
    details.append(f"  Arrival: {timing.get('arrival', 'N/A')}")
    details.append(f"  Duration: {timing.get('duration', 'N/A')}")
    
    # Pricing information
    pricing = offer.get('pricing', {})
    details.append(f"  Base Price: {pricing.get('base_price', 'N/A')}")
    details.append(f"  Total Price: {pricing.get('total_price', 'N/A')}")
    details.append(f"  Currency: {pricing.get('currency', 'N/A')}")
    
    # Cabin and service information
    details.append(f"  Cabin Class: {offer.get('cabin_class', 'N/A')}")
    details.append(f"  Baggage: {offer.get('baggage', 'N/A')}")
    
    return "\n".join(details)

def analyze_reference_data(ref_data: Dict) -> str:
    """Analyze and format reference data"""
    analysis = []
    analysis.append("=== REFERENCE DATA ANALYSIS ===")
    
    # Airline reference data
    airlines = ref_data.get('airlines', {})
    analysis.append(f"Airlines found: {len(airlines)}")
    for code, info in airlines.items():
        if isinstance(info, dict):
            analysis.append(f"  {code}: {info.get('name', 'N/A')} (Logo: {info.get('logo', 'N/A')})")
        else:
            analysis.append(f"  {code}: {info} (type: {type(info)})")
    
    # Airport reference data
    airports = ref_data.get('airports', {})
    analysis.append(f"\nAirports found: {len(airports)}")
    for code, info in airports.items():
        if isinstance(info, dict):
            analysis.append(f"  {code}: {info.get('name', 'N/A')} ({info.get('city', 'N/A')})")
        else:
            analysis.append(f"  {code}: {info} (type: {type(info)})")
    
    # Aircraft reference data
    aircraft = ref_data.get('aircraft', {})
    analysis.append(f"\nAircraft found: {len(aircraft)}")
    for code, info in aircraft.items():
        if isinstance(info, dict):
            analysis.append(f"  {code}: {info.get('name', 'N/A')}")
        else:
            analysis.append(f"  {code}: {info} (type: {type(info)})")
    
    return "\n".join(analysis)

def run_comprehensive_test():
    """Run comprehensive test and write results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"transform_test_results_{timestamp}.txt"
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE TRANSFORM_VERTEIL_TO_FRONTEND TEST RESULTS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        try:
            # Load API response
            f.write("Loading API response data...\n")
            api_response = load_api_response('airshoping_response.json')
            f.write(f"✓ Successfully loaded API response\n")
            f.write(f"  Top-level keys: {list(api_response.keys())}\n\n")
            
            # Transform the data
            f.write("Transforming data with transform_verteil_to_frontend...\n")
            result = transform_verteil_to_frontend(api_response)
            f.write(f"✓ Transformation completed successfully\n")
            f.write(f"  Result type: {type(result)}\n")
            f.write(f"  Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}\n\n")
            
            # Extract offers and reference data
            offers = result.get('offers', []) if isinstance(result, dict) else result
            ref_data = result.get('reference_data', {}) if isinstance(result, dict) else {}
            
            f.write(f"TRANSFORMATION SUMMARY:\n")
            f.write(f"  Total offers created: {len(offers)}\n")
            f.write(f"  Reference data available: {'Yes' if ref_data else 'No'}\n\n")
            
            # Analyze reference data
            if ref_data:
                f.write(analyze_reference_data(ref_data) + "\n\n")
            
            # Analyze offers in detail
            f.write("=== DETAILED OFFER ANALYSIS ===\n\n")
            
            if offers:
                # Group offers by airline
                airline_groups = {}
                for offer in offers:
                    airline_code = offer.get('airline', {}).get('code', 'UNKNOWN')
                    if airline_code not in airline_groups:
                        airline_groups[airline_code] = []
                    airline_groups[airline_code].append(offer)
                
                f.write(f"Offers grouped by airline: {len(airline_groups)} airlines\n\n")
                
                for airline_code, airline_offers in airline_groups.items():
                    f.write(f"AIRLINE: {airline_code} ({len(airline_offers)} offers)\n")
                    f.write("-" * 50 + "\n")
                    
                    # Show first 3 offers for each airline
                    for i, offer in enumerate(airline_offers[:3]):
                        f.write(f"Offer {i+1}:\n")
                        f.write(format_offer_details(offer) + "\n\n")
                    
                    if len(airline_offers) > 3:
                        f.write(f"... and {len(airline_offers) - 3} more offers\n\n")
                
                # Statistical analysis
                f.write("=== STATISTICAL ANALYSIS ===\n")
                
                # Count by direction
                direction_counts = {}
                for offer in offers:
                    direction = offer.get('direction', 'unknown')
                    direction_counts[direction] = direction_counts.get(direction, 0) + 1
                
                f.write(f"Offers by direction:\n")
                for direction, count in direction_counts.items():
                    f.write(f"  {direction}: {count}\n")
                
                # Count by cabin class
                cabin_counts = {}
                for offer in offers:
                    cabin = offer.get('cabin_class', 'unknown')
                    cabin_counts[cabin] = cabin_counts.get(cabin, 0) + 1
                
                f.write(f"\nOffers by cabin class:\n")
                for cabin, count in cabin_counts.items():
                    f.write(f"  {cabin}: {count}\n")
                
                # Price analysis
                prices = []
                for offer in offers:
                    pricing = offer.get('pricing', {})
                    total_price = pricing.get('total_price')
                    if total_price and isinstance(total_price, (int, float)):
                        prices.append(total_price)
                
                if prices:
                    f.write(f"\nPrice analysis ({len(prices)} offers with valid prices):\n")
                    f.write(f"  Min price: {min(prices)}\n")
                    f.write(f"  Max price: {max(prices)}\n")
                    f.write(f"  Average price: {sum(prices) / len(prices):.2f}\n")
                
            else:
                f.write("❌ No offers were created from the transformation\n")
            
            # Validation checks
            f.write("\n=== VALIDATION CHECKS ===\n")
            
            validation_results = []
            
            # Check if offers have required fields
            required_fields = ['id', 'airline', 'flight', 'route', 'timing', 'pricing']
            for i, offer in enumerate(offers[:5]):  # Check first 5 offers
                missing_fields = [field for field in required_fields if field not in offer]
                if missing_fields:
                    validation_results.append(f"Offer {i+1} missing fields: {missing_fields}")
                else:
                    validation_results.append(f"Offer {i+1}: ✓ All required fields present")
            
            # Check airline code consistency
            airline_codes = set()
            for offer in offers:
                code = offer.get('airline', {}).get('code')
                if code:
                    airline_codes.add(code)
            
            validation_results.append(f"Unique airline codes found: {len(airline_codes)}")
            validation_results.append(f"Airline codes: {sorted(airline_codes)}")
            
            # Check for duplicate offer IDs
            offer_ids = [offer.get('id') for offer in offers if offer.get('id')]
            unique_ids = set(offer_ids)
            if len(offer_ids) != len(unique_ids):
                validation_results.append(f"❌ Duplicate offer IDs detected: {len(offer_ids)} total, {len(unique_ids)} unique")
            else:
                validation_results.append(f"✓ All offer IDs are unique ({len(unique_ids)} offers)")
            
            for result in validation_results:
                f.write(result + "\n")
            
        except Exception as e:
            f.write(f"❌ ERROR during test execution: {str(e)}\n")
            import traceback
            f.write(f"Traceback:\n{traceback.format_exc()}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("TEST COMPLETED\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n✓ Comprehensive test completed!")
    print(f"Results written to: {output_path}")
    print(f"\nYou can now review the detailed results in the output file.")
    
    return output_path

if __name__ == "__main__":
    print("Starting comprehensive transform_verteil_to_frontend test...")
    output_file = run_comprehensive_test()
    print(f"\nTest results available in: {output_file}")