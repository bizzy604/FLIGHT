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
    console.log('🔍 [Validator] Starting flight data validation...');

    // Method 1: Try sessionStorage first (more reliable, higher quota)
    console.log('🔍 [Validator] Checking sessionStorage first...');
    try {
      const sessionData = sessionStorage.getItem('currentFlightSearch');
      if (sessionData) {
        const parsedSessionData = JSON.parse(sessionData);
        console.log('🔍 [Validator] SessionStorage data keys:', Object.keys(parsedSessionData));
        console.log('🔍 [Validator] SessionStorage has airShoppingResponse:', !!parsedSessionData.airShoppingResponse);

        if (parsedSessionData.expiresAt && parsedSessionData.expiresAt > Date.now() && parsedSessionData.airShoppingResponse) {
          console.log('✅ [Validator] Valid data found in sessionStorage');
          return {
            isValid: true,
            data: parsedSessionData,
            recovered: false,
            recoveredFrom: 'sessionStorage'
          };
        } else {
          console.log('❌ [Validator] SessionStorage data is invalid or expired');
        }
      } else {
        console.log('❌ [Validator] No sessionStorage data found');
      }
    } catch (e) {
      console.error('❌ [Validator] Failed to parse sessionStorage data:', e);
    }

    // Method 2: Try current flight data key in localStorage
    const currentFlightDataKey = localStorage.getItem('currentFlightDataKey');
    console.log('🔍 [Validator] Current flight data key:', currentFlightDataKey);

    if (currentFlightDataKey) {
      try {
        const storedData = JSON.parse(localStorage.getItem(currentFlightDataKey) || '{}');
        console.log('🔍 [Validator] Stored data keys:', Object.keys(storedData));
        console.log('🔍 [Validator] Has airShoppingResponse:', !!storedData.airShoppingResponse);
        console.log('🔍 [Validator] Expires at:', storedData.expiresAt, 'Current time:', Date.now());
        console.log('🔍 [Validator] Is expired:', storedData.expiresAt ? storedData.expiresAt < Date.now() : 'No expiry');

        if (storedData.expiresAt && storedData.expiresAt > Date.now() && storedData.airShoppingResponse) {
          console.log('✅ [Validator] Valid data found with current key');
          return {
            isValid: true,
            data: storedData,
            recovered: false,
            recoveredFrom: currentFlightDataKey
          };
        } else {
          console.log('❌ [Validator] Current key data is invalid or expired');
        }
      } catch (e) {
        console.error('❌ [Validator] Failed to parse current flight data:', e);
      }
    } else {
      console.log('❌ [Validator] No current flight data key found');
    }
    
    // Method 3: Search for any valid flight data in localStorage
    const flightDataKeys = Object.keys(localStorage).filter(key => key.startsWith('flightData_'));
    console.log('🔍 [Validator] Found flight data keys:', flightDataKeys);

    for (const key of flightDataKeys) {
      try {
        const storedData = JSON.parse(localStorage.getItem(key) || '{}');
        console.log(`🔍 [Validator] Checking key ${key}:`, {
          hasAirShopping: !!storedData.airShoppingResponse,
          expiresAt: storedData.expiresAt,
          isExpired: storedData.expiresAt ? storedData.expiresAt < Date.now() : 'No expiry',
          dataKeys: Object.keys(storedData)
        });

        if (storedData.expiresAt && storedData.expiresAt > Date.now() && storedData.airShoppingResponse) {
          // Update the current key for future use
          localStorage.setItem('currentFlightDataKey', key);
          console.log(`✅ [Validator] Flight data recovered from key: ${key}`);
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
        console.log(`🗑️ [Validator] Cleaned up corrupted flight data: ${key}`);
      }
    }

    console.log('❌ [Validator] No valid flight data found after checking all methods');
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
