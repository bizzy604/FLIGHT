/**
 * Flight Data Validator Utility
 * 
 * Provides functions to validate and recover flight data from localStorage
 * to prevent "No flight search data found" errors.
 */

export interface FlightDataValidationResult {
  isValid: boolean;
  data?: any;
  error?: string;
  recovered?: boolean;
  recoveredFrom?: string;
}

/**
 * Validate and retrieve flight data from localStorage with fallback recovery
 */
export function validateAndRecoverFlightData(): FlightDataValidationResult {
  try {
    // Method 1: Try current flight data key
    const currentFlightDataKey = localStorage.getItem('currentFlightDataKey');
    
    if (currentFlightDataKey) {
      try {
        const storedData = JSON.parse(localStorage.getItem(currentFlightDataKey) || '{}');
        if (storedData.expiresAt && storedData.expiresAt > Date.now() && storedData.airShoppingResponse) {
          return {
            isValid: true,
            data: storedData,
            recovered: false,
            recoveredFrom: currentFlightDataKey
          };
        }
      } catch (e) {
        console.error('Failed to parse current flight data:', e);
      }
    }
    
    // Method 2: Search for any valid flight data
    const flightDataKeys = Object.keys(localStorage).filter(key => key.startsWith('flightData_'));
    
    for (const key of flightDataKeys) {
      try {
        const storedData = JSON.parse(localStorage.getItem(key) || '{}');
        if (storedData.expiresAt && storedData.expiresAt > Date.now() && storedData.airShoppingResponse) {
          // Update the current key for future use
          localStorage.setItem('currentFlightDataKey', key);
          console.log(`✅ Flight data recovered from key: ${key}`);
          return {
            isValid: true,
            data: storedData,
            recovered: true,
            recoveredFrom: key
          };
        }
      } catch (e) {
        // Remove corrupted data
        localStorage.removeItem(key);
        console.log(`Cleaned up corrupted flight data: ${key}`);
      }
    }
    
    return {
      isValid: false,
      error: 'No valid flight search data found. Your session may have expired.'
    };
    
  } catch (error) {
    return {
      isValid: false,
      error: 'Error validating flight data: ' + (error as Error).message
    };
  }
}

/**
 * Clean up expired and corrupted flight data from localStorage
 */
export function cleanupFlightData(): number {
  let cleanedCount = 0;
  const now = Date.now();
  
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('flightData_') || key.startsWith('flight_')) {
      try {
        const data = JSON.parse(localStorage.getItem(key) || '{}');
        if (data.expiresAt && data.expiresAt < now) {
          localStorage.removeItem(key);
          cleanedCount++;
        }
      } catch (e) {
        // Remove corrupted data
        localStorage.removeItem(key);
        cleanedCount++;
      }
    }
  });
  
  return cleanedCount;
}

/**
 * Check if flight data exists and is valid
 */
export function hasValidFlightData(): boolean {
  const result = validateAndRecoverFlightData();
  return result.isValid;
}
