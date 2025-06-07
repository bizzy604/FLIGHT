"""
Tests for the flight search functionality.
"""
import os
import sys
import json
import logging
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import after setting up the path
from services.flight_service import search_flights
from services.flight.exceptions import FlightServiceError
from utils.auth import TokenManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_app():
    """Create a test Flask app with configuration."""
    app = Flask(__name__)
    
    # Configure the app
    app.config.update(
        TESTING=True,
        VERTEIL_API_BASE_URL='https://api.stage.verteil.com',
        VERTEIL_TOKEN_ENDPOINT='/oauth2/token',
        VERTEIL_USERNAME='reatravel_apitestuser',
        VERTEIL_PASSWORD='UZrNcyxpIFn2TOdiU5uc9kZrqJwxU44KdlyFBpiDOaaNom1xSySEtQmRq9IcDq3c',
        VERTEIL_THIRD_PARTY_ID='KQ',
        VERTEIL_OFFICE_ID='OFF3746',
        REQUEST_TIMEOUT=30,
        OAUTH2_TOKEN_EXPIRY_BUFFER=60
    )
    
    return app

class TestFlightSearch(unittest.TestCase):
    """Test cases for flight search functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_test_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Sample flight search parameters
        self.search_params = {
            'origin': 'JFK',
            'destination': 'LAX',
            'departure_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'return_date': (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d'),
            'adults': 1,
            'children': 0,
            'infants': 0,
            'cabin_class': 'ECONOMY',
            'trip_type': 'roundtrip'
        }
        
        # Sample API response
        self.sample_response = {
            'data': {
                'flightOffers': [
                    {
                        'id': '1',
                        'price': {
                            'total': '350.00',
                            'currency': 'USD'
                        },
                        'itineraries': [
                            {
                                'segments': [
                                    {
                                        'departure': {
                                            'iataCode': 'JFK',
                                            'at': '2024-02-15T10:00:00'
                                        },
                                        'arrival': {
                                            'iataCode': 'LAX',
                                            'at': '2024-02-15T13:30:00'
                                        },
                                        'carrierCode': 'AA',
                                        'number': '123'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'ctx') and self.ctx:
            self.ctx.pop()
    
    @patch('services.flight.core.FlightService._make_request')
    def test_search_flights_success(self, mock_make_request):
        """Test successful flight search."""
        # Mock the API response
        mock_make_request.return_value = self.sample_response
        
        # Call the function
        with self.app.app_context():
            result = search_flights(
                origin=self.search_params['origin'],
                destination=self.search_params['destination'],
                departure_date=self.search_params['departure_date'],
                return_date=self.search_params['return_date'],
                adults=self.search_params['adults'],
                children=self.search_params['children'],
                infants=self.search_params['infants'],
                cabin_class=self.search_params['cabin_class'],
                trip_type=self.search_params['trip_type'],
                config=self.app.config
            )
        
        # Debug: Print the actual result
        print(f"\nActual result: {result}")
        
        # Check that we got the correct response structure
        assert 'status' in result, f"Expected 'status' in result, got: {result.keys()}"
        if result['status'] != 'success':
            print(f"\nError details: {result.get('error', 'No error details')}")
            print(f"\nFull result: {result}")
        assert result['status'] == 'success', f"Expected status 'success', got: {result['status']}. Error: {result.get('error', 'No error details')}"
        assert 'data' in result, f"Expected 'data' in result, got: {result.keys()}"
        assert isinstance(result['data'], dict), "Data should be a dictionary"
        assert 'offers' in result['data'], f"Expected 'offers' in data, got: {result['data'].keys()}"
        assert isinstance(result['data']['offers'], list), "Offers should be a list"
    
    @patch('services.flight.core.FlightService._make_request')
    def test_search_flights_missing_required_params(self, mock_make_request):
        """Test flight search with missing required parameters."""
        with self.app.app_context():
            # Test with missing origin
            with self.assertRaises(FlightServiceError) as context:
                search_flights(
                    origin='',
                    destination=self.search_params['destination'],
                    departure_date=self.search_params['departure_date'],
                    config=self.app.config
                )
            self.assertIn("Origin is required", str(context.exception))
            
            # Test with missing destination
            with self.assertRaises(FlightServiceError) as context:
                search_flights(
                    origin=self.search_params['origin'],
                    destination='',
                    departure_date=self.search_params['departure_date'],
                    config=self.app.config
                )
            self.assertIn("Destination is required", str(context.exception))
            
            # Test with missing departure date
            with self.assertRaises(FlightServiceError) as context:
                search_flights(
                    origin=self.search_params['origin'],
                    destination=self.search_params['destination'],
                    departure_date='',
                    config=self.app.config
                )
            self.assertIn("Departure date is required", str(context.exception))
    
    @patch('services.flight.core.FlightService._make_request')
    def test_search_flights_api_error(self, mock_make_request):
        """Test handling of API errors during flight search."""
        # Mock an API error
        mock_make_request.side_effect = FlightServiceError("API request failed")
        
        # Call the function and expect an exception
        with self.app.app_context():
            with self.assertRaises(FlightServiceError) as context:
                search_flights(
                    origin=self.search_params['origin'],
                    destination=self.search_params['destination'],
                    departure_date=self.search_params['departure_date'],
                    config=self.app.config
                )
            self.assertIn("API request failed", str(context.exception))

def test_flight_search_integration():
    """Integration test for flight search with real API call."""
    # This test will make actual API calls - use with caution
    if not all([os.getenv('VERTEIL_USERNAME'), os.getenv('VERTEIL_PASSWORD')]):
        logger.warning("Skipping integration test - missing credentials")
        return
    
    app = create_test_app()
    
    with app.app_context():
        try:
            logger.info("Testing flight search integration with Verteil API...")
            
            # Test one-way flight
            result = search_flights(
                origin='JFK',
                destination='LAX',
                departure_date=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                adults=1,
                cabin_class='ECONOMY',
                trip_type='oneway'
            )
            
            logger.info("Flight search successful!")
            logger.info(f"Found {len(result.get('flightOffers', []))} flight offers")
            
            if 'flightOffers' in result and len(result['flightOffers']) > 0:
                logger.info(f"Sample offer price: {result['flightOffers'][0].get('price', {}).get('total')} "
                            f"{result['flightOffers'][0].get('price', {}).get('currency')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Flight search integration test failed: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    # Run the integration test if executed directly
    test_flight_search_integration()
