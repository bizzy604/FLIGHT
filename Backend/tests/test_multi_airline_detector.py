"""
Unit tests for Multi-Airline Detection Module

Tests the functionality of the MultiAirlineDetector class using real test data
from the air shopping response.

Author: FLIGHT Application
Created: 2025-07-02
"""

import json
import unittest
import sys
import os
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.multi_airline_detector import MultiAirlineDetector


class TestMultiAirlineDetector(unittest.TestCase):
    """Test cases for MultiAirlineDetector class."""
    
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
    
    def test_is_multi_airline_response_detection(self):
        """Test detection of multi-airline response."""
        print("\n🧪 Testing multi-airline response detection...")
        
        result = MultiAirlineDetector.is_multi_airline_response(self.multi_airline_response)
        
        self.assertTrue(result, "Should detect multi-airline response")
        print("✅ Multi-airline response correctly detected")
    
    def test_extract_airline_codes(self):
        """Test extraction of airline codes from response."""
        print("\n🧪 Testing airline code extraction...")
        
        airline_codes = MultiAirlineDetector.extract_airline_codes(self.multi_airline_response)
        
        # Verify we get a list
        self.assertIsInstance(airline_codes, list, "Should return a list")
        
        # Verify we have multiple airlines
        self.assertGreater(len(airline_codes), 1, "Should find multiple airline codes")
        
        # Verify expected airlines are present (based on the test data we examined)
        expected_airlines = ['KL', 'QR', 'LHG', 'EK']
        for airline in expected_airlines:
            self.assertIn(airline, airline_codes, f"Should find airline code {airline}")
        
        print(f"✅ Found airline codes: {airline_codes}")
    
    def test_get_airline_prefixed_references(self):
        """Test grouping of references by airline prefix."""
        print("\n🧪 Testing airline prefixed reference grouping...")
        
        airline_refs = MultiAirlineDetector.get_airline_prefixed_references(self.multi_airline_response)
        
        # Verify we get a dictionary
        self.assertIsInstance(airline_refs, dict, "Should return a dictionary")
        
        # Verify we have multiple airlines
        self.assertGreater(len(airline_refs), 1, "Should group references for multiple airlines")
        
        # Verify each airline has references
        for airline, refs in airline_refs.items():
            self.assertIsInstance(refs, list, f"References for {airline} should be a list")
            self.assertGreater(len(refs), 0, f"Should have references for airline {airline}")
            
            # Verify all references have the correct prefix
            for ref in refs:
                self.assertTrue(ref.startswith(f"{airline}-"), 
                              f"Reference {ref} should start with {airline}-")
        
        print(f"✅ Grouped references for airlines: {list(airline_refs.keys())}")
        for airline, refs in airline_refs.items():
            print(f"   {airline}: {len(refs)} references")
    
    def test_airline_code_pattern_validation(self):
        """Test airline code pattern validation."""
        print("\n🧪 Testing airline code pattern validation...")
        
        # Test valid airline codes
        valid_codes = ['KL', 'QR', 'LHG', 'EK', '6E']
        for code in valid_codes:
            self.assertTrue(MultiAirlineDetector.AIRLINE_CODE_PATTERN.match(code),
                          f"Should match valid airline code: {code}")
        
        # Test invalid airline codes
        invalid_codes = ['K', 'KLMM', '1', 'k1', 'KL-']
        for code in invalid_codes:
            self.assertIsNone(MultiAirlineDetector.AIRLINE_CODE_PATTERN.match(code),
                            f"Should not match invalid airline code: {code}")
        
        print("✅ Airline code pattern validation working correctly")
    
    def test_prefixed_reference_pattern_validation(self):
        """Test prefixed reference pattern validation."""
        print("\n🧪 Testing prefixed reference pattern validation...")
        
        # Test valid prefixed references
        valid_refs = [
            ('KL-SEG1', 'KL', 'SEG1'),
            ('LHG-Isgm5100f2e657476', 'LHG', 'Isgm5100f2e657476'),
            ('QR-PAX1', 'QR', 'PAX1'),
            ('6E-BA1', '6E', 'BA1')
        ]
        
        for ref, expected_airline, expected_suffix in valid_refs:
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(ref)
            self.assertIsNotNone(match, f"Should match valid reference: {ref}")
            self.assertEqual(match.group(1), expected_airline, 
                           f"Should extract airline code {expected_airline} from {ref}")
            self.assertEqual(match.group(2), expected_suffix,
                           f"Should extract suffix {expected_suffix} from {ref}")
        
        # Test invalid prefixed references
        invalid_refs = ['SEG1', 'K-SEG1', 'KLMM-SEG1', '-SEG1', 'KL-']
        for ref in invalid_refs:
            match = MultiAirlineDetector.PREFIXED_REFERENCE_PATTERN.match(ref)
            self.assertIsNone(match, f"Should not match invalid reference: {ref}")
        
        print("✅ Prefixed reference pattern validation working correctly")
    
    def test_shopping_response_ids_extraction(self):
        """Test extraction of ShoppingResponseIDs."""
        print("\n🧪 Testing ShoppingResponseID extraction...")
        
        shopping_ids = MultiAirlineDetector._extract_shopping_response_ids(self.multi_airline_response)
        
        # Verify we get a dictionary
        self.assertIsInstance(shopping_ids, dict, "Should return a dictionary")
        
        # Verify we have multiple shopping response IDs
        self.assertGreater(len(shopping_ids), 1, "Should find multiple ShoppingResponseIDs")
        
        # Verify expected airlines have shopping response IDs
        expected_airlines = ['KL', 'QR']
        for airline in expected_airlines:
            self.assertIn(airline, shopping_ids, 
                         f"Should find ShoppingResponseID for airline {airline}")
            self.assertIsInstance(shopping_ids[airline], str,
                                f"ShoppingResponseID for {airline} should be a string")
            self.assertGreater(len(shopping_ids[airline]), 0,
                             f"ShoppingResponseID for {airline} should not be empty")
        
        print(f"✅ Found ShoppingResponseIDs for airlines: {list(shopping_ids.keys())}")
    
    def test_error_handling_with_invalid_data(self):
        """Test error handling with invalid or missing data."""
        print("\n🧪 Testing error handling...")
        
        # Test with empty dictionary
        result = MultiAirlineDetector.is_multi_airline_response({})
        self.assertFalse(result, "Should handle empty dictionary gracefully")
        
        # Test with None
        result = MultiAirlineDetector.is_multi_airline_response(None)
        self.assertFalse(result, "Should handle None gracefully")
        
        # Test airline code extraction with empty data
        airline_codes = MultiAirlineDetector.extract_airline_codes({})
        self.assertEqual(airline_codes, [], "Should return empty list for empty data")
        
        print("✅ Error handling working correctly")


def run_tests():
    """Run all tests and provide detailed output."""
    print("🚀 Starting Multi-Airline Detector Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMultiAirlineDetector)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 All tests passed successfully!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
