import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { debounce } from 'lodash';
import { logger } from './logger';
import type { FlightSearchResponse } from '@/types/flight-api';

// Get backend URL from environment
const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://rea-travel-backend.onrender.com';

// Create axios instance with default config
const apiClient = axios.create({
    baseURL: BACKEND_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    withCredentials: true,
    timeout: 30000, // 30 seconds timeout
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
        
        // Add request timestamp
        config.headers['X-Request-Timestamp'] = new Date().toISOString();
        
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
        const response = await apiClient.post<FlightSearchResponse>('/api/verteil/air-shopping', params);
        resolve(response);
    } catch (error) {
        reject(error);
    }
}, 1000); // 1 second debounce delay

export const api = {
    // Flight Search with debouncing
    searchFlights: async (params: FlightSearchRequest): Promise<{ data: FlightSearchResponse }> => {
        return new Promise((resolve, reject) => {
            debouncedSearchFlights(params, resolve, reject);
        });
    },

    // Flight Pricing
    getFlightPrice: async (offerId: string, shoppingResponseId: string, airShoppingResponse: any) => {
        try {
            logger.info('Sending flight price request', {
                offerId,
                shoppingResponseId,
                hasAirShoppingResponse: !!airShoppingResponse,
                airShoppingResponseType: airShoppingResponse ? typeof airShoppingResponse : 'undefined'
            });
            
            const response = await apiClient.post('/api/verteil/flight-price', {
                offer_id: offerId,
                shopping_response_id: shoppingResponseId,
                air_shopping_response: airShoppingResponse
            });
            
            logger.info('Flight price response received', {
                status: response.status,
                data: response.data ? 'Received' : 'No data'
            });
            
            return response;
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            const errorResponse = error && typeof error === 'object' && 'response' in error 
                ? (error as any).response?.data 
                : undefined;
                
            logger.error('Error in getFlightPrice', {
                error: errorMessage,
                response: errorResponse
            });
            
            throw new Error(errorResponse?.message || errorMessage);
        }
    },

    // Booking - Use fetch directly to call Next.js API route
    createBooking: async (flightOffer: any, passengers: any[], payment: any, contactInfo: any) => {
        const response = await fetch('/api/verteil/order-create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                flight_offer: flightOffer,
                passengers,
                payment,
                contact_info: contactInfo
            })
        });
        
        const data = await response.json();
        
        // Log for debugging
        logger.info('API Response', { status: response.status, url: '/api/verteil/order-create' });
        
        if (!response.ok) {
            throw new Error(data.message || 'Booking failed');
        }
        
        return { data };
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
