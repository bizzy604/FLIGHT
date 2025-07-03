"use client"

import React from 'react';
import { PassengerInfo } from '@/utils/itinerary-data-transformer';

interface PassengerSectionProps {
  passengers: PassengerInfo[];
}

const PassengerSection: React.FC<PassengerSectionProps> = ({ passengers }) => {
  const formatDocumentExpiry = (expiryDate: string) => {
    try {
      const date = new Date(expiryDate);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return expiryDate;
    }
  };

  const formatBirthDate = (birthDate: string) => {
    try {
      const date = new Date(birthDate);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return birthDate;
    }
  };

  return (
    <div className="p-6 border-b border-gray-200">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
        <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
          👥
        </span>
        Passenger Information
      </h2>

      <div className="space-y-6">
        {passengers.map((passenger, index) => (
          <div key={passenger.objectKey} className="bg-gray-50 rounded-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <span className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                  {index + 1}
                </span>
                <div>
                  <h3 className="text-lg font-bold text-gray-800">{passenger.fullName}</h3>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {passenger.passengerTypeLabel}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-600">Ticket Number</p>
                <p className="text-lg font-bold text-blue-600">{passenger.ticketNumber}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Personal Information */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide border-b border-gray-300 pb-1">
                  Personal Details
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Date of Birth:</span>
                    <p className="text-gray-800">{formatBirthDate(passenger.birthDate)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Age:</span>
                    <p className="text-gray-800">{passenger.age} years</p>
                  </div>
                  {passenger.email && (
                    <div>
                      <span className="font-medium text-gray-600">Email:</span>
                      <p className="text-gray-800 break-all">{passenger.email}</p>
                    </div>
                  )}
                  {passenger.phone && (
                    <div>
                      <span className="font-medium text-gray-600">Phone:</span>
                      <p className="text-gray-800">{passenger.phone}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Document Information */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide border-b border-gray-300 pb-1">
                  Travel Document
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Document Type:</span>
                    <p className="text-gray-800">
                      {passenger.documentType === 'PT' ? 'Passport' : passenger.documentType}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Document Number:</span>
                    <p className="text-gray-800 font-mono">{passenger.documentNumber}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Expiry Date:</span>
                    <p className="text-gray-800">{formatDocumentExpiry(passenger.documentExpiry)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Issuing Country:</span>
                    <p className="text-gray-800">{passenger.countryOfIssuance}</p>
                  </div>
                  {passenger.countryOfResidence && (
                    <div>
                      <span className="font-medium text-gray-600">Residence:</span>
                      <p className="text-gray-800">{passenger.countryOfResidence}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Additional Information */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide border-b border-gray-300 pb-1">
                  Additional Info
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Passenger ID:</span>
                    <p className="text-gray-800 font-mono">{passenger.objectKey}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Passenger Type:</span>
                    <p className="text-gray-800">{passenger.passengerType}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Important Notice for Document Validity */}
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-xs text-yellow-800">
                <span className="font-semibold">⚠️ Important:</span> Please ensure your travel document is valid for at least 6 months from the date of travel and has sufficient blank pages for entry stamps.
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-6 bg-blue-50 rounded-lg p-4">
        <div className="flex items-center justify-between text-sm">
          <span className="font-semibold text-blue-800">
            Total Passengers: {passengers.length}
          </span>
          <div className="flex space-x-4">
            {['ADT', 'CHD', 'INF'].map(type => {
              const count = passengers.filter(p => p.passengerType === type).length;
              if (count > 0) {
                return (
                  <span key={type} className="text-blue-600">
                    {type}: {count}
                  </span>
                );
              }
              return null;
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PassengerSection;
