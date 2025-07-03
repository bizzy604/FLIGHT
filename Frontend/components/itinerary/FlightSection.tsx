"use client"

import React from 'react';
import { FlightSegment, PricingInfo } from '@/utils/itinerary-data-transformer';

interface FlightSectionProps {
  outboundFlight: FlightSegment[];
  returnFlight: FlightSegment[] | null;
  pricing: PricingInfo;
}

const FlightSection: React.FC<FlightSectionProps> = ({ 
  outboundFlight, 
  returnFlight, 
  pricing 
}) => {
  const renderFlightSegments = (segments: FlightSegment[], title: string, icon: string) => (
    <div className="mb-8">
      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <span className="text-2xl mr-3">{icon}</span>
        {title}
      </h3>
      
      <div className="space-y-4">
        {segments.map((segment, index) => (
          <div key={segment.segmentKey} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            {/* Flight Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  {segment.airlineCode}
                </div>
                <div>
                  <h4 className="text-lg font-bold text-gray-800">{segment.flightNumber}</h4>
                  <p className="text-sm text-gray-600">{segment.airline}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-600">Class of Service</p>
                <p className="text-lg font-bold text-blue-600">{segment.classOfService}</p>
              </div>
            </div>

            {/* Flight Route */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
              {/* Departure */}
              <div className="text-center md:text-left">
                <div className="space-y-2">
                  <h5 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                    Departure
                  </h5>
                  <div className="space-y-1">
                    <p className="text-2xl font-bold text-gray-800">{segment.departure.airport}</p>
                    <p className="text-sm text-gray-600">{segment.departure.airportName}</p>
                    <p className="text-lg font-semibold text-blue-600">{segment.departure.formattedDateTime}</p>
                    {segment.departure.terminal && (
                      <p className="text-sm text-gray-500">Terminal {segment.departure.terminal}</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Flight Info */}
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  <div className="w-4 h-4 bg-blue-600 rounded-full"></div>
                  <div className="flex-1 h-0.5 bg-blue-600 mx-2"></div>
                  <span className="text-sm text-gray-600 px-2">✈️</span>
                  <div className="flex-1 h-0.5 bg-blue-600 mx-2"></div>
                  <div className="w-4 h-4 bg-blue-600 rounded-full"></div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-gray-600">Duration</p>
                  <p className="text-lg font-bold text-gray-800">{segment.durationFormatted}</p>
                  <p className="text-xs text-gray-500">Aircraft: {segment.aircraft}</p>
                </div>
              </div>

              {/* Arrival */}
              <div className="text-center md:text-right">
                <div className="space-y-2">
                  <h5 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
                    Arrival
                  </h5>
                  <div className="space-y-1">
                    <p className="text-2xl font-bold text-gray-800">{segment.arrival.airport}</p>
                    <p className="text-sm text-gray-600">{segment.arrival.airportName}</p>
                    <p className="text-lg font-semibold text-blue-600">{segment.arrival.formattedDateTime}</p>
                    {segment.arrival.terminal && (
                      <p className="text-sm text-gray-500">Terminal {segment.arrival.terminal}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Additional Flight Details */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-600">Segment:</span>
                  <p className="text-gray-800">{segment.segmentKey}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-600">Cabin:</span>
                  <p className="text-gray-800">{segment.cabinClass}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-600">Fare Basis:</span>
                  <p className="text-gray-800 font-mono">{segment.fareBasisCode}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-600">Operating:</span>
                  <p className="text-gray-800">{segment.airline}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="p-6 border-b border-gray-200">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
        <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
          ✈️
        </span>
        Flight Details
      </h2>

      {/* Outbound Flight */}
      {renderFlightSegments(outboundFlight, 'Outbound Journey', '🛫')}

      {/* Return Flight */}
      {returnFlight && renderFlightSegments(returnFlight, 'Return Journey', '🛬')}

      {/* Pricing Summary */}
      <div className="mt-8 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <span className="text-2xl mr-3">💰</span>
          Total Fare
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="text-center md:text-left">
            <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Total Amount
            </p>
            <p className="text-3xl font-bold text-blue-600">{pricing.formattedTotal}</p>
          </div>
          
          <div className="text-center">
            <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Payment Method
            </p>
            <p className="text-lg font-semibold text-gray-800">{pricing.paymentMethodLabel}</p>
          </div>
          
          <div className="text-center md:text-right">
            <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Currency
            </p>
            <p className="text-lg font-semibold text-gray-800">{pricing.currency}</p>
          </div>
        </div>

        <div className="mt-4 p-3 bg-white rounded-md border border-blue-200">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">💡 Note:</span> This amount includes all applicable taxes and fees. 
            No additional charges will be applied at the airport for this booking.
          </p>
        </div>
      </div>

      {/* Journey Summary */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <span className="font-semibold text-gray-700">Total Segments:</span>
            <p className="text-lg font-bold text-blue-600">
              {outboundFlight.length + (returnFlight?.length || 0)}
            </p>
          </div>
          <div className="text-center">
            <span className="font-semibold text-gray-700">Trip Type:</span>
            <p className="text-lg font-bold text-blue-600">
              {returnFlight ? 'Round Trip' : 'One Way'}
            </p>
          </div>
          <div className="text-center">
            <span className="font-semibold text-gray-700">Airlines:</span>
            <p className="text-lg font-bold text-blue-600">
              {Array.from(new Set([
                ...outboundFlight.map(f => f.airlineCode),
                ...(returnFlight?.map(f => f.airlineCode) || [])
              ])).join(', ')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlightSection;
