import React from 'react';
import { Clock, Building, MapPin, Users, Armchair } from 'lucide-react';

interface FlightDetailsProps {
  boardingTime: string;
  terminal: string;
  gate: string;
  group: string;
  seat: string;
}

const FlightDetails: React.FC<FlightDetailsProps> = ({
  boardingTime,
  terminal,
  gate,
  group,
  seat
}) => {
  const details = [
    { icon: <Clock className="w-3 h-3 opacity-80" />, label: 'BOARDING', value: boardingTime },
    { icon: <Building className="w-3 h-3 opacity-80" />, label: 'TERMINAL', value: terminal },
    { icon: <MapPin className="w-3 h-3 opacity-80" />, label: 'GATE', value: gate },
    { icon: <Users className="w-3 h-3 opacity-80" />, label: 'GROUP', value: group },
    { icon: <Armchair className="w-3 h-3 opacity-80" />, label: 'SEAT', value: seat },
  ];

  return (
    <div className="mt-8 grid grid-cols-5 gap-3 text-xs font-semibold tracking-wider">
      {details.map((detail, index) => (
        <div key={index} className="text-center">
          <div className="flex items-center justify-center mb-1">
            {detail.icon}
          </div>
          <span className="block opacity-80 text-xs">{detail.label}</span>
          <span className="text-lg font-black">{detail.value}</span>
        </div>
      ))}
    </div>
  );
};

export default FlightDetails;
