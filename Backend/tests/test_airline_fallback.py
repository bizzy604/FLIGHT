import unittest
from test_booking_flight_extraction import MockFlightBookingService

class TestAirlineFallback(unittest.TestCase):
    def setUp(self):
        self.service = MockFlightBookingService()

    def test_airline_extraction_with_name_priority(self):
        """Test that Name takes priority over AirlineID when both are present"""
        flight_with_both = {
            'MarketingCarrier': {
                'Name': 'Kenya Airways',
                'AirlineID': {'value': 'KQ'}
            },
            'Departure': {'AirportCode': {'value': 'NBO'}},
            'Arrival': {'AirportCode': {'value': 'LHR'}}
        }
        
        result = self.service._extract_flight_details(flight_with_both)
        self.assertEqual(result['airline'], 'Kenya Airways')

    def test_airline_extraction_fallback_to_airline_id(self):
        """Test that AirlineID is used when Name is not available"""
        flight_with_id_only = {
            'MarketingCarrier': {
                'AirlineID': {'value': 'KL'}
            },
            'Departure': {'AirportCode': {'value': 'BLR'}},
            'Arrival': {'AirportCode': {'value': 'AMS'}}
        }
        
        result = self.service._extract_flight_details(flight_with_id_only)
        self.assertEqual(result['airline'], 'KL')

    def test_airline_extraction_with_empty_name(self):
        """Test that empty Name falls back to AirlineID"""
        flight_with_empty_name = {
            'MarketingCarrier': {
                'Name': '',
                'AirlineID': {'value': 'AF'}
            },
            'Departure': {'AirportCode': {'value': 'CDG'}},
            'Arrival': {'AirportCode': {'value': 'JFK'}}
        }
        
        result = self.service._extract_flight_details(flight_with_empty_name)
        self.assertEqual(result['airline'], 'AF')

    def test_airline_extraction_with_none_name(self):
        """Test that None Name falls back to AirlineID"""
        flight_with_none_name = {
            'MarketingCarrier': {
                'Name': None,
                'AirlineID': {'value': 'LH'}
            },
            'Departure': {'AirportCode': {'value': 'FRA'}},
            'Arrival': {'AirportCode': {'value': 'LAX'}}
        }
        
        result = self.service._extract_flight_details(flight_with_none_name)
        self.assertEqual(result['airline'], 'LH')

if __name__ == '__main__':
    unittest.main()