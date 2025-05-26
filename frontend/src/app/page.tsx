"use client";

import { useState } from 'react';
import SearchForm, { SearchFormData } from '../components/SearchForm';
import FlightResults, { Flight } from '../components/FlightResults';
import { searchFlights } from '../services/flightService';
import { FlightBookingProvider } from '../context/FlightBookingContext';

export default function Home() {
  const [searchResults, setSearchResults] = useState<Flight[]>([]);
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (data: SearchFormData) => {
    setIsLoading(true);
    setError(null);
    setSelectedFlight(null);
    
    try {
      // For demo purposes, let's use mock data instead of actual API call
      // In production, you would use the actual API call:
      // const results = await searchFlights(data);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Mock flight data
      const mockFlights: Flight[] = [
        {
          id: '1',
          airline: 'SkyWings',
          flightNumber: 'SW1234',
          departureTime: '08:30',
          departureAirport: data.origin,
          arrivalTime: '10:45',
          arrivalAirport: data.destination,
          duration: '2h 15m',
          price: 299.99,
          stops: 0,
          cabinClass: data.cabinClass
        },
        {
          id: '2',
          airline: 'GlobeAir',
          flightNumber: 'GA5678',
          departureTime: '12:15',
          departureAirport: data.origin,
          arrivalTime: '15:30',
          arrivalAirport: data.destination,
          duration: '3h 15m',
          price: 249.99,
          stops: 1,
          cabinClass: data.cabinClass
        },
        {
          id: '3',
          airline: 'BlueSky',
          flightNumber: 'BS9012',
          departureTime: '16:45',
          departureAirport: data.origin,
          arrivalTime: '19:00',
          arrivalAirport: data.destination,
          duration: '2h 15m',
          price: 329.99,
          stops: 0,
          cabinClass: data.cabinClass
        }
      ];
      
      setSearchResults(mockFlights);
    } catch (err) {
      setError('Failed to fetch flights. Please try again.');
      console.error('Error searching flights:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFlight = (flight: Flight) => {
    setSelectedFlight(flight);
    // In a real application, you would navigate to a booking details page
    console.log('Selected flight:', flight);
  };

  return (
    <FlightBookingProvider>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-blue-600 text-white p-4">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-2xl font-bold">Flight Booking System</h1>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Search Flights</h2>
              <SearchForm onSearch={handleSearch} isLoading={isLoading} />
            </div>
          </div>
          
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}
          
          {(searchResults.length > 0 || isLoading) && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <FlightResults 
                flights={searchResults} 
                isLoading={isLoading} 
                onSelect={handleSelectFlight} 
              />
            </div>
          )}
          
          {selectedFlight && (
            <div className="mt-8 bg-green-50 border-l-4 border-green-500 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-green-700">
                    Flight selected! In a complete application, you would proceed to passenger details and payment.
                  </p>
                </div>
              </div>
            </div>
          )}
        </main>
        
        <footer className="bg-gray-800 text-white py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <p className="text-center text-sm">© 2025 Flight Booking System. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </FlightBookingProvider>
  );
}
