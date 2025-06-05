// app/api/flights/search-advanced/route.ts
import { NextResponse } from 'next/server';
import { callVerteilAirShopping } from '@/lib/flight-api';
import { logger } from '@/lib/logger';

export const dynamic = 'force-dynamic';

// Define interfaces for the NDC payload
interface NDCOriginDestination {
  Departure: {
    AirportCode: {
      value: string;
    };
    Date: string;
  };
  Arrival: {
    AirportCode: {
      value: string;
    };
  };
  OriginDestinationKey: string;
}

interface NDCTraveler {
  AnonymousTraveler?: Array<{
    PTC: {
      value: string;
    };
  }>;
}

interface NDCPayload {
  CoreQuery?: {
    OriginDestinations?: {
      OriginDestination: NDCOriginDestination[];
    };
  };
  Travelers?: {
    Traveler: NDCTraveler[];
  };
  Preference?: {
    CabinPreferences?: {
      CabinType: Array<{
        Code: string;
      }>;
    };
  };
}

export async function POST(req: Request) {
  try {
    const payload: NDCPayload = await req.json();
    logger.info('Advanced flight search request', { payload: JSON.stringify(payload, null, 2) });

    // Extract data from the NDC payload
    const originDestinations = payload.CoreQuery?.OriginDestinations?.OriginDestination || [];
    const travelers = payload.Travelers?.Traveler || [];
    
    // Count passenger types
    const countPassengers = (type: string): number => 
      travelers.flatMap((t: NDCTraveler) => t.AnonymousTraveler || [])
        .filter(t => t.PTC?.value === type)
        .length;
    
    const adults = countPassengers('ADT');
    const children = countPassengers('CHD');
    const infants = countPassengers('INF');
    
    // Get cabin preference (default to ECONOMY)
    const cabinPreference = 
      payload.Preference?.CabinPreferences?.CabinType?.[0]?.Code || 'Y';

    // Map NDC cabin codes to our format
    const cabinMap: Record<string, string> = {
      'Y': 'ECONOMY',
      'W': 'PREMIUM_ECONOMY',
      'C': 'BUSINESS',
      'F': 'FIRST'
    };

    // Transform origin-destination segments
    const odSegments = originDestinations.map((od: NDCOriginDestination) => ({
      Origin: od.Departure?.AirportCode?.value || '',
      Destination: od.Arrival?.AirportCode?.value || '',
      DepartureDate: od.Departure?.Date || ''
    }));

    // Prepare the backend request matching FlightSearchRequest interface with correct property names
    const backendRequest = {
      tripType: odSegments.length > 1 ? 'ROUND_TRIP' : 'ONE_WAY',
      odSegments: odSegments.map(segment => ({
        origin: segment.Origin,         // Use camelCase 'origin' as expected by backend
        destination: segment.Destination, // Use camelCase 'destination' as expected by backend
        departureDate: segment.DepartureDate // Use camelCase 'departureDate' as expected by backend
      })),
      numAdults: adults || 1,
      numChildren: children || 0,
      numInfants: infants || 0,
      cabinPreference: cabinMap[cabinPreference] || 'ECONOMY', // Use 'cabinPreference' as expected by backend
      directOnly: false
    };

    logger.info('Sending to backend:', JSON.stringify(backendRequest, null, 2));
    const results = await callVerteilAirShopping(backendRequest);
    return NextResponse.json(results);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    logger.error('Error in advanced flight search', { error: errorMessage });
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}