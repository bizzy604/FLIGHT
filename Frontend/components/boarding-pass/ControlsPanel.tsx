import React, { RefObject } from 'react';
import { Moon, Sun, Wallet, Download, Share2, ChevronDown, Plane, Zap, Star } from 'lucide-react';

type Airline = 'AeroLux Airlines' | 'SkyLink Express' | 'CloudJet Premium';

interface ControlsPanelProps {
  isDarkMode: boolean;
  onDarkModeToggle: () => void;
  isInWallet: boolean;
  onWalletToggle: () => void;
  brightness: number;
  onBrightnessChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  airline: Airline;
  onAirlineSelect: (airline: Airline) => void;
  showAirlineMenu: boolean;
  onToggleAirlineMenu: () => void;
  onShare: () => void;
  onDownload: () => void;
  menuRef: RefObject<HTMLDivElement>;
}

const ControlsPanel: React.FC<ControlsPanelProps> = ({
  isDarkMode,
  onDarkModeToggle,
  isInWallet,
  onWalletToggle,
  brightness,
  onBrightnessChange,
  airline,
  onAirlineSelect,
  showAirlineMenu,
  onToggleAirlineMenu,
  onShare,
  onDownload,
  menuRef
}) => {
  const airlines = [
    { name: 'AeroLux Airlines', icon: <Plane className="w-4 h-4 text-blue-600" /> },
    { name: 'SkyLink Express', icon: <Zap className="w-4 h-4 text-emerald-600" /> },
    { name: 'CloudJet Premium', icon: <Star className="w-4 h-4 text-rose-600" /> },
  ] as const;

  return (
    <div className="mt-8 space-y-6 bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-xl">
      <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-settings">
          <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
        Pass Settings
      </h3>

      {/* Dark Mode Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Moon className="w-4 h-4 text-slate-600" />
          <label htmlFor="toggle" className="text-sm font-semibold text-slate-700">Dark Theme</label>
        </div>
        <label className="relative inline-flex cursor-pointer">
          <input 
            id="toggle" 
            type="checkbox" 
            className="sr-only peer" 
            checked={isDarkMode}
            onChange={onDarkModeToggle}
          />
          <div className="w-12 h-6 bg-slate-300 rounded-full peer-checked:bg-blue-700 relative transition-colors duration-300">
            <span className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-md peer-checked:translate-x-6 transition-transform duration-300 flex items-center justify-center">
              {isDarkMode ? (
                <Moon className="w-3 h-3 text-slate-700" />
              ) : (
                <Sun className="w-3 h-3 text-yellow-500" />
              )}
            </span>
          </div>
        </label>
      </div>

      {/* Add to Wallet */}
      <div className="flex items-center gap-3">
        <label className="relative inline-flex cursor-pointer">
          <input 
            id="wallet" 
            type="checkbox" 
            className="sr-only peer" 
            checked={isInWallet}
            onChange={onWalletToggle}
          />
          <div className={`w-5 h-5 rounded-md border-2 ${
            isInWallet ? 'bg-blue-700 border-blue-700' : 'border-slate-400'
          } flex items-center justify-center transition-all duration-200`}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="12" 
              height="12" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className={`text-white transition-opacity duration-200 ${isInWallet ? 'opacity-100' : 'opacity-0'}`}
            >
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>
        </label>
        <div className="flex items-center gap-2">
          <Wallet className="w-4 h-4 text-slate-600" />
          <label htmlFor="wallet" className="text-sm font-semibold text-slate-700 cursor-pointer">
            Add to Apple Wallet
          </label>
        </div>
      </div>

      {/* Brightness Control */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Sun className="w-4 h-4 text-slate-600" />
          <label htmlFor="brightness" className="text-sm font-semibold text-slate-700">
            Brightness: <span className="text-blue-700">{brightness}</span>%
          </label>
        </div>
        <input 
          id="brightness" 
          type="range" 
          min="30" 
          max="100" 
          value={brightness} 
          onChange={onBrightnessChange}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Airline Selection */}
      <div className="relative" ref={menuRef}>
        <div className="flex items-center gap-2 mb-2">
          <Plane className="w-4 h-4 text-slate-600" />
          <label className="text-sm font-semibold text-slate-700">Select Airline</label>
        </div>
        <button 
          id="airlineBtn" 
          onClick={onToggleAirlineMenu}
          className="w-full bg-white border-2 border-slate-200 rounded-xl px-4 py-3 flex items-center justify-between text-sm font-semibold shadow-sm hover:border-blue-700 transition-colors duration-200"
        >
          <span id="selectedAirline">{airline}</span>
          <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${
            showAirlineMenu ? 'rotate-180' : ''
          }`} />
        </button>
        
        {showAirlineMenu && (
          <div className="absolute z-20 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden">
            <ul className="text-sm">
              {airlines.map((item) => (
                <li 
                  key={item.name}
                  className={`px-4 py-3 hover:bg-blue-50 cursor-pointer ${
                    airline === item.name ? 'bg-blue-50' : ''
                  } ${
                    item.name !== 'CloudJet Premium' ? 'border-b border-slate-100' : ''
                  }`}
                  onClick={() => onAirlineSelect(item.name as Airline)}
                >
                  <div className="flex items-center gap-2 font-medium">
                    {item.icon}
                    {item.name}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 pt-4">
        <button 
          onClick={onShare}
          className="flex items-center justify-center gap-2 bg-slate-700 text-white text-sm font-semibold py-3 rounded-xl shadow-lg hover:bg-slate-800 transition-all duration-200 transform hover:scale-105"
        >
          <Share2 className="w-4 h-4" />
          Share
        </button>
        <button 
          onClick={onDownload}
          className="flex items-center justify-center gap-2 bg-blue-700 text-white text-sm font-semibold py-3 rounded-xl shadow-lg hover:bg-blue-800 transition-all duration-200 transform hover:scale-105"
        >
          <Download className="w-4 h-4" />
          Download
        </button>
      </div>
    </div>
  );
};

export default ControlsPanel;
