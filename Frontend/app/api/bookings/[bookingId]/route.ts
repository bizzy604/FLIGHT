import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

// Mock data - replace with actual database query in production
const mockBookings: Record<string, any> = {
  '123': {
    id: '123',
    passengerName: 'John Doe',
    flightNumber: 'AL 2847',
    departure: {
      city: 'NYC',
      airport: 'LaGuardia Airport',
      time: '07:25 AM EST',
      terminal: 'B',
      gate: 'C14',
    },
    arrival: {
      city: 'LAX',
      airport: 'Los Angeles Intl',
      time: '10:57 AM PST',
    },
    seat: '12A',
    boardingTime: '06:45',
    confirmation: 'AX7K92',
    duration: '5h 32m',
    class: 'BUSINESS',
    amenities: ['WIFI', 'MEAL'],
  },
};

export async function GET(
  request: Request,
  { params }: { params: { bookingId: string } }
) {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const bookingId = params.bookingId;
    const booking = mockBookings[bookingId];

    if (!booking) {
      return new NextResponse('Booking not found', { status: 404 });
    }

    // In a real app, verify the user has access to this booking
    // For now, we'll just return the mock data
    
    return NextResponse.json(booking);
  } catch (error) {
    console.error('[BOOKING_GET]', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
