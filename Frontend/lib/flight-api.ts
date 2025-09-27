import axios from "axios";

// In flight-api.ts, update the FlightSearchRequest interface to:
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

export async function callVerteilAirShopping(params: FlightSearchRequest) {
    try {
      const rawBackend = process.env.NEXT_PUBLIC_API_BASE_URL || '';
      const backend = rawBackend.replace(/\/+$/, '');
      const response = await axios.post(
        `${backend}/verteil/air-shopping`,
        params,
        {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error in callVerteilAirShopping:', error);
      throw error;
    }
}