# Flight Service Module

A modular and maintainable implementation of flight-related services for the Verteil NDC API integration.

## Structure

```
Backend/services/flight/
├── __init__.py         # Package initialization and exports
├── core.py            # Core functionality and base classes
├── search.py          # Flight search functionality
├── pricing.py         # Flight pricing functionality
├── booking.py         # Booking management
├── exceptions.py      # Custom exceptions
├── decorators.py      # Async decorators for caching and rate limiting
├── utils.py           # Utility functions
└── types.py           # Type definitions and data models
```

## Key Components

### Core Module (`core.py`)
- `FlightService`: Base class providing common functionality for all flight services
- Request/response handling
- Authentication and session management
- Error handling and logging

### Search Module (`search.py`)
- Flight search functionality
- AirShopping API integration
- Response processing and transformation

### Pricing Module (`pricing.py`)
- Flight pricing functionality
- FlightPrice API integration
- Fare rules and pricing details

### Booking Module (`booking.py`)
- Order creation and management
- OrderCreate API integration
- Booking retrieval and status updates

## Usage

### Initialization

```python
from Backend.services.flight import FlightSearchService, FlightPricingService, FlightBookingService

# Initialize services with optional config
search_service = FlightSearchService(config={
    'VERTEIL_API_KEY': 'your-api-key',
    'VERTEIL_API_SECRET': 'your-api-secret'
})

# Use context manager for automatic resource cleanup
async with FlightSearchService() as service:
    results = await service.search_flights(search_criteria)
```

### Making Requests

```python
# Search for flights
search_criteria = {
    'trip_type': 'ROUND_TRIP',
    'od_segments': [
        {'origin': 'JFK', 'destination': 'LAX', 'departure_date': '2023-12-01'},
        {'origin': 'LAX', 'destination': 'JFK', 'departure_date': '2023-12-15'}
    ],
    'num_adults': 1,
    'cabin_preference': 'ECONOMY'
}

async with FlightSearchService() as service:
    search_results = await service.search_flights(search_criteria)
```

## Configuration

Service configuration can be passed during initialization or loaded from environment variables:

```python
config = {
    'VERTEIL_API_BASE_URL': 'https://api.verteil.com/ndc',
    'VERTEIL_API_KEY': 'your-api-key',
    'VERTEIL_API_SECRET': 'your-api-secret',
    'VERTEIL_API_TIMEOUT': 30,
    'VERTEIL_MAX_RETRIES': 3,
    'CACHE_ENABLED': True,
    'CACHE_TTL': 300  # 5 minutes
}
```

## Error Handling

Custom exceptions are provided in `exceptions.py`:

```python
from Backend.services.flight.exceptions import (
    FlightServiceError,
    RateLimitExceeded,
    AuthenticationError,
    ValidationError,
    APIError,
    BookingError,
    PricingError
)

try:
    # Service call
    pass
except RateLimitExceeded as e:
    # Handle rate limiting
    pass
except AuthenticationError as e:
    # Handle auth errors
    pass
except FlightServiceError as e:
    # Handle other flight service errors
    pass
```

## Testing

Unit tests can be run using pytest:

```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit a pull request

## License

This project is licensed under the MIT License.
