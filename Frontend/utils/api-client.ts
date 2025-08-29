import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { debounce } from 'lodash';
import { logger } from './logger';
import { simpleApiManager } from './simple-api-manager';
import type { FlightSearchResponse } from '@/types/flight-api';

// Get backend URL from environment
const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';

// Create axios instance with default config
const apiClient = axios.create({
    baseURL: BACKEND_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    withCredentials: false, // Set to false for CORS
    timeout: 60000, // 60 seconds timeout for air shopping requests
});

// Request interceptor for API calls
apiClient.interceptors.request.use(
    (config) => {
        // Log the request
        logger.info(`API Request`, {
            url: config.url,
            method: config.method,
            data: config.data,
        });
        
        // Don't add X-Request-Timestamp as it can cause CORS issues
        // The backend doesn't need this header anyway
        
        return config;
    },
    (error) => {
        logger.error('Request Error:', error);
        return Promise.reject(error);
    }
);

// Add response interceptor
apiClient.interceptors.response.use(
    (response) => {
        logger.info('API Response', { status: response.status, url: response.config.url });
        return response;
    },
    (error) => {
        logger.error('API Response Error', { error });
        
        // Handle common error cases
        if (error.response) {
            // Server responded with error
            logger.error('Server Error Response', { 
                status: error.response.status,
                data: error.response.data 
            });
            return Promise.reject({
                status: error.response.status,
                message: error.response.data?.message || 'An error occurred',
                details: error.response.data
            });
        } else if (error.request) {
            // Request made but no response
            logger.error('No Response', { 
                url: error.request.responseURL 
            });
            return Promise.reject({
                status: 0,
                message: 'No response from server',
                details: error.request
            });
        } else {
            // Error in request configuration
            logger.error('Request Error', { error });
            return Promise.reject({
                status: 0,
                message: 'Request failed',
                details: error
            });
        }
    }
);

// Export typed API functions
export interface FlightSearchRequest {
    tripType: 'ONE_WAY' | 'ROUND_TRIP' | 'MULTI_CITY';
    odSegments: Array<{
        origin: string;
        destination: string;
        departureDate: string;
        returnDate?: string;
    }>;
    numAdults: number;
    numChildren?: number;
    numInfants?: number;
    cabinPreference?: string;
    outboundCabinClass?: string;
    returnCabinClass?: string;
    directOnly?: boolean;
    enableRoundtrip?: boolean;
}

export interface FlightOffer {
    id: string;
    price: number;
    currency: string;
    segments: Array<{
        origin: string;
        destination: string;
        departureTime: string;
        arrivalTime: string;
        duration: string;
        airline: string;
        flightNumber: string;
    }>;
}

// Create debounced search function to prevent rapid successive requests
const debouncedSearchFlights = debounce(async (params: FlightSearchRequest, resolve: (value: any) => void, reject: (reason?: any) => void) => {
    try {
        // [PASSENGER DEBUG] Log the search request payload
        console.log('[PASSENGER DEBUG] Frontend API Client - Sending air shopping request:');
        console.log('[PASSENGER DEBUG] Passenger counts:', {
            numAdults: params.numAdults,
            numChildren: params.numChildren,
            numInfants: params.numInfants,
            total: (params.numAdults || 0) + (params.numChildren || 0) + (params.numInfants || 0)
        });
        console.log('[PASSENGER DEBUG] Full request payload:', JSON.stringify(params, null, 2));

        const response = await apiClient.post<FlightSearchResponse>('/api/verteil/air-shopping', params);
        resolve(response);
    } catch (error) {
        reject(error);
    }
}, 1000); // 1 second debounce delay

export const api = {
    // Flight Search Cache Check
    checkFlightSearchCache: async (params: FlightSearchRequest): Promise<{ data: any }> => {
        try {
            const response = await apiClient.post('/api/verteil/air-shopping/cache-check', params);
            logger.info('Flight search cache check response:', response.data);
            return response;
        } catch (error) {
            logger.error('Error checking flight search cache:', error);
            throw error;
        }
    },

    // Flight Price Cache Check
    checkFlightPriceCache: async (offerId: string, shoppingResponseId: string): Promise<{ data: any }> => {
        try {
            const response = await apiClient.post('/api/verteil/flight-price/cache-check', {
                offer_id: offerId,
                shopping_response_id: shoppingResponseId
            });
            logger.info('Flight price cache check response:', response.data);
            return response;
        } catch (error) {
            logger.error('Error checking flight price cache:', error);
            throw error;
        }
    },

    // Booking Cache Check
    checkBookingCache: async (bookingId: string): Promise<{ data: any }> => {
        try {
            const response = await apiClient.post('/api/verteil/booking/cache-check', {
                booking_id: bookingId
            });
            logger.info('Booking cache check response:', response.data);
            return response;
        } catch (error) {
            logger.error('Error checking booking cache:', error);
            throw error;
        }
    },

    // Flight Search with debouncing
    searchFlights: async (params: FlightSearchRequest): Promise<{ data: FlightSearchResponse }> => {
        return new Promise((resolve, reject) => {
            debouncedSearchFlights(params, resolve, reject);
        });
    },

    // Flight Pricing - Using unified manager to eliminate duplicates
    getFlightPrice: async (flightIndex: number, shoppingResponseId: string, airShoppingResponse: any) => {
        try {
            logger.info('🚀 Using simple API manager for flight price request', {
                flightIndex,
                shoppingResponseId,
                hasAirShoppingResponse: !!airShoppingResponse
            });

            const response = await simpleApiManager.getFlightPrice(
                flightIndex, 
                shoppingResponseId, 
                airShoppingResponse
            );
            
            logger.info('✅ Flight price response received via simple manager', {
                success: response.success,
                cacheHit: response.cache_hit,
                hasData: !!response.data
            });
            
            // Response received from simple manager
            logger.info('✅ Simple manager response processed', {
                success: response.success,
                status: response.status,
                hasData: !!response.data
            });
            
            // Convert to expected format for backward compatibility
            // The existing code expects: response.data.status and response.data.data
            
            // Handle backend response format: { status: 'success'|'error', data: {...} }
            const isSuccess = response.success === true || response.status === 'success';
            
            const formattedResponse = { 
                data: {
                    status: isSuccess ? 'success' : 'error',
                    data: response.data,
                    error: isSuccess ? undefined : (response.error || 'Flight pricing failed')
                }, 
                status: 200 
            };
            
            // Response formatted for backward compatibility
            logger.info('✅ Response formatted for existing code', {
                dataStatus: formattedResponse.data.status,
                hasData: !!formattedResponse.data.data
            });
            
            return formattedResponse;
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            logger.error('❌ Error in simple getFlightPrice', {
                flightIndex,
                error: errorMessage
            });
            throw error;
        }
    },

    // Booking - Using simple manager for consistent session handling
    createBooking: async (flightOffer: any, passengers: any[], payment: any, contactInfo: any, extras?: any) => {
        try {
            logger.info('🚀 Using simple API manager for booking creation');
            
            const response = await simpleApiManager.createBooking(
                flightOffer,
                passengers,
                payment,
                contactInfo,
                extras
            );
            
            logger.info('✅ Booking created via simple manager', {
                success: response.success,
                hasData: !!response.data
            });
            
            return { data: response.data };
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            logger.error('❌ Error in simple createBooking', { error: errorMessage });
            throw error;
        }
    },

    // Airport Suggestions
    getAirportSuggestions: async (query: string): Promise<{ data: Array<{ code: string; name: string; city: string; country?: string }> }> => {
        if (!query || query.length < 2) {
            return { data: [] };
        }
        return apiClient.get(`/api/airports/autocomplete?query=${encodeURIComponent(query)}`);
    },

    // ServiceList API - Using simple manager with proactive caching
    getServiceList: async (flightPriceResponse: any): Promise<{ data: any }> => {
        try {
            logger.info('🚀 Using simple API manager for service list (proactive cache first)');
            
            const response = await simpleApiManager.getServiceList(flightPriceResponse);
            
            logger.info('✅ Service list received via simple manager', {
                hasData: !!response.data,
                source: response.cache_hit ? 'proactive_cache' : 'api_call'
            });
            
            return { data: response.data };
        } catch (error) {
            logger.error('❌ Error in simple getServiceList:', error);
            throw error;
        }
    },

    // ServiceList Cache Check - DISABLED: Using proactive loading instead
    checkServiceListCache: async (flightPriceResponse: any): Promise<{ data: any }> => {
        logger.info('🚀 Cache check bypassed - using proactive loading');
        // Return cache miss to trigger direct API call (which will use proactive cache)
        return { 
            data: { 
                cache_hit: false, 
                status: 'cache_miss', 
                message: 'Proactive loading enabled - use direct API call' 
            } 
        };
    },

    // SeatAvailability API - Using simple manager with proactive caching
    getSeatAvailability: async (flightPriceResponse: any, segmentKey?: string): Promise<{ data: any }> => {
        try {
            logger.info('🚀 Using simple API manager for seat availability (proactive cache first)');
            
            const response = await simpleApiManager.getSeatAvailability(
                flightPriceResponse,
                segmentKey
            );
            
            logger.info('✅ Seat availability received via simple manager', {
                hasData: !!response.data,
                source: response.cache_hit ? 'proactive_cache' : 'api_call'
            });
            
            return { data: response.data };
        } catch (error) {
            logger.error('❌ Error in simple getSeatAvailability:', error);
            throw error;
        }
    },

    // SeatAvailability Cache Check - DISABLED: Using proactive loading instead
    checkSeatAvailabilityCache: async (flightPriceResponse: any, segmentKey?: string): Promise<{ data: any }> => {
        logger.info('🚀 Cache check bypassed - using proactive loading');
        // Return cache miss to trigger direct API call (which will use proactive cache)
        return { 
            data: { 
                cache_hit: false, 
                status: 'cache_miss', 
                message: 'Proactive loading enabled - use direct API call' 
            } 
        };
    },

    // Health Check
    healthCheck: async () => {
        return apiClient.get('/api/health');
    },

    // Generic GET method
    get: async (url: string) => {
        // For local API routes, use fetch with relative URL
        if (url.startsWith('/api/')) {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                }
            });
            
            const data = await response.json();
            
            // Log for debugging
            logger.info('Local API Response', { status: response.status, url });
            
            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }
            
            return { data };
        }
        
        // For external API routes, use apiClient
        return apiClient.get(url);
    }
};

// Export the apiClient for use in other modules
export { apiClient };
export default apiClient;
