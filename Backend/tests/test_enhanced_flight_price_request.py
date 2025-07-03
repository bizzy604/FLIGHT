#!/usr/bin/env python3
"""
Enhanced Flight Price Request Building Test Suite
Tests the enhanced build_flight_price_request function with multi-airline support.
"""

import json
import logging
import sys
import time
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from scripts.build_flightprice_rq import build_flight_price_request
from utils.multi_airline_detector import MultiAirlineDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedFlightPriceRequestTester:
    """Test suite for enhanced flight price request building functionality."""
    
    def __init__(self, test_data_file: str = "postman/airshopingresponse.json"):
        """
        Initialize the tester with test data.
        
        Args:
            test_data_file (str): Path to the test data file
        """
        self.test_data_file = Path(test_data_file)
        self.test_data = None
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
            logger.info(f"Running test: {test_name}")
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
    
    def test_multi_airline_detection(self):
        """Test multi-airline response detection."""
        try:
            is_multi_airline = MultiAirlineDetector.is_multi_airline_response(self.test_data)
            logger.info(f"Multi-airline detection result: {is_multi_airline}")
            
            if is_multi_airline:
                airline_codes = MultiAirlineDetector.extract_airline_codes(self.test_data)
                logger.info(f"Detected airlines: {airline_codes}")
                return len(airline_codes) > 1
            else:
                logger.info("Detected as single-airline response")
                return True
                
        except Exception as e:
            logger.error(f"Multi-airline detection failed: {e}")
            return False
    
    def test_multi_airline_global_index_selection(self):
        """Test multi-airline flight price request with global index selection."""
        try:
            # Test with different global indices
            test_indices = [0, 5, 10, 15]
            
            for index in test_indices:
                try:
                    result = build_flight_price_request(
                        self.test_data,
                        selected_offer_index=index
                    )
                    
                    # Validate the result structure
                    if not self._validate_flight_price_request_structure(result):
                        logger.error(f"Invalid structure for global index {index}")
                        return False
                    
                    logger.info(f"✅ Global index {index} - Request built successfully")
                    
                except ValueError as e:
                    if "out of range" in str(e):
                        logger.info(f"Global index {index} out of range (expected)")
                        break
                    else:
                        logger.error(f"Unexpected error for index {index}: {e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Multi-airline global index test failed: {e}")
            return False
    
    def test_airline_specific_shopping_response_id(self):
        """Test airline-specific ShoppingResponseID extraction."""
        try:
            # Build request for first offer
            result = build_flight_price_request(
                self.test_data,
                selected_offer_index=0
            )
            
            # Check if ShoppingResponseID is present
            shopping_response_id = result.get("ShoppingResponseID")
            if not shopping_response_id:
                logger.error("ShoppingResponseID missing from request")
                return False
            
            logger.info(f"ShoppingResponseID structure: {shopping_response_id}")
            
            # Validate structure
            if isinstance(shopping_response_id, dict):
                if "value" in shopping_response_id or ("Owner" in shopping_response_id and "ResponseID" in shopping_response_id):
                    logger.info("✅ Valid ShoppingResponseID structure")
                    return True
                else:
                    logger.error("Invalid ShoppingResponseID structure")
                    return False
            else:
                logger.error("ShoppingResponseID is not a dictionary")
                return False
                
        except Exception as e:
            logger.error(f"Airline-specific ShoppingResponseID test failed: {e}")
            return False
    
    def test_backward_compatibility(self):
        """Test backward compatibility with single-airline logic."""
        try:
            # Test with airline owner specification (single-airline mode)
            result = build_flight_price_request(
                self.test_data,
                selected_offer_index=0,
                selected_airline_owner="KQ"  # Assuming KQ is present
            )
            
            # Validate the result structure
            if not self._validate_flight_price_request_structure(result):
                logger.error("Invalid structure for backward compatibility test")
                return False
            
            logger.info("✅ Backward compatibility test passed")
            return True
            
        except Exception as e:
            logger.error(f"Backward compatibility test failed: {e}")
            return False
    
    def test_performance_with_large_dataset(self):
        """Test performance with the large multi-airline dataset."""
        try:
            start_time = time.time()
            
            # Test multiple requests to measure performance
            test_indices = [0, 1, 2, 3, 4]
            
            for index in test_indices:
                result = build_flight_price_request(
                    self.test_data,
                    selected_offer_index=index
                )
                
                if not self._validate_flight_price_request_structure(result):
                    logger.error(f"Performance test failed for index {index}")
                    return False
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Performance test: {len(test_indices)} requests in {execution_time:.3f}s")
            
            # Performance threshold: should complete within reasonable time
            return execution_time < 10.0  # 10 seconds threshold
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return False
    
    def _validate_flight_price_request_structure(self, request: dict) -> bool:
        """
        Validate the structure of a flight price request.
        
        Args:
            request (dict): The flight price request to validate
            
        Returns:
            bool: True if structure is valid, False otherwise
        """
        required_fields = ["DataLists", "Query", "ShoppingResponseID"]
        
        for field in required_fields:
            if field not in request:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate Query structure
        query = request.get("Query", {})
        if "Offers" not in query or "Offer" not in query["Offers"]:
            logger.error("Invalid Query structure")
            return False
        
        # Validate DataLists structure
        data_lists = request.get("DataLists", {})
        if "FareGroup" not in data_lists:
            logger.error("Missing FareGroup in DataLists")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all test cases."""
        logger.info("🚀 Starting Enhanced Flight Price Request Building Test Suite")
        logger.info("=" * 80)
        
        if not self.load_test_data():
            logger.error("Failed to load test data. Aborting tests.")
            return False
        
        # Run all tests
        tests = [
            ("Multi-Airline Detection", self.test_multi_airline_detection),
            ("Multi-Airline Global Index Selection", self.test_multi_airline_global_index_selection),
            ("Airline-Specific ShoppingResponseID", self.test_airline_specific_shopping_response_id),
            ("Backward Compatibility", self.test_backward_compatibility),
            ("Performance with Large Dataset", self.test_performance_with_large_dataset),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        self._print_test_summary()
        
        return self.test_results['failed_tests'] == 0
    
    def _print_test_summary(self):
        """Print a summary of test results."""
        logger.info("=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed == 0:
            logger.info("🎉 ALL TESTS PASSED!")
        else:
            logger.warning(f"⚠️  {failed} TEST(S) FAILED")
        
        logger.info("=" * 80)


def main():
    """Main function to run the test suite."""
    tester = EnhancedFlightPriceRequestTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("✅ Enhanced Flight Price Request Building Test Suite completed successfully!")
        return 0
    else:
        logger.error("❌ Enhanced Flight Price Request Building Test Suite failed!")
        return 1


if __name__ == "__main__":
    exit(main())
