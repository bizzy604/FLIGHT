"""Simple test script to debug airline name retrieval issues"""

import sys
import os

# Add the Backend directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import _get_airline_name

def test_basic_functionality():
    """Test basic airline name retrieval"""
    print("Testing basic airline name retrieval...")
    
    # Test 1: Known airline codes without reference data
    test_codes = ['EK', 'QR', 'SQ', 'TK', 'LH', 'AF']
    
    for code in test_codes:
        result = _get_airline_name(code)
        print(f"{code} -> {result}")
    
    # Test 2: Edge cases
    edge_cases = [None, '', '  ', 'ek', '  EK  ', 'UNKNOWN']
    
    print("\nTesting edge cases:")
    for case in edge_cases:
        try:
            result = _get_airline_name(case)
            print(f"'{case}' -> '{result}'")
        except Exception as e:
            print(f"'{case}' -> ERROR: {e}")
    
    # Test 3: With reference data
    print("\nTesting with reference data:")
    reference_data = {
        'airlines': {
            'EK': 'Emirates Airlines Custom',
            'QR': 'Qatar Airways Custom'
        }
    }
    
    for code in ['EK', 'QR', 'SQ']:
        result = _get_airline_name(code, reference_data)
        print(f"{code} with ref data -> {result}")

if __name__ == '__main__':
    test_basic_functionality()
    print("\nTest completed successfully!")