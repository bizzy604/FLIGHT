"""
Unit tests for Enhanced Air Shopping Response Transformer

Tests the functionality of the EnhancedAirShoppingTransformer class using real test data
from the air shopping response.

Author: FLIGHT Application
Created: 2025-07-02
"""

import json
import unittest
import sys
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from transformers.enhanced_air_shopping_transformer import (
    EnhancedAirShoppingTransformer,
    transform_air_shopping_for_results_enhanced
)


class TestEnhancedAirShoppingTransformer(unittest.TestCase):
    """Test cases for EnhancedAirShoppingTransformer class."""
    
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
        
        # Create a mock single-airline response for testing
        cls.single_airline_response = {
            "DataLists": {
                "FlightSegmentList": {
                    "FlightSegment": [
                        {
                            "SegmentKey": "SEG1",
                            "Departure": {
                                "AirportCode": {"value": "NBO"},
                                "Date": "2024-12-15T10:30:00",
                                "Terminal": {"Name": "1A"}
                            },
                            "Arrival": {
                                "AirportCode": {"value": "CDG"},
                                "Date": "2024-12-15T18:45:00",
                                "Terminal": {"Name": "2E"}
                            },
                            "MarketingCarrier": {
                                "AirlineID": {"value": "KL"},
                                "FlightNumber": {"value": "1234"}
                            },
                            "Equipment": {"AircraftCode": {"value": "B777"}},
                            "FlightDetail": {"FlightDuration": {"value": "8h15m"}}
                        }
                    ]
                }
            },
            "OffersGroup": {
                "AirlineOffers": [
                    {
                        "AirlineOffer": [
                            {
                                "OfferID": {"value": "OFFER1", "Owner": "KL"},
                                "PricedOffer": {
                                    "OfferPrice": [
                                        {
                                            "RequestedDate": {
                                                "PriceDetail": {
                                                    "TotalAmount": {
                                                        "SimpleCurrencyPrice": {
                                                            "value": 850.00,
                                                            "Code": "USD"
                                                        }
                                                    }
                                                },
                                                "Associations": [
                                                    {
                                                        "ApplicableFlight": {
                                                            "FlightSegmentReference": [
                                                                {"ref": "SEG1"}
                                                            ]
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-shopping-id"}
            }
        }
    
    def test_multi_airline_initialization(self):
        """Test initialization with multi-airline response."""
        print("\n🧪 Testing multi-airline initialization...")
        
        transformer = EnhancedAirShoppingTransformer(self.multi_airline_response)
        
        self.assertTrue(transformer.is_multi_airline, "Should detect multi-airline response")
        self.assertEqual(transformer.response, self.multi_airline_response, "Should store response")
        self.assertIsNotNone(transformer.reference_extractor, "Should have reference extractor")
        self.assertIsNotNone(transformer.refs, "Should have extracted references")
        
        print("✅ Multi-airline initialization working correctly")
    
    def test_single_airline_initialization(self):
        """Test initialization with single-airline response."""
        print("\n🧪 Testing single-airline initialization...")
        
        transformer = EnhancedAirShoppingTransformer(self.single_airline_response)
        
        self.assertFalse(transformer.is_multi_airline, "Should detect single-airline response")
        self.assertEqual(transformer.response, self.single_airline_response, "Should store response")
        
        print("✅ Single-airline initialization working correctly")
    
    def test_multi_airline_transformation(self):
        """Test transformation for multi-airline response."""
        print("\n🧪 Testing multi-airline transformation...")
        
        transformer = EnhancedAirShoppingTransformer(self.multi_airline_response)
        result = transformer.transform_for_results()
        
        # Verify structure
        self.assertIn('offers', result, "Should have offers")
        self.assertIn('raw_response', result, "Should have raw response")
        self.assertIn('metadata', result, "Should have metadata")
        
        # Verify metadata
        metadata = result['metadata']
        self.assertTrue(metadata['is_multi_airline'], "Metadata should indicate multi-airline")
        self.assertGreater(metadata['airline_count'], 1, "Should have multiple airlines")
        self.assertIn('supported_airlines', metadata, "Should have supported airlines")
        self.assertIn('shopping_response_ids', metadata, "Should have shopping response IDs")
        
        # Verify offers
        offers = result['offers']
        self.assertIsInstance(offers, list, "Offers should be a list")
        
        if offers:
            # Check first offer structure
            first_offer = offers[0]
            required_fields = ['id', 'price', 'currency', 'airline', 'departure', 'arrival', 
                             'duration', 'stops', 'segments', 'airline_context']
            
            for field in required_fields:
                self.assertIn(field, first_offer, f"Offer should have {field}")
            
            # Verify airline context
            airline_context = first_offer['airline_context']
            self.assertIn('third_party_id', airline_context, "Should have ThirdParty ID")
            self.assertIn('shopping_response_id', airline_context, "Should have shopping response ID")
            self.assertIn('is_supported', airline_context, "Should have support status")
            
            # Verify offer indexing
            for i, offer in enumerate(offers):
                self.assertEqual(offer['id'], str(i), f"Offer {i} should have correct ID")
                self.assertEqual(offer['offer_index'], i, f"Offer {i} should have correct index")
        
        print(f"✅ Multi-airline transformation successful: {len(offers)} offers")
        print(f"   Airlines: {metadata.get('supported_airlines', [])}")
    
    def test_single_airline_transformation(self):
        """Test transformation for single-airline response."""
        print("\n🧪 Testing single-airline transformation...")
        
        transformer = EnhancedAirShoppingTransformer(self.single_airline_response)
        result = transformer.transform_for_results()
        
        # Verify structure
        self.assertIn('offers', result, "Should have offers")
        self.assertIn('raw_response', result, "Should have raw response")
        self.assertIn('metadata', result, "Should have metadata")
        
        # Verify metadata
        metadata = result['metadata']
        self.assertFalse(metadata['is_multi_airline'], "Metadata should indicate single-airline")
        self.assertEqual(metadata['airline_count'], 1, "Should have one airline")
        
        # Verify offers
        offers = result['offers']
        self.assertIsInstance(offers, list, "Offers should be a list")
        self.assertEqual(len(offers), 1, "Should have one offer")
        
        # Check offer structure
        offer = offers[0]
        self.assertEqual(offer['airline']['code'], 'KL', "Should have correct airline code")
        self.assertEqual(offer['price'], 850.00, "Should have correct price")
        self.assertEqual(offer['currency'], 'USD', "Should have correct currency")
        self.assertIn('airline_context', offer, "Should have airline context")
        
        print("✅ Single-airline transformation working correctly")
    
    def test_airline_context_enhancement(self):
        """Test airline context enhancement in offers."""
        print("\n🧪 Testing airline context enhancement...")
        
        transformer = EnhancedAirShoppingTransformer(self.multi_airline_response)
        result = transformer.transform_for_results()
        
        offers = result['offers']
        if offers:
            for offer in offers[:3]:  # Test first 3 offers
                airline_context = offer['airline_context']
                airline_code = offer['airline']['code']
                
                # Verify ThirdParty ID mapping
                self.assertIsInstance(airline_context['third_party_id'], str, 
                                    f"ThirdParty ID should be string for {airline_code}")
                self.assertGreater(len(airline_context['third_party_id']), 0, 
                                 f"ThirdParty ID should not be empty for {airline_code}")
                
                # Verify support status
                self.assertIsInstance(airline_context['is_supported'], bool, 
                                    f"Support status should be boolean for {airline_code}")
                
                # Verify shopping response ID
                if airline_context['shopping_response_id']:
                    self.assertIsInstance(airline_context['shopping_response_id'], str, 
                                        f"Shopping response ID should be string for {airline_code}")
                
                # Verify supported features
                self.assertIsInstance(airline_context['supported_features'], list, 
                                    f"Supported features should be list for {airline_code}")
                
                print(f"   ✅ {airline_code}: ThirdParty={airline_context['third_party_id']}, "
                      f"Supported={airline_context['is_supported']}")
        
        print("✅ Airline context enhancement working correctly")
    
    def test_offer_sorting_and_indexing(self):
        """Test offer sorting by price and proper indexing."""
        print("\n🧪 Testing offer sorting and indexing...")
        
        transformer = EnhancedAirShoppingTransformer(self.multi_airline_response)
        result = transformer.transform_for_results()
        
        offers = result['offers']
        if len(offers) > 1:
            # Verify sorting by price (ascending)
            for i in range(len(offers) - 1):
                current_price = float(offers[i]['price'])
                next_price = float(offers[i + 1]['price'])
                self.assertLessEqual(current_price, next_price, 
                                   f"Offers should be sorted by price: {current_price} <= {next_price}")
            
            # Verify indexing
            for i, offer in enumerate(offers):
                self.assertEqual(offer['id'], str(i), f"Offer {i} should have ID '{i}'")
                self.assertEqual(offer['offer_index'], i, f"Offer {i} should have index {i}")
        
        print(f"✅ Offer sorting and indexing working correctly for {len(offers)} offers")
    
    def test_error_handling(self):
        """Test error handling with invalid responses."""
        print("\n🧪 Testing error handling...")
        
        # Test with empty response
        empty_transformer = EnhancedAirShoppingTransformer({})
        empty_result = empty_transformer.transform_for_results()
        
        self.assertIn('offers', empty_result, "Should have offers field")
        self.assertEqual(empty_result['offers'], [], "Should have empty offers list")
        self.assertIn('metadata', empty_result, "Should have metadata")
        
        # Test with malformed response
        malformed_response = {"invalid": "structure"}
        malformed_transformer = EnhancedAirShoppingTransformer(malformed_response)
        malformed_result = malformed_transformer.transform_for_results()
        
        self.assertIn('offers', malformed_result, "Should handle malformed response")
        self.assertEqual(malformed_result['offers'], [], "Should return empty offers for malformed response")
        
        print("✅ Error handling working correctly")
    
    def test_airline_statistics(self):
        """Test airline statistics generation."""
        print("\n🧪 Testing airline statistics...")
        
        # Test multi-airline statistics
        transformer = EnhancedAirShoppingTransformer(self.multi_airline_response)
        stats = transformer.get_airline_statistics()
        
        self.assertIn('total_airlines', stats, "Should have total airlines count")
        self.assertIn('supported_airlines', stats, "Should have supported airlines count")
        self.assertIn('airline_codes', stats, "Should have airline codes list")
        self.assertIn('supported_codes', stats, "Should have supported codes list")
        
        self.assertGreater(stats['total_airlines'], 1, "Should have multiple airlines")
        self.assertGreater(stats['supported_airlines'], 0, "Should have supported airlines")
        
        # Test single-airline statistics
        single_transformer = EnhancedAirShoppingTransformer(self.single_airline_response)
        single_stats = single_transformer.get_airline_statistics()
        
        self.assertEqual(single_stats['total_airlines'], 1, "Should have one airline")
        self.assertEqual(single_stats['supported_airlines'], 1, "Should have one supported airline")
        self.assertTrue(single_stats['is_single_airline'], "Should indicate single airline")
        
        print(f"✅ Multi-airline stats: {stats['total_airlines']} total, {stats['supported_airlines']} supported")
        print(f"✅ Single-airline stats: {single_stats['total_airlines']} total")
    
    def test_main_transformation_function(self):
        """Test the main transformation function."""
        print("\n🧪 Testing main transformation function...")
        
        # Test with multi-airline response
        result = transform_air_shopping_for_results_enhanced(self.multi_airline_response)
        
        self.assertIn('offers', result, "Should have offers")
        self.assertIn('metadata', result, "Should have metadata")
        self.assertTrue(result['metadata']['is_multi_airline'], "Should detect multi-airline")
        
        # Test with single-airline response
        single_result = transform_air_shopping_for_results_enhanced(self.single_airline_response)
        
        self.assertIn('offers', single_result, "Should have offers")
        self.assertIn('metadata', single_result, "Should have metadata")
        self.assertFalse(single_result['metadata']['is_multi_airline'], "Should detect single-airline")
        
        print("✅ Main transformation function working correctly")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing structure."""
        print("\n🧪 Testing backward compatibility...")
        
        result = transform_air_shopping_for_results_enhanced(self.single_airline_response)
        
        # Verify the result has the expected structure for existing frontend
        self.assertIn('offers', result, "Should have offers for compatibility")
        self.assertIn('raw_response', result, "Should have raw_response for compatibility")
        
        offers = result['offers']
        if offers:
            offer = offers[0]
            
            # Check required fields for existing frontend
            required_fields = ['id', 'price', 'currency', 'airline', 'departure', 
                             'arrival', 'duration', 'stops', 'segments']
            
            for field in required_fields:
                self.assertIn(field, offer, f"Should have {field} for compatibility")
            
            # Check airline structure
            airline = offer['airline']
            self.assertIn('code', airline, "Should have airline code")
            self.assertIn('name', airline, "Should have airline name")
            self.assertIn('logo', airline, "Should have airline logo")
        
        print("✅ Backward compatibility maintained")


def run_tests():
    """Run all tests and provide detailed output."""
    print("🚀 Starting Enhanced Air Shopping Transformer Tests")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedAirShoppingTransformer)
    
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
