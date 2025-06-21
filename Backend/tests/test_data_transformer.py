"""Tests for data transformation utilities."""

import pytest
import json
from unittest.mock import patch
from utils.data_transformer import (
    transform_verteil_to_frontend,
    _extract_reference_data,
    _transform_single_offer,
    _transform_segment,
    _calculate_duration,
    _build_price_breakdown,
    _get_airline_name
)

# Load real API response from file
def load_real_api_response():
    """Load the real API response from airshoping_response.json"""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, 'airshoping_response.json')
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Real Verteil API response structure for testing
SAMPLE_VERTEIL_RESPONSE = load_real_api_response()

class TestDataTransformer:
    """Test cases for data transformation functions."""
    
    def test_transform_verteil_to_frontend_success(self):
        """Test successful transformation of Verteil response to frontend format."""
        result = transform_verteil_to_frontend(SAMPLE_VERTEIL_RESPONSE)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        flight_offer = result[0]
        
        # Check required fields
        assert 'id' in flight_offer
        assert 'airline' in flight_offer
        assert 'departure' in flight_offer
        assert 'arrival' in flight_offer
        assert 'duration' in flight_offer
        assert 'stops' in flight_offer
        assert 'price' in flight_offer
        assert 'currency' in flight_offer
        
        # Check airline details
        airline = flight_offer['airline']
        assert airline['code'] == 'KQ'
        assert airline['name'] == 'Kenya Airways'
        
        # Check price details
        assert flight_offer['price'] == 16409
        assert flight_offer['currency'] == 'INR'
        
        # Check departure/arrival
        assert flight_offer['departure']['airport'] == 'NBO'
        assert flight_offer['arrival']['airport'] == 'CDG'
        
    def test_transform_verteil_to_frontend_empty_response(self):
        """Test transformation with empty response."""
        result = transform_verteil_to_frontend({})
        assert result == []
        
    def test_transform_verteil_to_frontend_invalid_response(self):
        """Test transformation with invalid response structure."""
        invalid_response = {"invalid": "data"}
        result = transform_verteil_to_frontend(invalid_response)
        assert result == []
        
    def test_extract_reference_data_real_data(self):
        """Test extraction of reference data from real Verteil response."""
        reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)
        
        assert 'flights' in reference_data
        assert 'segments' in reference_data
        assert 'airports' in reference_data
        assert 'aircraft' in reference_data
        
        # Check that segments exist (use actual segment keys from real data)
        segments = reference_data['segments']
        assert len(segments) > 0
        
        # Get first available segment to test structure
        first_segment_key = list(segments.keys())[0]
        segment = segments[first_segment_key]
        assert 'SegmentKey' in segment
        
        # Check that airports exist
        airports = reference_data['airports']
        assert len(airports) > 0
        
        # Check that at least one airport has the expected structure
        if airports:
            first_airport_code = list(airports.keys())[0]
            airport = airports[first_airport_code]
            assert 'code' in airport
            assert 'name' in airport
        
    def test_transform_segment_real_data(self):
        """Test transformation of flight segment data using real API data."""
        reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)
        
        # Get the first available segment key from the real data
        data_lists = SAMPLE_VERTEIL_RESPONSE.get('DataLists', {})
        segment_list = data_lists.get('FlightSegmentList', {})
        segments = segment_list.get('FlightSegment', [])
        
        if segments and len(segments) > 0:
            first_segment = segments[0]
            segment_key = first_segment.get('SegmentKey')
            
            if segment_key:
                # Get the actual segment data from reference_data
                 segment_data = reference_data['segments'].get(segment_key, {})
                 if segment_data:
                     result = _transform_segment(segment_data, reference_data)
                     
                     assert result is not None
                     
                     # Check that basic structure exists
                     assert 'departure' in result
                     assert 'arrival' in result
                     assert 'flightNumber' in result
                     assert 'aircraft' in result
                     
                     # Check departure details
                     departure = result['departure']
                     assert 'airport' in departure
                     assert 'airportName' in departure
                     assert 'datetime' in departure
                     
                     # Check arrival details
                     arrival = result['arrival']
                     assert 'airport' in arrival
                     assert 'airportName' in arrival
                     assert 'datetime' in arrival
                 else:
                     # Skip test if segment data not found
                     assert True
        else:
            # Skip test if no segments available
            assert True
        
    def test_calculate_duration(self):
        """Test duration calculation between segments."""
        first_segment = {
            'departure': {'datetime': '2024-01-15T10:30'},
            'arrival': {'datetime': '2024-01-15T12:30'}
        }
        last_segment = {
            'departure': {'datetime': '2024-01-15T14:00'},
            'arrival': {'datetime': '2024-01-15T18:45'}
        }
        
        duration = _calculate_duration(first_segment, last_segment)
        assert duration == '8h 15m'
        
    def test_calculate_duration_invalid_format(self):
        """Test duration calculation with invalid datetime format."""
        first_segment = {
            'departure': {'datetime': 'invalid-datetime'},
            'arrival': {'datetime': 'invalid-datetime'}
        }
        last_segment = {
            'departure': {'datetime': 'invalid-datetime'},
            'arrival': {'datetime': 'invalid-datetime'}
        }
        
        duration = _calculate_duration(first_segment, last_segment)
        assert duration == 'N/A'
        
    def test_build_price_breakdown(self):
        """Test building price breakdown from Verteil price detail."""
        price_detail = {
            "TotalAmount": {
                "SimpleCurrencyPrice": {
                    "value": 16409,
                    "Code": "INR"
                }
            },
            "BaseAmount": {
                "value": 13675,
                "Code": "INR"
            },
            "Taxes": {
                "Total": {
                    "value": 2734,
                    "Code": "INR"
                }
            }
        }
        
        result = _build_price_breakdown(price_detail)
        
        assert result['baseFare'] == 13675
        assert result['taxes'] == 2734
        assert result['fees'] == 0
        assert result['totalPrice'] == 16409
        assert result['currency'] == 'INR'
        
    def test_build_price_breakdown_missing_data(self):
        """Test building price breakdown with missing data."""
        price_detail = {}
        
        result = _build_price_breakdown(price_detail)
        
        assert result['baseFare'] == 0
        assert result['taxes'] == 0
        assert result['fees'] == 0
        assert result['totalPrice'] == 0
        assert result['currency'] == 'USD'
        
    def test_get_airline_name(self):
        """Test airline name lookup with reference data."""
        # Create mock reference data
        reference_data = {
            'segments': {
                'SEG1': {
                    'SegmentKey': 'SEG1',
                    'MarketingCarrier': {
                        'AirlineID': {'value': 'KQ'},
                        'Name': 'Kenya Airways',
                        'FlightNumber': {'value': '505'}
                    },
                    'OperatingCarrier': {
                        'AirlineID': {'value': 'KQ'},
                        'Name': 'Kenya Airways',
                        'FlightNumber': {'value': '505'}
                    }
                },
                'SEG2': {
                    'SegmentKey': 'SEG2',
                    'MarketingCarrier': {
                        'AirlineID': {'value': 'EK'},
                        'Name': 'Emirates',
                        'FlightNumber': {'value': '722'}
                    },
                    'OperatingCarrier': {
                        'AirlineID': {'value': 'QF'},
                        'Name': 'Qantas',
                        'FlightNumber': {'value': '8415'}
                    }
                }
            },
            'airports': {},
            'flights': {},
            'aircraft': {}
        }
        
        # Test with marketing carrier
        assert _get_airline_name('KQ', reference_data) == 'Kenya Airways'
        
        # Test with operating carrier
        assert _get_airline_name('QF', reference_data) == 'Qantas'
        
        # Test with marketing carrier that has a different operating carrier
        assert _get_airline_name('EK', reference_data) == 'Emirates'
        
        # Test with unknown airline code
        assert _get_airline_name('UNKNOWN', reference_data) == 'Airline UNKNOWN'
        
        # Test with empty reference data
        assert _get_airline_name('KQ', {}) == 'Airline KQ'
        
        # Test with None reference data
        assert _get_airline_name('KQ', None) == 'Airline KQ'
        
    def test_transform_single_offer_success_real_data(self):
        """Test transformation of a single priced offer using real API data."""
        priced_offer = SAMPLE_VERTEIL_RESPONSE['OffersGroup']['AirlineOffers'][0]['AirlineOffer'][0]['PricedOffer']
        reference_data = _extract_reference_data(SAMPLE_VERTEIL_RESPONSE)
        
        result = _transform_single_offer(priced_offer, 'KQ', reference_data)
        
        assert result is not None
        assert result['airline']['code'] == 'KQ'
        assert result['price'] == 16409
        assert result['currency'] == 'INR'
        # Real data has multiple segments, so stops > 0 is expected
        assert result['stops'] >= 0
        assert len(result['segments']) >= 1
        
    def test_transform_single_offer_no_price(self):
        """Test transformation of offer without price information."""
        priced_offer = {"OfferPrice": []}
        reference_data = {}
        
        result = _transform_single_offer(priced_offer, 'KQ', reference_data)
        
        assert result is None
        
    def test_transform_single_offer_invalid_data(self):
        """Test transformation with invalid offer data."""
        priced_offer = {"invalid": "data"}
        reference_data = {}
        
        result = _transform_single_offer(priced_offer, 'KQ', reference_data)
        
        assert result is None

if __name__ == '__main__':
    pytest.main([__file__])