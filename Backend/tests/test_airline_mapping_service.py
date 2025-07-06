"""
Unit tests for Airline Code Mapping Service

Tests the functionality of the AirlineMappingService class for airline code
to ThirdParty ID mapping and airline-related configurations.

Author: FLIGHT Application
Created: 2025-07-02
"""

import unittest
import sys
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.airline_mapping_service import AirlineMappingService


class TestAirlineMappingService(unittest.TestCase):
    """Test cases for AirlineMappingService class."""
    
    def test_get_third_party_id_valid_codes(self):
        """Test ThirdParty ID mapping for valid airline codes."""
        print("\n🧪 Testing ThirdParty ID mapping for valid codes...")
        
        # Test known airline codes
        test_cases = [
            ('KL', 'KL'),
            ('QR', 'QR'),
            ('AF', 'AF'),
            ('LHG', 'LHG'),
            ('EK', 'EK'),
            ('KQ', 'KQ'),
            ('6E', '6E'),
            ('SN', 'SN'),  # Brussels Airlines
            ('LH', 'LH'),  # Lufthansa
            ('UA', 'UA'),  # United Airlines
            ('DL', 'DL'),  # Delta Air Lines
            ('BA', 'BA'),  # British Airways
            ('A3', 'A3'),  # Aegean Airlines
        ]
        
        for airline_code, expected_id in test_cases:
            result = AirlineMappingService.get_third_party_id(airline_code)
            self.assertEqual(result, expected_id, 
                           f"Should map {airline_code} to {expected_id}")
        
        print(f"✅ Successfully mapped {len(test_cases)} airline codes")
    
    def test_get_third_party_id_case_insensitive(self):
        """Test that airline code mapping is case insensitive."""
        print("\n🧪 Testing case insensitive mapping...")
        
        test_cases = [
            ('kl', 'KL'),
            ('qr', 'QR'),
            ('Af', 'AF'),
            ('lhg', 'LHG'),
        ]
        
        for airline_code, expected_id in test_cases:
            result = AirlineMappingService.get_third_party_id(airline_code)
            self.assertEqual(result, expected_id, 
                           f"Should map {airline_code} to {expected_id} (case insensitive)")
        
        print("✅ Case insensitive mapping working correctly")
    
    def test_get_third_party_id_invalid_codes(self):
        """Test ThirdParty ID mapping for invalid airline codes."""
        print("\n🧪 Testing ThirdParty ID mapping for invalid codes...")
        
        # Test invalid codes - should return the normalized code as fallback
        test_cases = ['XX', 'INVALID', 'ZZ']
        
        for airline_code in test_cases:
            result = AirlineMappingService.get_third_party_id(airline_code)
            self.assertEqual(result, airline_code.upper(), 
                           f"Should return normalized code {airline_code.upper()} for invalid input")
        
        # Test empty/None inputs
        empty_result = AirlineMappingService.get_third_party_id('')
        self.assertEqual(empty_result, 'UNKNOWN', "Should return 'UNKNOWN' for empty input")
        
        none_result = AirlineMappingService.get_third_party_id(None)
        self.assertEqual(none_result, 'UNKNOWN', "Should return 'UNKNOWN' for None input")
        
        print("✅ Invalid code handling working correctly")
    
    def test_validate_airline_code(self):
        """Test airline code validation."""
        print("\n🧪 Testing airline code validation...")
        
        # Test valid codes
        valid_codes = ['KL', 'QR', 'AF', 'LHG', 'EK', 'KQ', '6E']
        for code in valid_codes:
            self.assertTrue(AirlineMappingService.validate_airline_code(code),
                          f"Should validate {code} as valid")
        
        # Test invalid codes
        invalid_codes = ['XX', 'INVALID', '', None]
        for code in invalid_codes:
            self.assertFalse(AirlineMappingService.validate_airline_code(code),
                           f"Should validate {code} as invalid")
        
        # Test case insensitive validation
        self.assertTrue(AirlineMappingService.validate_airline_code('kl'),
                       "Should validate lowercase 'kl' as valid")
        
        print("✅ Airline code validation working correctly")
    
    def test_get_supported_airlines(self):
        """Test getting list of supported airlines."""
        print("\n🧪 Testing supported airlines retrieval...")
        
        supported = AirlineMappingService.get_supported_airlines()
        
        self.assertIsInstance(supported, list, "Should return a list")
        self.assertGreater(len(supported), 0, "Should have supported airlines")
        
        # Verify expected airlines are present
        expected_airlines = ['KL', 'QR', 'AF', 'LHG', 'EK', 'KQ']
        for airline in expected_airlines:
            self.assertIn(airline, supported, f"Should support airline {airline}")
        
        print(f"✅ Found {len(supported)} supported airlines: {supported}")
    
    def test_get_airline_display_name(self):
        """Test getting airline display names."""
        print("\n🧪 Testing airline display names...")
        
        test_cases = [
            ('KL', 'KLM Royal Dutch Airlines'),
            ('QR', 'Qatar Airways'),
            ('AF', 'Air France'),
            ('EK', 'Emirates'),
        ]
        
        for code, expected_name in test_cases:
            result = AirlineMappingService.get_airline_display_name(code)
            self.assertEqual(result, expected_name, 
                           f"Should return correct display name for {code}")
        
        # Test invalid code
        invalid_result = AirlineMappingService.get_airline_display_name('XX')
        self.assertEqual(invalid_result, 'Airline XX', 
                        "Should return fallback name for invalid code")
        
        # Test empty input
        empty_result = AirlineMappingService.get_airline_display_name('')
        self.assertEqual(empty_result, 'Unknown Airline', 
                        "Should return 'Unknown Airline' for empty input")
        
        print("✅ Airline display names working correctly")
    
    def test_get_airlines_by_region(self):
        """Test getting airlines by region."""
        print("\n🧪 Testing airlines by region...")
        
        # Test valid regions
        europe_airlines = AirlineMappingService.get_airlines_by_region('Europe')
        self.assertIsInstance(europe_airlines, list, "Should return a list")
        self.assertIn('KL', europe_airlines, "Europe should include KL")
        self.assertIn('AF', europe_airlines, "Europe should include AF")
        
        middle_east_airlines = AirlineMappingService.get_airlines_by_region('Middle East')
        self.assertIn('QR', middle_east_airlines, "Middle East should include QR")
        self.assertIn('EK', middle_east_airlines, "Middle East should include EK")
        
        # Test invalid region
        invalid_result = AirlineMappingService.get_airlines_by_region('Invalid Region')
        self.assertEqual(invalid_result, [], "Should return empty list for invalid region")
        
        print(f"✅ Europe: {europe_airlines}")
        print(f"✅ Middle East: {middle_east_airlines}")
    
    def test_get_all_regions(self):
        """Test getting all available regions."""
        print("\n🧪 Testing all regions retrieval...")
        
        regions = AirlineMappingService.get_all_regions()
        
        self.assertIsInstance(regions, list, "Should return a list")
        self.assertGreater(len(regions), 0, "Should have regions")
        
        expected_regions = ['Europe', 'Middle East', 'Africa', 'Asia']
        for region in expected_regions:
            self.assertIn(region, regions, f"Should include region {region}")
        
        print(f"✅ Found regions: {regions}")
    
    def test_supports_feature(self):
        """Test feature support checking."""
        print("\n🧪 Testing feature support...")
        
        # Test known feature support
        self.assertTrue(AirlineMappingService.supports_feature('KL', 'multi_airline_shopping'),
                       "KL should support multi_airline_shopping")
        
        self.assertTrue(AirlineMappingService.supports_feature('QR', 'flight_pricing'),
                       "QR should support flight_pricing")
        
        # Test invalid inputs
        self.assertFalse(AirlineMappingService.supports_feature('', 'multi_airline_shopping'),
                        "Empty airline should not support any feature")
        
        self.assertFalse(AirlineMappingService.supports_feature('KL', ''),
                        "Empty feature should not be supported")
        
        print("✅ Feature support checking working correctly")
    
    def test_get_airlines_supporting_feature(self):
        """Test getting airlines that support specific features."""
        print("\n🧪 Testing airlines supporting features...")
        
        # Test multi-airline shopping support
        multi_airline_airlines = AirlineMappingService.get_airlines_supporting_feature('multi_airline_shopping')
        self.assertIsInstance(multi_airline_airlines, list, "Should return a list")
        self.assertGreater(len(multi_airline_airlines), 0, "Should have airlines supporting multi-airline shopping")
        
        # Test invalid feature
        invalid_feature_airlines = AirlineMappingService.get_airlines_supporting_feature('invalid_feature')
        self.assertEqual(invalid_feature_airlines, [], "Should return empty list for invalid feature")
        
        print(f"✅ Multi-airline shopping supported by: {len(multi_airline_airlines)} airlines")
    
    def test_get_available_features(self):
        """Test getting all available features."""
        print("\n🧪 Testing available features...")
        
        features = AirlineMappingService.get_available_features()
        
        self.assertIsInstance(features, list, "Should return a list")
        self.assertGreater(len(features), 0, "Should have features")
        
        expected_features = ['multi_airline_shopping', 'flight_pricing', 'order_creation']
        for feature in expected_features:
            self.assertIn(feature, features, f"Should include feature {feature}")
        
        print(f"✅ Available features: {features}")
    
    def test_get_airline_info(self):
        """Test getting comprehensive airline information."""
        print("\n🧪 Testing comprehensive airline info...")
        
        # Test valid airline
        kl_info = AirlineMappingService.get_airline_info('KL')
        
        self.assertIsInstance(kl_info, dict, "Should return a dictionary")
        self.assertTrue(kl_info['is_supported'], "KL should be supported")
        self.assertEqual(kl_info['code'], 'KL', "Should have correct code")
        self.assertEqual(kl_info['third_party_id'], 'KL', "Should have correct ThirdParty ID")
        self.assertIn('display_name', kl_info, "Should have display name")
        self.assertIn('region', kl_info, "Should have region")
        self.assertIn('supported_features', kl_info, "Should have supported features")
        
        # Test invalid airline
        invalid_info = AirlineMappingService.get_airline_info('XX')
        self.assertFalse(invalid_info['is_supported'], "Invalid airline should not be supported")
        self.assertIn('error', invalid_info, "Should have error message")
        
        print(f"✅ KL info: {kl_info['display_name']}, Region: {kl_info['region']}, Features: {kl_info['feature_count']}")
    
    def test_bulk_validate_airlines(self):
        """Test bulk validation of airline codes."""
        print("\n🧪 Testing bulk airline validation...")
        
        test_codes = ['KL', 'QR', 'XX', 'AF', 'INVALID']
        results = AirlineMappingService.bulk_validate_airlines(test_codes)
        
        self.assertIsInstance(results, dict, "Should return a dictionary")
        self.assertEqual(len(results), len(test_codes), "Should validate all codes")
        
        # Check specific results
        self.assertTrue(results['KL'], "KL should be valid")
        self.assertTrue(results['QR'], "QR should be valid")
        self.assertFalse(results['XX'], "XX should be invalid")
        self.assertTrue(results['AF'], "AF should be valid")
        self.assertFalse(results['INVALID'], "INVALID should be invalid")
        
        print(f"✅ Bulk validation results: {results}")
    
    def test_get_mapping_statistics(self):
        """Test getting mapping statistics."""
        print("\n🧪 Testing mapping statistics...")
        
        stats = AirlineMappingService.get_mapping_statistics()
        
        self.assertIsInstance(stats, dict, "Should return a dictionary")
        self.assertIn('total_airlines', stats, "Should have total airlines count")
        self.assertIn('total_regions', stats, "Should have total regions count")
        self.assertIn('total_features', stats, "Should have total features count")
        self.assertIn('airlines_by_region', stats, "Should have airlines by region")
        self.assertIn('airlines_by_feature', stats, "Should have airlines by feature")
        self.assertIn('all_airline_codes', stats, "Should have all airline codes")
        
        self.assertGreater(stats['total_airlines'], 0, "Should have airlines")
        self.assertGreater(stats['total_regions'], 0, "Should have regions")
        self.assertGreater(stats['total_features'], 0, "Should have features")
        
        print(f"✅ Statistics: {stats['total_airlines']} airlines, {stats['total_regions']} regions, {stats['total_features']} features")


def run_tests():
    """Run all tests and provide detailed output."""
    print("🚀 Starting Airline Mapping Service Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAirlineMappingService)
    
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
