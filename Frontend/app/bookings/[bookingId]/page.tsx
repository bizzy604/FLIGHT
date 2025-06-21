'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { LoadingSpinner } from '@/components/loading-spinner';
import dynamic from 'next/dynamic';

// Dynamically import the BoardingPass component with SSR disabled
const BoardingPass = dynamic(
  () => import('@/components/boarding-pass/BoardingPass'),
  { ssr: false }
);

type BookingData = {
  id: string;
  passengerName: string;
  flightNumber: string;
  departure: {
    city: string;
    airport: string;
    time: string;
    terminal: string;
    gate: string;
  };
  arrival: {
    city: string;
    airport: string;
    time: string;
  };
  seat: string;
  boardingTime: string;
  confirmation: string;
  duration: string;
  class: string;
  amenities: string[];
};

export default function BookingPassPage() {
  const { bookingId } = useParams<{ bookingId: string }>();
  const { user, isLoaded } = useUser();
  const router = useRouter();
  const [booking, setBooking] = useState<BookingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded) return;

    const fetchBooking = async () => {
      try {
        // Replace with your actual API endpoint to fetch booking details
        const response = await fetch(`/api/bookings/${bookingId}`, {
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch booking details');
        }

        const data = await response.json();
        setBooking(data);
      } catch (err) {
        console.error('Error fetching booking:', err);
        setError('Failed to load booking details. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchBooking();
  }, [bookingId, isLoaded]);

  if (!isLoaded || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative max-w-md w-full" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
        <button
          onClick={() => router.back()}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative max-w-md w-full">
          <strong className="font-bold">No booking found</strong>
          <span className="block sm:inline"> We couldn't find the requested booking.</span>
        </div>
        <button
          onClick={() => router.push('/')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Return Home
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Your Boarding Pass</h1>
          <p className="mt-2 text-sm text-gray-600">
            Booking reference: {booking.confirmation}
          </p>
        </div>
        
        <div className="bg-white shadow-lg rounded-2xl overflow-hidden">
          <BoardingPass 
            passengerName={booking.passengerName}
            flightNumber={booking.flightNumber}
            departureCity={booking.departure.city}
            departureAirport={booking.departure.airport}
            departureTime={booking.departure.time}
            arrivalCity={booking.arrival.city}
            arrivalAirport={booking.arrival.airport}
            arrivalTime={booking.arrival.time}
            seat={booking.seat}
            boardingTime={booking.boardingTime}
            terminal={booking.departure.terminal}
            gate={booking.departure.gate}
            confirmation={booking.confirmation}
            duration={booking.duration}
            classType={booking.class}
            amenities={booking.amenities}
          />
        </div>
        
        <div className="mt-8 flex justify-between items-center">
          <button
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back to My Bookings
          </button>
          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Print Boarding Pass
          </button>
        </div>
      </div>
    </div>
  );
}
