# Token Management Optimization

## Background and Motivation

The current flight booking application has a token management inefficiency where multiple FlightService instances are created on each API call, each generating their own OAuth2 tokens instead of using the existing singleton TokenManager. This results in:

1. **Unnecessary API calls** to the token endpoint
2. **Performance degradation** due to redundant authentication requests
3. **Potential rate limiting issues** with the Verteil API
4. **Violation of the singleton pattern** designed for token management

### Current Problem

The standalone service functions in the flight module create new FlightService instances using the pattern:
```python
async with FlightService(config) as service:
    return await service.method()
```

Each FlightService instance has its own `_get_access_token()` method that generates tokens independently, bypassing the centralized TokenManager singleton.

### Affected Files
- `Backend/services/flight/search.py` - search_flights(), process_air_shopping()
- `Backend/services/flight/pricing.py` - get_flight_price(), process_flight_price()
- `Backend/services/flight/booking.py` - create_booking(), process_order_create(), get_booking_details()
- `Backend/services/flight/core.py` - FlightService._get_access_token() method

## Key Challenges and Analysis

1. **Architecture Mismatch**: FlightService implements its own token management instead of using TokenManager
2. **Instance Creation Pattern**: Each API call creates a new service instance
3. **Token Caching**: Multiple independent token caches instead of one centralized cache
4. **Configuration Handling**: Need to ensure TokenManager gets proper configuration

## High-level Task Breakdown

### Task 1: Create Feature Branch
- **Success Criteria**: Feature branch `fix/token-management-optimization` created from main
- **Commands**: 
  ```bash
  git checkout main
  git pull origin main
  git checkout -b fix/token-management-optimization
  ```

### Task 2: Modify FlightService to Use TokenManager
- **Success Criteria**: 
  - FlightService._get_access_token() method removed
  - FlightService uses TokenManager.get_token() instead
  - All token-related instance variables removed from FlightService
  - Tests pass for token integration
- **Files to Modify**: `Backend/services/flight/core.py`

### Task 3: Create Singleton FlightService Instance
- **Success Criteria**:
  - Single FlightService instance created and reused
  - Instance properly configured with TokenManager
  - Thread-safe access to the singleton instance
- **Files to Modify**: `Backend/services/flight/__init__.py` or new singleton module

### Task 4: Update Standalone Service Functions
- **Success Criteria**:
  - search_flights(), get_flight_price(), create_booking() functions use singleton instance
  - No more `async with FlightService(config) as service` patterns
  - All functions maintain backward compatibility
- **Files to Modify**: 
  - `Backend/services/flight/search.py`
  - `Backend/services/flight/pricing.py`
  - `Backend/services/flight/booking.py`

### Task 5: Update Tests and Validation
- **Success Criteria**:
  - All existing tests pass
  - Token generation happens only once per token lifetime
  - API calls use cached tokens appropriately
  - Integration tests verify single token usage
- **Files to Modify**: Test files in `Backend/tests/`

### Task 6: Documentation and Cleanup
- **Success Criteria**:
  - Code comments updated to reflect new architecture
  - README updated if necessary
  - Deprecated patterns removed
- **Files to Modify**: Documentation and code comments

## Branch Name
`fix/token-management-optimization`

## Project Status Board

### To Do
- [ ] Create feature branch
- [ ] Analyze current TokenManager implementation
- [ ] Modify FlightService to use TokenManager
- [ ] Create singleton FlightService pattern
- [ ] Update search.py functions
- [ ] Update pricing.py functions  
- [ ] Update booking.py functions
- [ ] Run and fix tests
- [ ] Validate token reuse behavior
- [ ] Update documentation
- [ ] Create pull request

### In Progress
- [ ] Debugging API service configuration errors

### Done
- [x] Identify root cause of token regeneration issue
- [x] Document affected files and functions
- [x] Create implementation plan
- [x] Confirmed duplicate service instances in production logs

## Current Status / Progress Tracking

**Current Phase**: Debugging API Configuration Errors
**Last Updated**: 2024-12-19
**Next Milestone**: Resolve service configuration errors preventing API responses

### Recent Progress
- ✅ Identified that FlightService instances create independent tokens
- ✅ Located all affected service functions
- ✅ Confirmed TokenManager singleton exists and works correctly
- ✅ Analyzed the async context manager pattern causing the issue
- ✅ Confirmed duplicate service instances in production logs (two simultaneous calls)
- ✅ Identified API returning service configuration errors instead of flight data

### Blockers
- API returning "Service configuration error" instead of flight search results
- Two simultaneous service instances being created per request

## Executor's Feedback or Assistance Requests

### Current Debugging Priority
**Issue**: API returning service configuration errors instead of flight data
**Evidence from logs**:
- Two simultaneous FlightService instances being created per request
- Both instances receive "Service configuration error" responses
- Transaction IDs: menBuM-1749248921744 and H7gP9O-1749248921809

### Immediate Actions Needed
1. Investigate why API is returning configuration errors
2. Check if the duplicate service calls are causing rate limiting or conflicts
3. Verify API credentials and endpoint configuration
4. Implement the token management optimization to prevent duplicate instances

### Questions for Planner
1. Should we prioritize fixing the API configuration errors first, or implement token management optimization?
2. Do we need to contact Verteil API support regarding the service configuration errors?
3. Should we implement request deduplication to prevent simultaneous calls?

### Technical Considerations
- Need to ensure thread safety when sharing FlightService instance
- TokenManager already handles thread safety, so this should be straightforward
- Configuration injection needs to be handled properly for the singleton
- API configuration errors may be related to duplicate simultaneous requests

## Lessons Learned

### [2024-12-19] Root Cause Analysis
- **Finding**: The `async with FlightService(config) as service` pattern creates new instances on every call
- **Impact**: Each instance has independent token management, bypassing the singleton TokenManager
- **Solution**: Use a singleton FlightService instance that leverages the existing TokenManager

### [2024-12-19] Architecture Insight
- **Finding**: TokenManager singleton is well-designed and thread-safe
- **Finding**: FlightService has redundant token management that should be removed
- **Recommendation**: Integrate FlightService with TokenManager rather than replacing it