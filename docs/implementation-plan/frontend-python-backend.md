# Frontend Integration with Python Backend Plan

## Overview
This plan focuses on modifying the Next.js frontend to integrate with the existing Python backend. All backend implementation remains unchanged - we only reference its API structure for frontend integration.

## Phase 1: Frontend API Client Update (1-2 days)

### 1.1 Environment Configuration
- Update `.env` with Python backend URL
- Configure API client base URL
- Set up request/response interceptors
- Implement error handling middleware

### 1.2 API Client Implementation
- Create new API client class
- Implement request/response handlers
- Add loading state management
- Configure retry logic

## Phase 2: Flight Search Integration (2-3 days)

### 2.1 Update Flight Search Form
- Modify search form component
- Update request payload format
- Add loading states
- Implement error handling

### 2.2 Update Search Results
- Modify results display component
- Update data mapping
- Handle Python backend response format
- Add loading indicators

## Phase 3: Booking Flow Integration (2-3 days)

### 3.1 Flight Pricing
- Update pricing component
- Modify request payload
- Handle response format
- Add loading states

### 3.2 Passenger Details
- Update passenger form
- Modify data structure
- Add validation
- Implement error handling

### 3.3 Booking Confirmation
- Update booking flow
- Modify request format
- Handle booking response
- Add success/error states

## Phase 4: Payment Integration (1-2 days)

### 4.1 Payment Form
- Update payment component
- Modify request format
- Add validation
- Implement error handling

### 4.2 Payment Processing
- Update payment flow
- Handle response format
- Add loading states
- Implement success/error states

## Phase 5: Admin Interface (1-2 days)

### 5.1 Booking Management
- Update booking management
- Modify API calls
- Handle response format
- Add error handling

### 5.2 Reports
- Update reports integration
- Modify data fetching
- Handle response format
- Add error handling

## Phase 6: Testing (2-3 days)

### 6.1 Unit Tests
- Update existing tests
- Add new tests for API integration
- Test error handling
- Verify loading states

### 6.2 Integration Tests
- Test complete booking flow
- Verify API responses
- Test edge cases
- Validate error handling

## Technical Details

### Backend API Reference (DO NOT MODIFY)
- `/api/verteil/air-shopping`
  - Request: tripType, odSegments, passenger counts, cabin preference
  - Response: flight offers with pricing

- `/api/verteil/flight-price`
  - Request: offer_id, shopping_response_id, air_shopping_rs
  - Response: detailed pricing information

- `/api/verteil/order-create`
  - Request: flight_offer, passengers, payment, contact_info
  - Response: booking confirmation

### Frontend Changes Only
- Update API client configuration
- Modify request/response handlers
- Update component data mapping
- Add proper error handling
- Implement loading states

## Success Criteria

1. Frontend successfully integrates with Python backend
2. All API calls properly formatted
3. Error handling implemented
4. Loading states working
5. Data mapping correct
6. User experience maintained
7. Tests passing

## Blockers and Risks

1. CORS configuration issues
2. Data format mismatches
3. Network latency
4. Error handling edge cases
5. Loading state management

## Monitoring

1. API response times
2. Error rates
3. User experience
4. Loading times
5. Booking success rate