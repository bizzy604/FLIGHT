'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/loading-spinner';
import { Plane, Ticket, Calendar, Clock, MapPin, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';

// Mock data - replace with actual API call
type Booking = {
  id: string;
  passengerName: string;
  flightNumber: string;
  departure: {
    city: string;
    airport: string;
    time: string;
    date: string;
  };
  arrival: {
    city: string;
    airport: string;
    time: string;
  };
  seat: string;
  confirmation: string;
  duration: string;
  class: string;
};

const mockBookings: Booking[] = [
  {
    id: '123',
    passengerName: 'John Doe',
    flightNumber: 'AL 2847',
    departure: {
      city: 'New York',
      airport: 'LGA',
      time: '07:25 AM',
      date: '2024-06-15',
    },
    arrival: {
      city: 'Los Angeles',
      airport: 'LAX',
      time: '10:57 AM',
    },
    seat: '12A',
    confirmation: 'AX7K92',
    duration: '5h 32m',
    class: 'Business',
  },
  {
    id: '124',
    passengerName: 'John Doe',
    flightNumber: 'AL 1234',
    departure: {
      city: 'San Francisco',
      airport: 'SFO',
      time: '02:15 PM',
      date: '2024-07-01',
    },
    arrival: {
      city: 'New York',
      airport: 'JFK',
      time: '10:30 PM',
    },
    seat: '8C',
    confirmation: 'BX9M45',
    duration: '5h 15m',
    class: 'Economy',
  },
];

export default function BookingsPage() {
  const { user, isLoaded } = useUser();
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded) return;

    const fetchBookings = async () => {
      try {
        // In a real app, fetch bookings from your API
        // const response = await fetch('/api/bookings', {
        //   headers: {
        //     'Content-Type': 'application/json',
        //   },
        //   credentials: 'include',
        // });
        // const data = await response.json();
        // setBookings(data);
        
        // Using mock data for now
        setTimeout(() => {
          setBookings(mockBookings);
          setIsLoading(false);
        }, 800); // Simulate network delay
      } catch (err) {
        console.error('Error fetching bookings:', err);
        setError('Failed to load bookings. Please try again later.');
        setIsLoading(false);
      }
    };

    fetchBookings();
  }, [isLoaded]);

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
        <Button 
          onClick={() => window.location.reload()} 
          className="mt-4"
          variant="outline"
        >
          Try Again
        </Button>
      </div>
    );
  }

  if (bookings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="text-center max-w-md">
          <Ticket className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">No bookings found</h1>
          <p className="text-gray-600 mb-6">You don't have any upcoming trips. Start by searching for flights to book your next adventure!</p>
          <Button onClick={() => router.push('/')}>
            Search Flights
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Bookings</h1>
          <p className="text-gray-600">View and manage your upcoming trips</p>
        </div>

        <div className="space-y-6">
          {bookings.map((booking) => (
            <Card key={booking.id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3 bg-blue-50">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl flex items-center gap-2">
                      <Plane className="w-5 h-5 text-blue-600" />
                      {booking.departure.city} to {booking.arrival.city}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Booking #{booking.confirmation}
                    </CardDescription>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {booking.class}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                      {format(new Date(booking.departure.date), 'EEE, MMM d, yyyy')}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Clock className="w-4 h-4 mr-2 text-gray-400" />
                      {booking.duration}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm">
                      <div className="font-medium">{booking.departure.time}</div>
                      <div className="text-gray-600">{booking.departure.airport}</div>
                    </div>
                    <div className="text-sm">
                      <div className="font-medium">{booking.arrival.time}</div>
                      <div className="text-gray-600">{booking.arrival.airport}</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm">
                      <div className="text-gray-500">Seat</div>
                      <div className="font-medium">{booking.seat}</div>
                    </div>
                    <div className="text-sm">
                      <div className="text-gray-500">Flight</div>
                      <div className="font-medium">{booking.flightNumber}</div>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="bg-gray-50 px-6 py-3">
                <Button 
                  variant="outline" 
                  className="ml-auto"
                  onClick={() => router.push(`/bookings/${booking.id}`)}
                >
                  View Boarding Pass <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
