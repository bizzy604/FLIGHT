"use client"

import React from 'react';
import { ItineraryData } from '@/utils/itinerary-data-transformer';
import '@/styles/compact-itinerary.css';

interface CompactItineraryProps {
  data: ItineraryData;
  className?: string;
}

const CompactItinerary: React.FC<CompactItineraryProps> = ({ data, className = '' }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const formatTime = (timeString: string) => {
    return timeString || 'N/A';
  };

  return (
    <div className={`bg-white text-black ${className}`} style={{
      fontSize: '14px',
      lineHeight: '1.4'
    }}>
        {/* Page 1 - Header and Flight Details */}
        <div className="min-h-[50vh] p-8">
        {/* Header */}
        <div className="text-center mb-8 border-b-2 border-blue-600 pb-6">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mr-4">
              <span className="text-white font-bold text-lg">✈️</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-blue-600">Rea Travels Agency</h1>
              <p className="text-gray-600">Your Trusted Travel Partner</p>
              <p className="text-sm text-gray-500">Licensed Travel Agency</p>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-800">OFFICIAL FLIGHT ITINERARY</h2>
          <p className="text-gray-600">Issue Date: {new Date().toLocaleDateString()}</p>
        </div>

        {/* Booking Summary */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="bg-blue-50 p-4 rounded-lg text-center">
            <h3 className="font-bold text-blue-800 mb-2">BOOKING REFERENCE</h3>
            <p className="text-2xl font-bold text-blue-600">{data.bookingInfo.bookingReference}</p>
            <p className="text-sm text-gray-600">Order ID: {data.bookingInfo.orderID}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg text-center">
            <h3 className="font-bold text-green-800 mb-2">PASSENGER COUNT</h3>
            <p className="text-2xl font-bold text-green-600">{data.passengers.length}</p>
            <p className="text-sm text-gray-600">Passenger{data.passengers.length > 1 ? 's' : ''}</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg text-center">
            <h3 className="font-bold text-purple-800 mb-2">STATUS</h3>
            <p className="text-lg font-bold text-green-600">✅ Confirmed</p>
            <p className="text-sm text-gray-600">Booking Status: {data.bookingInfo.status}</p>
          </div>
        </div>

        {/* Passenger Information */}
        <div className="mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm mr-3">👤</span>
            Passenger Information
          </h3>
          <div className="grid grid-cols-1 gap-3">
            {data.passengers.map((passenger, index) => (
              <div key={index} className="bg-gray-50 p-4 rounded-lg flex justify-between items-center">
                <div>
                  <p className="font-bold text-lg">{passenger.name}</p>
                  <p className="text-gray-600">{passenger.type} • Ticket: {passenger.ticketNumber || 'N/A'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">Passenger ID: {passenger.passengerID}</p>
                  <p className="text-sm text-gray-600">{passenger.documentType}: {passenger.documentNumber || 'N/A'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Contact Information */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-bold text-blue-800 mb-2">Contact Email</h4>
            <p className="text-gray-700">{data.contactInfo.email || 'N/A'}</p>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-bold text-blue-800 mb-2">Contact Phone</h4>
            <p className="text-gray-700">{data.contactInfo.phone || 'N/A'}</p>
          </div>
        </div>
      </div>

      {/* Page Break */}
      <div className="page-break"></div>

      {/* Page 2 - Flight Details and Important Info */}
      <div className="min-h-[50vh] p-8">
        {/* Flight Details */}
        <div className="mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
            <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm mr-3">✈️</span>
            Flight Details
          </h3>

          {/* Outbound Flight */}
          {data.outboundFlight && data.outboundFlight.length > 0 && (
            <div className="bg-blue-50 p-6 rounded-lg mb-6">
              <h4 className="text-lg font-bold text-blue-800 mb-4">Outbound Journey</h4>
              {data.outboundFlight.map((segment, index) => (
                <div key={index} className={index > 0 ? "mt-4 pt-4 border-t border-blue-300" : ""}>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h5 className="font-bold text-gray-700 mb-2">Departure</h5>
                      <p className="text-lg font-bold">{segment.departure?.airport || 'N/A'}</p>
                      <p className="text-gray-600">{segment.departure?.date ? formatDate(segment.departure.date) : 'N/A'}</p>
                      <p className="text-xl font-bold text-blue-600">{formatTime(segment.departure?.time || '')}</p>
                      <p className="text-sm text-gray-500">Terminal: {segment.departure?.terminal || 'N/A'}</p>
                    </div>
                    <div>
                      <h5 className="font-bold text-gray-700 mb-2">Arrival</h5>
                      <p className="text-lg font-bold">{segment.arrival?.airport || 'N/A'}</p>
                      <p className="text-gray-600">{segment.arrival?.date ? formatDate(segment.arrival.date) : 'N/A'}</p>
                      <p className="text-xl font-bold text-blue-600">{formatTime(segment.arrival?.time || '')}</p>
                      <p className="text-sm text-gray-500">Terminal: {segment.arrival?.terminal || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-blue-200">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center">
                        {segment.airlineLogo && (
                          <img
                            src={segment.airlineLogo}
                            alt={segment.airline}
                            className="w-8 h-8 mr-3 object-contain"
                            onError={(e) => { e.currentTarget.style.display = 'none'; }}
                          />
                        )}
                        <div>
                          <p className="font-bold text-lg">{segment.airline} {segment.flightNumber}</p>
                          <p className="text-gray-600">{segment.aircraft} • {segment.classOfService || 'N/A'}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Duration: {segment.duration || 'N/A'}</p>
                        <p className="text-sm text-gray-600">Cabin: {segment.cabinClass || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Return Flight */}
          {data.returnFlight && data.returnFlight.length > 0 && (
            <div className="bg-green-50 p-6 rounded-lg mb-6">
              <h4 className="text-lg font-bold text-green-800 mb-4">Return Journey</h4>
              {data.returnFlight.map((segment, index) => (
                <div key={index} className={index > 0 ? "mt-4 pt-4 border-t border-green-300" : ""}>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h5 className="font-bold text-gray-700 mb-2">Departure</h5>
                      <p className="text-lg font-bold">{segment.departure?.airport || 'N/A'}</p>
                      <p className="text-gray-600">{segment.departure?.date ? formatDate(segment.departure.date) : 'N/A'}</p>
                      <p className="text-xl font-bold text-green-600">{formatTime(segment.departure?.time || '')}</p>
                      <p className="text-sm text-gray-500">Terminal: {segment.departure?.terminal || 'N/A'}</p>
                    </div>
                    <div>
                      <h5 className="font-bold text-gray-700 mb-2">Arrival</h5>
                      <p className="text-lg font-bold">{segment.arrival?.airport || 'N/A'}</p>
                      <p className="text-gray-600">{segment.arrival?.date ? formatDate(segment.arrival.date) : 'N/A'}</p>
                      <p className="text-xl font-bold text-green-600">{formatTime(segment.arrival?.time || '')}</p>
                      <p className="text-sm text-gray-500">Terminal: {segment.arrival?.terminal || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-green-200">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center">
                        {segment.airlineLogo && (
                          <img
                            src={segment.airlineLogo}
                            alt={segment.airline}
                            className="w-8 h-8 mr-3 object-contain"
                            onError={(e) => { e.currentTarget.style.display = 'none'; }}
                          />
                        )}
                        <div>
                          <p className="font-bold text-lg">{segment.airline} {segment.flightNumber}</p>
                          <p className="text-gray-600">{segment.aircraft} • {segment.classOfService || 'N/A'}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Duration: {segment.duration || 'N/A'}</p>
                        <p className="text-sm text-gray-600">Cabin: {segment.cabinClass || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pricing Summary */}
        <div className="bg-yellow-50 p-6 rounded-lg mb-6">
          <h4 className="text-lg font-bold text-yellow-800 mb-4">💰 Total Fare</h4>
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">Total Amount</p>
            <p className="text-3xl font-bold text-yellow-800">{data.pricing.formattedTotal}</p>
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div className="text-center">
                <p className="text-gray-600">Payment Method</p>
                <p className="font-semibold">{data.pricing.paymentMethodLabel}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600">Currency</p>
                <p className="font-semibold">{data.pricing.currency}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Essential Information */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Baggage */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-bold text-blue-800 mb-3 flex items-center">
              <span className="mr-2">🧳</span>Baggage Allowance
            </h4>
            <div className="space-y-2">
              <p className="text-sm"><span className="font-semibold">Checked:</span> {data.baggageAllowance.checkedBags} piece(s)</p>
              <p className="text-sm"><span className="font-semibold">Carry-on:</span> {data.baggageAllowance.carryOnBags} piece(s)</p>
            </div>
          </div>

          {/* Check-in */}
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-bold text-green-800 mb-3 flex items-center">
              <span className="mr-2">✅</span>Check-in Guidelines
            </h4>
            <div className="space-y-1 text-sm">
              <p>• Online: 24 hours before departure</p>
              <p>• Airport: 3 hours for international</p>
              <p>• Domestic: 2 hours before departure</p>
            </div>
          </div>
        </div>

        {/* Important Notes */}
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <h4 className="font-bold text-red-800 mb-3 flex items-center">
            <span className="mr-2">⚠️</span>Important Information
          </h4>
          <div className="text-sm text-red-700 space-y-1">
            <p>• Please ensure your travel documents are valid for at least 6 months from the date of travel</p>
            <p>• Check visa requirements for your destination country</p>
            <p>• Arrive at the airport at least 3 hours before international flights</p>
            <p>• Changes and cancellations may incur fees as per fare rules</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-300 text-center">
          <p className="text-sm text-gray-600">
            Thank you for choosing Rea Travels Agency. Have a safe and pleasant journey!
          </p>
          <p className="text-xs text-gray-500 mt-2">
            For support, contact us at support@reatravels.com | Generated on {new Date().toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default CompactItinerary;
