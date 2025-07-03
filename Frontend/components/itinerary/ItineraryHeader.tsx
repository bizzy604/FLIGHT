"use client"

import React from 'react';
import Image from 'next/image';
import { BookingInfo } from '@/utils/itinerary-data-transformer';

interface ItineraryHeaderProps {
  bookingInfo: BookingInfo;
  contactInfo: {
    email: string;
    phone: string;
  };
  passengerCount: number;
}

const ItineraryHeader: React.FC<ItineraryHeaderProps> = ({ 
  bookingInfo, 
  contactInfo, 
  passengerCount 
}) => {
  return (
    <div className="border-b-2 border-blue-600 bg-gradient-to-r from-blue-50 to-blue-100 p-6">
      <div className="flex items-center justify-between mb-6">
        {/* Agency Logo and Info */}
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 rounded-full overflow-hidden bg-white shadow-md flex items-center justify-center">
            <Image
              src="/logo1.png"
              alt="Rea Travels Agency Logo"
              width={56}
              height={56}
              className="object-contain"
              priority
            />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-blue-800">Rea Travels Agency</h1>
            <p className="text-sm text-blue-600">Your Trusted Travel Partner</p>
            <p className="text-xs text-gray-600">Licensed Travel Agency</p>
          </div>
        </div>

        {/* Issue Date */}
        <div className="text-right">
          <p className="text-sm text-gray-600">Issue Date</p>
          <p className="font-semibold text-gray-800">{bookingInfo.issueDateFormatted}</p>
        </div>
      </div>

      {/* Itinerary Title */}
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">OFFICIAL FLIGHT ITINERARY</h2>
        <div className="w-32 h-1 bg-blue-600 mx-auto"></div>
      </div>

      {/* Booking Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-white rounded-lg p-6 shadow-sm">
        <div className="text-center md:text-left">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Booking Reference
          </h3>
          <p className="text-xl font-bold text-blue-600">{bookingInfo.bookingReference}</p>
          <p className="text-xs text-gray-500">Order ID: {bookingInfo.orderId}</p>
        </div>

        <div className="text-center">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Passenger Count
          </h3>
          <p className="text-xl font-bold text-gray-800">{passengerCount}</p>
          <p className="text-xs text-gray-500">
            {passengerCount === 1 ? 'Passenger' : 'Passengers'}
          </p>
        </div>

        <div className="text-center md:text-right">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Status
          </h3>
          <div className="flex items-center justify-center md:justify-end">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
              Confirmed
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Booking Status: {bookingInfo.status}</p>
        </div>
      </div>

      {/* Contact Information */}
      <div className="mt-6 bg-blue-50 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-center">
            <span className="font-semibold text-gray-700 mr-2">Contact Email:</span>
            <span className="text-blue-600">{contactInfo.email}</span>
          </div>
          <div className="flex items-center">
            <span className="font-semibold text-gray-700 mr-2">Contact Phone:</span>
            <span className="text-blue-600">{contactInfo.phone}</span>
          </div>
        </div>
      </div>

      {/* Discount Information */}
      {bookingInfo.discountApplied && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-center">
            <span className="text-green-700 font-semibold">
              🎉 {bookingInfo.discountApplied.name} Applied - {bookingInfo.discountApplied.percentage}% Discount
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ItineraryHeader;
