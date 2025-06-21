// Type definitions for custom modules
declare module '@/lib/flight-api' {
  export interface FlightSearchRequest {
    tripType: string;
    odSegments: Array<{
      origin: string;
      destination: string;
      departureDate: string;
    }>;
    numAdults: number;
    numChildren: number;
    numInfants: number;
    cabinPreference: string;
    directOnly: boolean;
  }

  export function callVerteilAirShopping(params: FlightSearchRequest): Promise<any>;
}

declare module '@/lib/logger' {
  export const logger: {
    info: (message: string, data?: any) => void;
    error: (message: string, error?: any) => void;
    debug: (message: string, data?: any) => void;
  };
}
