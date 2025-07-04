# Output Folder - API Payload and Response Logging

This folder contains automatically generated files that capture the payloads and responses for the three main flight booking endpoints. These files are created for debugging and cross-checking purposes to ensure data consistency between the UI and backend.

## File Types

### Frontend Request Data
- `FRONTEND_AIR_SHOPPING_REQUEST_*.json` - Data sent from frontend to backend for air shopping
- `FRONTEND_FLIGHT_PRICE_REQUEST_*.json` - Data sent from frontend to backend for flight pricing
- `FRONTEND_ORDER_CREATE_REQUEST_*.json` - Data sent from frontend to backend for order creation

### Backend Response Data
- `AIR_SHOPPING_BACKEND_RESPONSE_*.json` - Response data sent from backend to frontend for air shopping
- `FLIGHT_PRICE_BACKEND_RESPONSE_*.json` - Response data sent from backend to frontend for flight pricing
- `ORDER_CREATE_BACKEND_RESPONSE_*.json` - Response data sent from backend to frontend for order creation

### API Request/Response Data
- `AirShopping_REQUEST_*.json` - Actual payload sent to Verteil NDC API for air shopping
- `AirShopping_RESPONSE_*.json` - Raw response received from Verteil NDC API for air shopping
- `FlightPrice_REQUEST_*.json` - Actual payload sent to Verteil NDC API for flight pricing
- `FlightPrice_RESPONSE_*.json` - Raw response received from Verteil NDC API for flight pricing
- `OrderCreate_REQUEST_*.json` - Actual payload sent to Verteil NDC API for order creation
- `OrderCreate_RESPONSE_*.json` - Raw response received from Verteil NDC API for order creation

## File Structure

Each JSON file contains:
```json
{
  "timestamp": "2025-07-04T20:37:00.000Z",
  "description": "Description of the data",
  "data": {
    // Actual payload or response data
  }
}
```

## Usage

These files help you:
1. **Debug data transformation issues** - Compare what the frontend sends vs what the backend processes
2. **Verify API payloads** - Check the exact data being sent to the Verteil NDC API
3. **Analyze response structures** - Understand the raw API responses and how they're transformed
4. **Cross-check UI display** - Ensure the UI shows the correct data from the API responses

## File Naming Convention

Files are named with timestamps: `{TYPE}_{YYYYMMDD_HHMMSS}.json`

Example: `FRONTEND_AIR_SHOPPING_REQUEST_20250704_203700.json`

## Debug Code Locations for Future Cleanup

### Backend/services/flight/core.py
**Lines to remove when validation is complete:**

1. **Line 9**: Added `import os` for file operations
2. **Lines 37-69**: Added `write_output_file()` function
3. **Line 73**: Added `from datetime import datetime` import
4. **Lines 194-202**: Added request payload logging in `_make_request()` method:
   ```python
   # Write request payload to Output folder
   write_output_file(
       filename=f"{service_name}_REQUEST",
       data={...},
       description=f"{service_name} API Request Payload"
   )
   ```
5. **Lines 249-254**: Added response data logging in `_make_request()` method:
   ```python
   # Write response data to Output folder
   write_output_file(
       filename=f"{service_name}_RESPONSE",
       data=response_data,
       description=f"{service_name} API Response"
   )
   ```

### Backend/routes/verteil_flights.py
**Lines to remove when validation is complete:**

1. **Line 9**: Added `import os` for file operations
2. **Lines 19-36**: Added `write_frontend_data()` function
3. **Lines 390-395**: Added frontend air shopping request logging:
   ```python
   # Write frontend air shopping request data to Output folder
   write_frontend_data(
       filename="AIR_SHOPPING_REQUEST",
       data=data,
       description="Frontend Air Shopping Request Data"
   )
   ```
4. **Lines 553-558**: Added backend air shopping response logging:
   ```python
   # Write backend air shopping response data to Output folder
   write_frontend_data(
       filename="AIR_SHOPPING_BACKEND_RESPONSE",
       data=result,
       description="Backend Air Shopping Response Data"
   )
   ```
5. **Lines 627-632**: Added frontend flight price request logging:
   ```python
   # Write frontend flight price request data to Output folder
   write_frontend_data(
       filename="FLIGHT_PRICE_REQUEST",
       data=data,
       description="Frontend Flight Price Request Data"
   )
   ```
6. **Lines 696-701**: Added backend flight price response logging:
   ```python
   # Write backend flight price response data to Output folder
   write_frontend_data(
       filename="FLIGHT_PRICE_BACKEND_RESPONSE",
       data=result,
       description="Backend Flight Price Response Data"
   )
   ```
7. **Lines 740-745**: Added frontend order create request logging:
   ```python
   # Write frontend order create request data to Output folder
   write_frontend_data(
       filename="ORDER_CREATE_REQUEST",
       data=data,
       description="Frontend Order Create Request Data"
   )
   ```
8. **Lines 906-911**: Added backend order create response logging:
   ```python
   # Write backend order create response data to Output folder
   write_frontend_data(
       filename="ORDER_CREATE_BACKEND_RESPONSE",
       data=result,
       description="Backend Order Create Response Data"
   )
   ```

## Quick Cleanup Commands

When validation is complete, you can remove all debug code with these steps:

1. **Delete the entire Output folder:**
   ```bash
   rm -rf Output/
   ```

2. **Remove debug imports and functions:**
   - In `core.py`: Remove lines 9, 37-73
   - In `verteil_flights.py`: Remove lines 9, 19-36

3. **Remove debug logging calls:**
   - In `core.py`: Remove lines 194-202 and 249-254
   - In `verteil_flights.py`: Remove lines 390-395, 553-558, 627-632, 696-701, 740-745, 906-911

## Note

This is a temporary debugging feature. Files in this folder can be safely deleted when no longer needed. All debug code locations are documented above for easy cleanup after validation is complete.
