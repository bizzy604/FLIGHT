/**
 * Redis-based Flight Storage Service
 * 
 * This service provides persistent storage for flight data using Redis
 * through backend API endpoints, replacing browser storage limitations.
 */

import apiClient from './api-client';
import { logger } from './logger';

export interface RedisStorageResult<T = any> {
  success: boolean;
  data?: T;
  session_id?: string;
  expires_at?: string;
  stored_at?: string;
  error?: string;
  message?: string;
}

export interface FlightSearchData {
  airShoppingResponse: any;
  searchParams: any;
  timestamp: number;
  expiresAt: number;
}

export interface FlightPriceData {
  flightId: string;
  pricedOffer: any;
  rawResponse: any;
  searchParams: any;
  timestamp: number;
  expiresAt: number;
}

export interface BookingData {
  orderCreateResponse: any;
  timestamp: number;
  expiresAt: number;
}

class RedisFlightStorageService {
  private readonly TTL_SECONDS = 1800; // 30 minutes

  /**
   * Store flight search data in Redis
   */
  async storeFlightSearch(
    searchData: FlightSearchData,
    sessionId?: string
  ): Promise<RedisStorageResult<FlightSearchData>> {
    try {
      logger.info('[RedisStorage] Storing flight search data...');

      const response = await apiClient.post('/api/flight-storage/search', {
        search_data: searchData,
        session_id: sessionId,
        ttl: this.TTL_SECONDS
      });

      if (response.data.success) {
        logger.info('[RedisStorage] ✅ Flight search data stored successfully', {
          session_id: response.data.session_id,
          expires_at: response.data.expires_at
        });

        // Store session ID in localStorage for retrieval
        if (response.data.session_id) {
          localStorage.setItem('flight_session_id', response.data.session_id);
        }

        return response.data;
      } else {
        logger.error('[RedisStorage] ❌ Failed to store flight search data:', response.data.error);
        return response.data;
      }
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Error storing flight search data:', error);
      return {
        success: false,
        error: error.message || 'Failed to store flight search data',
        message: 'Network or server error occurred'
      };
    }
  }

  /**
   * Retrieve flight search data from Redis
   */
  async getFlightSearch(sessionId?: string): Promise<RedisStorageResult<FlightSearchData>> {
    try {
      // Use provided session ID or get from localStorage
      const targetSessionId = sessionId || localStorage.getItem('flight_session_id');
      
      if (!targetSessionId) {
        return {
          success: false,
          error: 'No session ID available',
          message: 'Session ID not found. Please start a new search.'
        };
      }

      logger.info('[RedisStorage] Retrieving flight search data...', { session_id: targetSessionId });

      const response = await apiClient.get(`/api/flight-storage/search/${targetSessionId}`);

      if (response.data.success) {
        logger.info('[RedisStorage] ✅ Flight search data retrieved successfully');
        return response.data;
      } else {
        logger.error('[RedisStorage] ❌ Failed to retrieve flight search data:', response.data.error);
        return response.data;
      }
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Error retrieving flight search data:', error);
      
      if (error.response?.status === 404) {
        return {
          success: false,
          error: 'Flight search data not found or expired',
          message: 'Your session may have expired. Please start a new search.'
        };
      }

      return {
        success: false,
        error: error.message || 'Failed to retrieve flight search data',
        message: 'Network or server error occurred'
      };
    }
  }

  /**
   * Store flight price data in Redis
   */
  async storeFlightPrice(
    priceData: FlightPriceData,
    sessionId?: string
  ): Promise<RedisStorageResult<FlightPriceData>> {
    try {
      // Use provided session ID or get from localStorage
      const targetSessionId = sessionId || localStorage.getItem('flight_session_id');
      
      if (!targetSessionId) {
        return {
          success: false,
          error: 'No session ID available',
          message: 'Session ID not found. Please start a new search.'
        };
      }

      logger.info('[RedisStorage] Storing flight price data...', { session_id: targetSessionId });

      const response = await apiClient.post('/api/flight-storage/price', {
        price_data: priceData,
        session_id: targetSessionId,
        ttl: this.TTL_SECONDS
      });

      if (response.data.success) {
        logger.info('[RedisStorage] ✅ Flight price data stored successfully');
        return response.data;
      } else {
        logger.error('[RedisStorage] ❌ Failed to store flight price data:', response.data.error);
        return response.data;
      }
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Error storing flight price data:', error);
      return {
        success: false,
        error: error.message || 'Failed to store flight price data',
        message: 'Network or server error occurred'
      };
    }
  }

  /**
   * Retrieve flight price data from Redis
   */
  async getFlightPrice(sessionId?: string): Promise<RedisStorageResult<FlightPriceData>> {
    try {
      // Use provided session ID or get from localStorage
      const targetSessionId = sessionId || localStorage.getItem('flight_session_id');

      if (!targetSessionId) {
        return {
          success: false,
          error: 'No session ID available',
          message: 'Session ID not found. Please start a new search.'
        };
      }

      logger.info('[RedisStorage] Retrieving flight price data...', { session_id: targetSessionId });

      const response = await apiClient.get(`/api/flight-storage/price/${targetSessionId}`);

      if (response.data.success) {
        logger.info('[RedisStorage] ✅ Flight price data retrieved successfully');
        return response.data;
      } else {
        logger.error('[RedisStorage] ❌ Failed to retrieve flight price data:', response.data.error);
        return response.data;
      }
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Error retrieving flight price data:', error);
      
      if (error.response?.status === 404) {
        return {
          success: false,
          error: 'Flight price data not found or expired',
          message: 'Your session may have expired. Please start a new search.'
        };
      }

      return {
        success: false,
        error: error.message || 'Failed to retrieve flight price data',
        message: 'Network or server error occurred'
      };
    }
  }

  /**
   * Store booking data in Redis
   */
  async storeBookingData(
    bookingData: BookingData,
    sessionId?: string
  ): Promise<RedisStorageResult<BookingData>> {
    try {
      // Use provided session ID or get from localStorage
      const targetSessionId = sessionId || localStorage.getItem('flight_session_id');
      
      if (!targetSessionId) {
        return {
          success: false,
          error: 'No session ID available',
          message: 'Session ID not found. Please start a new search.'
        };
      }

      logger.info('[RedisStorage] Storing booking data...', { session_id: targetSessionId });

      const response = await apiClient.post('/api/flight-storage/booking', {
        booking_data: bookingData,
        session_id: targetSessionId,
        ttl: this.TTL_SECONDS
      });

      if (response.data.success) {
        logger.info('[RedisStorage] ✅ Booking data stored successfully');
        return response.data;
      } else {
        logger.error('[RedisStorage] ❌ Failed to store booking data:', response.data.error);
        return response.data;
      }
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Error storing booking data:', error);
      return {
        success: false,
        error: error.message || 'Failed to store booking data',
        message: 'Network or server error occurred'
      };
    }
  }

  /**
   * Retrieve booking data from Redis
   */
  async getBookingData(sessionId?: string): Promise<RedisStorageResult<BookingData>> {
    try {
      // Use provided session ID or get from localStorage
      const targetSessionId = sessionId || localStorage.getItem('flight_session_id');
      
      if (!targetSessionId) {
        return {
          success: false,
          error: 'No session ID available',
          message: 'Session ID not found. Please start a new search.'
        };
      }

      logger.info('[RedisStorage] Retrieving booking data...', { session_id: targetSessionId });

      const response = await apiClient.get(`/api/flight-storage/booking/${targetSessionId}`);

      if (response.data.success) {
        logger.info('[RedisStorage] ✅ Booking data retrieved successfully');
        return response.data;
      } else {
        logger.error('[RedisStorage] ❌ Failed to retrieve booking data:', response.data.error);
        return response.data;
      }
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Error retrieving booking data:', error);
      
      if (error.response?.status === 404) {
        return {
          success: false,
          error: 'Booking data not found or expired',
          message: 'Your session may have expired. Please start a new search.'
        };
      }

      return {
        success: false,
        error: error.message || 'Failed to retrieve booking data',
        message: 'Network or server error occurred'
      };
    }
  }

  /**
   * Delete all session data
   */
  async deleteSessionData(sessionId?: string): Promise<RedisStorageResult> {
    try {
      // Use provided session ID or get from localStorage
      const targetSessionId = sessionId || localStorage.getItem('flight_session_id');
      
      if (!targetSessionId) {
        return {
          success: false,
          error: 'No session ID available',
          message: 'Session ID not found.'
        };
      }

      logger.info('[RedisStorage] Deleting session data...', { session_id: targetSessionId });

      const response = await apiClient.delete(`/api/flight-storage/session/${targetSessionId}`);

      if (response.data.success) {
        logger.info('[RedisStorage] ✅ Session data deleted successfully');
        // Clear session ID from localStorage
        localStorage.removeItem('flight_session_id');
        return response.data;
      } else {
        logger.error('[RedisStorage] ❌ Failed to delete session data:', response.data.error);
        return response.data;
      }
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Error deleting session data:', error);
      return {
        success: false,
        error: error.message || 'Failed to delete session data',
        message: 'Network or server error occurred'
      };
    }
  }

  /**
   * Get current session ID
   */
  getCurrentSessionId(): string | null {
    return localStorage.getItem('flight_session_id');
  }

  /**
   * Check if Redis storage service is healthy
   */
  async healthCheck(): Promise<RedisStorageResult> {
    try {
      const response = await apiClient.get('/api/flight-storage/health');
      return response.data;
    } catch (error: any) {
      logger.error('[RedisStorage] ❌ Health check failed:', error);
      return {
        success: false,
        error: error.message || 'Health check failed',
        message: 'Redis storage service is unavailable'
      };
    }
  }
}

// Export singleton instance
export const redisFlightStorage = new RedisFlightStorageService();
