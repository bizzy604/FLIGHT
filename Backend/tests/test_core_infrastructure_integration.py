"""
Integration Tests for Core Infrastructure

Comprehensive integration tests for all Phase 1 modules working together:
- MultiAirlineDetector
- EnhancedReferenceExtractor  
- AirlineMappingService

Tests the complete workflow using real test data from air shopping response.

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

from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor
from services.airline_mapping_service import AirlineMappingService


class TestCoreInfrastructureIntegration(unittest.TestCase):
    """Integration test cases for Phase 1 core infrastructure modules."""
    
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
    
    def test_complete_multi_airline_workflow(self):
        """Test the complete workflow for multi-airline response processing."""
        print("\n🧪 Testing complete multi-airline workflow...")
        
        # Step 1: Detect multi-airline response
        is_multi_airline = MultiAirlineDetector.is_multi_airline_response(self.multi_airline_response)
        self.assertTrue(is_multi_airline, "Should detect multi-airline response")
        
        # Step 2: Extract airline codes
        airline_codes = MultiAirlineDetector.extract_airline_codes(self.multi_airline_response)
        self.assertIsInstance(airline_codes, list, "Should return list of airline codes")
        self.assertGreater(len(airline_codes), 1, "Should have multiple airlines")
        
        # Step 3: Validate all detected airlines are supported
        validation_results = AirlineMappingService.bulk_validate_airlines(airline_codes)
        supported_airlines = [code for code, is_valid in validation_results.items() if is_valid]
        
        print(f"   Detected airlines: {airline_codes}")
        print(f"   Supported airlines: {supported_airlines}")
        
        # Step 4: Get ThirdParty IDs for all supported airlines
        third_party_mappings = {}
        for airline_code in supported_airlines:
            third_party_id = AirlineMappingService.get_third_party_id(airline_code)
            third_party_mappings[airline_code] = third_party_id
        
        self.assertEqual(len(third_party_mappings), len(supported_airlines), 
                        "Should have ThirdParty ID for each supported airline")
        
        # Step 5: Extract references with airline context
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        
        self.assertEqual(refs['type'], 'multi_airline', "Should extract as multi-airline")
        self.assertEqual(set(refs['airline_codes']), set(airline_codes), 
                        "Extracted airline codes should match detected codes")
        
        # Step 6: Verify airline-specific references
        for airline_code in supported_airlines:
            airline_refs = extractor.get_airline_references(airline_code)
            self.assertIsNotNone(airline_refs, f"Should have references for {airline_code}")
            
            # Verify reference structure
            expected_sections = ['segments', 'passengers', 'flights', 'origins', 'baggage', 'services']
            for section in expected_sections:
                self.assertIn(section, airline_refs, f"Should have {section} for {airline_code}")
        
        # Step 7: Verify ShoppingResponseID extraction
        shopping_ids = refs['shopping_response_ids']
        self.assertIsInstance(shopping_ids, dict, "Should have shopping response IDs")
        self.assertGreater(len(shopping_ids), 0, "Should have at least one shopping response ID")
        
        # Step 8: Test airline-specific ShoppingResponseID retrieval
        for airline_code in supported_airlines:
            if airline_code in shopping_ids:
                airline_shopping_id = extractor.get_shopping_response_id(airline_code)
                self.assertIsInstance(airline_shopping_id, str, "Should return string")
                self.assertGreater(len(airline_shopping_id), 0, "Should have non-empty shopping ID")
        
        print(f"✅ Complete workflow successful for {len(supported_airlines)} supported airlines")
        print(f"   ThirdParty mappings: {third_party_mappings}")
        
    def test_airline_feature_compatibility(self):
        """Test airline feature compatibility across all modules."""
        print("\n🧪 Testing airline feature compatibility...")
        
        # Get detected airlines
        airline_codes = MultiAirlineDetector.extract_airline_codes(self.multi_airline_response)
        
        # Test feature support for each airline
        features_to_test = ['multi_airline_shopping', 'flight_pricing', 'order_creation']
        
        feature_matrix = {}
        for airline_code in airline_codes:
            if AirlineMappingService.validate_airline_code(airline_code):
                feature_matrix[airline_code] = {}
                for feature in features_to_test:
                    supports = AirlineMappingService.supports_feature(airline_code, feature)
                    feature_matrix[airline_code][feature] = supports
        
        # Verify all supported airlines have multi-airline shopping capability
        for airline_code, features in feature_matrix.items():
            self.assertTrue(features.get('multi_airline_shopping', False),
                          f"Airline {airline_code} should support multi-airline shopping")
        
        print(f"✅ Feature compatibility verified for {len(feature_matrix)} airlines")
        
        # Print feature matrix
        for airline, features in feature_matrix.items():
            supported_features = [f for f, supported in features.items() if supported]
            print(f"   {airline}: {supported_features}")
    
    def test_reference_lookup_integration(self):
        """Test reference lookup integration across modules."""
        print("\n🧪 Testing reference lookup integration...")
        
        # Initialize extractor
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        
        # Test global reference lookup
        global_segments = refs['global']['segments']
        if global_segments:
            # Test lookup of first segment
            segment_key = list(global_segments.keys())[0]
            segment_data = extractor.get_reference_by_key(segment_key, 'segments')
            
            self.assertIsNotNone(segment_data, f"Should find segment {segment_key}")
            self.assertEqual(segment_data, global_segments[segment_key], 
                           "Lookup should return correct segment data")
            
            # Determine airline from segment key if prefixed
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(segment_key)
            if match:
                airline_code = match.group(1)
                
                # Verify airline is supported
                if AirlineMappingService.validate_airline_code(airline_code):
                    # Get airline info
                    airline_info = AirlineMappingService.get_airline_info(airline_code)
                    self.assertTrue(airline_info['is_supported'], 
                                  f"Airline {airline_code} should be supported")
                    
                    # Get ThirdParty ID
                    third_party_id = AirlineMappingService.get_third_party_id(airline_code)
                    self.assertEqual(third_party_id, airline_info['third_party_id'],
                                   "ThirdParty ID should match airline info")
                    
                    print(f"   ✅ Segment {segment_key} -> Airline {airline_code} -> ThirdParty {third_party_id}")
        
        print("✅ Reference lookup integration working correctly")
    
    def test_shopping_response_id_workflow(self):
        """Test ShoppingResponseID workflow for API calls."""
        print("\n🧪 Testing ShoppingResponseID workflow...")
        
        # Get airline codes
        airline_codes = MultiAirlineDetector.extract_airline_codes(self.multi_airline_response)
        
        # Initialize extractor
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        
        # Test ShoppingResponseID extraction for each airline
        shopping_ids = refs['shopping_response_ids']
        
        for airline_code in airline_codes:
            if AirlineMappingService.validate_airline_code(airline_code):
                # Get airline-specific shopping ID
                airline_shopping_id = extractor.get_shopping_response_id(airline_code)
                
                # Get ThirdParty ID for API headers
                third_party_id = AirlineMappingService.get_third_party_id(airline_code)
                
                # Simulate API call preparation
                api_headers = {
                    'ThirdParty-ID': third_party_id,
                    'Content-Type': 'application/json'
                }
                
                api_payload_context = {
                    'airline_code': airline_code,
                    'shopping_response_id': airline_shopping_id,
                    'third_party_id': third_party_id
                }
                
                # Verify all required data is available
                self.assertIsNotNone(airline_shopping_id, f"Should have shopping ID for {airline_code}")
                self.assertIsNotNone(third_party_id, f"Should have ThirdParty ID for {airline_code}")
                self.assertGreater(len(airline_shopping_id), 0, "Shopping ID should not be empty")
                self.assertGreater(len(third_party_id), 0, "ThirdParty ID should not be empty")
                
                print(f"   ✅ {airline_code}: ThirdParty={third_party_id}, ShoppingID={airline_shopping_id[:20]}...")
        
        print("✅ ShoppingResponseID workflow working correctly")
    
    def test_error_handling_integration(self):
        """Test error handling across all modules."""
        print("\n🧪 Testing error handling integration...")
        
        # Test with empty response
        empty_response = {}
        
        # MultiAirlineDetector with empty response
        is_multi_empty = MultiAirlineDetector.is_multi_airline_response(empty_response)
        self.assertFalse(is_multi_empty, "Empty response should not be multi-airline")
        
        codes_empty = MultiAirlineDetector.extract_airline_codes(empty_response)
        self.assertEqual(codes_empty, [], "Empty response should return empty airline codes")
        
        # EnhancedReferenceExtractor with empty response
        extractor_empty = EnhancedReferenceExtractor(empty_response)
        refs_empty = extractor_empty.extract_references()
        self.assertIn('type', refs_empty, "Should return valid structure even for empty response")
        
        # AirlineMappingService with invalid codes
        invalid_codes = ['', None, 'INVALID', 'XX']
        validation_results = AirlineMappingService.bulk_validate_airlines(invalid_codes)
        
        for code in invalid_codes:
            if code is not None:  # None is not included in results
                self.assertFalse(validation_results.get(code, False), 
                               f"Invalid code {code} should not be valid")
        
        print("✅ Error handling integration working correctly")
    
    def test_performance_with_large_dataset(self):
        """Test performance with the large test dataset."""
        print("\n🧪 Testing performance with large dataset...")
        
        import time
        
        # Measure detection time
        start_time = time.time()
        is_multi_airline = MultiAirlineDetector.is_multi_airline_response(self.multi_airline_response)
        detection_time = time.time() - start_time
        
        # Measure extraction time
        start_time = time.time()
        airline_codes = MultiAirlineDetector.extract_airline_codes(self.multi_airline_response)
        extraction_time = time.time() - start_time
        
        # Measure reference extraction time
        start_time = time.time()
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        reference_time = time.time() - start_time
        
        # Measure mapping time
        start_time = time.time()
        validation_results = AirlineMappingService.bulk_validate_airlines(airline_codes)
        mapping_time = time.time() - start_time
        
        # Performance assertions (should be fast)
        self.assertLess(detection_time, 1.0, "Detection should complete within 1 second")
        self.assertLess(extraction_time, 1.0, "Extraction should complete within 1 second")
        self.assertLess(reference_time, 5.0, "Reference extraction should complete within 5 seconds")
        self.assertLess(mapping_time, 0.1, "Mapping should complete within 0.1 seconds")
        
        print(f"   ✅ Detection: {detection_time:.3f}s")
        print(f"   ✅ Extraction: {extraction_time:.3f}s")
        print(f"   ✅ References: {reference_time:.3f}s")
        print(f"   ✅ Mapping: {mapping_time:.3f}s")
        print("✅ Performance tests passed")
    
    def test_data_consistency_validation(self):
        """Test data consistency across all modules."""
        print("\n🧪 Testing data consistency validation...")
        
        # Get airline codes from detector
        detected_codes = MultiAirlineDetector.extract_airline_codes(self.multi_airline_response)
        
        # Get airline codes from reference extractor
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        extracted_codes = refs['airline_codes']
        
        # Verify consistency
        self.assertEqual(set(detected_codes), set(extracted_codes),
                        "Detected and extracted airline codes should match")
        
        # Verify all detected airlines have references
        for airline_code in detected_codes:
            if airline_code in refs['by_airline']:
                airline_refs = refs['by_airline'][airline_code]
                
                # Check if airline has any references
                total_refs = sum(len(section_refs) for section_refs in airline_refs.values())
                
                # Log reference counts
                print(f"   {airline_code}: {total_refs} total references")
        
        # Verify shopping response IDs consistency
        shopping_ids = refs['shopping_response_ids']
        for airline_code in detected_codes:
            if airline_code in shopping_ids:
                shopping_id = shopping_ids[airline_code]
                self.assertIsInstance(shopping_id, str, f"Shopping ID for {airline_code} should be string")
                self.assertGreater(len(shopping_id), 0, f"Shopping ID for {airline_code} should not be empty")
        
        print("✅ Data consistency validation passed")


def run_integration_tests():
    """Run all integration tests and provide detailed output."""
    print("🚀 Starting Core Infrastructure Integration Tests")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreInfrastructureIntegration)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("🎉 All integration tests passed successfully!")
        print("\n📊 Phase 1: Core Infrastructure - COMPLETE")
        print("   ✅ Multi-Airline Detection")
        print("   ✅ Enhanced Reference Extraction")
        print("   ✅ Airline Code Mapping Service")
        print("   ✅ Integration Testing")
        return True
    else:
        print("❌ Some integration tests failed!")
        return False


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
