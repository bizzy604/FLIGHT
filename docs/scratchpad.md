# Flight Booking Portal - Development Scratchpad

## Current Active Tasks

### Token Management Optimization
- **File**: `docs/implementation-plan/token-management-optimization.md`
- **Status**: Planning
- **Priority**: High
- **Description**: Fix token generation inefficiency where services create new tokens on each call instead of using the singleton TokenManager

## Lessons Learned

### [2024-12-19] Token Management Anti-Pattern Identified
- **Issue**: Multiple FlightService instances are being created on each API call, each generating their own tokens
- **Root Cause**: Standalone service functions (search_flights, get_flight_price, create_booking, etc.) use `async with FlightService(config) as service` pattern
- **Impact**: Bypasses the singleton TokenManager, causing unnecessary token generation requests
- **Files Affected**: 
  - `Backend/services/flight/search.py`
  - `Backend/services/flight/pricing.py` 
  - `Backend/services/flight/booking.py`

### [2024-12-19] Proper Token Management Architecture
- **Correct Pattern**: Use singleton TokenManager from `Backend/utils/auth.py`
- **TokenManager Features**: Thread-safe caching, automatic renewal, expiry buffer handling
- **Integration Point**: FlightService should use TokenManager instead of implementing its own token logic

## Project Structure Notes

- **Authentication**: Centralized in `Backend/utils/auth.py` with TokenManager singleton
- **Flight Services**: Modular structure in `Backend/services/flight/` with core.py, search.py, pricing.py, booking.py
- **API Routes**: Located in `Backend/routes/verteil_flights.py`
- **Configuration**: Environment-based config in `Backend/config.py`