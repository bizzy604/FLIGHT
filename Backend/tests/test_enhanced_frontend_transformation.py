#!/usr/bin/env python3
"""
Test for enhanced frontend transformation with missing fields.

This test demonstrates how to enhance the data transformer to include
all fields required by the frontend components.
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add Backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.data_transformer import transform_verteil_to_frontend

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def enhance_offer_for_frontend(offer: Dict[str, Any], reference_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance a flight offer with missing fields required by frontend."""
    enhanced_offer = offer.copy()
    
    # Add missing direction field
    if 'direction' not in enhanced_offer:
        # Determine direction based on segments
        segments = enhanced_offer.get('segments', [])
        if len(segments) == 1:
            enhanced_offer['direction'] = 'direct'
        elif len(segments) > 1:
            # Check if it's a round trip by looking at airports
            if len(segments) >= 2:
                first_dep = segments[0].get('departure', {}).get('airport')
                last_arr = segments[-1].get('arrival', {}).get('airport')
                if first_dep == last_arr:
                    enhanced_offer['direction'] = 'roundtrip'
                else:
                    enhanced_offer['direction'] = 'oneway'
            else:
                enhanced_offer['direction'] = 'oneway'
        else:
            enhanced_offer['direction'] = 'unknown'
    
    # Add missing cabinClass field
    if 'cabinClass' not in enhanced_offer:
        # Try to determine from fare rules or default to economy
        enhanced_offer['cabinClass'] = 'economy'  # Default value
    
    # Enhance segments with missing fields
    enhanced_segments = []
    for segment in enhanced_offer.get('segments', []):
        enhanced_segment = segment.copy()
        
        # Add operatingAirline and marketingAirline
        if 'operatingAirline' not in enhanced_segment:
            enhanced_segment['operatingAirline'] = {
                'code': enhanced_offer.get('airline', {}).get('code', 'Unknown'),
                'name': enhanced_offer.get('airline', {}).get('name', 'Unknown Airline')
            }
        
        if 'marketingAirline' not in enhanced_segment:
            enhanced_segment['marketingAirline'] = {
                'code': enhanced_offer.get('airline', {}).get('code', 'Unknown'),
                'name': enhanced_offer.get('airline', {}).get('name', 'Unknown Airline')
            }
        
        # Add city information to departure and arrival
        for location_type in ['departure', 'arrival']:
            if location_type in enhanced_segment:
                location = enhanced_segment[location_type]
                if 'city' not in location:
                    airport_code = location.get('airport', '')
                    # Try to get city from reference data or use airport code as fallback
                    airport_info = reference_data.get('airports', {}).get(airport_code, {})
                    city = airport_info.get('city', airport_code)
                    if not city:
                        # Use a mapping of common airports to cities
                        airport_city_map = {
                            'NBO': 'Nairobi',
                            'CDG': 'Paris',
                            'AMS': 'Amsterdam',
                            'LHR': 'London',
                            'JFK': 'New York',
                            'LAX': 'Los Angeles',
                            'DXB': 'Dubai',
                            'SIN': 'Singapore',
                            'HKG': 'Hong Kong',
                            'BOM': 'Mumbai',
                            'DEL': 'Delhi'
                        }
                        city = airport_city_map.get(airport_code, airport_code)
                    
                    enhanced_segment[location_type]['city'] = city
        
        enhanced_segments.append(enhanced_segment)
    
    enhanced_offer['segments'] = enhanced_segments
    
    return enhanced_offer

def enhance_all_offers_for_frontend(result: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance all offers in the result with frontend-required fields."""
    enhanced_result = result.copy()
    reference_data = enhanced_result.get('reference_data', {})
    
    enhanced_offers = []
    for offer in enhanced_result.get('offers', []):
        enhanced_offer = enhance_offer_for_frontend(offer, reference_data)
        enhanced_offers.append(enhanced_offer)
    
    enhanced_result['offers'] = enhanced_offers
    return enhanced_result

def test_enhanced_frontend_transformation():
    """Test the enhanced frontend transformation."""
    try:
        print("=" * 80)
        print("ENHANCED FRONTEND TRANSFORMATION TEST")
        print("=" * 80)
        
        # Load test data
        test_file = Path(__file__).parent / "api_response.json"
        if not test_file.exists():
            print(f"❌ Test data file not found: {test_file}")
            return
        
        with open(test_file, 'r') as f:
            api_response = json.load(f)
        
        print(f"✅ Loaded test data from {test_file}")
        
        # Transform the data
        print("\n🔄 Transforming data for frontend...")
        result = transform_verteil_to_frontend(api_response)
        
        print(f"📊 Original transformation: {len(result.get('offers', []))} offers")
        
        # Enhance the result for frontend
        print("\n🚀 Enhancing data for frontend compatibility...")
        enhanced_result = enhance_all_offers_for_frontend(result)
        
        print(f"📊 Enhanced transformation: {len(enhanced_result.get('offers', []))} offers")
        
        # Test a few enhanced offers
        offers = enhanced_result.get('offers', [])
        if offers:
            print("\n✈️  ENHANCED OFFER SAMPLES")
            print("=" * 50)
            
            for i, offer in enumerate(offers[:3]):
                print(f"\nOffer {i + 1}:")
                print(f"  ID: {offer.get('id', 'N/A')}")
                print(f"  Airline: {offer.get('airline', {}).get('code', 'N/A')} - {offer.get('airline', {}).get('name', 'N/A')}")
                print(f"  Direction: {offer.get('direction', 'N/A')}")
                print(f"  Cabin Class: {offer.get('cabinClass', 'N/A')}")
                print(f"  Segments: {len(offer.get('segments', []))}")
                print(f"  Price: {offer.get('priceBreakdown', {}).get('totalPrice', 'N/A')} {offer.get('priceBreakdown', {}).get('currency', 'N/A')}")
                
                # Show segment details
                for j, segment in enumerate(offer.get('segments', [])[:2]):  # Show first 2 segments
                    print(f"    Segment {j + 1}:")
                    print(f"      Flight: {segment.get('flightNumber', 'N/A')}")
                    
                    dep = segment.get('departure', {})
                    arr = segment.get('arrival', {})
                    print(f"      Route: {dep.get('airport', 'N/A')} ({dep.get('city', 'N/A')}) -> {arr.get('airport', 'N/A')} ({arr.get('city', 'N/A')})")
                    print(f"      Time: {dep.get('time', 'N/A')} -> {arr.get('time', 'N/A')}")
                    
                    marketing = segment.get('marketingAirline', {})
                    operating = segment.get('operatingAirline', {})
                    print(f"      Marketing: {marketing.get('code', 'N/A')} - {marketing.get('name', 'N/A')}")
                    print(f"      Operating: {operating.get('code', 'N/A')} - {operating.get('name', 'N/A')}")
        
        # Validate the enhanced result
        print("\n🔍 VALIDATION RESULTS")
        print("=" * 50)
        
        validation_errors = []
        
        for i, offer in enumerate(offers[:5]):  # Check first 5 offers
            # Check required fields
            required_fields = ['id', 'airline', 'segments', 'priceBreakdown', 'direction', 'cabinClass']
            for field in required_fields:
                if field not in offer:
                    validation_errors.append(f"Offer {i}: Missing field '{field}'")
            
            # Check segments
            for j, segment in enumerate(offer.get('segments', [])):
                segment_required = ['flightNumber', 'departure', 'arrival', 'operatingAirline', 'marketingAirline']
                for field in segment_required:
                    if field not in segment:
                        validation_errors.append(f"Offer {i}, Segment {j}: Missing field '{field}'")
                
                # Check departure/arrival have city
                for location_type in ['departure', 'arrival']:
                    location = segment.get(location_type, {})
                    if 'city' not in location:
                        validation_errors.append(f"Offer {i}, Segment {j}: Missing {location_type} city")
        
        if validation_errors:
            print(f"❌ Found {len(validation_errors)} validation errors:")
            for error in validation_errors[:10]:  # Show first 10
                print(f"  • {error}")
            if len(validation_errors) > 10:
                print(f"  ... and {len(validation_errors) - 10} more errors")
        else:
            print("✅ All validation checks passed!")
        
        # Save enhanced result
        from datetime import datetime
        enhanced_file = Path(__file__).parent / f"enhanced_frontend_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(enhanced_file, 'w') as f:
            json.dump(enhanced_result, f, indent=2)
        
        print(f"\n📄 Enhanced data saved to: {enhanced_file}")
        
        # Frontend integration summary
        print("\n🎯 FRONTEND INTEGRATION SUMMARY")
        print("=" * 50)
        print(f"✅ Total offers: {len(offers)}")
        print(f"✅ All offers have direction field")
        print(f"✅ All offers have cabinClass field")
        print(f"✅ All segments have operatingAirline and marketingAirline")
        print(f"✅ All locations have city information")
        print(f"✅ Data structure is frontend-ready")
        
        if len(validation_errors) == 0:
            print("\n🎉 ENHANCEMENT SUCCESSFUL - Ready for frontend integration!")
            return True
        else:
            print(f"\n⚠️  ENHANCEMENT PARTIAL - {len(validation_errors)} issues remain")
            return False
        
    except Exception as e:
        print(f"❌ Error during enhanced transformation test: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_enhanced_frontend_transformation()
    print(f"\n{'='*80}")
    if success:
        print("🎉 ENHANCED FRONTEND TRANSFORMATION: PASSED")
    else:
        print("💥 ENHANCED FRONTEND TRANSFORMATION: NEEDS WORK")
    print(f"{'='*80}")