# REA Flight Portal - AI Development Guide

## Project Architecture

### System Overview
End-to-end NDC (New Distribution Capability) flight booking platform with Python/Quart backend and Next.js frontend. The system integrates with Verteil NDC APIs for multi-airline flight operations with heavy emphasis on **Redis-backed caching** to minimize API calls and support resilient booking flows.

**Critical Flow**: AirShopping → FlightPrice → SeatAvailability/ServiceList → OrderCreate

### Technology Stack
- **Backend**: Python 3.10+, Quart (async Flask), Redis, psycopg3, pytest
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, Clerk auth, Prisma
- **Infrastructure**: Redis (required), Hypercorn ASGI server, PostgreSQL

## Essential Architectural Patterns

### 1. Centralized Authentication (TokenManager Singleton)
**Location**: `Backend/utils/auth.py`

```python
# ALWAYS use the singleton instance - never create new instances
from utils.auth import TokenManager
token_manager = TokenManager.get_instance()
```

- **11+ hour token caching** with automatic refresh
- Thread-safe singleton pattern prevents duplicate token generation
- Tokens are persisted to disk to survive server restarts
- All flight services inherit from `FlightService` which uses this singleton

**Never** create manual token requests - the TokenManager handles everything.

### 2. Modular Flight Service Architecture
**Location**: `Backend/services/flight/`

```
flight/
  ├── core.py          # Base FlightService class with auth & HTTP handling
  ├── search.py        # FlightSearchService (AirShopping)
  ├── pricing.py       # FlightPricingService (FlightPrice)
  ├── booking.py       # FlightBookingService (OrderCreate)
  ├── exceptions.py    # Custom exception hierarchy
  ├── decorators.py    # @async_cache, @async_rate_limited
  └── types.py         # Type definitions
```

**Pattern**: All services inherit from `FlightService` and use async/await throughout.

### 3. Cache-First Architecture (The Critical Pattern)
**Primary Services**: 
- `Backend/services/unified_cache_service.py` - High-level cache abstraction
- `Backend/services/redis_flight_storage.py` - Low-level Redis operations
- `Backend/services/simple_flight_cache.py` - Simplified cache interface

**Key Principle**: Backend caches **raw NDC responses** (not transformed data) so the booking flow can proceed even if the frontend loses response data.

```python
# Cache key format examples:
flight_search_{session_id}
flight_price_raw_{request_id}_{timestamp}
seat_availability_{session_id}
service_list_{session_id}
```

**TTL Policies** (from `UnifiedCacheService`):
- Flight search/price: 1800s (30 min)
- Seat/Service data: 900s (15 min)  
- Booking data: 3600s (1 hour)

### 4. NDC Data Flow & Mapping
**Critical Document**: `documentations/vdc-api-documentation.md`

The OrderCreate payload is built by mapping data from THREE sources:
1. **FlightPriceRS** → OrderCreateRQ (base flight offer)
2. **SeatAvailabilityRS** → OrderCreateRQ (seat selections)
3. **ServiceListRS** → OrderCreateRQ (baggage/meals)

**Location**: `Backend/scripts/build_ordercreate_rq.py`

Key mapping functions:
- `process_payments_for_order_create_fixed()` - Payment structure
- `build_order_create_request()` - Main OrderCreate builder

**Common Pitfall**: Raw NDC responses must be unwrapped before use:
```python
# CORRECT - unwrap FlightPriceRS wrapper
if 'FlightPriceRS' in flight_price_response:
    flight_price_response = flight_price_response['FlightPriceRS']

# For seat/service - extract raw_response
if 'raw_response' in seat_data:
    seat_data = seat_data['raw_response']
```

### 5. Frontend API Integration Pattern
**Location**: `Frontend/utils/simple-api-manager.ts`

```typescript
// ✅ PREFERRED: Simple, focused API calls with deduplication
const api = SimpleApiManager.getInstance();
await api.getFlightPrice(flightIndex, shoppingResponseId, airShoppingResponse);
await api.getSeatAvailability(flightPriceResponse);
await api.createBooking(flightOffer, passengers, payment, contactInfo, extras);
```

**Cache Key Propagation**: Backend returns `storage_key` values that frontend passes back to enable cache retrieval without resending full responses.

## Development Workflows

### Running Tests
```bash
# Backend (from Backend/ directory)
python -m pytest                          # All tests
python -m pytest tests/test_*.py          # Specific test file
python -m pytest -v -s                    # Verbose with print output
python -m pytest --cov=Backend            # With coverage

# Frontend (from Frontend/ directory)
npm test                                  # Jest tests
npm run test:watch                        # Watch mode
```

### Running the Application
```bash
# Backend (Backend/)
python app.py                             # Development mode (port 5000)
# Production uses Hypercorn via render-build.sh

# Frontend (Frontend/)
npm run dev                               # Development (port 3000)
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000 npm run dev
```

### API Logging & Debugging
```bash
# Enable detailed API request/response logging
python scripts/manage_api_logging.py enable

# Check status
python scripts/manage_api_logging.py status

# Cleanup old logs
python scripts/manage_api_logging.py cleanup --days 7
```

### Redis Operations
```bash
# Clear all cached flight data
python Backend/clear_cache.py

# Enhanced cache clearing with pattern support
python Backend/enhanced_cache_clearer.py
```

## Project-Specific Conventions

### Backend Conventions

1. **All routes use `@route_cors` decorator** (from `quart_cors`):
```python
from quart_cors import route_cors

@bp.route('/endpoint', methods=['POST', 'OPTIONS'])
@route_cors(allow_origin=ALLOWED_ORIGINS, allow_methods=["POST", "OPTIONS"], ...)
async def handler():
    pass
```

2. **Request IDs for tracing**:
```python
request_id = data.get('request_id', str(uuid.uuid4()))
```

3. **Async context managers** for service cleanup:
```python
async with service._get_session() as session:
    # HTTP calls here
```

4. **Enhanced error logging pattern**:
```python
logger.info(f"🔥 Starting operation: {operation_name}")
logger.error(f"🔴 ERROR in {operation_name}: {error}", exc_info=True)
```

5. **Environment variable pattern** (from `config.py`):
```python
VERTEIL_API_BASE_URL = os.environ.get('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
```

### Frontend Conventions

1. **TypeScript strict mode** - all API responses are typed
2. **shadcn/ui components** - use existing components from `components/ui/`
3. **Session management** via `utils/session-manager.ts`
4. **Error boundaries** for flight search/booking flows
5. **Cache managers**: 
   - `utils/simple-cache-manager.ts` - Client-side caching
   - `utils/seat-service-cache-manager.ts` - Ancillary data caching

### Testing Conventions

1. **Backend**: pytest with fixtures, async test functions
```python
import pytest

@pytest.fixture
def sample_flight_data():
    return {...}

async def test_flight_pricing(sample_flight_data):
    result = await service.get_flight_price(...)
    assert result['status'] == 'success'
```

2. **Integration tests** include real cache operations (see `test_ancillary_cache_integration.py`)

## Critical Integration Points

### 1. Payment Flow
**Entry**: `Frontend/app/flights/[id]/payment/page.tsx`
**Backend**: `Backend/routes/verteil_flights.py` → `/order-create`

Payload structure:
```typescript
{
  flight_price_response: {...},      // Can be cache key OR full response
  passengers: [...],
  payment: {...},
  contact_info: {...},
  flight_price_cache_key: "...",     // ✅ Preferred - use cache
  seat_availability_cache_key: "...",
  service_list_cache_key: "...",
  selected_seats: [...],
  selected_services: [...]
}
```

### 2. Ancillary Pricing Routes
**Location**: `Backend/routes/ancillary_pricing_routes.py`

Three endpoints that support cache key retrieval:
- `/pricing/price-ancillaries` - Complete pricing (flight + seats + services)
- `/pricing/price-seats-only` - Seats only
- `/pricing/price-services-only` - Services only

**Pattern**: Accept `*_cache_key` parameters, retrieve from Redis, unwrap nested structures

### 3. Redis Storage Endpoints
**Location**: `Backend/routes/flight_storage.py`

Direct cache access for debugging:
- `GET /api/flight-storage/search?session_id=...`
- `GET /api/flight-storage/price?session_id=...`
- `GET /api/flight-storage/booking?session_id=...`

## Documentation Reference

Key docs (in `documentations/` and `Backend/`):
- `CLAUDE.md` - Development commands and architecture overview
- `vdc-api-documentation.md` - NDC API specification and mapping rules
- `ANCILLARY_CACHE_COMPLETE_IMPLEMENTATION.md` - Cache retrieval patterns
- `ORDERCREATE_FINAL_SOLUTION.md` - OrderCreate payload construction
- Backend/*.md files - Various implementation summaries and troubleshooting guides

## Common Pitfalls & Solutions

### ❌ Creating Multiple TokenManager Instances
```python
# WRONG
manager = TokenManager()

# RIGHT
manager = TokenManager.get_instance()
```

### ❌ Not Unwrapping NDC Responses
```python
# WRONG - may have nested FlightPriceRS wrapper
service.process(flight_price_response)

# RIGHT
if 'FlightPriceRS' in flight_price_response:
    flight_price_response = flight_price_response['FlightPriceRS']
```

### ❌ Sending Full Responses When Cache Keys Available
```python
# WRONG - wasteful, large payload
payload = {flight_price_response: {...huge object...}}

# RIGHT - use cache keys
payload = {flight_price_cache_key: "flight_price_raw_abc123"}
```

### ❌ Forgetting Async/Await
All backend service methods are async. Always use `await`.

## Environment Variables Checklist

**Backend** (`.env` in Backend/):
```bash
VERTEIL_API_BASE_URL=https://api.stage.verteil.com
VERTEIL_USERNAME=...
VERTEIL_PASSWORD=...
VERTEIL_OFFICE_ID=OFF3746
REDIS_URL=redis://localhost:6379/0  # Required!
API_DEBUG_LOGGING=true  # Optional
```

**Frontend** (`.env.local` in Frontend/):
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
DATABASE_URL=postgresql://...  # For Prisma
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
```

## Quick Start for AI Agents

1. **Understanding the flow**: Read `Backend/flow_diagram.txt` and `documentations/vdc-api-documentation.md`
2. **Making changes to services**: Start in `Backend/services/flight/` - inherit from `FlightService`
3. **Adding endpoints**: Use `Backend/routes/` blueprints with `@route_cors`
4. **Cache operations**: Use `UnifiedCacheService` or `SimpleFlightCache`, never raw Redis
5. **Testing changes**: Write pytest tests in `Backend/tests/`, run with `-v -s` for debugging
6. **Frontend changes**: Use TypeScript strict, follow existing patterns in `utils/` and `components/`

## Additional Notes

- **Airline filtering**: Set `FILTER_UNSUPPORTED_AIRLINES=true` to limit results (see `config.py`)
- **Request size limits**: Backend accepts up to 100MB requests (for large flight data)
- **Rate limiting**: Configured per-endpoint, uses `@async_rate_limited` decorator
- **CORS**: Explicitly configured in `config.py` CORS_ORIGINS list
- **Session IDs**: Generated via `uuid.uuid4()`, used for cache scoping
