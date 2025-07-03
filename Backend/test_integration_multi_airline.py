#!/usr/bin/env python3
"""
End-to-End Integration Testing for Multi-Airline Support
Tests the complete flow: Air Shopping → Flight Pricing → Order Creation

This test validates the entire multi-airline implementation using real data
and ensures seamless integration between all components.
"""

import os
import sys
import json
import time
import unittest
from typing import Dict, Any, List

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import multi-airline components
from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor
from scripts.build_flightprice_rq import build_flight_price_request
from scripts.build_ordercreate_rq import generate_order_create_rq


class TestMultiAirlineIntegration(unittest.TestCase):
    """End-to-end integration tests for multi-airline support."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for integration testing."""
        # Load multi-airline air shopping response
        airshopping_file = os.path.join(os.path.dirname(__file__), '..', 'postman', 'airshopingresponse.json')
        with open(airshopping_file, 'r') as f:
            cls.multi_airline_response = json.load(f)
        
        # Load real FlightPrice responses for testing
        cls.flight_price_responses = {}
        for airline in ['AF', 'KQ']:
            file_path = os.path.join(os.path.dirname(__file__), 'tests', f'FlightPriceRS_{airline}.json')
            with open(file_path, 'r') as f:
                cls.flight_price_responses[airline] = json.load(f)
        
        print(f"✅ Loaded multi-airline response with {len(cls.multi_airline_response.get('OffersGroup', {}).get('AirlineOffers', []))} airline offers")
        print(f"✅ Loaded FlightPrice responses for airlines: {list(cls.flight_price_responses.keys())}")

    def test_complete_multi_airline_flow(self):
        """Test the complete multi-airline flow from air shopping to order creation."""
        print("\n" + "="*80)
        print("TESTING COMPLETE MULTI-AIRLINE FLOW")
        print("="*80)
        
        # Test multiple airlines and offer indices
        test_cases = [
            {'airline': 'KL', 'offer_index': 0, 'description': 'KL first offer'},
            {'airline': 'LHG', 'offer_index': 3, 'description': 'LHG first offer'},
            {'airline': 'AF', 'offer_index': 81, 'description': 'AF first offer'},
            {'airline': 'QR', 'offer_index': 168, 'description': 'QR first offer'}
        ]
        
        results = []
        
        for test_case in test_cases:
            with self.subTest(airline=test_case['airline'], offer_index=test_case['offer_index']):
                print(f"\n--- Testing {test_case['description']} (Index: {test_case['offer_index']}) ---")
                
                start_time = time.time()
                
                # Step 1: Air Shopping Analysis
                detector = MultiAirlineDetector()
                is_multi_airline = detector.is_multi_airline_response(self.multi_airline_response)
                self.assertTrue(is_multi_airline, "Should detect multi-airline response")
                
                # Step 2: Reference Extraction
                extractor = EnhancedReferenceExtractor(self.multi_airline_response)
                references = extractor.extract_references()
                self.assertIn('type', references)
                self.assertEqual(references['type'], 'multi_airline')
                
                # Step 3: Flight Price Request Building
                flight_price_request = build_flight_price_request(
                    airshopping_response=self.multi_airline_response,
                    selected_offer_index=test_case['offer_index']
                )
                
                self.assertIsNotNone(flight_price_request, f"Should build FlightPrice request for {test_case['airline']}")
                self.assertIn('Query', flight_price_request)
                self.assertIn('DataLists', flight_price_request)
                
                # Verify airline consistency in request
                shopping_response_id = flight_price_request.get('Query', {}).get('ShoppingResponseID', {})
                response_id_value = shopping_response_id.get('ResponseID', {}).get('value', '')
                print(f"   ShoppingResponseID: {response_id_value}")
                # Note: The ShoppingResponseID structure may vary, so we'll validate the airline in OrderCreate instead
                
                # Step 4: Mock Flight Price Response (using real structure if available)
                if test_case['airline'] in self.flight_price_responses:
                    flight_price_response = self.flight_price_responses[test_case['airline']]
                    print(f"   Using real FlightPrice response for {test_case['airline']}")
                else:
                    # Create mock response with proper structure
                    flight_price_response = {
                        "PricedFlightOffers": {
                            "PricedFlightOffer": [{
                                "OfferID": {"Owner": test_case['airline'], "value": f"TEST_OFFER_{test_case['airline']}"},
                                "OfferPrice": [{
                                    "RequestedDate": {
                                        "PriceDetail": {
                                            "TotalAmount": {
                                                "SimpleCurrencyPrice": {"Code": "USD", "value": 750.00}
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
                        "ShoppingResponseID": flight_price_request.get('Query', {}).get('ShoppingResponseID', {})
                    }
                    print(f"   Using mock FlightPrice response for {test_case['airline']}")
                
                # Step 5: Order Creation
                passengers_data = [{
                    "PTC": "ADT",
                    "ObjectKey": "PAX1",
                    "Individual": {
                        "GivenName": ["John"],
                        "Surname": "Doe",
                        "Birthdate": "1990-01-01",
                        "Gender": "Male"
                    },
                    "IdentityDocument": {
                        "IdentityDocumentNumber": "P123456789",
                        "IdentityDocumentType": "PT",
                        "IssuingCountryCode": "US",
                        "ExpiryDate": "2030-01-01"
                    }
                }]
                
                payment_data = {"MethodType": "CASH", "Details": {"CashInd": True}}
                
                order_create_request = generate_order_create_rq(
                    flight_price_response=flight_price_response,
                    passengers_data=passengers_data,
                    payment_input_info=payment_data
                )
                
                # Step 6: Validation
                self.assertIn('Query', order_create_request, f"OrderCreate should have Query for {test_case['airline']}")
                
                query = order_create_request['Query']
                shopping_response = query['OrderItems']['ShoppingResponse']
                
                # Verify airline consistency throughout the flow
                self.assertEqual(shopping_response['Owner'], test_case['airline'],
                               f"Should maintain {test_case['airline']} airline throughout flow")
                
                # Verify passengers
                passengers = query.get('Passengers', {}).get('Passenger', [])
                if not isinstance(passengers, list):
                    passengers = [passengers] if passengers else []
                self.assertGreater(len(passengers), 0, f"Should have passengers for {test_case['airline']}")
                
                # Verify payments
                payments = query.get('Payments', {}).get('Payment', [])
                if not isinstance(payments, list):
                    payments = [payments] if payments else []
                self.assertGreater(len(payments), 0, f"Should have payments for {test_case['airline']}")
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Record results
                result = {
                    'airline': test_case['airline'],
                    'offer_index': test_case['offer_index'],
                    'processing_time': processing_time,
                    'passengers_count': len(passengers),
                    'payments_count': len(payments),
                    'success': True
                }
                results.append(result)
                
                print(f"   ✅ Flow completed in {processing_time:.3f}s")
                print(f"   ✅ Passengers: {len(passengers)}, Payments: {len(payments)}")
        
        # Summary
        print(f"\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"Total test cases: {len(results)}")
        print(f"Successful flows: {sum(1 for r in results if r['success'])}")
        if len(results) > 0:
            print(f"Average processing time: {sum(r['processing_time'] for r in results) / len(results):.3f}s")
            print(f"Airlines tested: {', '.join(set(r['airline'] for r in results))}")

        # All tests should pass
        self.assertEqual(len([r for r in results if r['success']]), len(test_cases),
                        "All integration flows should succeed")

    def test_performance_metrics(self):
        """Test performance metrics for multi-airline operations."""
        print("\n--- Testing Performance Metrics ---")

        # Test detection performance
        detector = MultiAirlineDetector()

        start_time = time.time()
        for _ in range(100):  # Run 100 times to get average
            is_multi_airline = detector.is_multi_airline_response(self.multi_airline_response)
        detection_time = (time.time() - start_time) / 100

        self.assertTrue(is_multi_airline, "Should detect multi-airline response")
        print(f"   ✅ Multi-airline detection: {detection_time*1000:.2f}ms average")

        # Test reference extraction performance
        start_time = time.time()
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        references = extractor.extract_references()
        extraction_time = time.time() - start_time

        self.assertIn('type', references)
        self.assertEqual(references['type'], 'multi_airline')
        print(f"   ✅ Reference extraction: {extraction_time*1000:.2f}ms")

        # Test flight price request building performance
        start_time = time.time()
        flight_price_request = build_flight_price_request(
            airshopping_response=self.multi_airline_response,
            selected_offer_index=0
        )
        build_time = time.time() - start_time

        self.assertIsNotNone(flight_price_request)
        print(f"   ✅ FlightPrice request building: {build_time*1000:.2f}ms")

        # Performance thresholds
        self.assertLess(detection_time, 0.01, "Detection should be under 10ms")
        self.assertLess(extraction_time, 0.1, "Extraction should be under 100ms")
        self.assertLess(build_time, 0.5, "Request building should be under 500ms")


if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)
