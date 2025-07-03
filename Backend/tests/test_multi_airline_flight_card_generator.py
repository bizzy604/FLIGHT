"""
Unit tests for Multi-Airline Flight Card Generator

Tests the functionality of the MultiAirlineFlightCardGenerator class using real test data
and mock offers to verify enhanced flight card generation.

Author: FLIGHT Application
Created: 2025-07-02
"""

import json
import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.multi_airline_flight_card_generator import (
    MultiAirlineFlightCardGenerator,
    generate_enhanced_flight_cards
)


class TestMultiAirlineFlightCardGenerator(unittest.TestCase):
    """Test cases for MultiAirlineFlightCardGenerator class."""
    
    @classmethod
    def setUpClass(cls):
        """Load test data once for all tests."""
        # Load the multi-airline test data
        test_data_path = Path(__file__).parent.parent.parent / "postman" / "airshopingresponse.json"
        
        try:
            with open(test_data_path, 'r', encoding='utf-8') as f:
                cls.multi_airline_response = json.load(f)
            print(f"✅ Loaded test data from {test_data_path}")
        except FileNotFoundError:
            cls.fail(f"Test data file not found: {test_data_path}")
        except json.JSONDecodeError as e:
            cls.fail(f"Invalid JSON in test data file: {e}")
        
        # Create mock offers for testing
        cls.mock_offers = [
            {
                "id": "0",
                "offer_index": 0,
                "original_offer_id": "KL-OFFER-001",
                "price": 850.00,
                "currency": "USD",
                "airline": {
                    "code": "KL",
                    "name": "KLM Royal Dutch Airlines",
                    "logo": "/logos/kl.png",
                    "flightNumber": "KL1234"
                },
                "departure": {
                    "airport": "NBO",
                    "datetime": "2024-12-15T10:30:00",
                    "time": "10:30",
                    "terminal": "1A"
                },
                "arrival": {
                    "airport": "CDG",
                    "datetime": "2024-12-15T18:45:00",
                    "time": "18:45",
                    "terminal": "2E"
                },
                "duration": "8h15m",
                "stops": 0,
                "stopDetails": [],
                "segments": [
                    {
                        "departure": {"airport": "NBO", "datetime": "2024-12-15T10:30:00", "time": "10:30"},
                        "arrival": {"airport": "CDG", "datetime": "2024-12-15T18:45:00", "time": "18:45"},
                        "airline": {"code": "KL", "name": "KLM", "flightNumber": "KL1234"},
                        "aircraft": "B777",
                        "duration": "8h15m"
                    }
                ],
                "baggage": {"checked": {"pieces": 1, "weight": "23kg"}},
                "fare": {"type": "Economy", "refundable": False},
                "priceBreakdown": {
                    "baseFare": 680.00,
                    "taxes": 127.50,
                    "fees": 42.50,
                    "totalPrice": 850.00,
                    "currency": "USD"
                },
                "airline_context": {
                    "third_party_id": "KL",
                    "shopping_response_id": "KL-SHOP-123",
                    "is_supported": True,
                    "region": "Europe",
                    "supported_features": ["online_checkin", "seat_selection", "meal_selection"]
                }
            },
            {
                "id": "1",
                "offer_index": 1,
                "original_offer_id": "EK-OFFER-001",
                "price": 1200.00,
                "currency": "USD",
                "airline": {
                    "code": "EK",
                    "name": "Emirates",
                    "logo": "/logos/ek.png",
                    "flightNumber": "EK721"
                },
                "departure": {
                    "airport": "NBO",
                    "datetime": "2024-12-15T14:20:00",
                    "time": "14:20",
                    "terminal": "1A"
                },
                "arrival": {
                    "airport": "CDG",
                    "datetime": "2024-12-16T06:30:00",
                    "time": "06:30",
                    "terminal": "2A"
                },
                "duration": "12h10m",
                "stops": 1,
                "stopDetails": [{"airport": "DXB", "duration": "2h30m"}],
                "segments": [
                    {
                        "departure": {"airport": "NBO", "datetime": "2024-12-15T14:20:00", "time": "14:20"},
                        "arrival": {"airport": "DXB", "datetime": "2024-12-15T21:45:00", "time": "21:45"},
                        "airline": {"code": "EK", "name": "Emirates", "flightNumber": "EK721"},
                        "aircraft": "A380",
                        "duration": "4h25m"
                    },
                    {
                        "departure": {"airport": "DXB", "datetime": "2024-12-16T00:15:00", "time": "00:15"},
                        "arrival": {"airport": "CDG", "datetime": "2024-12-16T06:30:00", "time": "06:30"},
                        "airline": {"code": "EK", "name": "Emirates", "flightNumber": "EK73"},
                        "aircraft": "A380",
                        "duration": "7h45m"
                    }
                ],
                "baggage": {"checked": {"pieces": 2, "weight": "30kg"}},
                "fare": {"type": "Economy", "refundable": True},
                "priceBreakdown": {
                    "baseFare": 960.00,
                    "taxes": 180.00,
                    "fees": 60.00,
                    "totalPrice": 1200.00,
                    "currency": "USD"
                },
                "airline_context": {
                    "third_party_id": "EK",
                    "shopping_response_id": "EK-SHOP-456",
                    "is_supported": True,
                    "region": "Middle East",
                    "supported_features": ["online_checkin", "seat_selection", "meal_selection", "lounge_access", "wifi"]
                }
            }
        ]
        
        # Create a single-airline response for testing
        cls.single_airline_response = {
            "DataLists": {
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "SEG1",
                            "Departure": {"AirportCode": {"value": "NBO"}, "Date": "2024-12-15T10:30:00"},
                            "Arrival": {"AirportCode": {"value": "CDG"}, "Date": "2024-12-15T18:45:00"},
                            "MarketingCarrier": {"AirlineID": {"value": "KL"}}
                        }
                    ]
                }
            },
            "OffersGroup": {"AirlineOffers": []},
            "ShoppingResponseID": {"ResponseID": {"value": "test-shopping-id"}}
        }
    
    def test_multi_airline_initialization(self):
        """Test initialization with multi-airline response."""
        print("\n🧪 Testing multi-airline initialization...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        
        self.assertTrue(generator.is_multi_airline, "Should detect multi-airline response")
        self.assertEqual(generator.response, self.multi_airline_response, "Should store response")
        self.assertIsNotNone(generator.reference_extractor, "Should have reference extractor")
        self.assertIsNotNone(generator.refs, "Should have extracted references")
        
        print("✅ Multi-airline initialization working correctly")
    
    def test_single_airline_initialization(self):
        """Test initialization with single-airline response."""
        print("\n🧪 Testing single-airline initialization...")
        
        generator = MultiAirlineFlightCardGenerator(self.single_airline_response)
        
        self.assertFalse(generator.is_multi_airline, "Should detect single-airline response")
        self.assertEqual(generator.response, self.single_airline_response, "Should store response")
        
        print("✅ Single-airline initialization working correctly")
    
    def test_single_flight_card_generation(self):
        """Test generation of a single flight card."""
        print("\n🧪 Testing single flight card generation...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        
        # Test with KL offer
        kl_offer = self.mock_offers[0]
        flight_card = generator._generate_single_flight_card(kl_offer)
        
        self.assertIsNotNone(flight_card, "Should generate flight card")
        
        # Verify core structure
        required_fields = ['id', 'airline', 'departure', 'arrival', 'price', 'currency', 
                          'segments', 'airline_context', 'display_enhancements', 'compatibility']
        
        for field in required_fields:
            self.assertIn(field, flight_card, f"Flight card should have {field}")
        
        # Verify airline information
        airline = flight_card['airline']
        self.assertEqual(airline['code'], 'KL', "Should have correct airline code")
        self.assertIn('third_party_id', airline, "Should have ThirdParty ID")
        self.assertIn('supported_features', airline, "Should have supported features")
        
        # Verify airline context
        airline_context = flight_card['airline_context']
        self.assertIn('is_multi_airline_response', airline_context, "Should have multi-airline flag")
        self.assertIn('third_party_id', airline_context, "Should have ThirdParty ID")
        self.assertIn('airline_priority', airline_context, "Should have airline priority")
        
        # Verify display enhancements
        display = flight_card['display_enhancements']
        self.assertIn('airline_badge', display, "Should have airline badge")
        self.assertIn('price_confidence', display, "Should have price confidence")
        self.assertIn('recommendation_score', display, "Should have recommendation score")
        
        # Verify compatibility features
        compatibility = flight_card['compatibility']
        self.assertIsInstance(compatibility['supports_online_checkin'], bool, "Should have boolean compatibility flags")
        
        print("✅ Single flight card generation working correctly")
    
    def test_multi_airline_flight_cards_generation(self):
        """Test generation of multiple flight cards with multi-airline enhancements."""
        print("\n🧪 Testing multi-airline flight cards generation...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        flight_cards = generator.generate_flight_cards(self.mock_offers)
        
        self.assertEqual(len(flight_cards), 2, "Should generate 2 flight cards")
        
        # Verify multi-airline enhancements
        for card in flight_cards:
            self.assertIn('multi_airline_context', card, "Should have multi-airline context")
            
            multi_context = card['multi_airline_context']
            self.assertIn('total_airlines_in_response', multi_context, "Should have total airlines count")
            self.assertIn('airline_offer_count', multi_context, "Should have airline offer count")
            self.assertIn('airline_rank_by_price', multi_context, "Should have price rank")
            self.assertIn('competitive_advantages', multi_context, "Should have competitive advantages")
            
            # Verify display hints
            display_hints = card['display_enhancements']['multi_airline_hints']
            self.assertIn('show_airline_badge', display_hints, "Should have airline badge hint")
            self.assertIn('highlight_best_price', display_hints, "Should have best price hint")
        
        # Verify KL card has lowest price advantage
        kl_card = next(card for card in flight_cards if card['airline']['code'] == 'KL')
        self.assertIn('lowest_price', kl_card['multi_airline_context']['competitive_advantages'], 
                     "KL should have lowest price advantage")
        
        # Verify EK card has premium features
        ek_card = next(card for card in flight_cards if card['airline']['code'] == 'EK')
        self.assertGreater(len(ek_card['airline']['supported_features']), 
                          len(kl_card['airline']['supported_features']),
                          "EK should have more features than KL")
        
        print("✅ Multi-airline flight cards generation working correctly")
    
    def test_segment_enhancement(self):
        """Test segment enhancement with airline context."""
        print("\n🧪 Testing segment enhancement...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        
        # Test with EK offer (has multiple segments)
        ek_offer = self.mock_offers[1]
        segments = ek_offer['segments']
        enhanced_segments = generator._enhance_segments(segments, 'EK')
        
        self.assertEqual(len(enhanced_segments), 2, "Should have 2 enhanced segments")
        
        for segment in enhanced_segments:
            self.assertIn('airline_context', segment, "Should have airline context")
            
            context = segment['airline_context']
            self.assertIn('is_codeshare', context, "Should have codeshare flag")
            self.assertIn('operating_airline', context, "Should have operating airline")
            self.assertIn('third_party_id', context, "Should have ThirdParty ID")
            self.assertIn('is_supported', context, "Should have support flag")
        
        print("✅ Segment enhancement working correctly")
    
    def test_airline_priority_calculation(self):
        """Test airline priority calculation."""
        print("\n🧪 Testing airline priority calculation...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        
        # Test different airlines
        kl_priority = generator._calculate_airline_priority('KL')
        ek_priority = generator._calculate_airline_priority('EK')
        
        self.assertIsInstance(kl_priority, int, "Priority should be integer")
        self.assertIsInstance(ek_priority, int, "Priority should be integer")
        self.assertGreaterEqual(kl_priority, 1, "Priority should be at least 1")
        self.assertLessEqual(kl_priority, 10, "Priority should be at most 10")
        self.assertGreaterEqual(ek_priority, 1, "Priority should be at least 1")
        self.assertLessEqual(ek_priority, 10, "Priority should be at most 10")
        
        print(f"   ✅ KL Priority: {kl_priority}, EK Priority: {ek_priority}")
    
    def test_price_comparison(self):
        """Test price comparison functionality."""
        print("\n🧪 Testing price comparison...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        
        # Test with KL offer (lower price)
        kl_card = self.mock_offers[0]
        price_comparison = generator._get_price_comparison(kl_card, self.mock_offers)
        
        self.assertIn('is_lowest', price_comparison, "Should have lowest price flag")
        self.assertIn('vs_average', price_comparison, "Should have average comparison")
        self.assertIn('savings_vs_highest', price_comparison, "Should have savings calculation")
        
        self.assertTrue(price_comparison['is_lowest'], "KL should have lowest price")
        self.assertGreater(price_comparison['savings_vs_highest'], 0, "Should have savings vs highest")
        
        print(f"   ✅ Price comparison: {price_comparison}")
    
    def test_time_limits_generation(self):
        """Test time limits generation."""
        print("\n🧪 Testing time limits generation...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        
        # Test with different airlines
        kl_offer = self.mock_offers[0]
        ek_offer = self.mock_offers[1]
        
        kl_limits = generator._generate_time_limits(kl_offer, 'KL')
        ek_limits = generator._generate_time_limits(ek_offer, 'EK')
        
        # Verify structure
        required_fields = ['offer_expiration', 'payment_deadline', 'booking_deadline']
        for field in required_fields:
            self.assertIn(field, kl_limits, f"Should have {field}")
            self.assertIn(field, ek_limits, f"Should have {field}")
        
        # Verify times are in the future
        for limits in [kl_limits, ek_limits]:
            expiration = datetime.fromisoformat(limits['offer_expiration'])
            self.assertGreater(expiration, datetime.now(), "Expiration should be in future")
        
        print("✅ Time limits generation working correctly")
    
    def test_error_handling(self):
        """Test error handling with invalid offers."""
        print("\n🧪 Testing error handling...")
        
        generator = MultiAirlineFlightCardGenerator(self.multi_airline_response)
        
        # Test with empty offers
        empty_result = generator.generate_flight_cards([])
        self.assertEqual(empty_result, [], "Should handle empty offers")
        
        # Test with malformed offer
        malformed_offer = {"invalid": "structure"}
        result = generator.generate_flight_cards([malformed_offer])
        self.assertIsInstance(result, list, "Should return list even with malformed offers")
        
        print("✅ Error handling working correctly")
    
    def test_main_generation_function(self):
        """Test the main generation function."""
        print("\n🧪 Testing main generation function...")
        
        # Test with multi-airline response
        result = generate_enhanced_flight_cards(self.multi_airline_response, self.mock_offers)
        
        self.assertIsInstance(result, list, "Should return list")
        self.assertEqual(len(result), 2, "Should generate 2 cards")
        
        # Verify enhanced structure
        for card in result:
            self.assertIn('airline_context', card, "Should have airline context")
            self.assertIn('display_enhancements', card, "Should have display enhancements")
            self.assertIn('compatibility', card, "Should have compatibility info")
        
        print("✅ Main generation function working correctly")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing frontend."""
        print("\n🧪 Testing backward compatibility...")
        
        result = generate_enhanced_flight_cards(self.single_airline_response, [self.mock_offers[0]])
        
        if result:
            card = result[0]
            
            # Check required fields for existing frontend
            required_fields = ['id', 'airline', 'departure', 'arrival', 'price', 'currency', 
                             'duration', 'stops', 'segments']
            
            for field in required_fields:
                self.assertIn(field, card, f"Should have {field} for compatibility")
            
            # Check airline structure
            airline = card['airline']
            self.assertIn('code', airline, "Should have airline code")
            self.assertIn('name', airline, "Should have airline name")
            self.assertIn('logo', airline, "Should have airline logo")
        
        print("✅ Backward compatibility maintained")


def run_tests():
    """Run all tests and provide detailed output."""
    print("🚀 Starting Multi-Airline Flight Card Generator Tests")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMultiAirlineFlightCardGenerator)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("🎉 All tests passed successfully!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
