"""
Unit tests for Enhanced Reference Extractor Module

Tests the functionality of the EnhancedReferenceExtractor class using real test data
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

from utils.reference_extractor import EnhancedReferenceExtractor


class TestEnhancedReferenceExtractor(unittest.TestCase):
    """Test cases for EnhancedReferenceExtractor class."""
    
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
                        {"SegmentKey": "SEG1", "Departure": {"AirportCode": {"value": "NBO"}}},
                        {"SegmentKey": "SEG2", "Departure": {"AirportCode": {"value": "CDG"}}}
                    ]
                },
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [
                        {"ObjectKey": "PAX1", "PTC": {"value": "ADT"}}
                    ]
                }
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-shopping-id"}
            }
        }
    
    def test_multi_airline_initialization(self):
        """Test initialization with multi-airline response."""
        print("\n🧪 Testing multi-airline initialization...")
        
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        
        self.assertTrue(extractor.is_multi_airline, "Should detect multi-airline response")
        self.assertEqual(extractor.response, self.multi_airline_response, "Should store response")
        self.assertIsNone(extractor._references_cache, "Cache should be empty initially")
        
        print("✅ Multi-airline initialization working correctly")
    
    def test_single_airline_initialization(self):
        """Test initialization with single-airline response."""
        print("\n🧪 Testing single-airline initialization...")
        
        extractor = EnhancedReferenceExtractor(self.single_airline_response)
        
        self.assertFalse(extractor.is_multi_airline, "Should detect single-airline response")
        self.assertEqual(extractor.response, self.single_airline_response, "Should store response")
        
        print("✅ Single-airline initialization working correctly")
    
    def test_multi_airline_reference_extraction(self):
        """Test reference extraction for multi-airline response."""
        print("\n🧪 Testing multi-airline reference extraction...")
        
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        
        # Verify structure
        self.assertEqual(refs['type'], 'multi_airline', "Should have multi_airline type")
        self.assertIn('by_airline', refs, "Should have by_airline section")
        self.assertIn('global', refs, "Should have global section")
        self.assertIn('airline_codes', refs, "Should have airline_codes")
        self.assertIn('shopping_response_ids', refs, "Should have shopping_response_ids")
        
        # Verify airline codes
        airline_codes = refs['airline_codes']
        self.assertIsInstance(airline_codes, list, "Airline codes should be a list")
        self.assertGreater(len(airline_codes), 1, "Should have multiple airlines")
        
        # Verify each airline has reference structure
        for airline in airline_codes:
            self.assertIn(airline, refs['by_airline'], f"Should have references for {airline}")
            airline_refs = refs['by_airline'][airline]
            
            expected_sections = ['segments', 'passengers', 'flights', 'origins', 'baggage', 'services']
            for section in expected_sections:
                self.assertIn(section, airline_refs, f"Should have {section} for {airline}")
                self.assertIsInstance(airline_refs[section], dict, f"{section} should be a dict")
        
        # Verify global references
        global_refs = refs['global']
        self.assertIsInstance(global_refs, dict, "Global refs should be a dict")
        
        # Verify shopping response IDs
        shopping_ids = refs['shopping_response_ids']
        self.assertIsInstance(shopping_ids, dict, "Shopping IDs should be a dict")
        self.assertGreater(len(shopping_ids), 0, "Should have shopping response IDs")
        
        print(f"✅ Multi-airline extraction successful for {len(airline_codes)} airlines")
        print(f"   Airlines: {airline_codes}")
        print(f"   Shopping IDs: {list(shopping_ids.keys())}")
    
    def test_single_airline_reference_extraction(self):
        """Test reference extraction for single-airline response."""
        print("\n🧪 Testing single-airline reference extraction...")
        
        extractor = EnhancedReferenceExtractor(self.single_airline_response)
        refs = extractor.extract_references()
        
        # Verify structure
        self.assertEqual(refs['type'], 'single_airline', "Should have single_airline type")
        
        expected_sections = ['segments', 'passengers', 'flights', 'origins', 'baggage', 'services']
        for section in expected_sections:
            self.assertIn(section, refs, f"Should have {section} section")
            self.assertIsInstance(refs[section], dict, f"{section} should be a dict")
        
        # Verify shopping response ID
        self.assertIn('shopping_response_id', refs, "Should have shopping_response_id")
        self.assertEqual(refs['shopping_response_id'], 'test-shopping-id', "Should extract correct shopping ID")
        
        # Verify segments were extracted
        segments = refs['segments']
        self.assertEqual(len(segments), 2, "Should extract 2 segments")
        self.assertIn('SEG1', segments, "Should have SEG1")
        self.assertIn('SEG2', segments, "Should have SEG2")
        
        # Verify passengers were extracted
        passengers = refs['passengers']
        self.assertEqual(len(passengers), 1, "Should extract 1 passenger")
        self.assertIn('PAX1', passengers, "Should have PAX1")
        
        print("✅ Single-airline extraction working correctly")
    
    def test_reference_lookup_by_key(self):
        """Test reference lookup by key."""
        print("\n🧪 Testing reference lookup by key...")
        
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        
        # Test segment lookup
        # First, let's get some actual segment keys from the response
        refs = extractor.extract_references()
        global_segments = refs['global']['segments']
        
        if global_segments:
            # Test with an actual segment key
            segment_key = list(global_segments.keys())[0]
            segment_data = extractor.get_reference_by_key(segment_key, 'segments')
            
            self.assertIsNotNone(segment_data, f"Should find segment {segment_key}")
            self.assertIsInstance(segment_data, dict, "Segment data should be a dict")
            
            print(f"✅ Successfully looked up segment: {segment_key}")
        
        # Test non-existent key
        non_existent = extractor.get_reference_by_key('NON-EXISTENT', 'segments')
        self.assertIsNone(non_existent, "Should return None for non-existent key")
        
        print("✅ Reference lookup working correctly")
    
    def test_airline_specific_references(self):
        """Test getting airline-specific references."""
        print("\n🧪 Testing airline-specific reference retrieval...")
        
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        
        # Test with actual airline codes
        airline_codes = refs['airline_codes']
        if airline_codes:
            test_airline = airline_codes[0]
            airline_refs = extractor.get_airline_references(test_airline)
            
            self.assertIsNotNone(airline_refs, f"Should get references for {test_airline}")
            self.assertIsInstance(airline_refs, dict, "Airline refs should be a dict")
            
            expected_sections = ['segments', 'passengers', 'flights', 'origins', 'baggage', 'services']
            for section in expected_sections:
                self.assertIn(section, airline_refs, f"Should have {section} for {test_airline}")
            
            print(f"✅ Successfully retrieved references for airline: {test_airline}")
        
        # Test with single-airline response
        single_extractor = EnhancedReferenceExtractor(self.single_airline_response)
        single_airline_refs = single_extractor.get_airline_references('KL')
        self.assertIsNone(single_airline_refs, "Should return None for single-airline response")
        
        print("✅ Airline-specific reference retrieval working correctly")
    
    def test_shopping_response_id_retrieval(self):
        """Test ShoppingResponseID retrieval."""
        print("\n🧪 Testing ShoppingResponseID retrieval...")
        
        # Test multi-airline
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        refs = extractor.extract_references()
        
        # Test general ID retrieval
        general_id = extractor.get_shopping_response_id()
        self.assertIsInstance(general_id, str, "Should return a string")
        
        # Test airline-specific ID retrieval
        airline_codes = refs['airline_codes']
        if airline_codes:
            test_airline = airline_codes[0]
            airline_id = extractor.get_shopping_response_id(test_airline)
            self.assertIsInstance(airline_id, str, "Should return a string")
            
            print(f"✅ Retrieved ShoppingResponseID for {test_airline}: {airline_id[:20]}...")
        
        # Test single-airline
        single_extractor = EnhancedReferenceExtractor(self.single_airline_response)
        single_id = single_extractor.get_shopping_response_id()
        self.assertEqual(single_id, 'test-shopping-id', "Should return correct single-airline ID")
        
        print("✅ ShoppingResponseID retrieval working correctly")
    
    def test_statistics_generation(self):
        """Test statistics generation."""
        print("\n🧪 Testing statistics generation...")
        
        # Test multi-airline stats
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        stats = extractor.get_statistics()
        
        self.assertEqual(stats['type'], 'multi_airline', "Should have correct type")
        self.assertTrue(stats['is_multi_airline'], "Should be multi-airline")
        self.assertIn('airline_count', stats, "Should have airline count")
        self.assertIn('airlines', stats, "Should have airlines list")
        self.assertIn('by_airline', stats, "Should have by_airline stats")
        self.assertIn('global_totals', stats, "Should have global totals")
        
        print(f"✅ Multi-airline stats: {stats['airline_count']} airlines")
        
        # Test single-airline stats
        single_extractor = EnhancedReferenceExtractor(self.single_airline_response)
        single_stats = single_extractor.get_statistics()
        
        self.assertEqual(single_stats['type'], 'single_airline', "Should have correct type")
        self.assertFalse(single_stats['is_multi_airline'], "Should not be multi-airline")
        self.assertIn('totals', single_stats, "Should have totals")
        
        print("✅ Statistics generation working correctly")
    
    def test_caching_mechanism(self):
        """Test that references are cached after first extraction."""
        print("\n🧪 Testing caching mechanism...")
        
        extractor = EnhancedReferenceExtractor(self.multi_airline_response)
        
        # First extraction
        refs1 = extractor.extract_references()
        self.assertIsNotNone(extractor._references_cache, "Cache should be populated")
        
        # Second extraction should use cache
        refs2 = extractor.extract_references()
        self.assertIs(refs1, refs2, "Should return same object from cache")
        
        print("✅ Caching mechanism working correctly")


def run_tests():
    """Run all tests and provide detailed output."""
    print("🚀 Starting Enhanced Reference Extractor Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedReferenceExtractor)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 All tests passed successfully!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
