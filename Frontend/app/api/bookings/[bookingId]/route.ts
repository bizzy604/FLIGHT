import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { prisma } from '@/utils/prisma';

export async function GET(
  request: Request,
  { params }: { params: { bookingId: string } }
) {
  try {
    const { userId } = await auth();

    // For development purposes, allow unauthenticated requests
    // In production, you would want to remove this and require authentication
    const userIdToUse = userId || "dev-user-id";

    const bookingId = params.bookingId;

    // Build the where clause - match the logic from bookings list API
    const where: any = {
      OR: [
        { bookingReference: bookingId },
        { id: parseInt(bookingId) || 0 }
      ]
    };

    // Only filter by userId if authenticated (same logic as bookings list)
    if (userId) {
      where.userId = userId;
    }

    // Try to find booking by booking reference first, then by ID
    let booking = await prisma.booking.findFirst({
      where,
      include: {
        payments: true
      }
    });

    if (!booking) {
      return new NextResponse('Booking not found', { status: 404 });
    }



    return NextResponse.json(booking);
  } catch (error) {
    console.error('Error fetching booking:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
