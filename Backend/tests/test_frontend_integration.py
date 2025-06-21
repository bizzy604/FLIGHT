#!/usr/bin/env python3
"""
Frontend Integration Test

This test demonstrates how the enhanced flight data can be consumed
by frontend components and validates the complete data flow.
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add Backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.data_transformer import transform_verteil_to_frontend

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlightCardComponent:
    """Simulates a frontend flight card component."""
    
    def __init__(self, offer_data: Dict[str, Any]):
        self.offer = offer_data
        self.is_valid = self._validate_data()
    
    def _validate_data(self) -> bool:
        """Validate that all required fields are present."""
        required_fields = [
            'id', 'airline', 'departure', 'arrival', 'duration',
            'price', 'currency', 'segments', 'direction', 'cabinClass'
        ]
        
        for field in required_fields:
            if field not in self.offer:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate segments
        for i, segment in enumerate(self.offer.get('segments', [])):
            segment_required = [
                'departure', 'arrival', 'flightNumber', 
                'operatingAirline', 'marketingAirline'
            ]
            for field in segment_required:
                if field not in segment:
                    logger.error(f"Segment {i}: Missing required field: {field}")
                    return False
            
            # Validate location data
            for location in ['departure', 'arrival']:
                loc_data = segment[location]
                if 'city' not in loc_data:
                    logger.error(f"Segment {i} {location}: Missing city information")
                    return False
        
        return True
    
    def render_summary(self) -> str:
        """Render a text summary of the flight card."""
        if not self.is_valid:
            return "❌ Invalid flight data"
        
        airline = self.offer['airline']
        dep = self.offer['departure']
        arr = self.offer['arrival']
        
        summary = f"""
┌─ Flight Card ─────────────────────────────────────────────┐
│ {airline['code']} {airline['name']:<45} │
│ {dep['airport']} ({dep['city']}) → {arr['airport']} ({arr['city']})                    │
│ Departure: {dep['time']} | Arrival: {arr['time']}           │
│ Duration: {self.offer['duration']:<10} | Stops: {self.offer.get('stops', 0):<10}     │
│ Direction: {self.offer['direction']:<10} | Class: {self.offer['cabinClass']:<10}     │
│ Price: {self.offer['price']} {self.offer['currency']:<30}                │
└───────────────────────────────────────────────────────────┘"""
        return summary
    
    def get_booking_data(self) -> Dict[str, Any]:
        """Extract data needed for booking process."""
        if not self.is_valid:
            return {}
        
        return {
            'offerId': self.offer['id'],
            'airline': self.offer['airline']['code'],
            'totalPrice': self.offer['price'],
            'currency': self.offer['currency'],
            'direction': self.offer['direction'],
            'cabinClass': self.offer['cabinClass'],
            'segments': [
                {
                    'flightNumber': seg['flightNumber'],
                    'departure': {
                        'airport': seg['departure']['airport'],
                        'city': seg['departure']['city'],
                        'time': seg['departure']['time']
                    },
                    'arrival': {
                        'airport': seg['arrival']['airport'],
                        'city': seg['arrival']['city'],
                        'time': seg['arrival']['time']
                    },
                    'operatingAirline': seg['operatingAirline']['code'],
                    'marketingAirline': seg['marketingAirline']['code']
                }
                for seg in self.offer['segments']
            ]
        }

class FlightSearchResults:
    """Simulates a frontend flight search results component."""
    
    def __init__(self, offers_data: List[Dict[str, Any]], reference_data: Dict[str, Any]):
        self.offers = offers_data
        self.reference_data = reference_data
        self.flight_cards = [FlightCardComponent(offer) for offer in offers_data]
        self.valid_cards = [card for card in self.flight_cards if card.is_valid]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search results statistics."""
        if not self.valid_cards:
            return {'total': 0, 'valid': 0, 'invalid': 0}
        
        prices = [card.offer['price'] for card in self.valid_cards]
        airlines = list(set(card.offer['airline']['code'] for card in self.valid_cards))
        directions = list(set(card.offer['direction'] for card in self.valid_cards))
        
        return {
            'total': len(self.offers),
            'valid': len(self.valid_cards),
            'invalid': len(self.offers) - len(self.valid_cards),
            'price_range': {
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0,
                'avg': sum(prices) / len(prices) if prices else 0
            },
            'airlines': airlines,
            'directions': directions,
            'airports': {
                'count': len(self.reference_data.get('airports', {})),
                'codes': list(self.reference_data.get('airports', {}).keys())[:10]
            }
        }
    
    def filter_by_price(self, max_price: float) -> List[FlightCardComponent]:
        """Filter flights by maximum price."""
        return [card for card in self.valid_cards if card.offer['price'] <= max_price]
    
    def filter_by_airline(self, airline_code: str) -> List[FlightCardComponent]:
        """Filter flights by airline."""
        return [card for card in self.valid_cards if card.offer['airline']['code'] == airline_code]
    
    def sort_by_price(self, ascending: bool = True) -> List[FlightCardComponent]:
        """Sort flights by price."""
        return sorted(self.valid_cards, key=lambda x: x.offer['price'], reverse=not ascending)

def test_frontend_integration():
    """Test complete frontend integration workflow."""
    try:
        print("=" * 80)
        print("FRONTEND INTEGRATION TEST")
        print("=" * 80)
        
        # Load test data
        test_file = Path(__file__).parent / "api_response.json"
        if not test_file.exists():
            print(f"❌ Test data file not found: {test_file}")
            return False
        
        with open(test_file, 'r') as f:
            api_response = json.load(f)
        
        print(f"✅ Loaded test data from {test_file}")
        
        # Transform data for frontend
        print("\n🔄 Transforming data for frontend...")
        result = transform_verteil_to_frontend(api_response)
        
        # Enhance data (simulate the enhancement we created earlier)
        from test_enhanced_frontend_transformation import enhance_all_offers_for_frontend
        enhanced_result = enhance_all_offers_for_frontend(result)
        
        print(f"📊 Enhanced {len(enhanced_result.get('offers', []))} offers for frontend")
        
        # Create frontend components
        print("\n🎨 Creating frontend components...")
        search_results = FlightSearchResults(
            enhanced_result.get('offers', []),
            enhanced_result.get('reference_data', {})
        )
        
        # Display statistics
        stats = search_results.get_statistics()
        print("\n📊 SEARCH RESULTS STATISTICS")
        print("=" * 50)
        print(f"Total offers: {stats['total']}")
        print(f"Valid offers: {stats['valid']}")
        print(f"Invalid offers: {stats['invalid']}")
        print(f"Price range: {stats['price_range']['min']:.0f} - {stats['price_range']['max']:.0f} (avg: {stats['price_range']['avg']:.0f})")
        print(f"Airlines: {', '.join(stats['airlines'][:5])}{'...' if len(stats['airlines']) > 5 else ''}")
        print(f"Directions: {', '.join(stats['directions'])}")
        print(f"Airports: {stats['airports']['count']} total")
        
        # Test flight card rendering
        print("\n✈️  FLIGHT CARD SAMPLES")
        print("=" * 50)
        
        valid_cards = search_results.valid_cards[:3]
        for i, card in enumerate(valid_cards):
            print(f"\nCard {i + 1}:")
            print(card.render_summary())
        
        # Test filtering and sorting
        print("\n🔍 FILTERING AND SORTING TESTS")
        print("=" * 50)
        
        # Price filter test
        max_price = stats['price_range']['avg']
        price_filtered = search_results.filter_by_price(max_price)
        print(f"Offers under {max_price:.0f}: {len(price_filtered)}")
        
        # Airline filter test
        if stats['airlines']:
            airline_code = stats['airlines'][0]
            airline_filtered = search_results.filter_by_airline(airline_code)
            print(f"Offers from {airline_code}: {len(airline_filtered)}")
        
        # Sort by price test
        sorted_cards = search_results.sort_by_price()
        if sorted_cards:
            cheapest = sorted_cards[0]
            most_expensive = sorted_cards[-1]
            print(f"Cheapest: {cheapest.offer['price']} {cheapest.offer['currency']}")
            print(f"Most expensive: {most_expensive.offer['price']} {most_expensive.offer['currency']}")
        
        # Test booking data extraction
        print("\n💳 BOOKING DATA EXTRACTION")
        print("=" * 50)
        
        if valid_cards:
            booking_data = valid_cards[0].get_booking_data()
            print(f"Sample booking data for offer {booking_data.get('offerId', 'N/A')[:20]}...")
            print(f"  Airline: {booking_data.get('airline')}")
            print(f"  Price: {booking_data.get('totalPrice')} {booking_data.get('currency')}")
            print(f"  Direction: {booking_data.get('direction')}")
            print(f"  Segments: {len(booking_data.get('segments', []))}")
        
        # Frontend readiness assessment
        print("\n🎯 FRONTEND READINESS ASSESSMENT")
        print("=" * 50)
        
        readiness_score = 0
        total_checks = 6
        
        # Check 1: Data transformation success
        if stats['valid'] > 0:
            print("✅ Data transformation: PASS")
            readiness_score += 1
        else:
            print("❌ Data transformation: FAIL")
        
        # Check 2: Required fields present
        if stats['invalid'] == 0:
            print("✅ Required fields: PASS")
            readiness_score += 1
        else:
            print(f"⚠️  Required fields: PARTIAL ({stats['invalid']} invalid offers)")
        
        # Check 3: Price data validity
        if stats['price_range']['min'] > 0 and stats['price_range']['max'] > 0:
            print("✅ Price data: PASS")
            readiness_score += 1
        else:
            print("❌ Price data: FAIL")
        
        # Check 4: Airline data completeness
        if len(stats['airlines']) > 0:
            print("✅ Airline data: PASS")
            readiness_score += 1
        else:
            print("❌ Airline data: FAIL")
        
        # Check 5: Reference data availability
        if stats['airports']['count'] > 0:
            print("✅ Reference data: PASS")
            readiness_score += 1
        else:
            print("❌ Reference data: FAIL")
        
        # Check 6: Component rendering
        if len(valid_cards) > 0 and all(card.is_valid for card in valid_cards[:5]):
            print("✅ Component rendering: PASS")
            readiness_score += 1
        else:
            print("❌ Component rendering: FAIL")
        
        # Final assessment
        readiness_percentage = (readiness_score / total_checks) * 100
        print(f"\n📈 OVERALL READINESS: {readiness_percentage:.1f}% ({readiness_score}/{total_checks})")
        
        if readiness_percentage >= 90:
            print("🎉 EXCELLENT - Ready for production frontend integration!")
            return True
        elif readiness_percentage >= 70:
            print("✅ GOOD - Ready for frontend integration with minor improvements")
            return True
        elif readiness_percentage >= 50:
            print("⚠️  FAIR - Needs improvements before frontend integration")
            return False
        else:
            print("❌ POOR - Significant work needed before frontend integration")
            return False
        
    except Exception as e:
        print(f"❌ Error during frontend integration test: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_frontend_integration()
    print(f"\n{'='*80}")
    if success:
        print("🎉 FRONTEND INTEGRATION TEST: PASSED")
    else:
        print("💥 FRONTEND INTEGRATION TEST: NEEDS WORK")
    print(f"{'='*80}")