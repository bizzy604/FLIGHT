"use client"

import React from 'react';
import { BookingInfo } from '@/utils/itinerary-data-transformer';

interface ImportantInfoProps {
  baggageAllowance: {
    checkedBags: number;
    carryOnBags: number;
  };
  bookingInfo: BookingInfo;
}

const ImportantInfo: React.FC<ImportantInfoProps> = ({ 
  baggageAllowance, 
  bookingInfo 
}) => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
        <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
          ℹ️
        </span>
        Important Information
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Baggage Information */}
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h3 className="text-lg font-bold text-blue-800 mb-4 flex items-center">
            <span className="text-xl mr-2">🧳</span>
            Baggage Allowance
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-700">Checked Baggage:</span>
              <span className="font-bold text-blue-600">{baggageAllowance.checkedBags} piece(s)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-700">Carry-on Baggage:</span>
              <span className="font-bold text-blue-600">{baggageAllowance.carryOnBags} piece(s)</span>
            </div>
            <div className="mt-4 p-3 bg-white rounded-md border border-blue-200">
              <p className="text-xs text-blue-800">
                <span className="font-semibold">📏 Size Limits:</span> Checked bags max 23kg (50lbs), 
                Carry-on max 7kg (15lbs). Additional fees may apply for excess baggage.
              </p>
            </div>
          </div>
        </div>

        {/* Check-in Information */}
        <div className="bg-green-50 rounded-lg p-6 border border-green-200">
          <h3 className="text-lg font-bold text-green-800 mb-4 flex items-center">
            <span className="text-xl mr-2">✅</span>
            Check-in Guidelines
          </h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-start">
              <span className="font-medium text-gray-700 mr-2">Online:</span>
              <span className="text-gray-800">24 hours before departure</span>
            </div>
            <div className="flex items-start">
              <span className="font-medium text-gray-700 mr-2">Airport:</span>
              <span className="text-gray-800">3 hours for international flights</span>
            </div>
            <div className="flex items-start">
              <span className="font-medium text-gray-700 mr-2">Domestic:</span>
              <span className="text-gray-800">2 hours before departure</span>
            </div>
            <div className="mt-4 p-3 bg-white rounded-md border border-green-200">
              <p className="text-xs text-green-800">
                <span className="font-semibold">💡 Tip:</span> Complete online check-in to save time at the airport. 
                Mobile boarding passes are accepted.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Travel Requirements */}
      <div className="mt-6 bg-yellow-50 rounded-lg p-6 border border-yellow-200">
        <h3 className="text-lg font-bold text-yellow-800 mb-4 flex items-center">
          <span className="text-xl mr-2">📋</span>
          Travel Requirements & Important Notes
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">
              Documentation
            </h4>
            <ul className="text-sm text-gray-800 space-y-1">
              <li>• Valid passport required (6+ months validity)</li>
              <li>• Visa requirements vary by destination</li>
              <li>• COVID-19 requirements may apply</li>
              <li>• Travel insurance recommended</li>
            </ul>
          </div>
          <div className="space-y-3">
            <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">
              At the Airport
            </h4>
            <ul className="text-sm text-gray-800 space-y-1">
              <li>• Arrive early for security screening</li>
              <li>• Keep documents easily accessible</li>
              <li>• Check gate information regularly</li>
              <li>• Follow airline baggage policies</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Booking Changes & Cancellation */}
      <div className="mt-6 bg-red-50 rounded-lg p-6 border border-red-200">
        <h3 className="text-lg font-bold text-red-800 mb-4 flex items-center">
          <span className="text-xl mr-2">⚠️</span>
          Changes & Cancellation Policy
        </h3>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Making Changes</h4>
              <ul className="text-sm text-gray-800 space-y-1">
                <li>• Contact Rea Travels Agency immediately</li>
                <li>• Changes subject to airline policies</li>
                <li>• Additional fees may apply</li>
                <li>• Some fares are non-changeable</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">Cancellation</h4>
              <ul className="text-sm text-gray-800 space-y-1">
                <li>• 24-hour free cancellation may apply</li>
                <li>• Refund policies vary by fare type</li>
                <li>• Processing fees may be charged</li>
                <li>• Contact us for assistance</li>
              </ul>
            </div>
          </div>
          <div className="mt-4 p-3 bg-white rounded-md border border-red-200">
            <p className="text-sm text-red-800">
              <span className="font-semibold">📞 Need Help?</span> Contact Rea Travels Agency at +254 700 000 000 
              or email info@reatravels.com for any changes or assistance.
            </p>
          </div>
        </div>
      </div>

      {/* Emergency Contacts */}
      <div className="mt-6 bg-gray-50 rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
          <span className="text-xl mr-2">🆘</span>
          Emergency Contacts
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <h4 className="font-semibold text-gray-700 mb-2">Rea Travels Agency</h4>
            <p className="text-gray-800">+254 700 000 000</p>
            <p className="text-gray-600">24/7 Support</p>
          </div>
          <div className="text-center">
            <h4 className="font-semibold text-gray-700 mb-2">Airline Customer Service</h4>
            <p className="text-gray-800">Check airline website</p>
            <p className="text-gray-600">For flight updates</p>
          </div>
          <div className="text-center">
            <h4 className="font-semibold text-gray-700 mb-2">Travel Insurance</h4>
            <p className="text-gray-800">Policy Number</p>
            <p className="text-gray-600">If applicable</p>
          </div>
        </div>
      </div>

      {/* Terms and Conditions */}
      <div className="mt-6 p-4 bg-gray-100 rounded-lg border border-gray-300">
        <h4 className="font-semibold text-gray-700 mb-2 text-sm">Terms and Conditions</h4>
        <p className="text-xs text-gray-600 leading-relaxed">
          This itinerary is subject to the terms and conditions of the airline and Rea Travels Agency. 
          Passengers are responsible for ensuring they have valid travel documents and meet all entry requirements 
          for their destination. Flight schedules are subject to change by the airline. Rea Travels Agency is not 
          responsible for delays, cancellations, or changes made by the airline. Travel insurance is strongly recommended. 
          By traveling, passengers agree to comply with all airline policies and regulations.
        </p>
      </div>
    </div>
  );
};

export default ImportantInfo;
