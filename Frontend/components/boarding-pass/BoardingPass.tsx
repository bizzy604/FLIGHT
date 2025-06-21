import React, { useState, useEffect, useRef } from 'react';

import FlightHeader from './FlightHeader';
import RouteInfo from './RouteInfo';
import PassengerInfo from './PassengerInfo';
import ClassTags from './ClassTags';
import FlightDetails from './FlightDetails';
import SecurityInfo from './SecurityInfo';
import QRCode from './QRCode';
import ControlsPanel from './ControlsPanel';

export interface BoardingPassProps { // Added export keyword
  passengerName: string;
  flightNumber: string;
  departureCity: string;
  departureAirport: string;
  departureTime: string;
  departureDate?: string;
  arrivalCity: string;
  arrivalAirport: string;
  arrivalTime: string;
  arrivalDate?: string;
  seat: string;
  boardingTime: string;
  terminal: string;
  gate: string;
  confirmation: string;
  duration: string;
  classType: string;
  amenities: string[];
  isStatic?: boolean; // Added for conditional rendering of controls
}

type Airline = 'AeroLux Airlines' | 'SkyLink Express' | 'CloudJet Premium';

const BoardingPass: React.FC<BoardingPassProps> = ({
  passengerName,
  flightNumber,
  departureCity,
  departureAirport,
  departureTime,
  departureDate,
  arrivalCity,
  arrivalAirport,
  arrivalTime,
  arrivalDate,
  seat,
  boardingTime,
  terminal,
  gate,
  confirmation,
  duration,
  classType,
  amenities,
  isStatic // Added isStatic here
}) => {
  const [brightness, setBrightness] = useState(100);
  const [airline, setAirline] = useState<Airline>('AeroLux Airlines');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isInWallet, setIsInWallet] = useState(false);
  const [showAirlineMenu, setShowAirlineMenu] = useState(false);
  
  const airlineMenuRef = useRef<HTMLDivElement>(null);
  const [currentDate] = useState(() => {
    const date = new Date();
    return date.toLocaleDateString('en-US', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric' 
    }).toUpperCase();
  });
  
  // Close airline menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (airlineMenuRef.current && !airlineMenuRef.current.contains(event.target as Node)) {
        setShowAirlineMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const airlineThemes = {
    'AeroLux Airlines': 'from-blue-900 to-blue-700',
    'SkyLink Express': 'from-emerald-900 to-emerald-700',
    'CloudJet Premium': 'from-rose-900 to-rose-700'
  };

  const handleBrightnessChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBrightness(Number(e.target.value));
  };

  const handleAirlineSelect = (selectedAirline: Airline) => {
    setAirline(selectedAirline);
    setShowAirlineMenu(false);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: 'My Boarding Pass',
        text: 'Check out my digital boarding pass!',
        url: window.location.href
      }).catch(console.error);
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  const handleDownload = () => {
    const source = document.documentElement.outerHTML;
    const blob = new Blob([source], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'aerolux_boarding_pass.html';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      URL.revokeObjectURL(url);
      a.remove();
    }, 0);
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4 sm:p-6 flex flex-col items-center justify-center ${
      isDarkMode ? 'dark' : ''
    }`}>
      <div className="w-full max-w-sm sm:max-w-md lg:max-w-lg">
        {/* Boarding Pass */}
        <div 
          className={`ticket rounded-3xl text-white shadow-2xl overflow-hidden transform hover:scale-105 transition-all duration-300 bg-gradient-to-r ${airlineThemes[airline]}`}
          style={{ opacity: brightness / 100 }}
        >
          <div className="p-6 sm:p-8">
            <FlightHeader 
              airline={airline} 
              flightNumber={flightNumber} 
              date={currentDate}
            />
            
            <RouteInfo 
              departureCity={departureCity}
              departureAirport={departureAirport}
              departureTime={departureTime}
              departureDate={departureDate}
              arrivalCity={arrivalCity}
              arrivalAirport={arrivalAirport}
              arrivalTime={arrivalTime}
              arrivalDate={arrivalDate}
              duration={duration}
            />
            
            <PassengerInfo 
              name={passengerName}
              confirmation={confirmation}
            />
            
            <ClassTags 
              tags={[classType, ...amenities]} 
            />
            
            <FlightDetails 
              boardingTime={boardingTime}
              terminal={terminal}
              gate={gate}
              group={String(Math.floor(Math.random() * 5) + 1)} // Random group for demo
              seat={seat}
            />
            
            <div className="border-t-2 border-white/30 my-6"></div>
            
            <SecurityInfo hasTsaPreCheck={true} />
            
            <QRCode 
              data={`${airline}-${flightNumber}-${passengerName.toUpperCase().replace(/\s+/g, '-')}-${seat}`}
              alt="Boarding Pass QR Code"
              caption="Scan at security checkpoint and gate"
            />
          </div>
        </div>

        {!isStatic && <ControlsPanel 
          isDarkMode={isDarkMode}
          onDarkModeToggle={() => setIsDarkMode(!isDarkMode)}
          isInWallet={isInWallet}
          onWalletToggle={() => setIsInWallet(!isInWallet)}
          brightness={brightness}
          onBrightnessChange={handleBrightnessChange}
          airline={airline}
          onAirlineSelect={handleAirlineSelect}
          showAirlineMenu={showAirlineMenu}
          onToggleAirlineMenu={() => setShowAirlineMenu(!showAirlineMenu)}
          onShare={handleShare}
          onDownload={handleDownload}
          menuRef={airlineMenuRef}
        />}
      </div>
    </div>
  );
};

export default BoardingPass;
