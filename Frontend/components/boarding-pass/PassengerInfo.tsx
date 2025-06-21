import React from 'react';

interface PassengerInfoProps {
  name: string;
  confirmation: string;
}

const PassengerInfo: React.FC<PassengerInfoProps> = ({ name, confirmation }) => {
  return (
    <div className="mt-8">
      <div className="text-xl font-bold tracking-wide">{name}</div>
      <div className="text-sm opacity-90 mt-1">Confirmation: {confirmation}</div>
    </div>
  );
};

export default PassengerInfo;
