#!/usr/bin/env python3
"""
Comprehensive test for frontend data structure validation.

This test validates that the transform_verteil_to_frontend function returns
data in the exact format expected by the frontend components.
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

def validate_offer_structure(offer: Dict[str, Any], offer_index: int) -> List[str]:
    """Validate a single flight offer structure against frontend requirements."""
    errors = []
    
    # Required top-level fields for frontend
    required_fields = [
        'id', 'airline', 'segments', 'priceBreakdown', 'direction',
        'cabinClass', 'baggage', 'fareRules', 'duration', 'stops'
    ]
    
    for field in required_fields:
        if field not in offer:
            errors.append(f"Offer {offer_index}: Missing required field '{field}'")
    
    # Validate airline structure
    if 'airline' in offer:
        airline = offer['airline']
        if not isinstance(airline, dict):
            errors.append(f"Offer {offer_index}: 'airline' should be a dict, got {type(airline)}")
        else:
            airline_required = ['code', 'name', 'logo']
            for field in airline_required:
                if field not in airline:
                    errors.append(f"Offer {offer_index}: Missing airline field '{field}'")
    
    # Validate segments structure
    if 'segments' in offer:
        segments = offer['segments']
        if not isinstance(segments, list):
            errors.append(f"Offer {offer_index}: 'segments' should be a list, got {type(segments)}")
        elif len(segments) == 0:
            errors.append(f"Offer {offer_index}: 'segments' list is empty")
        else:
            for seg_idx, segment in enumerate(segments):
                segment_required = [
                    'flightNumber', 'departure', 'arrival', 'duration',
                    'aircraft', 'operatingAirline', 'marketingAirline'
                ]
                for field in segment_required:
                    if field not in segment:
                        errors.append(f"Offer {offer_index}, Segment {seg_idx}: Missing field '{field}'")
                
                # Validate departure/arrival structure
                for location_type in ['departure', 'arrival']:
                    if location_type in segment:
                        location = segment[location_type]
                        if not isinstance(location, dict):
                            errors.append(f"Offer {offer_index}, Segment {seg_idx}: '{location_type}' should be a dict")
                        else:
                            location_required = ['airport', 'city', 'time', 'terminal']
                            for field in location_required:
                                if field not in location:
                                    errors.append(f"Offer {offer_index}, Segment {seg_idx}: Missing {location_type} field '{field}'")
    
    # Validate priceBreakdown structure
    if 'priceBreakdown' in offer:
        price_breakdown = offer['priceBreakdown']
        if not isinstance(price_breakdown, dict):
            errors.append(f"Offer {offer_index}: 'priceBreakdown' should be a dict, got {type(price_breakdown)}")
        else:
            price_required = ['baseFare', 'taxes', 'fees', 'totalPrice', 'currency']
            for field in price_required:
                if field not in price_breakdown:
                    errors.append(f"Offer {offer_index}: Missing priceBreakdown field '{field}'")
    
    # Validate baggage structure
    if 'baggage' in offer:
        baggage = offer['baggage']
        if not isinstance(baggage, dict):
            errors.append(f"Offer {offer_index}: 'baggage' should be a dict, got {type(baggage)}")
        else:
            baggage_required = ['carryOn', 'checked']
            for field in baggage_required:
                if field not in baggage:
                    errors.append(f"Offer {offer_index}: Missing baggage field '{field}'")
    
    # Validate fareRules structure
    if 'fareRules' in offer:
        fare_rules = offer['fareRules']
        if not isinstance(fare_rules, dict):
            errors.append(f"Offer {offer_index}: 'fareRules' should be a dict, got {type(fare_rules)}")
        else:
            fare_rules_required = ['changeFee', 'refundable', 'exchangeable']
            for field in fare_rules_required:
                if field not in fare_rules:
                    errors.append(f"Offer {offer_index}: Missing fareRules field '{field}'")
    
    return errors

def validate_reference_data_structure(reference_data: Dict[str, Any]) -> List[str]:
    """Validate reference data structure."""
    errors = []
    
    # Expected reference data fields
    expected_fields = [
        'flights', 'segments', 'airports', 'aircraft', 'airlines',
        'carry_on_allowances', 'checked_bag_allowances', 'penalties'
    ]
    
    for field in expected_fields:
        if field not in reference_data:
            errors.append(f"Reference data: Missing field '{field}'")
        elif not isinstance(reference_data[field], dict):
            errors.append(f"Reference data: Field '{field}' should be a dict, got {type(reference_data[field])}")
    
    return errors

def analyze_frontend_compatibility(result: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the result for frontend compatibility and provide detailed insights."""
    analysis = {
        'structure_valid': True,
        'offers_count': 0,
        'errors': [],
        'warnings': [],
        'offer_samples': [],
        'reference_data_summary': {},
        'frontend_readiness': 'Unknown'
    }
    
    # Validate top-level structure
    if not isinstance(result, dict):
        analysis['errors'].append(f"Result should be a dict, got {type(result)}")
        analysis['structure_valid'] = False
        return analysis
    
    if 'offers' not in result:
        analysis['errors'].append("Missing 'offers' key in result")
        analysis['structure_valid'] = False
    
    if 'reference_data' not in result:
        analysis['errors'].append("Missing 'reference_data' key in result")
        analysis['structure_valid'] = False
    
    if not analysis['structure_valid']:
        return analysis
    
    # Validate offers
    offers = result['offers']
    if not isinstance(offers, list):
        analysis['errors'].append(f"'offers' should be a list, got {type(offers)}")
        analysis['structure_valid'] = False
    else:
        analysis['offers_count'] = len(offers)
        
        # Validate each offer
        for i, offer in enumerate(offers[:5]):  # Check first 5 offers
            offer_errors = validate_offer_structure(offer, i)
            analysis['errors'].extend(offer_errors)
            
            # Store sample offer for analysis
            if i < 3:  # Store first 3 offers as samples
                analysis['offer_samples'].append({
                    'index': i,
                    'id': offer.get('id', 'N/A'),
                    'airline_code': offer.get('airline', {}).get('code', 'N/A'),
                    'segments_count': len(offer.get('segments', [])),
                    'total_price': offer.get('priceBreakdown', {}).get('totalPrice', 'N/A'),
                    'currency': offer.get('priceBreakdown', {}).get('currency', 'N/A'),
                    'direction': offer.get('direction', 'N/A')
                })
    
    # Validate reference data
    reference_data = result['reference_data']
    ref_errors = validate_reference_data_structure(reference_data)
    analysis['errors'].extend(ref_errors)
    
    # Summarize reference data
    analysis['reference_data_summary'] = {
        'airlines_count': len(reference_data.get('airlines', {})),
        'airports_count': len(reference_data.get('airports', {})),
        'segments_count': len(reference_data.get('segments', {})),
        'flights_count': len(reference_data.get('flights', {})),
        'aircraft_count': len(reference_data.get('aircraft', {}))
    }
    
    # Determine frontend readiness
    if len(analysis['errors']) == 0:
        analysis['frontend_readiness'] = 'Ready'
    elif len(analysis['errors']) <= 5:
        analysis['frontend_readiness'] = 'Minor Issues'
    else:
        analysis['frontend_readiness'] = 'Major Issues'
    
    return analysis

def test_frontend_data_structure():
    """Main test function to validate frontend data structure."""
    try:
        print("=" * 80)
        print("FRONTEND DATA STRUCTURE VALIDATION TEST")
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
        
        # Analyze the result
        print("\n📊 Analyzing frontend compatibility...")
        analysis = analyze_frontend_compatibility(result)
        
        # Print results
        print(f"\n📈 ANALYSIS RESULTS")
        print(f"{'='*50}")
        print(f"Frontend Readiness: {analysis['frontend_readiness']}")
        print(f"Total Offers: {analysis['offers_count']}")
        print(f"Structure Valid: {analysis['structure_valid']}")
        print(f"Errors Found: {len(analysis['errors'])}")
        print(f"Warnings: {len(analysis['warnings'])}")
        
        # Reference data summary
        ref_summary = analysis['reference_data_summary']
        print(f"\n📚 REFERENCE DATA SUMMARY")
        print(f"{'='*50}")
        print(f"Airlines: {ref_summary['airlines_count']}")
        print(f"Airports: {ref_summary['airports_count']}")
        print(f"Flight Segments: {ref_summary['segments_count']}")
        print(f"Flights: {ref_summary['flights_count']}")
        print(f"Aircraft: {ref_summary['aircraft_count']}")
        
        # Sample offers
        if analysis['offer_samples']:
            print(f"\n✈️  SAMPLE OFFERS")
            print(f"{'='*50}")
            for sample in analysis['offer_samples']:
                print(f"Offer {sample['index'] + 1}:")
                print(f"  ID: {sample['id']}")
                print(f"  Airline: {sample['airline_code']}")
                print(f"  Segments: {sample['segments_count']}")
                print(f"  Price: {sample['total_price']} {sample['currency']}")
                print(f"  Direction: {sample['direction']}")
                print()
        
        # Errors and warnings
        if analysis['errors']:
            print(f"\n❌ ERRORS FOUND ({len(analysis['errors'])})")
            print(f"{'='*50}")
            for error in analysis['errors'][:10]:  # Show first 10 errors
                print(f"• {error}")
            if len(analysis['errors']) > 10:
                print(f"... and {len(analysis['errors']) - 10} more errors")
        
        if analysis['warnings']:
            print(f"\n⚠️  WARNINGS ({len(analysis['warnings'])})")
            print(f"{'='*50}")
            for warning in analysis['warnings']:
                print(f"• {warning}")
        
        # Frontend integration recommendations
        print(f"\n🎯 FRONTEND INTEGRATION RECOMMENDATIONS")
        print(f"{'='*50}")
        
        if analysis['frontend_readiness'] == 'Ready':
            print("✅ Data structure is fully compatible with frontend requirements")
            print("✅ All required fields are present and properly formatted")
            print("✅ Ready for frontend integration")
        elif analysis['frontend_readiness'] == 'Minor Issues':
            print("⚠️  Minor issues detected - frontend may work with fallbacks")
            print("🔧 Consider adding null checks and default values in frontend")
        else:
            print("❌ Major issues detected - frontend integration will likely fail")
            print("🔧 Fix data transformation issues before frontend integration")
        
        # Write detailed results to file
        results_file = Path(__file__).parent / f"frontend_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'analysis': analysis,
                'sample_offers': analysis['offer_samples'],
                'reference_data_summary': analysis['reference_data_summary'],
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return analysis['frontend_readiness'] == 'Ready'
        
    except Exception as e:
        print(f"❌ Error during frontend validation test: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    from datetime import datetime
    success = test_frontend_data_structure()
    print(f"\n{'='*80}")
    if success:
        print("🎉 FRONTEND DATA STRUCTURE VALIDATION: PASSED")
    else:
        print("💥 FRONTEND DATA STRUCTURE VALIDATION: FAILED")
    print(f"{'='*80}")