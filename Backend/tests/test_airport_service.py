import unittest
from unittest.mock import patch, MagicMock
import os

# Adjust the path to import AirportService from the Backend.services.flight package
# This assumes the tests are run from the FLIGHT project root directory.
import sys
# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
backend_path = os.path.join(project_root, 'Backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from services.flight.airport_service import AirportService

# Sample data that would be returned by a successful parse_airport_data call
MOCK_AIRPORT_DATA = [
    {'iata_code': 'LHR', 'airport_name': 'London Heathrow', 'city': 'London', 'country': 'United Kingdom'},
    {'iata_code': 'LGW', 'airport_name': 'London Gatwick', 'city': 'London', 'country': 'United Kingdom'},
    {'iata_code': 'CDG', 'airport_name': 'Charles de Gaulle', 'city': 'Paris', 'country': 'France'},
    {'iata_code': 'JFK', 'airport_name': 'John F. Kennedy', 'city': 'New York', 'country': 'United States'},
    {'iata_code': 'LAX', 'airport_name': 'Los Angeles International', 'city': 'Los Angeles', 'country': 'United States'},
    {'iata_code': 'LTN', 'airport_name': 'London Luton', 'city': 'London', 'country': 'United Kingdom'}
]

class TestAirportService(unittest.TestCase):

    def setUp(self):
        # Reset class variable for each test to ensure isolation
        AirportService._airports_data = None
        AirportService._csv_path = None

    @patch('services.flight.airport_service.parse_airport_data')
    @patch('services.flight.airport_service.os.path.exists')
    def test_initialization_and_data_loading_success(self, mock_exists, mock_parse_data):
        """Test successful initialization and data loading."""
        mock_exists.return_value = True  # Assume CSV file exists
        mock_parse_data.return_value = MOCK_AIRPORT_DATA

        service = AirportService(csv_file_path='/fake/path/to/airports.csv')
        self.assertIsNotNone(service)
        self.assertEqual(len(AirportService._airports_data), len(MOCK_AIRPORT_DATA))
        mock_parse_data.assert_called_once_with('/fake/path/to/airports.csv')

    @patch('services.flight.airport_service.parse_airport_data')
    @patch('services.flight.airport_service.os.path.exists')
    def test_initialization_default_path(self, mock_exists, mock_parse_data):
        """Test initialization uses default CSV path when none is provided."""
        mock_exists.return_value = True
        mock_parse_data.return_value = MOCK_AIRPORT_DATA
        
        # Expected default path construction
        # FLIGHT/Backend/services/flight/airport_service.py -> FLIGHT/airports.csv
        expected_default_csv_path = os.path.abspath(os.path.join(project_root, 'airports.csv'))

        service = AirportService() # No path provided
        self.assertIsNotNone(service)
        mock_parse_data.assert_called_once_with(expected_default_csv_path)
        self.assertEqual(AirportService._csv_path, expected_default_csv_path)

    @patch('services.flight.airport_service.parse_airport_data')
    @patch('services.flight.airport_service.os.path.exists')
    def test_initialization_file_not_found(self, mock_exists, mock_parse_data):
        """Test initialization when CSV file is not found."""
        mock_exists.return_value = False # Assume CSV file does NOT exist
        # mock_parse_data.return_value = [] # This line is not needed as parse_airport_data is not called if file doesn't exist

        with patch('builtins.print') as mock_print:
            # Reset _airports_data to ensure it's None before AirportService initialization for this specific test case
            AirportService._airports_data = None 
            service = AirportService(csv_file_path='/fake/nonexistent.csv')
            self.assertIsNone(AirportService._airports_data) # Expect None if file not found during init
            mock_parse_data.assert_not_called() # parse_airport_data shouldn't be called if os.path.exists is false
            # Check for the specific error message
            mock_print.assert_any_call("Error: Airport CSV file not found at /fake/nonexistent.csv. Airport search will not work.")

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_by_city_found(self, mock_exists, mock_parse_data):
        """Test searching airports by city with matching results."""
        service = AirportService()
        results = service.search_airports(query='London', search_by='city')
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r['city'] == 'London' for r in results))
        # Check if all expected fields are present
        for r in results:
            self.assertIn('iata', r)
            self.assertIn('name', r)
            self.assertIn('city', r)
            self.assertIn('country', r)

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_by_city_not_found(self, mock_exists, mock_parse_data):
        """Test searching airports by city with no matching results."""
        service = AirportService()
        results = service.search_airports(query='Atlantis', search_by='city')
        self.assertEqual(len(results), 0)

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_by_city_case_insensitive(self, mock_exists, mock_parse_data):
        """Test case-insensitive search for city."""
        service = AirportService()
        results = service.search_airports(query='london', search_by='city')
        self.assertEqual(len(results), 3)

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_by_name_found(self, mock_exists, mock_parse_data):
        """Test searching airports by name with matching results."""
        service = AirportService()
        results = service.search_airports(query='Heathrow', search_by='airport_name')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'London Heathrow')

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_by_name_partial_match(self, mock_exists, mock_parse_data):
        """Test searching airports by partial name."""
        service = AirportService()
        results = service.search_airports(query='London', search_by='airport_name') # Matches 'London Heathrow', 'London Gatwick', 'London Luton'
        self.assertEqual(len(results), 3)

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_by_name_not_found(self, mock_exists, mock_parse_data):
        """Test searching airports by name with no matching results."""
        service = AirportService()
        results = service.search_airports(query='NonExistentName', search_by='airport_name')
        self.assertEqual(len(results), 0)

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_empty_query(self, mock_exists, mock_parse_data):
        """Test searching with an empty query string."""
        service = AirportService()
        results = service.search_airports(query='', search_by='city')
        self.assertEqual(len(results), 0)

    @patch('services.flight.airport_service.parse_airport_data', return_value=MOCK_AIRPORT_DATA)
    @patch('services.flight.airport_service.os.path.exists', return_value=True)
    def test_search_airports_invalid_search_by_param(self, mock_exists, mock_parse_data):
        """Test search with an invalid 'search_by' parameter, should default to 'city'."""
        service = AirportService()
        with patch('builtins.print') as mock_print:
            results = service.search_airports(query='Paris', search_by='country_code') # Invalid
            self.assertEqual(len(results), 1) # Should find Paris by city (default)
            self.assertEqual(results[0]['city'], 'Paris')
            mock_print.assert_any_call("Warning: Invalid search_by parameter 'country_code'. Defaulting to 'city'.")

    def test_search_when_data_not_loaded(self):
        """Test search behavior when airport data failed to load initially."""
        # Simulate data loading failure by not mocking parse_airport_data or os.path.exists to True
        AirportService._airports_data = None # Ensure it's None initially for the class
        test_csv_path = '/fake/failing_path.csv'

        # Patch os.path.exists to always return False for this test's scope
        with patch('services.flight.airport_service.os.path.exists', return_value=False) as mock_exists:
            with patch('builtins.print') as mock_print:
                # Instantiate the service. Since os.path.exists is False, _load_data will set _airports_data to []
                # and print the "CSV file not found" error.
                # We pass test_csv_path to ensure the constructor uses it.
                service = AirportService(csv_file_path=test_csv_path)
                
                # CRITICAL: To test the specific error in search_airports when data is truly not loaded (i.e., _airports_data is None),
                # we must reset it to None here. The constructor would have set it to [].
                AirportService._airports_data = None

                results = service.search_airports(query='London')
                self.assertEqual(len(results), 0)

                # Verify os.path.exists was called with the fake path
                # It will be called once in __init__ and once in search_airports
                mock_exists.assert_any_call(test_csv_path) # os.path.exists is now a MagicMock
                
                # Check for the print calls
                # The first error message comes from _load_data() called by __init__
                mock_print.assert_any_call(f"Error: Airport CSV file not found at {test_csv_path}. Airport search will not work.")
                # The second error message comes from search_airports() when _airports_data is still None
                mock_print.assert_any_call("Error: Airport data is not loaded. Cannot perform search.")

if __name__ == '__main__':
    unittest.main()