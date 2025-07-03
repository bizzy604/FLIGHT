"use client"

import React from 'react';
import { ItineraryData } from '@/utils/itinerary-data-transformer';
import ItineraryHeader from './ItineraryHeader';
import PassengerSection from './PassengerSection';
import FlightSection from './FlightSection';
import ImportantInfo from './ImportantInfo';
import BaggageSection from './BaggageSection';
import FareRulesSection from './FareRulesSection';

interface OfficialItineraryProps {
  data: ItineraryData;
  className?: string;
}

const OfficialItinerary: React.FC<OfficialItineraryProps> = ({ data, className = '' }) => {
  return (
    <div className={`bg-white text-black min-h-screen ${className}`} id="official-itinerary">
      {/* Header Section */}
      <ItineraryHeader 
        bookingInfo={data.bookingInfo}
        contactInfo={data.contactInfo}
        passengerCount={data.passengers.length}
      />

      {/* Passenger Information Section */}
      <PassengerSection passengers={data.passengers} />

      {/* Flight Information Section */}
      <FlightSection
        outboundFlight={data.outboundFlight}
        returnFlight={data.returnFlight}
        pricing={data.pricing}
      />

      {/* Baggage Information Section */}
      <BaggageSection baggageAllowance={data.baggageAllowance} />

      {/* Fare Rules Section */}
      <FareRulesSection fareRules={data.fareRules} />

      {/* Important Information Section */}
      <ImportantInfo
        baggageAllowance={data.baggageAllowance}
        bookingInfo={data.bookingInfo}
      />

      {/* Footer */}
      <div className="border-t border-gray-300 p-6 bg-gray-50">
        <div className="text-center space-y-2">
          <h3 className="font-bold text-lg text-gray-800">Rea Travels Agency</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p>📧 Email: info@reatravels.com | 📞 Phone: +254 700 000 000</p>
            <p>🌐 Website: www.reatravels.com</p>
            <p className="text-xs text-gray-500 mt-4">
              This is an official flight itinerary. Please arrive at the airport at least 2 hours before domestic flights and 3 hours before international flights.
            </p>
            <p className="text-xs text-gray-500">
              For any changes or cancellations, please contact us immediately. Terms and conditions apply.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OfficialItinerary;
