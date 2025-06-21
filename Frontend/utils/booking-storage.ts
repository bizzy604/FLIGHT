/**
 * Utility functions for persistent booking data storage
 * Implements hybrid localStorage/sessionStorage approach for better persistence
 */

interface BookingStorageData {
  data: any;
  timestamp: number;
  expiresAt: number;
}

const STORAGE_KEY = 'completedBooking';
const EXPIRY_MINUTES = 30; // 30 minutes expiry for localStorage (data will be retrieved from database after this)
const DEV_STORAGE_KEY = 'dev_completedBooking'; // Separate key for development

/**
 * Check if we're in development environment
 */
function isDevelopment(): boolean {
  return process.env.NODE_ENV === 'development';
}

/**
 * Get the appropriate storage key based on environment
 */
function getStorageKey(): string {
  return isDevelopment() ? DEV_STORAGE_KEY : STORAGE_KEY;
}

/**
 * Store booking data in both sessionStorage and localStorage for persistence
 * @param bookingData - The booking data to store
 */
export function storeBookingData(bookingData: any): void {
  try {
    const timestamp = Date.now();
    const expiresAt = timestamp + (EXPIRY_MINUTES * 60 * 1000);
    const storageKey = getStorageKey();
    
    const storageData: BookingStorageData = {
      data: bookingData,
      timestamp,
      expiresAt
    };
    
    const serializedData = JSON.stringify(storageData);
    
    // Store in sessionStorage (primary)
    sessionStorage.setItem(storageKey, JSON.stringify(bookingData));
    
    // Store in localStorage (backup with expiry)
    localStorage.setItem(storageKey, serializedData);
    
    // In development, also store with a persistent key that survives hot reloads
    if (isDevelopment()) {
      localStorage.setItem(`${storageKey}_persistent`, serializedData);
      console.log('[BookingStorage] Development mode: Data stored with persistent backup');
    }
    
    console.log(`[BookingStorage] Data stored in both session and local storage (${isDevelopment() ? 'DEV' : 'PROD'} mode)`);
  } catch (error) {
    console.error('[BookingStorage] Failed to store booking data:', error);
  }
}

/**
 * Retrieve booking data with fallback priority: sessionStorage → localStorage → null
 * @returns The booking data or null if not found/expired
 */
export function getBookingData(): any | null {
  try {
    const storageKey = getStorageKey();
    
    // First try sessionStorage (primary)
    const sessionData = sessionStorage.getItem(storageKey);
    if (sessionData) {
      console.log('[BookingStorage] Retrieved data from sessionStorage');
      return JSON.parse(sessionData);
    }
    
    // Fallback to localStorage (backup)
    const localData = localStorage.getItem(storageKey);
    if (localData) {
      const storageData: BookingStorageData = JSON.parse(localData);
      
      // Check if data has expired
      if (Date.now() > storageData.expiresAt) {
        console.log('[BookingStorage] localStorage data expired, cleaning up');
        localStorage.removeItem(storageKey);
        if (isDevelopment()) {
          localStorage.removeItem(`${storageKey}_persistent`);
        }
        return null;
      }
      
      console.log('[BookingStorage] Retrieved data from localStorage (fallback)');
      
      // Restore to sessionStorage for future requests
      sessionStorage.setItem(storageKey, JSON.stringify(storageData.data));
      
      return storageData.data;
    }
    
    // In development, try the persistent backup (survives hot reloads)
    if (isDevelopment()) {
      const persistentData = localStorage.getItem(`${storageKey}_persistent`);
      if (persistentData) {
        const storageData: BookingStorageData = JSON.parse(persistentData);
        
        // Check if data has expired
        if (Date.now() > storageData.expiresAt) {
          console.log('[BookingStorage] Persistent data expired, cleaning up');
          localStorage.removeItem(`${storageKey}_persistent`);
          return null;
        }
        
        console.log('[BookingStorage] Retrieved data from persistent backup (development)');
        
        // Restore to both sessionStorage and regular localStorage
        sessionStorage.setItem(storageKey, JSON.stringify(storageData.data));
        localStorage.setItem(storageKey, persistentData);
        
        return storageData.data;
      }
    }
    
    console.log('[BookingStorage] No booking data found in storage');
    return null;
  } catch (error) {
    console.error('[BookingStorage] Failed to retrieve booking data:', error);
    return null;
  }
}

/**
 * Clear booking data from both storage locations
 */
export function clearBookingData(): void {
  try {
    const storageKey = getStorageKey();
    sessionStorage.removeItem(storageKey);
    localStorage.removeItem(storageKey);
    
    // In development, also clear persistent backup
    if (isDevelopment()) {
      localStorage.removeItem(`${storageKey}_persistent`);
    }
    
    console.log(`[BookingStorage] Booking data cleared from all storages (${isDevelopment() ? 'DEV' : 'PROD'} mode)`);
  } catch (error) {
    console.error('[BookingStorage] Failed to clear booking data:', error);
  }
}

/**
 * Check if booking data exists in any storage
 * @returns boolean indicating if data exists
 */
export function hasBookingData(): boolean {
  return getBookingData() !== null;
}

/**
 * Get storage info for debugging
 * @returns object with storage status information
 */
export function getStorageInfo(): {
  hasSessionData: boolean;
  hasLocalData: boolean;
  localDataExpired?: boolean;
  hasPersistentData?: boolean;
  persistentDataExpired?: boolean;
  timestamp?: number;
  environment: string;
} {
  const storageKey = getStorageKey();
  const hasSessionData = !!sessionStorage.getItem(storageKey);
  const localData = localStorage.getItem(storageKey);
  
  let result: {
    hasSessionData: boolean;
    hasLocalData: boolean;
    localDataExpired?: boolean;
    hasPersistentData?: boolean;
    persistentDataExpired?: boolean;
    timestamp?: number;
    environment: string;
  } = {
    hasSessionData,
    hasLocalData: false,
    environment: isDevelopment() ? 'development' : 'production'
  };
  
  if (localData) {
    try {
      const storageData: BookingStorageData = JSON.parse(localData);
      const localDataExpired = Date.now() > storageData.expiresAt;
      
      result = {
        ...result,
        hasLocalData: true,
        localDataExpired,
        timestamp: storageData.timestamp
      };
    } catch {
      result.hasLocalData = false;
    }
  }
  
  // Check persistent backup in development
  if (isDevelopment()) {
    const persistentData = localStorage.getItem(`${storageKey}_persistent`);
    if (persistentData) {
      try {
        const storageData: BookingStorageData = JSON.parse(persistentData);
        const persistentDataExpired = Date.now() > storageData.expiresAt;
        
        result = {
          ...result,
          hasPersistentData: true,
          persistentDataExpired
        };
      } catch {
        result.hasPersistentData = false;
      }
    }
  }
  
  return result;
}