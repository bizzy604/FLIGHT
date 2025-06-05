// Type definitions for custom modules
declare module '@/lib/flight-api' {
  export interface FlightSearchRequest {
    tripType: string;
    odSegments: Array<{
      Origin: string;
      Destination: string;
      DepartureDate: string;
    }>;
    numAdults: number;
    numChildren: number;
    numInfants: number;
    cabinPreference: string;
  }

  export interface FlightOffer {
    // Define the FlightOffer interface based on your backend response
    id: string;
    // Add other flight offer properties
  }

  export function callVerteilAirShopping(params: FlightSearchRequest): Promise<FlightOffer[]>;
  export function getFlightDetails(offerId: string): Promise<FlightOffer>;
}

declare module '@/lib/logger' {
  export const logger: {
    info: (message: string, data?: any) => void;
    error: (message: string, error?: any) => void;
    debug: (message: string, data?: any) => void;
  };
}
