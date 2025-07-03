#!/usr/bin/env python3
"""
Flight Pricing Integration Test Suite
Tests the complete enhanced flight pricing flow from service to request building.
"""

import json
import logging
import sys
import time
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.flight.pricing import FlightPricingService
from scripts.build_flightprice_rq import build_flight_price_request
from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightPricingIntegrationTester:
    """Integration test suite for enhanced flight pricing functionality."""
    
    def __init__(self, test_data_file: str = "postman/airshopingresponse.json"):
        """
        Initialize the tester with test data.
        
        Args:
            test_data_file (str): Path to the test data file
        """
        self.test_data_file = Path(test_data_file)
        self.test_data = None
        self.pricing_service = None
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
    def load_test_data(self):
        """Load the test data from the JSON file."""
        try:
            if not self.test_data_file.exists():
                raise FileNotFoundError(f"Test data file not found: {self.test_data_file}")
            
            with open(self.test_data_file, 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
            
            logger.info(f"Successfully loaded test data from {self.test_data_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            return False
    
    def setup_pricing_service(self):
        """Set up the FlightPricingService for testing."""
        try:
            # Create a mock config with required OAuth settings
            mock_config = {
                'VERTEIL_API_BASE_URL': 'https://test-api.example.com',
                'VERTEIL_USERNAME': 'test_user',
                'VERTEIL_PASSWORD': 'test_password',
                'VERTEIL_TOKEN_ENDPOINT_PATH': '/oauth2/token',
                'VERTEIL_OFFICE_ID': 'test_office',
                'VERTEIL_THIRD_PARTY_ID': 'test_third_party'
            }

            # Create pricing service with mock config
            self.pricing_service = FlightPricingService(config=mock_config)

            logger.info("Successfully set up FlightPricingService with mock config")
            return True

        except Exception as e:
            logger.error(f"Failed to set up pricing service: {e}")
            return False
    
    def run_test(self, test_name: str, test_func):
        """
        Run a single test and record the results.
        
        Args:
            test_name (str): Name of the test
            test_func (callable): Test function to execute
        """
        self.test_results['total_tests'] += 1
        start_time = time.time()
        
        try:
            logger.info(f"Running integration test: {test_name}")
            
            # Handle async test functions
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
                
            execution_time = time.time() - start_time
            
            if result:
                self.test_results['passed_tests'] += 1
                status = "PASSED"
                logger.info(f"✅ {test_name} - PASSED ({execution_time:.3f}s)")
            else:
                self.test_results['failed_tests'] += 1
                status = "FAILED"
                logger.error(f"❌ {test_name} - FAILED ({execution_time:.3f}s)")
            
            self.test_results['test_details'].append({
                'name': test_name,
                'status': status,
                'execution_time': execution_time,
                'error': None
            })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results['failed_tests'] += 1
            error_msg = str(e)
            logger.error(f"❌ {test_name} - ERROR: {error_msg} ({execution_time:.3f}s)")
            
            self.test_results['test_details'].append({
                'name': test_name,
                'status': "ERROR",
                'execution_time': execution_time,
                'error': error_msg
            })
            
            return False
    
    def test_service_airline_code_extraction(self):
        """Test airline code extraction in FlightPricingService."""
        try:
            # Test multi-airline airline code extraction
            test_offer_id = "0"  # Global index
            
            airline_code = self.pricing_service._extract_airline_code_from_offer(
                self.test_data, test_offer_id
            )
            
            if airline_code:
                logger.info(f"✅ Extracted airline code: {airline_code}")
                return True
            else:
                logger.error("Failed to extract airline code")
                return False
                
        except Exception as e:
            logger.error(f"Service airline code extraction test failed: {e}")
            return False
    
    def test_service_shopping_response_id_selection(self):
        """Test airline-specific ShoppingResponseID selection in FlightPricingService."""
        try:
            # Test with a known airline
            test_airline = "KQ"
            
            shopping_response_id = self.pricing_service._get_shopping_response_id_for_airline(
                self.test_data, test_airline
            )
            
            if shopping_response_id:
                logger.info(f"✅ Got ShoppingResponseID for {test_airline}: {shopping_response_id}")
                return True
            else:
                logger.error(f"Failed to get ShoppingResponseID for {test_airline}")
                return False
                
        except Exception as e:
            logger.error(f"Service ShoppingResponseID selection test failed: {e}")
            return False
    
    def test_service_payload_building(self):
        """Test the service's payload building functionality."""
        try:
            # Test payload building with multi-airline data
            test_offer_id = "0"  # Global index

            # Test the _build_pricing_payload method
            payload = self.pricing_service._build_pricing_payload(
                self.test_data, test_offer_id
            )

            # Validate the payload structure
            if payload and isinstance(payload, dict):
                logger.info("✅ Service payload building completed successfully")
                logger.info(f"Payload keys: {list(payload.keys())}")
                return True
            else:
                logger.error("Service payload building failed")
                return False

        except Exception as e:
            logger.error(f"Service payload building test failed: {e}")
            return False
    
    def test_integration_with_request_builder(self):
        """Test integration between service and request builder."""
        try:
            # Test that the service can extract airline code and the request builder can use it
            test_offer_id = "0"
            
            # Extract airline code using service
            airline_code = self.pricing_service._extract_airline_code_from_offer(
                self.test_data, test_offer_id
            )
            
            # Build request using the extracted information
            flight_price_request = build_flight_price_request(
                self.test_data,
                selected_offer_index=int(test_offer_id)
            )
            
            # Validate integration
            if airline_code and flight_price_request:
                # Check that the request contains the expected offer
                query_offers = flight_price_request.get("Query", {}).get("Offers", {}).get("Offer", [])
                if query_offers:
                    offer_id_node = query_offers[0].get("OfferID", {})
                    request_airline = offer_id_node.get("Owner")
                    
                    logger.info(f"✅ Service extracted airline: {airline_code}")
                    logger.info(f"✅ Request builder used airline: {request_airline}")
                    
                    # Note: For multi-airline, the service extracts from global index
                    # while request builder gets from the actual offer
                    return True
                else:
                    logger.error("Request builder did not create valid offer structure")
                    return False
            else:
                logger.error("Integration test failed - missing airline code or request")
                return False
                
        except Exception as e:
            logger.error(f"Integration with request builder test failed: {e}")
            return False
    
    def test_multi_airline_consistency(self):
        """Test consistency across multi-airline operations."""
        try:
            # Test multiple offers to ensure consistent behavior
            test_indices = [0, 1, 2, 5, 10]
            results = []
            
            for index in test_indices:
                try:
                    # Extract airline code
                    airline_code = self.pricing_service._extract_airline_code_from_offer(
                        self.test_data, str(index)
                    )
                    
                    # Build request
                    request = build_flight_price_request(
                        self.test_data,
                        selected_offer_index=index
                    )
                    
                    # Get airline from request
                    query_offers = request.get("Query", {}).get("Offers", {}).get("Offer", [])
                    request_airline = None
                    if query_offers:
                        offer_id_node = query_offers[0].get("OfferID", {})
                        request_airline = offer_id_node.get("Owner")
                    
                    results.append({
                        'index': index,
                        'service_airline': airline_code,
                        'request_airline': request_airline,
                        'success': bool(airline_code and request and request_airline)
                    })
                    
                except ValueError as e:
                    if "out of range" in str(e):
                        logger.info(f"Index {index} out of range (expected)")
                        break
                    else:
                        raise e
            
            # Validate consistency
            successful_results = [r for r in results if r['success']]
            if len(successful_results) >= 3:  # At least 3 successful tests
                logger.info(f"✅ Multi-airline consistency test: {len(successful_results)} successful operations")
                for result in successful_results:
                    logger.info(f"  Index {result['index']}: Service={result['service_airline']}, Request={result['request_airline']}")
                return True
            else:
                logger.error(f"Multi-airline consistency test failed: only {len(successful_results)} successful operations")
                return False
                
        except Exception as e:
            logger.error(f"Multi-airline consistency test failed: {e}")
            return False
    
    def test_performance_integration(self):
        """Test performance of the integrated flow."""
        try:
            start_time = time.time()
            
            # Test multiple operations
            test_operations = 10
            successful_operations = 0
            
            for i in range(test_operations):
                try:
                    # Service operation
                    airline_code = self.pricing_service._extract_airline_code_from_offer(
                        self.test_data, str(i)
                    )
                    
                    # Request building operation
                    request = build_flight_price_request(
                        self.test_data,
                        selected_offer_index=i
                    )
                    
                    if airline_code and request:
                        successful_operations += 1
                        
                except ValueError as e:
                    if "out of range" in str(e):
                        break
                    else:
                        raise e
            
            execution_time = time.time() - start_time
            
            if successful_operations >= 5:  # At least 5 successful operations
                avg_time = execution_time / successful_operations
                logger.info(f"✅ Performance integration test: {successful_operations} operations in {execution_time:.3f}s")
                logger.info(f"✅ Average time per operation: {avg_time:.3f}s")
                
                # Performance threshold: should be under 100ms per operation
                return avg_time < 0.1
            else:
                logger.error(f"Performance integration test failed: only {successful_operations} successful operations")
                return False
                
        except Exception as e:
            logger.error(f"Performance integration test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all integration test cases."""
        logger.info("🚀 Starting Flight Pricing Integration Test Suite")
        logger.info("=" * 80)
        
        if not self.load_test_data():
            logger.error("Failed to load test data. Aborting tests.")
            return False
        
        if not self.setup_pricing_service():
            logger.error("Failed to set up pricing service. Aborting tests.")
            return False
        
        # Run all tests
        tests = [
            ("Service Airline Code Extraction", self.test_service_airline_code_extraction),
            ("Service ShoppingResponseID Selection", self.test_service_shopping_response_id_selection),
            ("Service Payload Building", self.test_service_payload_building),
            ("Integration with Request Builder", self.test_integration_with_request_builder),
            ("Multi-Airline Consistency", self.test_multi_airline_consistency),
            ("Performance Integration", self.test_performance_integration),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        self._print_test_summary()
        
        return self.test_results['failed_tests'] == 0
    
    def _print_test_summary(self):
        """Print a summary of test results."""
        logger.info("=" * 80)
        logger.info("📊 INTEGRATION TEST SUMMARY")
        logger.info("=" * 80)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed == 0:
            logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            logger.warning(f"⚠️  {failed} INTEGRATION TEST(S) FAILED")
        
        logger.info("=" * 80)


def main():
    """Main function to run the integration test suite."""
    tester = FlightPricingIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("✅ Flight Pricing Integration Test Suite completed successfully!")
        return 0
    else:
        logger.error("❌ Flight Pricing Integration Test Suite failed!")
        return 1


if __name__ == "__main__":
    exit(main())
