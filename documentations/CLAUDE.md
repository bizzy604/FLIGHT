# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_air_shopping_service.py

# Run tests with coverage
python -m pytest --cov=Backend

# Run tests in verbose mode
python -m pytest -v

# Run specific test by pattern
python -m pytest -k "test_flight_pricing"
```

### Running the Application
```bash
# Development mode (with debug)
python app.py

# Production mode
export QUART_ENV=production
python app.py

# Using gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### API Logging Management
```bash
# Enable API request/response logging
python scripts/manage_api_logging.py enable

# Check logging status
python scripts/manage_api_logging.py status

# Disable logging
python scripts/manage_api_logging.py disable

# Clean up old logs (older than 7 days)
python scripts/manage_api_logging.py cleanup

# Clean up logs older than specific days
python scripts/manage_api_logging.py cleanup --days 3
```

### Build and Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Build for Render deployment
./render-build.sh
```

## Architecture Overview

### Core Application Structure
- **app.py**: Main Quart application factory with CORS, error handling, and route registration
- **config.py**: Environment-specific configuration classes (Development, Testing, Production)
- **wsgi.py**: WSGI entry point for production deployment

### Authentication System
- **Centralized TokenManager**: Singleton pattern in `utils/auth.py` handles OAuth2 token lifecycle
- **11+ hour token caching**: Tokens are cached and automatically refreshed on expiry
- **All API endpoints use the same TokenManager instance**: No duplicate token generation

### Service Architecture (Modular Flight Package)
Located in `services/flight/`:
- **core.py**: Base `FlightService` class with common functionality
- **search.py**: `FlightSearchService` for AirShopping API integration
- **pricing.py**: `FlightPricingService` for FlightPrice API integration
- **booking.py**: `FlightBookingService` for OrderCreate API integration
- **exceptions.py**: Custom exception hierarchy for flight services
- **types.py**: Type definitions and data models

All flight services inherit from `FlightService` and use the centralized `TokenManager`.

### API Routes Structure
- **routes/verteil_flights.py**: Main flight search, pricing, and booking endpoints with comprehensive caching
- **routes/airport_routes.py**: Airport data and search endpoints with autocomplete caching
- **routes/itinerary_routes.py**: Itinerary management endpoints
- **routes/flight_storage.py**: Redis-based flight data storage endpoints

### Caching Endpoints
- **`/api/verteil/air-shopping/cache-check`**: Flight search cache validation
- **`/api/verteil/flight-price/cache-check`**: Flight pricing cache validation
- **`/api/verteil/booking/cache-check`**: Booking data cache validation
- **`/api/airports/autocomplete`**: Airport search with intelligent caching (1hr TTL)
- **`/api/flight-storage/*`**: Direct Redis storage management endpoints

### Data Processing Pipeline
- **transformers/**: Enhanced air shopping response transformation
- **utils/**: Data transformers, API loggers, cache managers, and utility functions
- **Multi-airline support**: Configurable via `VERTEIL_MULTI_AIRLINE_ID` environment variable

### Redis Configuration
- **Redis Cloud integration**: Migrated from localhost to Redis Cloud
- **Enhanced connection handling**: Centralized configuration in `config/redis_config.py`
- **Comprehensive caching system**: Full-stack cache-first architecture across all API endpoints
- **Multi-endpoint caching**: Flight search, pricing, booking, airport autocomplete, and itinerary data
- **Session-based cache keys**: Deterministic cache key generation with MD5 hashing
- **Data compression**: 70-77% compression ratio for efficient storage (average 75%)
- **Intelligent TTL management**: Variable cache expiration (15min-2hr) based on data type
- **Cache validation endpoints**: Dedicated cache-check endpoints for all major operations
- **Performance optimization**: 95%+ API call reduction, sub-100ms cache lookups
- **Automatic cache management**: Smart cache hit/miss handling with graceful fallback
- **Connection resilience**: Automatic fallback and improved error handling

## Environment Configuration

### Required Environment Variables
```bash
# Verteil NDC API Configuration
VERTEIL_API_BASE_URL=https://api.stage.verteil.com
VERTEIL_USERNAME=your_username
VERTEIL_PASSWORD=your_password
VERTEIL_CLIENT_ID=your_client_id
VERTEIL_CLIENT_SECRET=your_client_secret
VERTEIL_OFFICE_ID=OFF3746
VERTEIL_THIRD_PARTY_ID=KQ

# Multi-airline Configuration
VERTEIL_MULTI_AIRLINE_ID=""  # Empty for multi-airline, specific code for single airline

# Redis Configuration (Redis Cloud)
REDIS_URL=redis://default:your_password@redis-14657.c89.us-east-1-3.ec2.redns.redis-cloud.com:14657/0

# Legacy Redis Configuration (fallback)
REDIS_HOST=redis-14657.c89.us-east-1-3.ec2.redns.redis-cloud.com
REDIS_PORT=14657
REDIS_DB=0
REDIS_PASSWORD=your_password

# Application Configuration
QUART_ENV=development  # or testing, production
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret

# API Timeout Configuration
VERTEIL_API_TIMEOUT=60
REQUEST_TIMEOUT=30

# Logging Configuration
LOG_LEVEL=INFO
API_DEBUG_LOGGING=false  # Set to true for API request/response logging
```

## Key Development Patterns

### Making API Calls to Verteil
Always use the flight service classes which automatically handle authentication:

```python
from services.flight import FlightSearchService, FlightPricingService

async with FlightSearchService() as service:
    results = await service.search_flights(search_criteria)
```

### Error Handling
Use the custom exception hierarchy from `services.flight.exceptions`:
- `FlightServiceError`: Base exception
- `AuthenticationError`: OAuth/token issues
- `RateLimitExceeded`: Rate limiting errors
- `ValidationError`: Request validation errors

### Adding New Endpoints
1. Create route in appropriate file under `routes/`
2. Use existing service classes or extend `FlightService`
3. Register blueprint in `app.py`
4. Add tests in `tests/`

### Multi-Airline Development
- Use `VERTEIL_MULTI_AIRLINE_ID=""` for multi-airline searches
- Airline filtering configurable via `FILTER_UNSUPPORTED_AIRLINES`
- Airline mapping handled in `utils/airline_data.py`

## Testing Guidelines

### Test Structure
- Tests are located in `tests/` directory
- Use pytest with asyncio support for async tests
- API integration tests use the actual service classes
- Mock external API calls when needed

### Running Specific Tests
- Flight pricing tests: `pytest tests/test_flight_pricing_*.py`
- Air shopping tests: `pytest tests/test_air_shopping_*.py`
- Multi-airline tests: `pytest tests/test_multi_airline_*.py`

## Debug and Monitoring

### API Logging
When `API_DEBUG_LOGGING=true`, all API requests and responses are logged to `api_logs/` directory with structured JSON format for debugging.

### Health Check
- Endpoint: `GET /api/health`
- Returns application health status

### Token Status
- Debug endpoint available for monitoring token lifecycle
- Check authentication audit report for token usage patterns

## Deployment Notes

### Render Deployment
- Uses `render-build.sh` for build process
- Installs Rust dependencies for some Python packages
- Configured via `render.yaml`

### Docker Support
- `Dockerfile` available for containerized deployment
- `Procfile` for Heroku-style deployments

## Code References

When referencing specific functions or pieces of code include the pattern `file_path:line_number` to allow the user to easily navigate to the source code location.

<example>
user: Where are errors from the client handled?
assistant: Clients are marked as failed in the `connectToServer` function in src/services/process.ts:712.
</example>