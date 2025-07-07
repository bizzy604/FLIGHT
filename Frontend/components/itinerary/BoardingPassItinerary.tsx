'use client'

import React from 'react'
import Image from 'next/image'
import { ItineraryData, FlightSegment } from '@/utils/itinerary-data-transformer'

interface BoardingPassItineraryProps {
  data: ItineraryData
  className?: string
}

const BoardingPassItinerary: React.FC<BoardingPassItineraryProps> = React.memo(({ data, className = '' }) => {

  // Early return if no data
  if (!data) {
    console.warn('🎫 BoardingPassItinerary: No data provided');
    return (
      <div className="bg-white p-8 text-center rounded-lg border border-gray-200">
        <div className="text-gray-500">No itinerary data available</div>
      </div>
    );
  }

  // Validate required data structure
  if (!data.bookingInfo || !data.passengers || !data.outboundFlight) {
    console.error('🎫 BoardingPassItinerary: Invalid data structure', {
      hasBookingInfo: !!data.bookingInfo,
      hasPassengers: !!data.passengers,
      hasOutboundFlight: !!data.outboundFlight
    });
    return (
      <div className="bg-white p-8 text-center rounded-lg border border-red-200">
        <div className="text-red-500">Invalid itinerary data structure</div>
      </div>
    );
  }
  
  // Function to render connecting flights as one journey
  const renderConnectingFlightSegments = (segments: FlightSegment[], isReturn: boolean = false) => {
    if (!segments || segments.length === 0) return null;

    // For connecting flights, use the first segment's airline for the header
    const primarySegment = segments[0];
    const lastSegment = segments[segments.length - 1];

    return (
      <div className="boarding-pass-segment mb-3">
        {/* Main Boarding Pass Card */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
          {/* Header with Airline Branding */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Image
                  src={primarySegment.airlineLogo || `/airlines/${primarySegment.airlineCode}.svg`}
                  alt={primarySegment.airline}
                  width={32}
                  height={32}
                  className="rounded-full bg-white p-1"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/airlines/default.svg';
                  }}
                />
                <div>
                  <h3 className="font-bold text-lg">{primarySegment.airline}</h3>
                  <p className="text-xs opacity-90">
                    {isReturn ? 'RETURN JOURNEY' : 'OUTBOUND JOURNEY'}
                    {segments.length > 1 && ` • ${segments.length - 1} Stop${segments.length > 2 ? 's' : ''}`}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs opacity-90">Flight</div>
                <div className="font-bold text-lg">{primarySegment.flightNumber}</div>
                {segments.length > 1 && (
                  <div className="text-xs opacity-75">+ {segments.length - 1} more</div>
                )}
              </div>
            </div>
          </div>

          {/* Main Boarding Pass Content */}
          <div className="flex flex-col lg:flex-row">
            {/* Left Side - Flight Details */}
            <div className="flex-1 p-3 lg:p-4 bg-gradient-to-b from-blue-50 to-white">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4 mb-4">
                {/* From */}
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">From:</div>
                  <div className="text-lg sm:text-2xl font-bold text-blue-800">{primarySegment.departure.airport}</div>
                  <div className="text-xs text-gray-700">{primarySegment.departure.airportName}</div>
                  <div className="text-sm font-semibold mt-1">{primarySegment.departure.time}</div>
                  <div className="text-xs text-gray-600">{primarySegment.departure.date}</div>
                </div>

                {/* Route with Connections */}
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">Route:</div>
                  <div className="flex items-center justify-center space-x-1 text-sm">
                    <span className="font-bold text-blue-800">{primarySegment.departure.airport}</span>
                    {segments.map((seg, idx) => (
                      <React.Fragment key={idx}>
                        <span className="text-gray-400">→</span>
                        <span className="font-bold text-blue-800">{seg.arrival.airport}</span>
                      </React.Fragment>
                    ))}
                  </div>
                  {segments.length > 1 && (
                    <div className="text-xs text-orange-600 mt-1">
                      Via: {segments.slice(0, -1).map(seg => seg.arrival.airport).join(', ')}
                    </div>
                  )}
                </div>

                {/* To */}
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">To:</div>
                  <div className="text-lg sm:text-2xl font-bold text-blue-800">{lastSegment.arrival.airport}</div>
                  <div className="text-xs text-gray-700">{lastSegment.arrival.airportName}</div>
                  <div className="text-sm font-semibold mt-1">{lastSegment.arrival.time}</div>
                  <div className="text-xs text-gray-600">{lastSegment.arrival.date}</div>
                </div>
              </div>

              {/* Flight Segments Details */}
              <div className="space-y-2">
                {segments.map((segment, idx) => (
                  <div key={idx} className="bg-white rounded p-2 border border-gray-200">
                    <div className="flex justify-between items-center text-sm">
                      <div className="font-semibold">
                        {segment.flightNumber} • {segment.departure.airport} → {segment.arrival.airport}
                      </div>
                      <div className="text-gray-600">
                        {segment.departure.time} - {segment.arrival.time}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {segment.aircraft} • {segment.classOfService} • Duration: {segment.durationFormatted}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Side - Passenger Info */}
            <div className="w-full lg:w-80 p-3 lg:p-4 bg-gray-50 border-l border-gray-200">
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-gray-600 mb-1">Passenger Name:</div>
                  <div className="font-bold text-gray-800">{data.passengers[0]?.fullName || 'N/A'}</div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Flight:</div>
                    <div className="font-bold text-gray-800">{primarySegment.flightNumber}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Date:</div>
                    <div className="font-bold text-gray-800">{primarySegment.departure.date}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Time:</div>
                    <div className="font-bold text-gray-800">{primarySegment.departure.time}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 mb-1">Class:</div>
                    <div className="font-bold text-gray-800">{primarySegment.classOfService}</div>
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-600 mb-1">Status:</div>
                  <div className="font-bold text-green-600">CONFIRMED</div>
                </div>

                <div className="pt-2 border-t border-gray-300">
                  <div className="text-xs text-gray-600 mb-1">Booking Reference:</div>
                  <div className="font-bold text-gray-800">{data.bookingInfo.bookingReference || 'N/A'}</div>
                  <div className="mt-2">
                    <svg className="w-full h-8" viewBox="0 0 200 20">
                      <rect width="200" height="20" fill="black"/>
                      <g fill="white">
                        {Array.from({length: 50}, (_, i) => (
                          <rect key={i} x={i * 4} y={2} width={2} height={Math.random() * 16 + 2}/>
                        ))}
                      </g>
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderFlightSegment = (segment: FlightSegment, index: number, isReturn: boolean = false) => (
    <div key={index} className="boarding-pass-segment mb-3">
      {/* Main Boarding Pass Card */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
        {/* Header with Airline Branding */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Image
                src={segment.airlineLogo || `/airlines/${segment.airlineCode}.svg`}
                alt={segment.airline}
                width={32}
                height={32}
                className="rounded-full bg-white p-1"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/airlines/default.svg';
                }}
              />
              <div>
                <h3 className="font-bold text-lg">{segment.airline}</h3>
                <p className="text-xs opacity-90">{isReturn ? 'RETURN JOURNEY' : 'OUTBOUND JOURNEY'}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs opacity-90">Flight</div>
              <div className="font-bold text-lg">{segment.flightNumber}</div>
            </div>
          </div>
        </div>

        {/* Main Boarding Pass Content */}
        <div className="flex flex-col lg:flex-row">
          {/* Left Side - Flight Details */}
          <div className="flex-1 p-3 lg:p-4 bg-gradient-to-b from-blue-50 to-white">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4 mb-4">
              {/* From */}
              <div className="text-center">
                <div className="text-xs text-gray-600 mb-1">From:</div>
                <div className="text-lg sm:text-2xl font-bold text-blue-800">{segment.departure.airport}</div>
                <div className="text-xs text-gray-700">{segment.departure.airportName}</div>
                <div className="text-sm font-semibold mt-1">{segment.departure.time}</div>
                <div className="text-xs text-gray-600">{segment.departure.date}</div>
              </div>

              {/* Airplane Icon */}
              <div className="flex items-center justify-center sm:block hidden">
                <div className="text-blue-600">
                  <svg className="w-6 h-6 sm:w-8 sm:h-8" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
                  </svg>
                </div>
              </div>

              {/* To */}
              <div className="text-center">
                <div className="text-xs text-gray-600 mb-1">To:</div>
                <div className="text-lg sm:text-2xl font-bold text-blue-800">{segment.arrival.airport}</div>
                <div className="text-xs text-gray-700">{segment.arrival.airportName}</div>
                <div className="text-sm font-semibold mt-1">{segment.arrival.time}</div>
                <div className="text-xs text-gray-600">{segment.arrival.date}</div>
              </div>
            </div>

            {/* Flight Details Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 text-xs border-t border-gray-200 pt-3">
              <div>
                <span className="text-gray-600">Aircraft:</span>
                <div className="font-semibold">{segment.aircraft || segment.aircraftCode || 'N/A'}</div>
              </div>
              <div>
                <span className="text-gray-600">Duration:</span>
                <div className="font-semibold">{segment.durationFormatted || segment.duration || 'N/A'}</div>
              </div>
              <div>
                <span className="text-gray-600">Class:</span>
                <div className="font-semibold">{segment.classOfService || 'ECONOMY'}</div>
              </div>
              <div>
                <span className="text-gray-600">Status:</span>
                <div className="font-semibold text-green-600">CONFIRMED</div>
              </div>
            </div>
          </div>

          {/* Right Side - Boarding Pass Stub */}
          <div className="w-full lg:w-48 bg-gradient-to-b from-gray-50 to-gray-100 border-t-2 lg:border-t-0 lg:border-l-2 border-dashed border-gray-300 p-3 lg:p-4">
            <div className="text-center mb-4">
              <div className="text-xs text-gray-600 mb-1">Passenger Name:</div>
              <div className="font-bold text-sm">{data.passengers[0]?.fullName || 'PASSENGER'}</div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Flight:</span>
                <span className="font-bold">{segment.flightNumber}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Date:</span>
                <span className="font-bold">{segment.departure.date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Time:</span>
                <span className="font-bold">{segment.departure.time}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Class:</span>
                <span className="font-bold">{segment.classOfService || 'ECONOMY'}</span>
              </div>
            </div>

            {/* Barcode Area */}
            <div className="mt-4 pt-3 border-t border-gray-300">
              <div className="text-center mb-2">
                <div className="text-xs text-gray-600">Booking Reference</div>
                <div className="font-bold text-sm">{data.bookingInfo.bookingReference}</div>
              </div>
              {/* Simulated Barcode */}
              <div className="flex justify-center space-x-px">
                {Array.from({ length: 20 }, (_, i) => (
                  <div key={i} className={`w-1 ${i % 3 === 0 ? 'h-8' : i % 2 === 0 ? 'h-6' : 'h-4'} bg-black`}></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`bg-white text-black landscape-container ${className}`} id="boarding-pass-itinerary">
      {/* Agency Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-4 mb-4 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center">
              <Image
                src="/logo1.png"
                alt="Rea Travels Agency"
                width={48}
                height={48}
                className="object-contain"
              />
            </div>
            <div>
              <h1 className="text-2xl font-bold">REA TRAVELS AGENCY</h1>
              <p className="text-sm opacity-90">Official Flight Itinerary</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm opacity-90">Issue Date</div>
            <div className="font-bold text-lg">{data.bookingInfo.issueDateFormatted}</div>
          </div>
        </div>
      </div>

      {/* Booking Summary Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <h3 className="font-bold text-blue-800 mb-2">BOOKING DETAILS</h3>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Reference:</span>
              <span className="font-bold text-blue-600">{data.bookingInfo.bookingReference}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className="font-bold text-green-600">CONFIRMED</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Passengers:</span>
              <span className="font-bold">{data.passengers.length}</span>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
          <h3 className="font-bold text-green-800 mb-2">TOTAL FARE</h3>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{data.pricing.formattedTotal}</div>
            <div className="text-sm text-gray-600">{data.pricing.paymentMethodLabel}</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
          <h3 className="font-bold text-purple-800 mb-2">CONTACT INFO</h3>
          <div className="text-sm space-y-1">
            <div className="break-all">{data.contactInfo.email}</div>
            <div className="font-semibold">{data.contactInfo.phone}</div>
          </div>
        </div>
      </div>

      {/* Flight Segments */}
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-800 mb-3 flex items-center">
          <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm mr-3">✈️</span>
          Flight Details
        </h2>
        
        {/* Outbound Flight - Group connecting segments */}
        {data.outboundFlight && data.outboundFlight.length > 0 && renderConnectingFlightSegments(data.outboundFlight, false)}

        {/* Return Flight - Group connecting segments */}
        {data.returnFlight && data.returnFlight.length > 0 && renderConnectingFlightSegments(data.returnFlight, true)}
      </div>



      {/* Additional Information - Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-4 mb-4">
        {/* Baggage Information */}
        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
          <h3 className="font-bold text-yellow-800 mb-3 flex items-center">
            <span className="mr-2">🧳</span>
            BAGGAGE ALLOWANCE
          </h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white p-3 rounded border">
              <h4 className="font-semibold text-gray-700 mb-2">Checked Baggage</h4>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-600">Allowed Pieces:</span>
                  <span className="font-bold">{data.baggageAllowance?.checkedBags || 1}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Weight Limit:</span>
                  <span className="font-bold">23kg (50lbs)</span>
                </div>
                <div className="text-xs text-gray-600 mt-2">
                  Note: Checked bag Weight Allowance
                </div>
              </div>
            </div>
            <div className="bg-white p-3 rounded border">
              <h4 className="font-semibold text-gray-700 mb-2">Carry-On Baggage</h4>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-600">Allowed Pieces:</span>
                  <span className="font-bold">{data.baggageAllowance?.carryOnBags || 1}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Weight Limit:</span>
                  <span className="font-bold">7kg (15lbs)</span>
                </div>
                <div className="text-xs text-gray-600 mt-2">
                  Note: Carry-On Bag Allowance
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Important Information */}
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <h3 className="font-bold text-red-800 mb-3 flex items-center">
            <span className="mr-2">⚠️</span>
            IMPORTANT INFORMATION
          </h3>
          <div className="space-y-3 text-sm">
            <div className="bg-white p-3 rounded border">
              <h4 className="font-semibold text-gray-700 mb-2">Check-in Guidelines</h4>
              <ul className="text-xs space-y-1 text-gray-600">
                <li>• Online: 24 hours before departure</li>
                <li>• Airport: 3 hours for international flights</li>
                <li>• Domestic: 2 hours before departure</li>
              </ul>
            </div>
            <div className="bg-white p-3 rounded border">
              <h4 className="font-semibold text-gray-700 mb-2">Changes & Cancellation</h4>
              <ul className="text-xs space-y-1 text-gray-600">
                <li>• Contact Rea Travels Agency immediately</li>
                <li>• Changes subject to airline policies</li>
                <li>• Additional fees may apply</li>
                <li>• Some fares are non-changeable</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-lg p-4 text-center">
        <div className="mb-2">
          <h3 className="font-bold text-lg">REA TRAVELS AGENCY</h3>
          <div className="flex justify-center items-center space-x-4 text-sm">
            <span>📧 info@reatravels.com</span>
            <span>📞 +254 700 000 000</span>
            <span>🌐 www.reatravels.com</span>
          </div>
        </div>
        <div className="text-xs opacity-90 border-t border-blue-500 pt-2">
          This is an official flight itinerary. Please arrive at the airport at least 2-3 hours before departure.
          For changes or cancellations, contact us immediately. Terms and conditions apply.
        </div>
      </div>
    </div>
  );
});

BoardingPassItinerary.displayName = 'BoardingPassItinerary';

export default BoardingPassItinerary;
