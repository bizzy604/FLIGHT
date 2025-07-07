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
    console.log('[BookingStorage] 🔍 Input booking data:', bookingData);

    // Handle the actual frontend API response structure based on the output file analysis
    // Structure: { status: "success", data: { bookingReference: "1802386", order_id: "DELFCG", ... } }
    let extractedBookingReference = 'Unknown';
    let extractedOrderId = 'Unknown';
    let extractedPassengers = {};

    try {
      console.log('[BookingStorage] 🔍 Analyzing booking data structure:', {
        hasStatus: !!bookingData.status,
        hasData: !!bookingData.data,
        hasDirectBookingRef: !!bookingData.bookingReference,
        topLevelKeys: Object.keys(bookingData)
      });

      // Primary: Check if this is the actual frontend API response structure from output file
      if (bookingData.status === 'success' && bookingData.data) {
        // This matches the exact structure from FRONTEND_ORDER_CREATE_BACKEND_RESPONSE
        extractedBookingReference = bookingData.data.bookingReference || 'Unknown';
        extractedOrderId = bookingData.data.order_id || bookingData.data.orderItemId || 'Unknown';
        extractedPassengers = bookingData.data.passengerDetails ||
                             bookingData.data.passengerTypes ||
                             {};

        console.log('[BookingStorage] ✅ Extracted from actual frontend API response structure:', {
          bookingReference: extractedBookingReference,
          orderId: extractedOrderId,
          status: bookingData.data.status,
          createdAt: bookingData.data.createdAt
        });
      }
      // Secondary: Check if this is direct data structure (without status wrapper)
      else if (bookingData.bookingReference || bookingData.data?.bookingReference) {
        extractedBookingReference = bookingData.bookingReference ||
                                   bookingData.data?.bookingReference ||
                                   'Unknown';
        extractedOrderId = bookingData.order_id ||
                          bookingData.data?.order_id ||
                          bookingData.orderItemId ||
                          bookingData.data?.orderItemId ||
                          'Unknown';
        extractedPassengers = bookingData.passengerDetails ||
                             bookingData.data?.passengerDetails ||
                             bookingData.passengerTypes ||
                             bookingData.data?.passengerTypes ||
                             {};

        console.log('[BookingStorage] ✅ Extracted from direct data structure:', {
          bookingReference: extractedBookingReference,
          orderId: extractedOrderId,
          dataKeys: Object.keys(bookingData.data || bookingData)
        });
      }
      // Tertiary: Check raw OrderCreate response structure (fallback)
      else if (bookingData.raw_order_create_response?.Response?.Order?.[0] || bookingData.Response?.Order?.[0]) {
        const rawResponse = bookingData.raw_order_create_response || bookingData;
        const order = rawResponse.Response.Order[0];

        extractedOrderId = order.OrderID?.value || 'Unknown';

        const bookingRefs = order.BookingReferences?.BookingReference;
        if (bookingRefs && Array.isArray(bookingRefs) && bookingRefs.length > 0) {
          extractedBookingReference = bookingRefs[0].ID || 'Unknown';
        }

        if (rawResponse.Response.Passengers?.Passenger) {
          extractedPassengers = rawResponse.Response.Passengers.Passenger;
        }

        console.log('[BookingStorage] ✅ Extracted from raw OrderCreate response (fallback):', {
          bookingReference: extractedBookingReference,
          orderId: extractedOrderId,
          passengerCount: Array.isArray(extractedPassengers) ? extractedPassengers.length : 0
        });
      }
      // Quaternary: Generic fallback
      else {
        extractedBookingReference = bookingData.booking_reference ||
                                   bookingData.order_id ||
                                   'Unknown';
        extractedOrderId = bookingData.order_id ||
                          bookingData.orderId ||
                          'Unknown';
        extractedPassengers = bookingData.passengerInfo ||
                             bookingData.passengerDetails ||
                             {};

        console.log('[BookingStorage] ⚠️ Using generic fallback logic:', {
          bookingReference: extractedBookingReference,
          orderId: extractedOrderId,
          inputKeys: Object.keys(bookingData)
        });
      }
    } catch (error) {
      console.error('[BookingStorage] ❌ Error extracting booking data:', error);
    }

    const bookingDataForStorage: BookingData = {
      bookingReference: extractedBookingReference,
      orderId: extractedOrderId,
      passengerInfo: extractedPassengers,
      flightDetails: bookingData.flightDetails ||
                    bookingData.data?.flightDetails ||
                    {},
      paymentInfo: bookingData.paymentInfo ||
                  bookingData.pricing ||
                  bookingData.payment ||
                  bookingData.data?.pricing ||
                  {},
      timestamp: Date.now(),
      // Store the complete raw data for fallback
      rawData: bookingData
    };

    console.log('[BookingStorage] 🔍 Processed booking data for storage:', bookingDataForStorage);

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