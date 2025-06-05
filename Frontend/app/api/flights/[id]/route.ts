import { NextResponse } from 'next/server';
import { getFlightDetails } from '@/lib/flight-api';
import { logger } from '@/lib/logger';

interface FlightDetailsParams {
  id: string;
}

// Type definition for the error object
type ErrorWithMessage = {
  message: string;
  response?: {
    data: any;
    status: number;
  };
};

export const dynamic = 'force-dynamic';

export async function GET(
  request: Request,
  { params }: { params: FlightDetailsParams }
) {
  try {
    const { id } = params;
    if (!id) {
      return NextResponse.json(
        { error: 'Flight ID is required' },
        { status: 400 }
      );
    }

    const flightDetails = await getFlightDetails(id);
    return NextResponse.json(flightDetails);
  } catch (error) {
    logger.error('Error fetching flight details', { error });
    return NextResponse.json(
      { error: 'Failed to fetch flight details' },
      { status: 500 }
    );
  }
}