import React from 'react';
import { Plane } from 'lucide-react';

type Airline = 'AeroLux Airlines' | 'SkyLink Express' | 'CloudJet Premium';

interface FlightHeaderProps {
  airline: Airline;
  flightNumber: string;
  date: string;
}

const FlightHeader: React.FC<FlightHeaderProps> = ({ airline, flightNumber, date }) => {
  return (
    <div className="flex items-center justify-between text-sm font-semibold tracking-wider">
      <div className="flex items-center gap-2">
        <Plane className="w-5 h-5" />
        <span className="text-base">{airline.split(' ')[0]}</span>
      </div>
      <div className="text-right">
        <div className="text-lg font-bold">{flightNumber}</div>
        <div className="text-xs opacity-90">{date}</div>
      </div>
    </div>
  );
};

export default FlightHeader;
