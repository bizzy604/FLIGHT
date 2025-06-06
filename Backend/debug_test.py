#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '.')

try:
    from services.flight_service import search_flights, FlightServiceError
    print(f"search_flights type: {type(search_flights)}")
    print(f"search_flights: {search_flights}")
    print(f"FlightServiceError: {FlightServiceError}")
    
    # Try to call the function with minimal args to see what happens
    try:
        result = search_flights(origin='JFK', destination='LAX', departure_date='2024-02-01')
        print(f"Function call successful: {type(result)}")
    except Exception as e:
        print(f"Function call failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Write full error to file
        with open('error_log.txt', 'w') as f:
            f.write(f"Error: {type(e).__name__}: {str(e)}\n")
            f.write(traceback.format_exc())
        
except Exception as e:
    print(f"Import failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()