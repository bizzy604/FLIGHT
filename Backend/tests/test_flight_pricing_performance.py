#!/usr/bin/env python3
"""
Flight Pricing Performance Validation Test Suite

This module provides comprehensive performance testing for the enhanced flight pricing system,
including large dataset handling, memory usage analysis, concurrent request processing,
and scalability validation.

Author: Enhanced Flight Pricing System
Date: 2025-07-02
Phase: 3.4 - Flight Pricing Performance Validation
"""

import asyncio
import json
import logging
import os
import sys
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple
import threading
import psutil
import gc

# Add Backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from services.flight.pricing import FlightPricingService
    from scripts.build_flightprice_rq import build_flight_price_request
    from utils.multi_airline_detector import MultiAirlineDetector
    from utils.reference_extractor import EnhancedReferenceExtractor
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the FLIGHT directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class FlightPricingPerformanceTester:
    """
    Comprehensive performance testing suite for enhanced flight pricing system.
    
    Tests include:
    - Large dataset performance validation
    - Memory usage analysis and optimization
    - Concurrent request handling
    - Performance benchmarking against baseline
    - Scalability validation and limits testing
    """
    
    def __init__(self):
        """Initialize the performance tester."""
        self.test_data = None
        self.pricing_service = None
        self.performance_results = {
            'large_dataset_tests': [],
            'memory_usage_tests': [],
            'concurrent_tests': [],
            'benchmark_tests': [],
            'scalability_tests': []
        }
        self.baseline_metrics = {}
        
        logger.info("🚀 Initializing Flight Pricing Performance Test Suite")
        logger.info("=" * 80)
    
    def load_test_data(self) -> bool:
        """Load the multi-airline test data."""
        try:
            test_file_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'postman', 'airshopingresponse.json'
            )
            
            with open(test_file_path, 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
            
            # Validate test data
            offers_count = len(self.test_data.get("OffersGroup", {}).get("AirlineOffers", []))
            total_offers = 0
            
            for airline_offers in self.test_data.get("OffersGroup", {}).get("AirlineOffers", []):
                airline_offers_list = airline_offers.get("AirlineOffer", [])
                if not isinstance(airline_offers_list, list):
                    airline_offers_list = [airline_offers_list]
                total_offers += len([offer for offer in airline_offers_list if offer.get("PricedOffer")])
            
            logger.info(f"Successfully loaded test data with {offers_count} airlines and {total_offers} total offers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            return False
    
    def setup_pricing_service(self) -> bool:
        """Set up the FlightPricingService for performance testing."""
        try:
            # Create mock config with required OAuth settings
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
            
            logger.info("Successfully set up FlightPricingService for performance testing")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up pricing service: {e}")
            return False
    
    def measure_memory_usage(self, func, *args, **kwargs) -> Tuple[Any, Dict[str, float]]:
        """
        Measure memory usage of a function execution.
        
        Returns:
            Tuple of (function_result, memory_metrics)
        """
        # Start memory tracing
        tracemalloc.start()
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute function
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Get peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_metrics = {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_increase_mb': final_memory - initial_memory,
            'peak_traced_memory_mb': peak / 1024 / 1024,
            'execution_time_s': execution_time
        }
        
        return result, memory_metrics
    
    def test_large_dataset_performance(self) -> bool:
        """Test performance with large multi-airline datasets."""
        logger.info("Running test: Large Dataset Performance")
        
        try:
            # Test with different batch sizes
            test_indices = [0, 10, 50, 100, 500, 1000, 1499]  # Various offer indices
            
            for batch_size in [1, 5, 10, 25, 50]:
                logger.info(f"Testing batch size: {batch_size}")
                
                start_time = time.time()
                successful_operations = 0
                
                # Process batch of offers
                for i in range(min(batch_size, len(test_indices))):
                    offer_index = test_indices[i]
                    
                    try:
                        # Test airline code extraction
                        airline_code = self.pricing_service._extract_airline_code_from_offer(
                            self.test_data, str(offer_index)
                        )
                        
                        # Test request building
                        request_payload = build_flight_price_request(
                            self.test_data, offer_index
                        )
                        
                        if airline_code and request_payload:
                            successful_operations += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to process offer {offer_index}: {e}")
                
                batch_time = time.time() - start_time
                avg_time_per_operation = batch_time / batch_size if batch_size > 0 else 0
                
                batch_result = {
                    'batch_size': batch_size,
                    'successful_operations': successful_operations,
                    'total_time_s': batch_time,
                    'avg_time_per_operation_s': avg_time_per_operation,
                    'operations_per_second': successful_operations / batch_time if batch_time > 0 else 0
                }
                
                self.performance_results['large_dataset_tests'].append(batch_result)
                
                logger.info(f"✅ Batch {batch_size}: {successful_operations}/{batch_size} successful, "
                          f"{avg_time_per_operation:.4f}s avg, {batch_result['operations_per_second']:.2f} ops/sec")
            
            return True
            
        except Exception as e:
            logger.error(f"Large dataset performance test failed: {e}")
            return False

    def test_memory_usage_analysis(self) -> bool:
        """Analyze memory usage patterns during flight pricing operations."""
        logger.info("Running test: Memory Usage Analysis")

        try:
            # Test memory usage for different operation types
            test_operations = [
                ("airline_code_extraction", lambda: self.pricing_service._extract_airline_code_from_offer(self.test_data, "0")),
                ("request_building", lambda: build_flight_price_request(self.test_data, 0)),
                ("multi_airline_detection", lambda: MultiAirlineDetector.is_multi_airline_response(self.test_data)),
                ("reference_extraction", lambda: EnhancedReferenceExtractor(self.test_data).extract_references())
            ]

            for operation_name, operation_func in test_operations:
                logger.info(f"Analyzing memory usage for: {operation_name}")

                # Run operation multiple times to get average
                memory_results = []

                for run in range(5):  # 5 runs for averaging
                    # Force garbage collection before test
                    gc.collect()

                    result, memory_metrics = self.measure_memory_usage(operation_func)
                    memory_results.append(memory_metrics)

                # Calculate averages
                avg_memory_metrics = {
                    'operation': operation_name,
                    'avg_execution_time_s': sum(m['execution_time_s'] for m in memory_results) / len(memory_results),
                    'avg_memory_increase_mb': sum(m['memory_increase_mb'] for m in memory_results) / len(memory_results),
                    'max_memory_increase_mb': max(m['memory_increase_mb'] for m in memory_results),
                    'avg_peak_memory_mb': sum(m['peak_traced_memory_mb'] for m in memory_results) / len(memory_results)
                }

                self.performance_results['memory_usage_tests'].append(avg_memory_metrics)

                logger.info(f"✅ {operation_name}: {avg_memory_metrics['avg_execution_time_s']:.4f}s avg, "
                          f"{avg_memory_metrics['avg_memory_increase_mb']:.2f}MB avg increase")

            return True

        except Exception as e:
            logger.error(f"Memory usage analysis failed: {e}")
            return False

    def test_concurrent_request_handling(self) -> bool:
        """Test concurrent flight pricing request handling."""
        logger.info("Running test: Concurrent Request Handling")

        try:
            # Test different concurrency levels
            concurrency_levels = [1, 2, 5, 10, 20]
            test_indices = list(range(0, min(100, 1500), 5))  # Every 5th offer up to 100

            for concurrency in concurrency_levels:
                logger.info(f"Testing concurrency level: {concurrency}")

                start_time = time.time()
                successful_operations = 0
                failed_operations = 0

                # Create thread pool for concurrent execution
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    # Submit tasks
                    futures = []
                    for i in range(min(concurrency * 2, len(test_indices))):  # 2x concurrency for good load
                        offer_index = test_indices[i % len(test_indices)]

                        # Submit airline code extraction task
                        future = executor.submit(
                            self._concurrent_pricing_operation,
                            offer_index
                        )
                        futures.append(future)

                    # Collect results
                    for future in as_completed(futures):
                        try:
                            result = future.result(timeout=30)  # 30 second timeout
                            if result:
                                successful_operations += 1
                            else:
                                failed_operations += 1
                        except Exception as e:
                            failed_operations += 1
                            logger.warning(f"Concurrent operation failed: {e}")

                total_time = time.time() - start_time
                total_operations = successful_operations + failed_operations

                concurrent_result = {
                    'concurrency_level': concurrency,
                    'total_operations': total_operations,
                    'successful_operations': successful_operations,
                    'failed_operations': failed_operations,
                    'success_rate': successful_operations / total_operations if total_operations > 0 else 0,
                    'total_time_s': total_time,
                    'operations_per_second': successful_operations / total_time if total_time > 0 else 0
                }

                self.performance_results['concurrent_tests'].append(concurrent_result)

                logger.info(f"✅ Concurrency {concurrency}: {successful_operations}/{total_operations} successful, "
                          f"{concurrent_result['success_rate']:.2%} success rate, "
                          f"{concurrent_result['operations_per_second']:.2f} ops/sec")

            return True

        except Exception as e:
            logger.error(f"Concurrent request handling test failed: {e}")
            return False

    def _concurrent_pricing_operation(self, offer_index: int) -> bool:
        """
        Helper method for concurrent testing.

        Args:
            offer_index: The offer index to process

        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            # Test airline code extraction
            airline_code = self.pricing_service._extract_airline_code_from_offer(
                self.test_data, str(offer_index)
            )

            # Test request building
            request_payload = build_flight_price_request(
                self.test_data, offer_index
            )

            return bool(airline_code and request_payload)

        except Exception:
            return False

    def test_performance_benchmarking(self) -> bool:
        """Benchmark performance against baseline metrics."""
        logger.info("Running test: Performance Benchmarking")

        try:
            # Define baseline expectations (based on integration test results)
            baseline_expectations = {
                'airline_code_extraction_ms': 5.0,  # 5ms baseline
                'request_building_ms': 25.0,        # 25ms baseline
                'complete_operation_ms': 30.0,      # 30ms baseline
                'memory_increase_mb': 10.0,         # 10MB baseline
                'operations_per_second': 100.0      # 100 ops/sec baseline
            }

            # Run benchmark tests
            benchmark_results = {}

            # Test 1: Airline code extraction speed
            start_time = time.time()
            for i in range(100):  # 100 operations
                self.pricing_service._extract_airline_code_from_offer(self.test_data, str(i % 10))
            extraction_time = (time.time() - start_time) * 1000 / 100  # ms per operation

            # Test 2: Request building speed
            start_time = time.time()
            for i in range(50):  # 50 operations (more expensive)
                build_flight_price_request(self.test_data, i % 10)
            building_time = (time.time() - start_time) * 1000 / 50  # ms per operation

            # Test 3: Complete operation speed
            start_time = time.time()
            for i in range(20):  # 20 complete operations
                airline_code = self.pricing_service._extract_airline_code_from_offer(self.test_data, str(i % 10))
                request_payload = build_flight_price_request(self.test_data, i % 10)
            complete_time = (time.time() - start_time) * 1000 / 20  # ms per operation

            # Test 4: Memory efficiency
            _, memory_metrics = self.measure_memory_usage(
                lambda: [build_flight_price_request(self.test_data, i) for i in range(10)]
            )

            # Test 5: Throughput
            start_time = time.time()
            successful_ops = 0
            for i in range(200):  # 200 operations for throughput test
                try:
                    airline_code = self.pricing_service._extract_airline_code_from_offer(self.test_data, str(i % 10))
                    if airline_code:
                        successful_ops += 1
                except:
                    pass
            throughput_time = time.time() - start_time
            ops_per_second = successful_ops / throughput_time if throughput_time > 0 else 0

            # Compile benchmark results
            benchmark_results = {
                'airline_code_extraction_ms': extraction_time,
                'request_building_ms': building_time,
                'complete_operation_ms': complete_time,
                'memory_increase_mb': memory_metrics['memory_increase_mb'],
                'operations_per_second': ops_per_second
            }

            # Compare against baselines
            performance_analysis = {}
            for metric, actual_value in benchmark_results.items():
                baseline_value = baseline_expectations[metric]
                performance_ratio = actual_value / baseline_value

                if performance_ratio <= 1.0:
                    status = "✅ EXCELLENT"
                elif performance_ratio <= 1.5:
                    status = "✅ GOOD"
                elif performance_ratio <= 2.0:
                    status = "⚠️ ACCEPTABLE"
                else:
                    status = "❌ NEEDS_OPTIMIZATION"

                performance_analysis[metric] = {
                    'actual': actual_value,
                    'baseline': baseline_value,
                    'ratio': performance_ratio,
                    'status': status
                }

                logger.info(f"{status} {metric}: {actual_value:.2f} (baseline: {baseline_value:.2f}, ratio: {performance_ratio:.2f}x)")

            self.performance_results['benchmark_tests'] = {
                'results': benchmark_results,
                'analysis': performance_analysis,
                'baseline_expectations': baseline_expectations
            }

            return True

        except Exception as e:
            logger.error(f"Performance benchmarking failed: {e}")
            return False

    def test_scalability_validation(self) -> bool:
        """Test system scalability and identify performance limits."""
        logger.info("Running test: Scalability Validation")

        try:
            # Test with increasing dataset sizes
            dataset_sizes = [10, 50, 100, 500, 1000, 1500]

            for size in dataset_sizes:
                logger.info(f"Testing scalability with {size} offers")

                # Limit test size to available offers
                actual_size = min(size, 1500)

                start_time = time.time()
                successful_operations = 0
                memory_usage_start = psutil.Process().memory_info().rss / 1024 / 1024

                # Process offers sequentially to test scalability
                for i in range(actual_size):
                    try:
                        # Alternate between different operations
                        if i % 3 == 0:
                            airline_code = self.pricing_service._extract_airline_code_from_offer(
                                self.test_data, str(i % 100)
                            )
                        elif i % 3 == 1:
                            request_payload = build_flight_price_request(
                                self.test_data, i % 100
                            )
                        else:
                            # Combined operation
                            airline_code = self.pricing_service._extract_airline_code_from_offer(
                                self.test_data, str(i % 100)
                            )
                            request_payload = build_flight_price_request(
                                self.test_data, i % 100
                            )

                        successful_operations += 1

                    except Exception as e:
                        logger.warning(f"Operation {i} failed: {e}")

                total_time = time.time() - start_time
                memory_usage_end = psutil.Process().memory_info().rss / 1024 / 1024
                memory_increase = memory_usage_end - memory_usage_start

                scalability_result = {
                    'dataset_size': actual_size,
                    'successful_operations': successful_operations,
                    'total_time_s': total_time,
                    'avg_time_per_operation_ms': (total_time * 1000) / actual_size if actual_size > 0 else 0,
                    'operations_per_second': successful_operations / total_time if total_time > 0 else 0,
                    'memory_increase_mb': memory_increase,
                    'memory_per_operation_kb': (memory_increase * 1024) / actual_size if actual_size > 0 else 0
                }

                self.performance_results['scalability_tests'].append(scalability_result)

                logger.info(f"✅ Size {actual_size}: {successful_operations} ops in {total_time:.2f}s, "
                          f"{scalability_result['operations_per_second']:.2f} ops/sec, "
                          f"{memory_increase:.2f}MB memory increase")

                # Force garbage collection between tests
                gc.collect()

            return True

        except Exception as e:
            logger.error(f"Scalability validation failed: {e}")
            return False

    def run_all_performance_tests(self) -> bool:
        """
        Run all performance validation tests.

        Returns:
            bool: True if all tests pass, False otherwise
        """
        logger.info("🚀 Starting Flight Pricing Performance Validation Suite")
        logger.info("=" * 80)

        # Setup phase
        if not self.load_test_data():
            logger.error("❌ Failed to load test data")
            return False

        if not self.setup_pricing_service():
            logger.error("❌ Failed to setup pricing service")
            return False

        # Define test suite
        performance_tests = [
            ("Large Dataset Performance", self.test_large_dataset_performance),
            ("Memory Usage Analysis", self.test_memory_usage_analysis),
            ("Concurrent Request Handling", self.test_concurrent_request_handling),
            ("Performance Benchmarking", self.test_performance_benchmarking),
            ("Scalability Validation", self.test_scalability_validation)
        ]

        # Run tests
        passed_tests = 0
        total_tests = len(performance_tests)

        for test_name, test_func in performance_tests:
            logger.info(f"Running performance test: {test_name}")

            try:
                start_time = time.time()
                success = test_func()
                test_time = time.time() - start_time

                if success:
                    logger.info(f"✅ {test_name} - PASSED ({test_time:.3f}s)")
                    passed_tests += 1
                else:
                    logger.error(f"❌ {test_name} - FAILED ({test_time:.3f}s)")

            except Exception as e:
                logger.error(f"❌ {test_name} - ERROR: {e}")

        # Print comprehensive summary
        self._print_performance_summary(passed_tests, total_tests)

        return passed_tests == total_tests

    def _print_performance_summary(self, passed_tests: int, total_tests: int):
        """Print comprehensive performance test summary."""
        logger.info("=" * 80)
        logger.info("📊 PERFORMANCE VALIDATION SUMMARY")
        logger.info("=" * 80)

        # Test results summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        logger.info(f"Performance Tests: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")

        if passed_tests == total_tests:
            logger.info("🎉 ALL PERFORMANCE TESTS PASSED!")
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} PERFORMANCE TEST(S) FAILED")

        # Detailed performance metrics
        logger.info("\n📈 PERFORMANCE METRICS SUMMARY:")

        # Large dataset performance
        if self.performance_results['large_dataset_tests']:
            best_batch = max(self.performance_results['large_dataset_tests'],
                           key=lambda x: x['operations_per_second'])
            logger.info(f"• Best Throughput: {best_batch['operations_per_second']:.2f} ops/sec "
                       f"(batch size: {best_batch['batch_size']})")

        # Memory usage
        if self.performance_results['memory_usage_tests']:
            total_memory = sum(test['avg_memory_increase_mb'] for test in self.performance_results['memory_usage_tests'])
            logger.info(f"• Total Memory Usage: {total_memory:.2f}MB across all operations")

        # Concurrent performance
        if self.performance_results['concurrent_tests']:
            best_concurrent = max(self.performance_results['concurrent_tests'],
                                key=lambda x: x['operations_per_second'])
            logger.info(f"• Best Concurrent Performance: {best_concurrent['operations_per_second']:.2f} ops/sec "
                       f"(concurrency: {best_concurrent['concurrency_level']})")

        # Benchmark results
        if self.performance_results['benchmark_tests']:
            benchmark = self.performance_results['benchmark_tests']
            excellent_metrics = sum(1 for analysis in benchmark['analysis'].values()
                                  if 'EXCELLENT' in analysis['status'])
            total_metrics = len(benchmark['analysis'])
            logger.info(f"• Benchmark Performance: {excellent_metrics}/{total_metrics} metrics excellent")

        # Scalability results
        if self.performance_results['scalability_tests']:
            largest_test = max(self.performance_results['scalability_tests'],
                             key=lambda x: x['dataset_size'])
            logger.info(f"• Scalability: Handled {largest_test['dataset_size']} offers at "
                       f"{largest_test['operations_per_second']:.2f} ops/sec")

        logger.info("=" * 80)


def main():
    """Main function to run the performance validation suite."""
    tester = FlightPricingPerformanceTester()
    success = tester.run_all_performance_tests()

    if success:
        logger.info("✅ Flight Pricing Performance Validation completed successfully!")
        return 0
    else:
        logger.error("❌ Flight Pricing Performance Validation failed!")
        return 1


if __name__ == "__main__":
    exit(main())
