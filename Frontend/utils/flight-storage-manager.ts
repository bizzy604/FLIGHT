/**
 * Flight Data Storage Manager - Specialized storage for flight-related data
 * Built on top of the robust StorageManager to prevent corruption
 */

import { storageManager, StorageResult, StorageOptions } from './storage-manager';

// Flight data type definitions
interface FlightSearchData {
  airShoppingResponse: any;
  searchParams: {
    origin: string;
    destination: string;
    departDate: string;
    returnDate?: string;
    tripType: string;
    passengers: {
      adults: number;
      children: number;
      infants: number;
    };
    cabinClass: string;
    outboundCabinClass?: string;
    returnCabinClass?: string;
  };
  timestamp: number;
  expiresAt: number;
}

interface FlightPriceData {
  flightId: string;
  pricedOffer: any;
  rawResponse: any;
  searchParams: any;
  timestamp: number;
  expiresAt: number;
}

interface BookingData {
  bookingReference?: string;
  orderId?: string;
  passengerInfo: any;
  flightDetails: any;
  paymentInfo: any;
  timestamp: number;
}

// Storage keys enum for consistency
enum StorageKeys {
  FLIGHT_SEARCH = 'flight_search_data',
  FLIGHT_PRICE = 'flight_price_data',
  BOOKING_DATA = 'booking_data',
  SELECTED_FLIGHT = 'selected_flight_data'
}

export class FlightStorageManager {
  private static instance: FlightStorageManager;
  private readonly DEFAULT_EXPIRY_MINUTES = 30;

  private constructor() {}

  static getInstance(): FlightStorageManager {
    if (!FlightStorageManager.instance) {
      FlightStorageManager.instance = new FlightStorageManager();
    }
    return FlightStorageManager.instance;
  }

  /**
   * Store flight search results
   */
  async storeFlightSearch(data: FlightSearchData): Promise<StorageResult<FlightSearchData>> {
    console.log('[FlightStorage] Storing flight search data...');
    
    const options: StorageOptions = {
      expiryMinutes: this.DEFAULT_EXPIRY_MINUTES,
      validateOnRead: true,
      retryAttempts: 3
    };

    const result = await storageManager.store(
      StorageKeys.FLIGHT_SEARCH,
      data,
      'flight_search',
      options
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Flight search data stored successfully');
    } else {
      console.error('[FlightStorage] ❌ Failed to store flight search data:', result.error);
    }

    return result;
  }

  /**
   * Retrieve flight search results
   */
  async getFlightSearch(): Promise<StorageResult<FlightSearchData>> {
    console.log('[FlightStorage] Retrieving flight search data...');
    
    const result = await storageManager.retrieve<FlightSearchData>(
      StorageKeys.FLIGHT_SEARCH,
      'flight_search'
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Flight search data retrieved successfully');
      if (result.recovered) {
        console.log('[FlightStorage] 🔄 Data was recovered from backup storage');
      }
    } else {
      console.log('[FlightStorage] ❌ Flight search data not found or invalid:', result.error);
    }

    return result;
  }

  /**
   * Store flight price data
   */
  async storeFlightPrice(data: FlightPriceData): Promise<StorageResult<FlightPriceData>> {
    console.log('[FlightStorage] Storing flight price data...');
    
    const options: StorageOptions = {
      expiryMinutes: this.DEFAULT_EXPIRY_MINUTES,
      validateOnRead: true,
      retryAttempts: 3
    };

    const result = await storageManager.store(
      StorageKeys.FLIGHT_PRICE,
      data,
      'flight_price',
      options
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Flight price data stored successfully');
    } else {
      console.error('[FlightStorage] ❌ Failed to store flight price data:', result.error);
    }

    return result;
  }

  /**
   * Retrieve flight price data
   */
  async getFlightPrice(): Promise<StorageResult<FlightPriceData>> {
    console.log('[FlightStorage] Retrieving flight price data...');
    
    const result = await storageManager.retrieve<FlightPriceData>(
      StorageKeys.FLIGHT_PRICE,
      'flight_price'
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Flight price data retrieved successfully');
      if (result.recovered) {
        console.log('[FlightStorage] 🔄 Data was recovered from backup storage');
      }
    } else {
      console.log('[FlightStorage] ❌ Flight price data not found or invalid:', result.error);
    }

    return result;
  }

  /**
   * Store booking data
   */
  async storeBookingData(data: BookingData): Promise<StorageResult<BookingData>> {
    console.log('[FlightStorage] Storing booking data...');
    
    const options: StorageOptions = {
      expiryMinutes: this.DEFAULT_EXPIRY_MINUTES,
      validateOnRead: true,
      retryAttempts: 3
    };

    const result = await storageManager.store(
      StorageKeys.BOOKING_DATA,
      data,
      'booking_data',
      options
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Booking data stored successfully');
    } else {
      console.error('[FlightStorage] ❌ Failed to store booking data:', result.error);
    }

    return result;
  }

  /**
   * Retrieve booking data
   */
  async getBookingData(): Promise<StorageResult<BookingData>> {
    console.log('[FlightStorage] Retrieving booking data...');
    
    const result = await storageManager.retrieve<BookingData>(
      StorageKeys.BOOKING_DATA,
      'booking_data'
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Booking data retrieved successfully');
      if (result.recovered) {
        console.log('[FlightStorage] 🔄 Data was recovered from backup storage');
      }
    } else {
      console.log('[FlightStorage] ❌ Booking data not found or invalid:', result.error);
    }

    return result;
  }

  /**
   * Store selected flight data
   */
  async storeSelectedFlight(flightData: any): Promise<StorageResult<any>> {
    console.log('[FlightStorage] Storing selected flight data...');
    
    const options: StorageOptions = {
      expiryMinutes: this.DEFAULT_EXPIRY_MINUTES,
      validateOnRead: true,
      retryAttempts: 3
    };

    const result = await storageManager.store(
      StorageKeys.SELECTED_FLIGHT,
      flightData,
      'selected_flight',
      options
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Selected flight data stored successfully');
    } else {
      console.error('[FlightStorage] ❌ Failed to store selected flight data:', result.error);
    }

    return result;
  }

  /**
   * Retrieve selected flight data
   */
  async getSelectedFlight(): Promise<StorageResult<any>> {
    console.log('[FlightStorage] Retrieving selected flight data...');
    
    const result = await storageManager.retrieve(
      StorageKeys.SELECTED_FLIGHT,
      'selected_flight'
    );

    if (result.success) {
      console.log('[FlightStorage] ✅ Selected flight data retrieved successfully');
      if (result.recovered) {
        console.log('[FlightStorage] 🔄 Data was recovered from backup storage');
      }
    } else {
      console.log('[FlightStorage] ❌ Selected flight data not found or invalid:', result.error);
    }

    return result;
  }

  /**
   * Clear all flight-related data
   */
  async clearAllFlightData(): Promise<void> {
    console.log('[FlightStorage] Clearing all flight data...');
    
    await Promise.all([
      storageManager.remove(StorageKeys.FLIGHT_SEARCH),
      storageManager.remove(StorageKeys.FLIGHT_PRICE),
      storageManager.remove(StorageKeys.BOOKING_DATA),
      storageManager.remove(StorageKeys.SELECTED_FLIGHT)
    ]);

    console.log('[FlightStorage] ✅ All flight data cleared');
  }

  /**
   * Validate flight search data structure (supports both optimized and legacy formats)
   */
  validateFlightSearchData(data: any): data is FlightSearchData {
    if (!data || typeof data !== 'object' || !data.searchParams ||
        typeof data.timestamp !== 'number' || typeof data.expiresAt !== 'number') {
      return false;
    }

    // Check if airShoppingResponse exists
    if (!data.airShoppingResponse) {
      return false;
    }

    // Support optimized format (metadata only) and legacy format (full offers)
    const airShoppingResponse = data.airShoppingResponse;

    // Optimized format: has metadata with cache key
    if (airShoppingResponse.data?.metadata?.raw_response_cache_key) {
      console.log('✅ [FlightStorage] Validated optimized flight search data with cache key');
      return true;
    }

    // Legacy format: has offers array
    if (airShoppingResponse.offers || airShoppingResponse.data?.offers) {
      console.log('✅ [FlightStorage] Validated legacy flight search data with offers');
      return true;
    }

    // Check for other valid structures
    if (airShoppingResponse.data || airShoppingResponse.status) {
      console.log('✅ [FlightStorage] Validated flight search data with basic structure');
      return true;
    }

    console.log('❌ [FlightStorage] Flight search data validation failed - no valid structure found');
    return false;
  }

  /**
   * Validate flight price data structure
   */
  validateFlightPriceData(data: any): data is FlightPriceData {
    return (
      data &&
      typeof data === 'object' &&
      typeof data.flightId === 'string' &&
      data.pricedOffer &&
      data.rawResponse &&
      typeof data.timestamp === 'number' &&
      typeof data.expiresAt === 'number'
    );
  }

  /**
   * Get storage statistics for monitoring
   */
  getStorageStats() {
    return storageManager.getStorageStats();
  }

  /**
   * Health check for all flight data
   */
  async healthCheck(): Promise<{
    flightSearch: boolean;
    flightPrice: boolean;
    bookingData: boolean;
    selectedFlight: boolean;
    overallHealth: boolean;
  }> {
    const [searchResult, priceResult, bookingResult, selectedResult] = await Promise.all([
      this.getFlightSearch(),
      this.getFlightPrice(),
      this.getBookingData(),
      this.getSelectedFlight()
    ]);

    const health = {
      flightSearch: searchResult.success,
      flightPrice: priceResult.success,
      bookingData: bookingResult.success,
      selectedFlight: selectedResult.success,
      overallHealth: false
    };

    health.overallHealth = health.flightSearch || health.flightPrice || health.bookingData || health.selectedFlight;

    console.log('[FlightStorage] Health check results:', health);
    return health;
  }
}

// Export singleton instance
export const flightStorageManager = FlightStorageManager.getInstance();

// Export types
export type { FlightSearchData, FlightPriceData, BookingData };
