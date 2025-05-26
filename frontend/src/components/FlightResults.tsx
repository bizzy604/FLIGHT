"use client";

import { useState } from 'react';

export type Flight = {
  id: string;
  airline: string;
  flightNumber: string;
  departureTime: string;
  departureAirport: string;
  arrivalTime: string;
  arrivalAirport: string;
  duration: string;
  price: number;
  stops: number;
  cabinClass: string;
};

type FlightResultsProps = {
  flights: Flight[];
  isLoading: boolean;
  onSelect: (flight: Flight) => void;
};

const FlightResults = ({ flights, isLoading, onSelect }: FlightResultsProps) => {
  const [selectedFlightId, setSelectedFlightId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (flights.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <h3 className="text-xl font-medium text-gray-900 mb-2">No flights found</h3>
        <p className="text-gray-600">Try adjusting your search criteria</p>
      </div>
    );
  }

  const handleSelect = (flight: Flight) => {
    setSelectedFlightId(flight.id);
    onSelect(flight);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Available Flights</h2>
      
      {flights.map((flight) => (
        <div 
          key={flight.id} 
          className={`bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow ${selectedFlightId === flight.id ? 'ring-2 ring-blue-500' : ''}`}
        >
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4">
            <div className="flex items-center">
              <div className="mr-4">
                <span className="font-bold text-gray-900">{flight.airline}</span>
                <span className="text-gray-500 text-sm ml-2">{flight.flightNumber}</span>
              </div>
            </div>
            <div className="font-bold text-xl text-blue-600">${flight.price}</div>
          </div>

          <div className="flex flex-col md:flex-row justify-between mb-4">
            <div className="flex flex-col">
              <span className="text-gray-500 text-sm">Departure</span>
              <span className="font-bold text-gray-900">{flight.departureTime}</span>
              <span className="text-gray-700">{flight.departureAirport}</span>
            </div>
            
            <div className="flex flex-col items-center my-2 md:my-0">
              <div className="text-gray-500 text-sm">{flight.duration}</div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                <div className="w-16 md:w-32 border-t border-gray-300 mx-2"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              </div>
              <div className="text-gray-500 text-xs">
                {flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
              </div>
            </div>

            <div className="flex flex-col text-right">
              <span className="text-gray-500 text-sm">Arrival</span>
              <span className="font-bold text-gray-900">{flight.arrivalTime}</span>
              <span className="text-gray-700">{flight.arrivalAirport}</span>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              <span className="inline-block px-2 py-1 bg-gray-100 rounded text-gray-700">
                {flight.cabinClass}
              </span>
            </div>
            <button 
              onClick={() => handleSelect(flight)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors duration-200"
            >
              Select
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FlightResults;
