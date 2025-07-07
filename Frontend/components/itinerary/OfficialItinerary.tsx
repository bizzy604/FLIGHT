"use client"

import React from 'react';
import Image from 'next/image';
import { ItineraryData, FlightSegment } from '@/utils/itinerary-data-transformer';

interface OfficialItineraryProps {
  data: ItineraryData;
  className?: string;
}

const OfficialItinerary: React.FC<OfficialItineraryProps> = ({ data, className = '' }) => {
  // Safety check for data
  if (!data) {
    return (
      <div className="bg-white text-black p-8 text-center">
        <h2 className="text-xl font-bold text-red-600 mb-4">Error Loading Itinerary</h2>
        <p className="text-gray-600">Itinerary data is not available.</p>
      </div>
    );
  }

  const isCompactMode = className.includes('compact-mode');

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString || 'N/A';
    }
  };

  const formatTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    } catch {
      return dateString || 'N/A';
    }
  };

  const renderFlightSegment = (segment: FlightSegment, index: number) => (
    <div key={index} className={`border border-gray-200 rounded-lg ${isCompactMode ? 'p-2 mb-1' : 'p-3 mb-2'}`}>
      <div className={`grid grid-cols-4 gap-2 ${isCompactMode ? 'text-xs' : 'text-xs'}`}>
        <div className="flex items-center space-x-2">
          <div className="flex-shrink-0">
            <Image
              src={segment.airlineLogo || `/airlines/${segment.airlineCode}.svg`}
              alt={segment.airline}
              width={isCompactMode ? 20 : 24}
              height={isCompactMode ? 20 : 24}
              className="rounded-full object-contain"
              onError={(e) => {
                // Fallback to a default airline icon if logo fails to load
                (e.target as HTMLImageElement).src = '/airlines/default.svg';
              }}
            />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-semibold text-blue-600 truncate">
              {segment.airline}
            </div>
            <div className="text-gray-600">{segment.flightNumber}</div>
          </div>
        </div>
        <div>
          <div className="font-semibold">{segment.departure.airport}</div>
          <div className="text-gray-600">{segment.departure.time}</div>
          <div className="text-xs text-gray-500">{segment.departure.date}</div>
        </div>
        <div>
          <div className="font-semibold">{segment.arrival.airport}</div>
          <div className="text-gray-600">{segment.arrival.time}</div>
          <div className="text-xs text-gray-500">{segment.arrival.date}</div>
        </div>
        <div className="text-right">
          <div className="text-gray-600">{segment.cabinClass}</div>
          <div className="text-xs text-gray-500">{segment.duration}</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`bg-white text-black ${isCompactMode ? 'text-xs leading-tight' : 'text-sm leading-tight'} ${className}`} id="official-itinerary">
      {/* PAGE 1 */}
      <div className={isCompactMode ? 'min-h-[40vh]' : 'min-h-[50vh]'}>
        {/* Compact Header */}
        <div className={`bg-gradient-to-r from-blue-600 to-blue-700 text-white ${isCompactMode ? 'p-3 mb-3' : 'p-4 mb-4'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                <Image
                  src="/logo1.png"
                  alt="Rea Travels Agency"
                  width={40}
                  height={40}
                  className="object-contain"
                />
              </div>
              <div>
                <h1 className="text-xl font-bold">REA TRAVELS AGENCY</h1>
                <p className="text-xs opacity-90">Official Flight Itinerary</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs opacity-90">Issue Date</div>
              <div className="font-semibold">{data.bookingInfo.issueDateFormatted}</div>
            </div>
          </div>
        </div>

        {/* Booking & Passenger Info - Side by Side */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Booking Details */}
          <div className="border border-gray-200 rounded-lg p-3">
            <h3 className="font-bold text-gray-800 mb-2 text-sm">BOOKING DETAILS</h3>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Reference:</span>
                <span className="font-semibold text-blue-600">{data.bookingInfo.bookingReference}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Order ID:</span>
                <span className="font-mono text-xs">{data.bookingInfo.orderId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="font-semibold text-green-600">Confirmed</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Passengers:</span>
                <span className="font-semibold">{data.passengers.length}</span>
              </div>
            </div>
          </div>

          {/* Contact Info */}
          <div className="border border-gray-200 rounded-lg p-3">
            <h3 className="font-bold text-gray-800 mb-2 text-sm">CONTACT INFORMATION</h3>
            <div className="space-y-1 text-xs">
              <div>
                <span className="text-gray-600">Email:</span>
                <div className="font-semibold break-all">{data.contactInfo.email}</div>
              </div>
              <div>
                <span className="text-gray-600">Phone:</span>
                <div className="font-semibold">{data.contactInfo.phone}</div>
              </div>
              {data.bookingInfo.discountApplied && (
                <div className="bg-yellow-50 p-2 rounded mt-2">
                  <span className="text-yellow-700 text-xs">
                    🎉 {data.bookingInfo.discountApplied.name} - {data.bookingInfo.discountApplied.percentage}% Discount
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Passenger Information - Compact Table */}
        <div className="border border-gray-200 rounded-lg p-3 mb-4">
          <h3 className="font-bold text-gray-800 mb-2 text-sm">PASSENGER INFORMATION</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-1 px-2 font-semibold text-gray-700">Name</th>
                  <th className="text-left py-1 px-2 font-semibold text-gray-700">Type</th>
                  <th className="text-left py-1 px-2 font-semibold text-gray-700">Document</th>
                  <th className="text-left py-1 px-2 font-semibold text-gray-700">Ticket #</th>
                </tr>
              </thead>
              <tbody>
                {data.passengers.map((passenger, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-1 px-2 font-semibold">{passenger.fullName}</td>
                    <td className="py-1 px-2">{passenger.passengerTypeLabel}</td>
                    <td className="py-1 px-2 font-mono text-xs">{passenger.documentNumber}</td>
                    <td className="py-1 px-2 font-mono text-xs">{passenger.ticketNumber}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Flight Information */}
        <div className="border border-gray-200 rounded-lg p-3 mb-4">
          <h3 className="font-bold text-gray-800 mb-2 text-sm">FLIGHT DETAILS</h3>

          {/* Outbound Flight */}
          <div className="mb-3">
            <h4 className="font-semibold text-blue-600 mb-2 text-xs">🛫 OUTBOUND JOURNEY</h4>
            {data.outboundFlight.map((segment, index) => renderFlightSegment(segment, index))}
          </div>

          {/* Return Flight */}
          {data.returnFlight && (
            <div>
              <h4 className="font-semibold text-blue-600 mb-2 text-xs">RETURN JOURNEY</h4>
              {data.returnFlight.map((segment, index) => renderFlightSegment(segment, index))}
            </div>
          )}
        </div>

        {/* Pricing Summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <h3 className="font-bold text-blue-800 mb-2 text-sm">TOTAL FARE</h3>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-gray-600">Total Amount:</span>
              <div className="text-xl font-bold text-blue-600">{data.pricing.formattedTotal}</div>
            </div>
            <div>
              <span className="text-gray-600">Payment Method:</span>
              <div className="font-semibold">{data.pricing.paymentMethodLabel}</div>
            </div>
            <div>
              <span className="text-gray-600">Currency:</span>
              <div className="font-semibold">{data.pricing.currency}</div>
            </div>
          </div>
          <div className="mt-2 p-2 bg-yellow-50 rounded text-xs text-yellow-700">
            💡 Note: This amount includes all applicable taxes and fees. No additional charges will be applied at the airport for this booking.
          </div>
        </div>
      </div>

      {/* PAGE BREAK */}
      <div className="print-break"></div>

      {/* PAGE 2 */}
      <div className="min-h-[50vh]">
        {/* Baggage Information - Compact */}
        <div className="border border-gray-200 rounded-lg p-3 mb-4">
          <h3 className="font-bold text-gray-800 mb-2 text-sm">🧳 BAGGAGE ALLOWANCE</h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="bg-gray-50 p-2 rounded">
              <h4 className="font-semibold text-gray-700 mb-1">Checked Baggage</h4>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span>Allowed Pieces:</span>
                  <span className="font-semibold">{data.baggageAllowance.checkedBags}</span>
                </div>
                <div className="flex justify-between">
                  <span>Weight Limit:</span>
                  <span className="font-semibold">40 Kilogram</span>
                </div>
                <div className="text-xs text-blue-600">Note: Checked Bag Weight Allowance</div>
              </div>
            </div>
            <div className="bg-gray-50 p-2 rounded">
              <h4 className="font-semibold text-gray-700 mb-1">Carry-On Baggage</h4>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span>Allowed Pieces:</span>
                  <span className="font-semibold">{data.baggageAllowance.carryOnBags} pieces</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Allowance:</span>
                  <span className="font-semibold">2 pieces</span>
                </div>
                <div className="text-xs text-blue-600">Note: Carry On Bag Allowance</div>
              </div>
            </div>
          </div>
          <div className="mt-2 p-2 bg-yellow-50 rounded text-xs">
            <div className="font-semibold text-yellow-800 mb-1">📏 Size Limits:</div>
            <div className="text-yellow-700">
              Checked bags max 23kg (50lbs), Carry-on max 7kg (15lbs). Additional fees may apply for excess baggage.
            </div>
          </div>
        </div>

        {/* Fare Rules - Compact */}
        <div className="border border-gray-200 rounded-lg p-3 mb-4">
          <h3 className="font-bold text-gray-800 mb-2 text-sm">📋 FARE RULES</h3>
          {data.fareRules && data.fareRules.length > 0 ? (
            <div className="text-xs">
              {data.fareRules.map((passengerRules, index) => (
                <div key={index} className="mb-2">
                  <div className="font-semibold text-blue-600 mb-1">{passengerRules.passengerType}</div>
                  <div className="grid grid-cols-2 gap-2">
                    {passengerRules.rules.map((rule, ruleIndex) => (
                      <div key={ruleIndex} className="bg-gray-50 p-2 rounded">
                        <div className="font-semibold">{rule.type === 'Cancel' ? '❌' : '🔄'} {rule.type}</div>
                        <div className="text-gray-600">
                          {rule.allowed ? 'Allowed' : 'Not Allowed'} - {rule.minAmount} {rule.currency}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
              No specific fare rules available for this booking.
            </div>
          )}
        </div>

        {/* Important Information - Compact */}
        <div className="border border-gray-200 rounded-lg p-3 mb-4">
          <h3 className="font-bold text-gray-800 mb-2 text-sm">⚠️ IMPORTANT INFORMATION</h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <h4 className="font-semibold text-green-700 mb-1">✅ Check-in Guidelines</h4>
              <ul className="space-y-1 text-gray-700">
                <li>• Online: 24 hours before departure</li>
                <li>• Airport: 3 hours for international flights</li>
                <li>• Domestic: 2 hours before departure</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-yellow-700 mb-1">⚠️ Changes & Cancellation</h4>
              <ul className="space-y-1 text-gray-700">
                <li>• Contact Rea Travels Agency immediately</li>
                <li>• Changes subject to airline policies</li>
                <li>• Additional fees may apply</li>
                <li>• Some fares are non-changeable</li>
              </ul>
            </div>
          </div>

          <div className="mt-3 p-2 bg-red-50 rounded">
            <h4 className="font-semibold text-red-700 mb-1 text-xs">🚨 Emergency Contacts</h4>
            <div className="text-xs text-red-600">
              📞 Need Help? Contact Rea Travels Agency at +254 700 000 000 or email info@reatravels.com for any changes or assistance.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t-2 border-blue-600 bg-gradient-to-r from-blue-50 to-blue-100 p-3 rounded-lg">
          <div className="text-center">
            <h3 className="font-bold text-blue-800 text-sm">REA TRAVELS AGENCY</h3>
            <div className="text-xs text-blue-600 space-y-1">
              <p>📧 info@reatravels.com | 📞 +254 700 000 000 | 🌐 www.reatravels.com</p>
              <p className="text-xs text-gray-600 mt-2">
                This is an official flight itinerary. Please arrive at the airport at least 2-3 hours before departure.
                For changes or cancellations, contact us immediately. Terms and conditions apply.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OfficialItinerary;
