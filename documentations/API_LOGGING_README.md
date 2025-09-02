# API Request/Response Logging

This document explains how to use the API logging functionality to debug and monitor API interactions with the Verteil NDC API.

## Overview

The API logging system captures:
- **Request payloads** sent to the Verteil API
- **Response data** received from the Verteil API
- **Request metadata** (headers, endpoints, timing)
- **Response metadata** (status codes, response times)

All data is written to JSON files organized by service type for easy analysis.

## Quick Start

### 1. Enable Logging

```bash
# Navigate to Backend directory
cd Backend

# Enable API logging
python scripts/manage_api_logging.py enable
```

### 2. Restart Your Application

After enabling logging, restart your backend application to apply the changes.

### 3. Make API Calls

Use your frontend or make API calls to any of these endpoints:
- Air Shopping (`/api/verteil/air-shopping`)
- Flight Price (`/api/verteil/flight-price`)
- Booking (`/api/verteil/booking`)

### 4. View Logs

Logs are automatically written to the `api_logs/` directory:

```
api_logs/
├── air_shopping/
│   ├── 20250710_143022_abc123_request.json
│   └── 20250710_143023_abc123_response.json
├── flight_price/
│   ├── 20250710_143045_def456_request.json
│   └── 20250710_143046_def456_response.json
└── booking/
    ├── 20250710_143102_ghi789_request.json
    └── 20250710_143103_ghi789_response.json
```

## Log File Structure

### Request Files (`*_request.json`)

```json
{
  "timestamp": "2025-07-10T14:30:22.123456",
  "service": "AirShopping",
  "request_id": "abc123",
  "endpoint": "/entrygate/rest/request:airShopping",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer ***12345678",
    "service": "AirShopping",
    "ThirdpartyId": "***ABCD"
  },
  "payload": {
    "Query": {
      "OriginDestination": [...],
      "Travelers": {...}
    }
  }
}
```

### Response Files (`*_response.json`)

```json
{
  "timestamp": "2025-07-10T14:30:23.456789",
  "service": "AirShopping",
  "request_id": "abc123",
  "status_code": 200,
  "response_time_ms": 1234.56,
  "response": {
    "AirShoppingRS": {
      "DataLists": {...},
      "OffersGroup": {...}
    }
  }
}
```

## Management Commands

### Check Status

```bash
python scripts/manage_api_logging.py status
```

### Disable Logging

```bash
python scripts/manage_api_logging.py disable
```

### Clean Up Old Logs

```bash
# Clean logs older than 7 days (default)
python scripts/manage_api_logging.py cleanup

# Clean logs older than 3 days
python scripts/manage_api_logging.py cleanup --days 3
```

## Environment Configuration

The logging is controlled by the `API_DEBUG_LOGGING` environment variable:

```bash
# Enable logging
export API_DEBUG_LOGGING=true

# Disable logging
export API_DEBUG_LOGGING=false
# or
unset API_DEBUG_LOGGING
```

You can also add this to your `.env` file:

```env
API_DEBUG_LOGGING=true
```

## Security Features

- **Sensitive data masking**: Authorization tokens and API keys are automatically masked in logs
- **Configurable**: Logging can be easily enabled/disabled without code changes
- **Automatic cleanup**: Old logs can be automatically removed to save disk space

## Use Cases

### 1. Debugging API Issues

When an API call fails, check both request and response files to understand:
- What payload was sent
- What response was received
- Response times and status codes

### 2. Payload Validation

Compare the actual payloads being sent with expected formats:
- Verify request structure matches API documentation
- Check if all required fields are present
- Validate data types and formats

### 3. Performance Monitoring

Monitor API response times:
- Identify slow endpoints
- Track performance trends
- Optimize request payloads

### 4. Multi-airline Testing

When testing multi-airline support:
- Verify different airline codes in requests
- Check response variations by airline
- Validate airline-specific data handling

## File Naming Convention

Files are named using the pattern:
```
{YYYYMMDD}_{HHMMSS}_{request_id}_{type}.json
```

Where:
- `YYYYMMDD_HHMMSS`: Timestamp when the log was created
- `request_id`: Unique identifier for the request
- `type`: Either `request` or `response`

## Best Practices

1. **Enable only when needed**: Logging creates many files and should be disabled in production
2. **Regular cleanup**: Use the cleanup command to remove old logs
3. **Monitor disk space**: Logs can accumulate quickly with high API usage
4. **Secure sensitive data**: Never share log files containing real API keys or tokens

## Troubleshooting

### Logs not being created

1. Check if logging is enabled:
   ```bash
   python scripts/manage_api_logging.py status
   ```

2. Verify environment variable:
   ```bash
   # On Windows PowerShell
   echo $env:API_DEBUG_LOGGING

   # On Linux/Mac
   echo $API_DEBUG_LOGGING
   ```

3. Check application restart after enabling

4. Verify the environment variable is set in your application:
   ```bash
   # For current session (Windows PowerShell)
   $env:API_DEBUG_LOGGING="true"

   # For current session (Linux/Mac)
   export API_DEBUG_LOGGING=true
   ```

### Permission errors

Ensure the application has write permissions to the `api_logs/` directory.

### Large log files

If individual log files are very large, consider:
- Checking for circular references in response data
- Implementing response size limits if needed
- More frequent cleanup of old logs

### Module import errors

If you get "No module named 'utils'" when running cleanup:
- The script has been updated with fallback functionality
- Make sure you're running from the Backend directory
- The script will automatically handle import issues

### Cleanup command issues

The cleanup command has been fixed and now includes:
- Automatic path resolution for imports
- Fallback implementation if module imports fail
- Better error handling and user feedback
