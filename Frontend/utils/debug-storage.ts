/**
 * Debug utility to inspect localStorage and sessionStorage for flight data
 */

export function debugFlightStorage() {
  console.log('=== FLIGHT DATA STORAGE DEBUG ===');
  
  // Check localStorage
  console.log('\n📦 localStorage keys:');
  const localKeys = Object.keys(localStorage);
  const flightKeys = localKeys.filter(key => 
    key.includes('flight') || key.includes('Flight') || key.includes('current')
  );
  
  if (flightKeys.length === 0) {
    console.log('❌ No flight-related keys found in localStorage');
  } else {
    flightKeys.forEach(key => {
      try {
        const data = JSON.parse(localStorage.getItem(key) || '{}');
        const hasAirShopping = !!data.airShoppingResponse;
        const isExpired = data.expiresAt ? data.expiresAt < Date.now() : 'No expiry';
        
        console.log(`🔑 ${key}:`);
        console.log(`   - Has airShoppingResponse: ${hasAirShopping}`);
        console.log(`   - Expired: ${isExpired}`);
        console.log(`   - Data keys: ${Object.keys(data).join(', ')}`);
        
        if (data.airShoppingResponse) {
          console.log(`   - AirShopping keys: ${Object.keys(data.airShoppingResponse).join(', ')}`);
        }
      } catch (e) {
        console.log(`🔑 ${key}: ❌ Invalid JSON`);
      }
    });
  }
  
  // Check sessionStorage
  console.log('\n💾 sessionStorage keys:');
  const sessionKeys = Object.keys(sessionStorage);
  const sessionFlightKeys = sessionKeys.filter(key => 
    key.includes('flight') || key.includes('Flight') || key.includes('current')
  );
  
  if (sessionFlightKeys.length === 0) {
    console.log('❌ No flight-related keys found in sessionStorage');
  } else {
    sessionFlightKeys.forEach(key => {
      try {
        const data = JSON.parse(sessionStorage.getItem(key) || '{}');
        console.log(`🔑 ${key}: ${Object.keys(data).join(', ')}`);
      } catch (e) {
        console.log(`🔑 ${key}: ❌ Invalid JSON`);
      }
    });
  }
  
  // Check current flight data key
  console.log('\n🎯 Current flight data key check:');
  const currentKey = localStorage.getItem('currentFlightDataKey');
  if (currentKey) {
    console.log(`Current key: ${currentKey}`);
    try {
      const data = JSON.parse(localStorage.getItem(currentKey) || '{}');
      console.log(`Data exists: ${!!data}`);
      console.log(`Has airShoppingResponse: ${!!data.airShoppingResponse}`);
      console.log(`Expired: ${data.expiresAt ? data.expiresAt < Date.now() : 'No expiry'}`);
    } catch (e) {
      console.log(`❌ Failed to parse data for current key`);
    }
  } else {
    console.log('❌ No current flight data key set');
  }
  
  console.log('\n=== END DEBUG ===');
}

/**
 * Clean up localStorage to free space
 */
export function cleanupLocalStorage() {
  console.log('🧹 Cleaning up localStorage...');

  let removedCount = 0;
  const now = Date.now();

  // Get all keys
  const allKeys = Object.keys(localStorage);

  // Remove expired data
  allKeys.forEach(key => {
    if (key.startsWith('flightData_') || key.startsWith('flight_') || key.startsWith('flightPrice_')) {
      try {
        const data = JSON.parse(localStorage.getItem(key) || '{}');
        if (data.expiresAt && data.expiresAt < now) {
          localStorage.removeItem(key);
          removedCount++;
          console.log(`🗑️ Removed expired: ${key}`);
        }
      } catch (e) {
        localStorage.removeItem(key);
        removedCount++;
        console.log(`🗑️ Removed corrupted: ${key}`);
      }
    }
  });

  // Remove old booking/order data
  allKeys.forEach(key => {
    if (key.includes('booking') || key.includes('order') || key.includes('Order')) {
      try {
        const data = JSON.parse(localStorage.getItem(key) || '{}');
        if (data.timestamp && (now - data.timestamp) > (7 * 24 * 60 * 60 * 1000)) { // 7 days old
          localStorage.removeItem(key);
          removedCount++;
          console.log(`🗑️ Removed old booking data: ${key}`);
        }
      } catch (e) {
        localStorage.removeItem(key);
        removedCount++;
        console.log(`🗑️ Removed corrupted booking data: ${key}`);
      }
    }
  });

  console.log(`✅ Cleanup complete. Removed ${removedCount} items.`);
  return removedCount;
}

/**
 * Attempt to fix flight storage issues by restoring from sessionStorage
 */
export function fixFlightStorage() {
  console.log('🔧 Attempting to fix flight storage...');

  // First clean up space
  cleanupLocalStorage();

  // Try to restore from sessionStorage
  const sessionData = sessionStorage.getItem('currentFlightSearch');
  if (sessionData) {
    try {
      const parsedData = JSON.parse(sessionData);
      if (parsedData.airShoppingResponse) {
        const timestamp = Date.now();
        const storageKey = `flightData_fixed_${timestamp}`;

        try {
          localStorage.setItem(storageKey, sessionData);
          localStorage.setItem('currentFlightDataKey', storageKey);

          console.log('✅ Flight data restored from sessionStorage to localStorage');
          console.log('🔑 New storage key:', storageKey);
          return true;
        } catch (e) {
          console.error('❌ Still not enough space in localStorage:', e);
          console.log('💡 Data is available in sessionStorage, flight selection should work');
          return false;
        }
      }
    } catch (e) {
      console.error('❌ Failed to parse sessionStorage data:', e);
    }
  }

  console.log('❌ No valid sessionStorage data found to restore');
  return false;
}

// Make functions available globally for browser console
if (typeof window !== 'undefined') {
  (window as any).debugFlightStorage = debugFlightStorage;
  (window as any).cleanupLocalStorage = cleanupLocalStorage;
  (window as any).fixFlightStorage = fixFlightStorage;
}
