# Backend API Tests

This directory contains integration tests for the Verteil NDC API endpoints.

## Test Files

- `test_endpoints.py`: Integration tests for the complete flow (AirShopping -> FlightPrice -> OrderCreate)
- `test_flight_search.py`: Unit tests for flight search functionality
- `test_auth.py`: Tests for authentication functionality

## Prerequisites

1. Python 3.8+
2. Install test dependencies:
   ```
   pip install -r requirements-test.txt
   ```
3. Set up environment variables in a `.env` file (copy from `.env.example`)

## Running Tests

To run all tests:
```bash
python -m pytest tests/
```

To run a specific test file:
```bash
python -m pytest tests/test_endpoints.py -v
```

To run a specific test case:
```bash
python -m pytest tests/test_endpoints.py::TestVerteilEndpoints::test_1_air_shopping -v
```

## Test Cases

### 1. AirShopping Test (`test_1_air_shopping`)
- Tests the `/api/verteil/air-shopping` endpoint
- Verifies that flight search returns valid results
- Saves the first offer for use in subsequent tests

### 2. FlightPrice Test (`test_2_flight_price`)
- Tests the `/api/verteil/flight-price` endpoint
- Uses the offer ID from the AirShopping test
- Verifies that pricing information is returned

### 3. OrderCreate Test (`test_3_order_create`)
- **Note: Disabled by default**
- Tests the `/api/verteil/order-create` endpoint
- Creates a real booking, so use with caution
- Uncomment the `@unittest.skip` decorator to enable

## Test Data

Test data is defined in the `TestVerteilEndpoints` class setup:
- Sample flight search (JFK to LAX, 30 days from now)
- Sample passenger information
- Sample contact information
- Sample payment information (use test credentials in production)

## Environment Variables

Create a `.env` file with the following variables:
```
VERTEIL_API_BASE_URL=https://api.stage.verteil.com
VERTEIL_USERNAME=your_username
VERTEIL_PASSWORD=your_password
VERTEIL_TOKEN_ENDPOINT=/oauth2/token
VERTEIL_OFFICE_ID=your_office_id
VERTEIL_THIRD_PARTY_ID=your_third_party_id
```

## Debugging

Set the logging level to DEBUG for more verbose output:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. Always mock external API calls in unit tests
2. Use real API calls only in integration tests
3. Clean up any test data after tests complete
4. Use meaningful test method names
5. Keep tests independent and isolated
