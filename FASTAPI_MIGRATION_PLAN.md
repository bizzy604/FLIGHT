# FastAPI Migration Plan - REA Flight Portal Backend

## 🎯 Executive Summary

**Current State**: Quart-based backend with 8,000+ lines, heavy Redis dependency, complex caching layer
**Target State**: FastAPI-based backend with ~2,000 lines, no Redis, KISS principle, industry best practices

**Estimated Effort**: 3-5 days
**Risk Level**: Medium (API contracts must remain compatible with existing frontend)

---

## 📊 Current Architecture Analysis

### Problems Identified

1. **Over-Engineering**
   - Complex Redis caching layer with 3+ cache service implementations
   - Singleton patterns for simple HTTP clients
   - Disk persistence for tokens (unnecessary complexity)
   - Multiple service layers doing similar things

2. **Code Bloat & Duplication**
   - 10 separate route files for 5 core endpoints
   - Multiple transformer classes with overlapping logic
   - 3 different cache services (`UnifiedCacheService`, `SimpleFlightCache`, `RedisFlightStorage`)
   - Duplicate payload builders across multiple files

3. **Poor Separation of Concerns**
   - Business logic mixed with HTTP handling in routes
   - Transformers contain business rules
   - Cache logic scattered across services
   - Authentication tied to service classes

4. **Unnecessary Dependencies**
   - Redis for simple session data (frontend can handle this)
   - SQLAlchemy without database usage
   - psycopg3 without PostgreSQL
   - Quart-specific CORS handling

### Current File Structure

```
Backend/
├── app.py (300+ lines)                    # Quart app setup
├── config.py (200+ lines)                 # Over-configured
├── routes/ (10 files, 3000+ lines)        # Too fragmented
│   ├── verteil_flights.py (1976 lines!)
│   ├── ancillary_pricing_routes.py
│   ├── clean_seat_service.py
│   ├── enhanced_ordercreate_routes.py
│   ├── seat_and_service_routes.py
│   ├── airport_routes.py
│   ├── itinerary_routes.py
│   ├── flight_storage.py
│   ├── cache_health.py
│   └── cache_test_routes.py
├── services/ (6 files, 2000+ lines)       # Over-abstracted
│   ├── flight/
│   │   ├── core.py
│   │   ├── search.py
│   │   ├── pricing.py
│   │   ├── booking.py
│   │   ├── decorators.py
│   │   └── types.py
│   ├── unified_cache_service.py
│   ├── simple_flight_cache.py
│   ├── redis_flight_storage.py
│   └── airline_mapping_service.py
├── utils/ (15+ files, 2500+ lines)        # Utility hell
│   ├── auth.py (537 lines!)
│   ├── cache_manager.py
│   ├── air_shopping_transformer.py
│   ├── flight_price_transformer.py
│   ├── seat_availability_transformer.py
│   ├── service_list_transformer.py
│   ├── data_transformer.py
│   ├── data_transformer_roundtrip.py
│   ├── request_builders.py
│   ├── reference_extractor.py
│   └── ... (5+ more)
└── scripts/ (5+ files)                    # Mostly debugging
```

**Total**: ~8,000 lines of production code + 5,000 lines of test files

---

## 🎨 Target Architecture (FastAPI)

### Design Principles

1. **KISS (Keep It Simple, Stupid)**
   - One file per concern
   - No unnecessary abstractions
   - Direct, readable code

2. **Separation of Concerns**
   - Routes handle HTTP only
   - Services handle business logic
   - Models handle data validation
   - Utils are pure functions

3. **Industry Standards**
   - PEP 8 style guide
   - Type hints everywhere
   - Dependency injection
   - OpenAPI/Swagger auto-docs

4. **No Premature Optimization**
   - No caching until proven necessary
   - No Redis (frontend can cache)
   - No complex patterns for simple tasks

### New File Structure

```
Backend/
├── main.py                              # FastAPI app entry point (100 lines)
├── config.py                            # Environment config (50 lines)
├── requirements.txt                     # Minimal dependencies (10 packages)
│
├── app/
│   ├── __init__.py
│   ├── models/                          # Pydantic models
│   │   ├── __init__.py
│   │   ├── requests.py                  # Request models (150 lines)
│   │   └── responses.py                 # Response models (150 lines)
│   │
│   ├── api/                             # API routes
│   │   ├── __init__.py
│   │   ├── deps.py                      # Dependencies (auth, etc.) (50 lines)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py                # Health check (20 lines)
│   │       ├── flights.py               # Flight endpoints (250 lines)
│   │       └── airports.py              # Airport lookup (50 lines)
│   │
│   ├── core/                            # Core functionality
│   │   ├── __init__.py
│   │   ├── auth.py                      # TokenManager (100 lines)
│   │   └── client.py                    # Verteil HTTP client (150 lines)
│   │
│   └── services/                        # Business logic
│       ├── __init__.py
│       ├── payload_builder.py           # All request builders (200 lines)
│       └── transformer.py               # All response transformers (150 lines)
│
├── tests/                               # Pytest tests
│   ├── __init__.py
│   ├── conftest.py                      # Test fixtures
│   ├── test_auth.py
│   ├── test_client.py
│   ├── test_routes.py
│   └── test_transformers.py
│
└── scripts/                             # Utility scripts
    └── generate_sample_data.py
```

**Total**: ~1,500-2,000 lines of production code

---

## 🔧 Migration Strategy

### Phase 1: Setup FastAPI Foundation (Day 1)

**Goal**: Create minimal FastAPI app with auth and health check

**Tasks**:
1. Create new `app/` directory structure
2. Install FastAPI dependencies
3. Implement `main.py` with basic app setup
4. Port `config.py` (simplify to essentials only)
5. Implement `app/core/auth.py` (simplified TokenManager)
6. Implement `app/core/client.py` (basic HTTP client)
7. Create health check endpoint
8. Test authentication works

**Files Created**:
- `main.py`
- `config.py`
- `requirements.txt`
- `app/__init__.py`
- `app/core/auth.py`
- `app/core/client.py`
- `app/api/deps.py`
- `app/api/routes/health.py`

**Success Criteria**:
- ✅ FastAPI app starts
- ✅ Health check returns 200
- ✅ Token authentication works
- ✅ Swagger docs accessible at `/docs`

---

### Phase 2: Core API Endpoints (Day 2)

**Goal**: Implement 5 core Verteil NDC endpoints

**Tasks**:
1. Define Pydantic models for requests/responses
2. Implement payload builders (consolidate from old code)
3. Implement transformers (consolidate from old code)
4. Create `/air-shopping` endpoint
5. Create `/flight-price` endpoint
6. Create `/seat-availability` endpoint
7. Create `/service-list` endpoint
8. Create `/order-create` endpoint
9. Add CORS middleware
10. Add error handling

**Files Created**:
- `app/models/requests.py`
- `app/models/responses.py`
- `app/services/payload_builder.py`
- `app/services/transformer.py`
- `app/api/routes/flights.py`

**Success Criteria**:
- ✅ All 5 endpoints respond
- ✅ Request validation works (Pydantic)
- ✅ Transformers convert NDC responses correctly
- ✅ CORS headers present
- ✅ Error responses are consistent

---

### Phase 3: Airport & Utility Endpoints (Day 3)

**Goal**: Implement supporting endpoints

**Tasks**:
1. Port airport lookup functionality
2. Create airport search endpoint
3. Remove all Redis dependencies
4. Remove all cache-related endpoints
5. Simplify response structures
6. Add request/response logging (optional)

**Files Created**:
- `app/api/routes/airports.py`

**Success Criteria**:
- ✅ Airport search works
- ✅ No Redis code remains
- ✅ All endpoints documented in Swagger

---

### Phase 4: Testing & Validation (Day 4)

**Goal**: Ensure API compatibility with frontend

**Tasks**:
1. Write unit tests for all endpoints
2. Write integration tests for full booking flow
3. Test with actual frontend (or Postman)
4. Document API differences (if any)
5. Create migration guide for frontend team
6. Performance testing (ensure no regressions)

**Files Created**:
- `tests/conftest.py`
- `tests/test_auth.py`
- `tests/test_client.py`
- `tests/test_routes.py`
- `tests/test_transformers.py`
- `MIGRATION_NOTES.md`

**Success Criteria**:
- ✅ 80%+ test coverage
- ✅ All critical paths tested
- ✅ Frontend integration confirmed
- ✅ Response times < 2s (95th percentile)

---

### Phase 5: Deployment & Cleanup (Day 5)

**Goal**: Deploy to production, remove old code

**Tasks**:
1. Update `render.yaml` for FastAPI
2. Create new `Dockerfile` (if needed)
3. Update environment variables
4. Deploy to staging
5. Smoke test all endpoints
6. Deploy to production
7. Archive old Quart code
8. Update documentation

**Files Updated**:
- `render.yaml`
- `Dockerfile`
- `.env.example`
- `README.md`

**Success Criteria**:
- ✅ Staging deployment successful
- ✅ Production deployment successful
- ✅ All smoke tests pass
- ✅ Old code archived (not deleted yet)

---

## 📦 Dependencies Comparison

### Current (Quart)
```txt
quart>=0.18.0
quart-cors>=0.0.4
python-dotenv>=1.0.0
pyjwt>=2.8.0
requests>=2.31.0
python-multipart>=0.0.6
psycopg[binary]~=3.2           # ❌ Not used
SQLAlchemy>=2.0.20             # ❌ Not used
aiohttp>=3.8.6
cryptography>=41.0.3
pydantic>=1.10.12,<2.0.0
pydantic_core>=2.1.2,<3.0.0
urllib3>=2.0.4
websockets>=11.0.3             # ❌ Not needed
yarl>=1.9.2
gunicorn==21.2.0
uvicorn[standard]==0.23.2
Werkzeug==2.3.7
alembic==1.14.1                # ❌ Not used
redis>=4.5.0                   # ❌ Removing
```

**Total**: ~25 packages

### Target (FastAPI)
```txt
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# HTTP Client
httpx>=0.25.0

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Environment
python-dotenv>=1.0.0

# Authentication
python-jose[cryptography]>=3.3.0  # For JWT tokens

# Utilities
python-multipart>=0.0.6           # For file uploads (if needed)
```

**Total**: ~8 packages (68% reduction)

---

## 🔄 API Contract Mapping

### Endpoint Comparison

| Old Route (Quart) | New Route (FastAPI) | Status | Changes |
|-------------------|---------------------|--------|---------|
| `POST /api/verteil/air-shopping` | `POST /api/flights/search` | ✅ Keep | Rename for clarity |
| `POST /api/verteil/flight-price` | `POST /api/flights/price` | ✅ Keep | Rename for clarity |
| `POST /api/verteil/seat-availability` | `POST /api/flights/seats` | ✅ Keep | Rename for clarity |
| `POST /api/verteil/service-list` | `POST /api/flights/services` | ✅ Keep | Rename for clarity |
| `POST /api/verteil/order-create` | `POST /api/flights/book` | ✅ Keep | Rename for clarity |
| `GET /api/airports/search` | `GET /api/airports/search` | ✅ Keep | No change |
| `GET /api/health` | `GET /api/health` | ✅ Keep | No change |
| `GET /api/cache-health` | N/A | ❌ Remove | No Redis |
| `POST /api/pricing/*` | N/A | ❌ Remove | Merge into main endpoints |
| `GET /api/flight-storage/*` | N/A | ❌ Remove | No caching |

### Request/Response Format Changes

**All endpoints will maintain backward compatibility** except:
- Remove all `*_cache_key` parameters (no longer needed)
- Remove `storage_key` from responses
- Simplify error response format to FastAPI standard

---

## 🎯 Code Consolidation Map

### Authentication (537 lines → 100 lines)

**Remove**:
- Disk persistence for tokens
- Metrics tracking
- Complex cooldown logic
- Thread-safe singleton (FastAPI handles this with DI)

**Keep**:
- Token refresh logic
- Basic auth token generation
- Token expiry checking

### Services (2000+ lines → 350 lines)

**Consolidate**:
- `services/flight/core.py` + `search.py` + `pricing.py` + `booking.py` → `app/core/client.py`
- All cache services → Delete entirely
- `airline_mapping_service.py` → Inline into transformer

### Routes (3000+ lines → 300 lines)

**Consolidate**:
- All `routes/*.py` → `app/api/routes/flights.py` (250 lines)
- `airport_routes.py` → `app/api/routes/airports.py` (50 lines)

### Utils (2500+ lines → 350 lines)

**Consolidate**:
- All `*_transformer.py` files → `app/services/transformer.py` (150 lines)
- All `*_builder.py` files → `app/services/payload_builder.py` (200 lines)
- `auth.py` → `app/core/auth.py` (100 lines, simplified)

**Delete**:
- `cache_manager.py`
- `reference_extractor.py` (inline if needed)
- `multi_airline_*.py` (inline if needed)

---

## 🧪 Testing Strategy

### Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical paths
- **E2E Tests**: Full booking flow

### Test Structure

```
tests/
├── conftest.py                    # Fixtures
├── unit/
│   ├── test_auth.py              # Token manager
│   ├── test_payload_builder.py   # Request builders
│   └── test_transformer.py       # Response transformers
├── integration/
│   ├── test_flight_search.py     # Air shopping flow
│   ├── test_booking_flow.py      # Full booking
│   └── test_error_handling.py    # Error scenarios
└── e2e/
    └── test_complete_booking.py   # End-to-end
```

### Key Test Scenarios

1. **Authentication**
   - Token generation
   - Token refresh
   - Token expiry handling

2. **Flight Search**
   - One-way search
   - Round-trip search
   - Multi-city search
   - Invalid input handling

3. **Booking Flow**
   - Search → Price → Seats → Services → Book
   - Error handling at each step
   - Validation errors

4. **Error Handling**
   - Network errors
   - API errors
   - Validation errors
   - Rate limiting (if added)

---

## 🚀 Deployment Changes

### Environment Variables

**Remove**:
```bash
REDIS_URL
CACHE_TYPE
CACHE_REDIS_URL
CACHE_DEFAULT_TIMEOUT
RATELIMIT_DEFAULT
API_KEY_AUTH_ENABLED
API_KEYS
REQUEST_DEDUPLICATION_ENABLED
REQUEST_DEDUPLICATION_TTL
```

**Keep**:
```bash
VERTEIL_API_BASE_URL
VERTEIL_USERNAME
VERTEIL_PASSWORD
VERTEIL_OFFICE_ID
VERTEIL_THIRD_PARTY_ID
VERTEIL_API_TIMEOUT
JWT_SECRET_KEY
CORS_ORIGINS
LOG_LEVEL
```

**Add**:
```bash
# FastAPI specific
FASTAPI_ENV=production
WORKERS=4
```

### Render.yaml Changes

```yaml
services:
  - type: web
    name: flight-portal-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4"
    envVars:
      - key: FASTAPI_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.11
```

### Docker Changes

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## ⚠️ Risk Assessment

### High Risk Items

1. **API Contract Changes**
   - **Risk**: Frontend breaks if request/response format changes
   - **Mitigation**: Maintain exact same request/response schemas
   - **Fallback**: Keep old Quart app running in parallel during migration

2. **Token Management**
   - **Risk**: Simplified token manager might have bugs
   - **Mitigation**: Thorough testing with real API
   - **Fallback**: Copy old token logic if needed

### Medium Risk Items

1. **Performance Regression**
   - **Risk**: Removing cache might slow down responses
   - **Mitigation**: Benchmark before/after, add caching if needed
   - **Fallback**: Add simple in-memory cache (functools.lru_cache)

2. **Missing Edge Cases**
   - **Risk**: Old code handles edge cases we don't know about
   - **Mitigation**: Extensive testing, gradual rollout
   - **Fallback**: Keep old code for reference

### Low Risk Items

1. **Dependency Issues**
   - **Risk**: FastAPI ecosystem incompatibility
   - **Mitigation**: Use stable, well-maintained packages
   - **Fallback**: N/A (FastAPI is production-ready)

---

## 📋 Implementation Checklist

### Pre-Migration
- [ ] Backup current codebase
- [ ] Document all current API endpoints
- [ ] Review frontend API usage patterns
- [ ] Set up new Git branch: `feature/fastapi-migration`

### Phase 1: Foundation
- [ ] Create `app/` directory structure
- [ ] Install FastAPI and dependencies
- [ ] Implement `main.py`
- [ ] Port `config.py` (simplified)
- [ ] Implement `app/core/auth.py`
- [ ] Implement `app/core/client.py`
- [ ] Create health check endpoint
- [ ] Test token generation

### Phase 2: Core Endpoints
- [ ] Define Pydantic request models
- [ ] Define Pydantic response models
- [ ] Implement payload builders
- [ ] Implement transformers
- [ ] Create `/air-shopping` endpoint
- [ ] Create `/flight-price` endpoint
- [ ] Create `/seat-availability` endpoint
- [ ] Create `/service-list` endpoint
- [ ] Create `/order-create` endpoint
- [ ] Add CORS middleware
- [ ] Add error handling middleware

### Phase 3: Support Features
- [ ] Implement airport search
- [ ] Remove all Redis code
- [ ] Remove cache endpoints
- [ ] Add request logging (optional)
- [ ] Update Swagger docs

### Phase 4: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test with frontend
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Create migration guide

### Phase 5: Deployment
- [ ] Update `requirements.txt`
- [ ] Update `render.yaml`
- [ ] Update `.env.example`
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Archive old code

### Post-Migration
- [ ] Update documentation
- [ ] Train team on new structure
- [ ] Delete old code (after 2 weeks)
- [ ] Celebrate! 🎉

---

## 📚 Key Files Reference

### Must Read Before Starting

1. **Current Implementation**
   - `Backend/app.py` - Current Quart app setup
   - `Backend/routes/verteil_flights.py` - Main route logic
   - `Backend/utils/auth.py` - Token management
   - `Backend/services/flight/core.py` - HTTP client logic

2. **Data Flow Documentation**
   - `documentations/vdc-api-documentation.md` - NDC API spec
   - `Backend/flow_diagram.txt` - Current flow
   - `.github/copilot-instructions.md` - Architecture notes

### Must Create

1. **New Core Files**
   - `main.py` - FastAPI app entry
   - `app/core/auth.py` - Simplified token manager
   - `app/core/client.py` - HTTP client
   - `app/services/payload_builder.py` - Request builders
   - `app/services/transformer.py` - Response transformers
   - `app/api/routes/flights.py` - All flight endpoints

---

## 🎓 Best Practices to Follow

### Python Style (PEP 8)

```python
# ✅ Good
class FlightSearchRequest(BaseModel):
    """Request model for flight search."""
    trip_type: str = Field(..., description="ONE_WAY or ROUND_TRIP")
    segments: List[FlightSegment]
    adults: int = Field(1, ge=1, le=9)

# ❌ Bad
class flightSearchRequest:  # Wrong naming
    tripType: str  # Wrong casing, no validation
```

### Type Hints

```python
# ✅ Good
async def search_flights(
    request: FlightSearchRequest,
    client: VerteilClient = Depends(get_client)
) -> FlightSearchResponse:
    """Search for flights."""
    # ...

# ❌ Bad
async def search_flights(request, client):  # No types
    # ...
```

### Dependency Injection

```python
# ✅ Good
from fastapi import Depends

async def get_client() -> VerteilClient:
    """Get Verteil API client."""
    return VerteilClient()

@app.post("/search")
async def search(
    request: FlightSearchRequest,
    client: VerteilClient = Depends(get_client)
):
    # client is injected automatically

# ❌ Bad
client = VerteilClient()  # Global singleton

@app.post("/search")
async def search(request: FlightSearchRequest):
    # Using global client
```

### Error Handling

```python
# ✅ Good
from fastapi import HTTPException

@app.post("/search")
async def search(request: FlightSearchRequest):
    try:
        result = await client.search_flights(request)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=502, detail="External API error")

# ❌ Bad
@app.post("/search")
async def search(request: FlightSearchRequest):
    result = await client.search_flights(request)  # No error handling
    return result
```

---

## 🏁 Success Metrics

### Code Quality
- ✅ Total lines of code < 2,000 (75% reduction)
- ✅ Cyclomatic complexity < 10 per function
- ✅ Test coverage > 80%
- ✅ No linting errors (flake8, mypy)

### Performance
- ✅ Response times ≤ current system
- ✅ Startup time < 1 second
- ✅ Memory usage < 200MB

### Maintainability
- ✅ New developer can understand codebase in < 2 hours
- ✅ All functions have docstrings
- ✅ Type hints on all functions
- ✅ Swagger docs auto-generated

### Reliability
- ✅ All tests passing
- ✅ No production errors in first week
- ✅ 99.9% uptime

---

## 📞 Support & Resources

### FastAPI Resources
- [Official Docs](https://fastapi.tiangolo.com)
- [Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

### Python Style Guides
- [PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Type Hints Guide](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)

### Tools
- [Black](https://black.readthedocs.io/) - Code formatter
- [mypy](http://mypy-lang.org/) - Type checker
- [flake8](https://flake8.pycqa.org/) - Linter
- [pytest](https://docs.pytest.org/) - Testing framework

---

## 🎉 Expected Outcomes

After migration:
1. **Codebase is 75% smaller** (easier to maintain)
2. **No Redis dependency** (simpler deployment)
3. **Industry-standard patterns** (easier onboarding)
4. **Auto-generated API docs** (better DX)
5. **Type safety** (fewer bugs)
6. **Faster startup** (< 1 second)
7. **Better testability** (dependency injection)
8. **Cleaner architecture** (separation of concerns)

---

**Document Version**: 1.0  
**Last Updated**: October 27, 2025  
**Author**: AI Assistant  
**Status**: Ready for Review
