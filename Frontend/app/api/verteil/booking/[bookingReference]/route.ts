import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/utils/prisma';

export async function GET(request: NextRequest, { params }: { params: { bookingReference: string } }) {
  try {
    const { bookingReference } = params;
    
    console.log('[[ DEBUG ]] Fetching booking from database with reference:', bookingReference);
    
    // Fetch booking from local database
    const booking = await prisma.booking.findUnique({
      where: {
        bookingReference: bookingReference
      },
      include: {
        payments: true // Include payment information if needed
      }
    });
    
    if (!booking) {
      console.log('[[ DEBUG ]] Booking not found in database:', bookingReference);
      return NextResponse.json(
        { 
          error: '404 Not Found: The requested URL was not found on the server.',
          message: 'The requested resource was not found.',
          status: 'error'
        },
        { status: 404 }
      );
    }
    
    console.log('[[ DEBUG ]] Booking found in database:', booking.id);
    
    // Return booking data in the expected format
    return NextResponse.json({
      status: 'success',
      data: booking
    });
  } catch (error) {
    console.error('Error fetching booking from database:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: 'An error occurred while fetching the booking.'
      },
      { status: 500 }
    );
  }
}