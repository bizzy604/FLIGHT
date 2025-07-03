#!/usr/bin/env python3
"""
Comprehensive unit tests for multi-airline support functionality.
Tests all components of the multi-airline implementation.
"""

import unittest
import json
import os
import sys

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor
from scripts.build_flightprice_rq import build_flight_price_request
from scripts.build_ordercreate_rq import (
    generate_order_create_rq,
    _is_multi_airline_flight_price_response,
    _extract_airline_from_flight_price_response,
    _filter_airline_specific_data_for_order_create
)
from services.flight.pricing import FlightPricingService
from services.flight.booking import FlightBookingService


class TestMultiAirlineSupport(unittest.TestCase):
    """Test suite for multi-airline support functionality."""

    @classmethod
    def setUpClass(cls):
        """Load test data once for all tests."""
        # Try to load the multi-airline test data
        possible_paths = [
            'postman/airshopingresponse.json',
            '../postman/airshopingresponse.json',
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'postman', 'airshopingresponse.json')
        ]
        
        cls.multi_airline_response = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    cls.multi_airline_response = json.load(f)
                break
        
        if cls.multi_airline_response is None:
            raise unittest.SkipTest("Multi-airline test data not found")
        
        # Create a mock single-airline response for comparison
        cls.single_airline_response = {
            "OffersGroup": {
                "AirlineOffers": [{
                    "Owner": {"value": "KQ"},
                    "AirlineOffer": [{
                        "OfferID": {"Owner": "KQ", "value": "SINGLE_OFFER_1"}
                    }]
                }]
            },
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [{
                        "ObjectKey": "PAX1",
                        "PTC": {"value": "ADT"}
                    }]
                },
                "FlightSegmentList": {
                    "FlightSegment": [{
                        "SegmentKey": "SEG1"
                    }]
                }
            },
            "Metadata": {
                "Shopping": {
                    "ShopMetadataGroup": [{
                        "Name": "ShoppingResponseID",
                        "MetadataKey": "SINGLE_RESPONSE_ID"
                    }]
                }
            }
        }

    def test_multi_airline_detection(self):
        """Test detection of multi-airline responses."""
        # Test multi-airline response detection
        is_multi = MultiAirlineDetector.is_multi_airline_response(self.multi_airline_response)
        self.assertTrue(is_multi, "Should detect multi-airline response")
        
        # Test single-airline response detection
        is_single = MultiAirlineDetector.is_multi_airline_response(self.single_airline_response)
        self.assertFalse(is_single, "Should detect single-airline response")

    def test_airline_code_extraction(self):
        """Test airline code extraction from responses."""
        # Test multi-airline code extraction
        airline_codes = MultiAirlineDetector.extract_airline_codes(self.multi_airline_response)
        self.assertIsInstance(airline_codes, list, "Should return a list of airline codes")
        self.assertGreater(len(airline_codes), 1, "Should find multiple airline codes")
        
        # Verify expected airlines are present
        expected_airlines = ['KL', 'LHG', 'AF', 'ET', 'QR', 'KQ', 'EK']
        for airline in expected_airlines:
            self.assertIn(airline, airline_codes, f"Should find airline {airline}")

    def test_reference_extraction(self):
        """Test airline-prefixed reference extraction."""
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        references = extractor.extract_references()

        # Test structure
        self.assertIn('type', references)
        self.assertEqual(references['type'], 'multi_airline')
        self.assertIn('airline_codes', references)
        self.assertIn('by_airline', references)

        # Test airline-specific references
        for airline_code in references['airline_codes']:
            self.assertIn(airline_code, references['by_airline'])
            airline_refs = references['by_airline'][airline_code]
            self.assertIn('passengers', airline_refs)
            self.assertIn('segments', airline_refs)

    def test_shopping_response_id_extraction(self):
        """Test extraction of airline-specific ShoppingResponseIDs."""
        shopping_ids = MultiAirlineDetector._extract_shopping_response_ids(self.multi_airline_response)
        
        self.assertIsInstance(shopping_ids, dict, "Should return a dictionary")
        self.assertGreater(len(shopping_ids), 1, "Should find multiple shopping response IDs")
        
        # Verify format: each ID should end with the airline code
        for airline_code, shopping_id in shopping_ids.items():
            self.assertTrue(shopping_id.endswith(f"-{airline_code}"), 
                          f"Shopping ID {shopping_id} should end with -{airline_code}")

    def test_flight_price_request_building(self):
        """Test FlightPrice request building for multi-airline."""
        # Test with different offer indices for different airlines
        test_cases = [
            (0, 'KL'),    # First KL offer
            (3, 'LHG'),   # First LHG offer  
            (81, 'AF'),   # First AF offer
            (168, 'QR'),  # First QR offer
        ]
        
        for offer_index, expected_airline in test_cases:
            with self.subTest(offer_index=offer_index, airline=expected_airline):
                payload = build_flight_price_request(
                    airshopping_response=self.multi_airline_response,
                    selected_offer_index=offer_index
                )
                
                # Verify payload structure
                self.assertIn('DataLists', payload)
                self.assertIn('ShoppingResponseID', payload)
                
                # Verify airline-specific filtering
                shopping_id = payload['ShoppingResponseID']
                if isinstance(shopping_id, dict) and 'Owner' in shopping_id:
                    self.assertEqual(shopping_id['Owner'], expected_airline)

    def test_flight_price_response_detection(self):
        """Test detection of multi-airline flight price responses."""
        # Create a mock multi-airline flight price response
        mock_multi_response = {
            "ShoppingResponseID": {
                "Owner": "KL",
                "ResponseID": {"value": "test-response-KL"}
            },
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [{
                        "ObjectKey": "KL-PAX1",
                        "PTC": {"value": "ADT"}
                    }]
                }
            }
        }
        
        # Create a mock single-airline flight price response
        mock_single_response = {
            "ShoppingResponseID": {"value": "simple-response"},
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [{
                        "ObjectKey": "PAX1",
                        "PTC": {"value": "ADT"}
                    }]
                }
            }
        }
        
        # Test detection
        is_multi = _is_multi_airline_flight_price_response(mock_multi_response)
        self.assertTrue(is_multi, "Should detect multi-airline flight price response")
        
        is_single = _is_multi_airline_flight_price_response(mock_single_response)
        self.assertFalse(is_single, "Should detect single-airline flight price response")

    def test_airline_extraction_from_flight_price(self):
        """Test airline code extraction from flight price responses."""
        mock_response = {
            "ShoppingResponseID": {
                "Owner": "KL",
                "ResponseID": {"value": "test-response-KL"}
            }
        }
        
        airline = _extract_airline_from_flight_price_response(mock_response)
        self.assertEqual(airline, "KL", "Should extract correct airline code")

    def test_order_create_data_filtering(self):
        """Test airline-specific data filtering for OrderCreate."""
        mock_flight_price_response = {
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [
                        {"ObjectKey": "KL-PAX1", "PTC": {"value": "ADT"}},
                        {"ObjectKey": "QR-PAX1", "PTC": {"value": "ADT"}},
                        {"ObjectKey": "AF-PAX1", "PTC": {"value": "ADT"}}
                    ]
                },
                "FlightSegmentList": {
                    "FlightSegment": [
                        {"SegmentKey": "KL-SEG1"},
                        {"SegmentKey": "QR-SEG1"}
                    ]
                }
            }
        }
        
        # Filter for KL airline
        filtered = _filter_airline_specific_data_for_order_create(mock_flight_price_response, "KL")
        
        # Verify filtering
        travelers = filtered['DataLists']['AnonymousTravelerList']['AnonymousTraveler']
        self.assertEqual(len(travelers), 1, "Should have only 1 KL traveler")
        self.assertEqual(travelers[0]['ObjectKey'], "PAX1", "Should transform KL-PAX1 to PAX1")
        
        segments = filtered['DataLists']['FlightSegmentList']['FlightSegment']
        self.assertEqual(len(segments), 1, "Should have only 1 KL segment")
        self.assertEqual(segments[0]['SegmentKey'], "SEG1", "Should transform KL-SEG1 to SEG1")

    def test_backward_compatibility(self):
        """Test that single-airline responses still work."""
        # Test single-airline detection
        is_multi = MultiAirlineDetector.is_multi_airline_response(self.single_airline_response)
        self.assertFalse(is_multi, "Should correctly identify single-airline response")

        # Test reference extraction for single-airline
        extractor = EnhancedReferenceExtractor(self.single_airline_response)
        references = extractor.extract_references()

        self.assertEqual(references['type'], 'single_airline', "Should mark as single-airline")
        self.assertIn('shopping_response_id', references)

    def test_end_to_end_flow(self):
        """Test the complete end-to-end multi-airline flow."""
        # Test with KL airline (offer index 0)
        offer_index = 0

        # Step 1: Build FlightPrice request
        flight_price_request = build_flight_price_request(
            airshopping_response=self.multi_airline_response,
            selected_offer_index=offer_index
        )

        self.assertIsNotNone(flight_price_request, "Should build FlightPrice request")

        # Step 2: Create mock FlightPrice response
        mock_flight_price_response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferID": {"Owner": "KL", "value": "TEST_OFFER"},
                    "OfferPrice": [{
                        "OfferItemID": {"Owner": "KL", "value": "TEST_ITEM"},
                        "RequestedDate": {
                            "PriceDetail": {
                                "TotalAmount": {
                                    "SimpleCurrencyPrice": {"Code": "USD", "value": 500.00}
                                }
                            },
                            "Associations": [{
                                "AssociatedTraveler": {"TravelerReferences": ["PAX1"]}
                            }]
                        }
                    }]
                }]
            },
            "DataLists": flight_price_request.get('DataLists', {}),
            "ShoppingResponseID": flight_price_request.get('ShoppingResponseID', {})
        }

        # Step 3: Build OrderCreate request
        passengers_data = [{
            "PTC": "ADT",
            "ObjectKey": "PAX1",
            "Individual": {"GivenName": ["John"], "Surname": "Doe"}
        }]

        payment_data = {"MethodType": "CASH", "Details": {"CashInd": True}}

        order_create_request = generate_order_create_rq(
            flight_price_response=mock_flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )

        # Verify OrderCreate structure
        self.assertIn('Query', order_create_request)
        query = order_create_request['Query']

        # Verify airline consistency
        shopping_response = query['OrderItems']['ShoppingResponse']
        self.assertEqual(shopping_response['Owner'], 'KL', "Should maintain KL airline throughout flow")

    def test_order_create_with_real_flight_price_responses(self):
        """Test OrderCreate generation using real FlightPrice response files."""
        # Test cases with real FlightPrice response files
        test_cases = [
            {
                'file': 'FlightPriceRS_AF.json',
                'airline': 'AF',
                'expected_travelers': ['PAX1', 'PAX2']
            },
            {
                'file': 'FlightPriceRS_KQ.json',
                'airline': 'KQ',
                'expected_travelers': ['PAX11']
            }
        ]

        for test_case in test_cases:
            with self.subTest(airline=test_case['airline']):
                # Load real FlightPrice response
                file_path = os.path.join(os.path.dirname(__file__), test_case['file'])
                with open(file_path, 'r') as f:
                    flight_price_response = json.load(f)

                # Create passenger data matching the response
                passengers_data = []
                for i, traveler_ref in enumerate(test_case['expected_travelers']):
                    passengers_data.append({
                        "PTC": "ADT",
                        "ObjectKey": traveler_ref,
                        "Individual": {
                            "GivenName": [f"Passenger{i+1}"],
                            "Surname": f"Test{i+1}",
                            "Birthdate": "1990-01-01",
                            "Gender": "Male"
                        },
                        "IdentityDocument": {
                            "IdentityDocumentNumber": f"P12345678{i}",
                            "IdentityDocumentType": "PT",
                            "IssuingCountryCode": "US",
                            "ExpiryDate": "2030-01-01"
                        }
                    })

                # Create payment data
                payment_data = {"MethodType": "CASH", "Details": {"CashInd": True}}

                # Generate OrderCreate request
                order_create_request = generate_order_create_rq(
                    flight_price_response=flight_price_response,
                    passengers_data=passengers_data,
                    payment_input_info=payment_data
                )

                # Validate the generated request
                self.assertIn('Query', order_create_request, f"OrderCreate should have Query section for {test_case['airline']}")

                query = order_create_request['Query']

                # Verify airline consistency
                shopping_response = query['OrderItems']['ShoppingResponse']
                self.assertEqual(shopping_response['Owner'], test_case['airline'],
                               f"Should maintain {test_case['airline']} airline throughout flow")

                # Verify passengers
                passengers = query.get('Passengers', {}).get('Passenger', [])
                if not isinstance(passengers, list):
                    passengers = [passengers] if passengers else []

                self.assertEqual(len(passengers), len(test_case['expected_travelers']),
                               f"Should have {len(test_case['expected_travelers'])} passengers for {test_case['airline']}")

                # Verify payments
                payments = query.get('Payments', {}).get('Payment', [])
                if not isinstance(payments, list):
                    payments = [payments] if payments else []

                self.assertGreater(len(payments), 0, f"Should have payments for {test_case['airline']}")

                # Verify ShoppingResponseID structure
                shopping_id = shopping_response.get('ResponseID', {}).get('value', '')
                self.assertTrue(shopping_id.endswith(f"-{test_case['airline']}"),
                              f"ShoppingResponseID should end with -{test_case['airline']}")

                print(f"✅ OrderCreate test passed for {test_case['airline']} with {len(passengers)} passengers")


def run_tests():
    """Run all multi-airline support tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMultiAirlineSupport)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"MULTI-AIRLINE UNIT TESTS SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
