/**
 * Utility functions for persistent booking data storage
 * Now uses the robust storage manager for corruption-free storage
 */

import { flightStorageManager, BookingData } from './flight-storage-manager';

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
 * Store booking data using robust storage manager
 * @param bookingData - The booking data to store
 */
export async function storeBookingData(bookingData: any): Promise<boolean> {
  try {
    const bookingDataForStorage: BookingData = {
      bookingReference: bookingData.bookingReference,
      orderId: bookingData.orderId,
      passengerInfo: bookingData.passengerInfo,
      flightDetails: bookingData.flightDetails,
      paymentInfo: bookingData.paymentInfo,
      timestamp: Date.now()
    };

    const result = await flightStorageManager.storeBookingData(bookingDataForStorage);

    if (result.success) {
      console.log(`[BookingStorage] ✅ Data stored successfully with robust storage manager`);
      return true;
    } else {
      console.error('[BookingStorage] ❌ Failed to store booking data:', result.error);
      return false;
    }
  } catch (error) {
    console.error('[BookingStorage] Failed to store booking data:', error);
    return false;
  }
}

/**
 * Retrieve booking data using robust storage manager
 * @returns The booking data or null if not found/expired
 */
export async function getBookingData(): Promise<any | null> {
  try {
    const result = await flightStorageManager.getBookingData();

    if (result.success) {
      console.log('[BookingStorage] ✅ Retrieved data successfully');
      if (result.recovered) {
        console.log('[BookingStorage] 🔄 Data was recovered from backup storage');
      }
      return result.data;
    } else {
      console.log('[BookingStorage] ❌ No booking data found:', result.error);
      return null;
    }
  } catch (error) {
    console.error('[BookingStorage] Failed to retrieve booking data:', error);
    return null;
  }
}

/**
 * Clear booking data using robust storage manager
 */
export async function clearBookingData(): Promise<void> {
  try {
    await flightStorageManager.clearAllFlightData();
    console.log(`[BookingStorage] ✅ Booking data cleared successfully`);
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