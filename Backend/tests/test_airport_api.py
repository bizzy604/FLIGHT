import pytest
import json
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the Python path to allow imports from Backend
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
backend_path = os.path.join(project_root, 'Backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Now we can import create_app from app
from app import create_app
from services.flight.airport_service import AirportService # For direct mocking if needed

# Sample data for mocking AirportService.search_airports
MOCK_SEARCH_RESULTS_LONDON = [
    {'iata': 'LHR', 'name': 'London Heathrow', 'city': 'London', 'country': 'United Kingdom'},
    {'iata': 'LGW', 'name': 'London Gatwick', 'city': 'London', 'country': 'United Kingdom'}
]
MOCK_SEARCH_RESULTS_PARIS = [
    {'iata': 'CDG', 'name': 'Charles de Gaulle', 'city': 'Paris', 'country': 'France'}
]
MOCK_SEARCH_RESULTS_EMPTY = []

@pytest.fixture(scope='session')
def app_fixture():
    """Create and configure a new app instance for each test session."""
    # Create a test app instance
    # Ensure that the AirportService uses a predictable, mockable CSV path during tests
    # or that its data loading is fully mocked.
    # For these tests, we'll primarily mock the `search_airports` method of the service instance.
    app = create_app({'TESTING': True, 'DEBUG': False})
    return app

@pytest.fixture
def client(app_fixture):
    """A test client for the app."""
    return app_fixture.test_client()

@pytest.fixture(autouse=True)
def reset_airport_service_data_for_tests():
    """Ensure AirportService data is reset before each test run if it's a class-level singleton."""
    # This helps if AirportService caches data at the class level
    AirportService._airports_data = None
    AirportService._csv_path = None
    yield
    AirportService._airports_data = None
    AirportService._csv_path = None

# Test cases for the /api/airports/autocomplete endpoint
@patch('services.flight.airport_service.AirportService.search_airports')
@pytest.mark.asyncio
async def test_airport_autocomplete_success_city_search(mock_search_airports, client):
    """Test successful autocomplete by city."""
    mock_search_airports.return_value = MOCK_SEARCH_RESULTS_LONDON
    
    response = await client.get('/api/airports/autocomplete?query=London&search_by=city')
    
    assert response.status_code == 200
    data = await response.get_json()
    assert data['status'] == 'success'
    assert len(data['data']) == 2
    assert data['data'][0]['city'] == 'London'
    mock_search_airports.assert_called_once_with(query='London', search_by='city')

@patch('services.flight.airport_service.AirportService.search_airports')
@pytest.mark.asyncio
async def test_airport_autocomplete_success_airport_name_search(mock_search_airports, client):
    """Test successful autocomplete by airport name."""
    mock_search_airports.return_value = [MOCK_SEARCH_RESULTS_LONDON[0]] # Heathrow only
    
    response = await client.get('/api/airports/autocomplete?query=Heathrow&search_by=airport_name')
    
    assert response.status_code == 200
    data = await response.get_json()
    assert data['status'] == 'success'
    assert len(data['data']) == 1
    assert data['data'][0]['name'] == 'London Heathrow'
    mock_search_airports.assert_called_once_with(query='Heathrow', search_by='airport_name')

@patch('services.flight.airport_service.AirportService.search_airports')
@pytest.mark.asyncio
async def test_airport_autocomplete_default_search_by_city(mock_search_airports, client):
    """Test that search_by defaults to 'city' if not provided."""
    mock_search_airports.return_value = MOCK_SEARCH_RESULTS_PARIS
    
    response = await client.get('/api/airports/autocomplete?query=Paris') # No search_by param
    
    assert response.status_code == 200
    data = await response.get_json()
    assert data['status'] == 'success'
    assert len(data['data']) == 1
    assert data['data'][0]['city'] == 'Paris'
    mock_search_airports.assert_called_once_with(query='Paris', search_by='city')

@patch('services.flight.airport_service.AirportService.search_airports')
@pytest.mark.asyncio
async def test_airport_autocomplete_no_results(mock_search_airports, client):
    """Test autocomplete when no results are found."""
    mock_search_airports.return_value = MOCK_SEARCH_RESULTS_EMPTY
    
    response = await client.get('/api/airports/autocomplete?query=NonExistentCity&search_by=city')
    
    assert response.status_code == 200
    data = await response.get_json()
    assert data['status'] == 'success'
    assert len(data['data']) == 0
    mock_search_airports.assert_called_once_with(query='NonExistentCity', search_by='city')

@pytest.mark.asyncio
async def test_airport_autocomplete_query_too_short(client):
    """Test autocomplete with a query that is too short."""
    response = await client.get('/api/airports/autocomplete?query=L&search_by=city')
    
    assert response.status_code == 400
    data = await response.get_json()
    assert data['status'] == 'error'
    assert 'Query parameter is required and must be at least 2 characters long' in data['message']

@pytest.mark.asyncio
async def test_airport_autocomplete_no_query(client):
    """Test autocomplete with no query parameter."""
    response = await client.get('/api/airports/autocomplete?search_by=city')
    
    assert response.status_code == 400
    data = await response.get_json()
    assert data['status'] == 'error'
    assert 'Query parameter is required and must be at least 2 characters long' in data['message']

@patch('services.flight.airport_service.AirportService.search_airports')
@pytest.mark.asyncio
async def test_airport_autocomplete_invalid_search_by_defaults_to_city(mock_search_airports, client):
    """Test that an invalid search_by parameter defaults to 'city'."""
    mock_search_airports.return_value = MOCK_SEARCH_RESULTS_LONDON
    
    response = await client.get('/api/airports/autocomplete?query=London&search_by=country_code')
    
    assert response.status_code == 200
    data = await response.get_json()
    assert data['status'] == 'success'
    assert len(data['data']) == 2
    # Service should have been called with search_by='city'
    mock_search_airports.assert_called_once_with(query='London', search_by='city')

@patch('services.flight.airport_service.AirportService.search_airports')
@pytest.mark.asyncio
async def test_airport_autocomplete_service_exception(mock_search_airports, client):
    """Test error handling when AirportService raises an exception."""
    mock_search_airports.side_effect = Exception("Service unavailable")
    
    response = await client.get('/api/airports/autocomplete?query=Berlin&search_by=city')
    
    assert response.status_code == 500
    data = await response.get_json()
    assert data['status'] == 'error'
    assert 'An internal server error occurred' in data['message']
    mock_search_airports.assert_called_once_with(query='Berlin', search_by='city')

@pytest.mark.asyncio
async def test_airport_autocomplete_options_request(client):
    """Test that OPTIONS preflight requests are handled correctly."""
    response = await client.options('/api/airports/autocomplete')
    assert response.status_code == 200
    # Check for CORS headers if your app is configured to send them on OPTIONS
    # For Quart, a simple 200 with empty body is often enough for preflight.
    # The @cors decorator on the blueprint/route handles the actual CORS headers.
    data = await response.get_data(as_text=True)
    assert data.strip() == '{}' # Quart default for jsonify({}) on OPTIONS, strip whitespace

# To run these tests, you would typically use pytest from your project root:
# pytest Backend/tests/test_airport_api.py
# pytest Backend/tests/test_airport_api.py