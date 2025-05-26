"use client";

import { createContext, useContext, useState, ReactNode } from 'react';
import { SearchFormData } from '../components/SearchForm';
import { Flight } from '../components/FlightResults';

type FlightBookingContextType = {
  searchCriteria: SearchFormData | null;
  setSearchCriteria: (criteria: SearchFormData) => void;
  searchResults: Flight[];
  setSearchResults: (results: Flight[]) => void;
  selectedFlight: Flight | null;
  setSelectedFlight: (flight: Flight | null) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
};

const FlightBookingContext = createContext<FlightBookingContextType | undefined>(undefined);

export const FlightBookingProvider = ({ children }: { children: ReactNode }) => {
  const [searchCriteria, setSearchCriteria] = useState<SearchFormData | null>(null);
  const [searchResults, setSearchResults] = useState<Flight[]>([]);
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <FlightBookingContext.Provider value={{
      searchCriteria,
      setSearchCriteria,
      searchResults,
      setSearchResults,
      selectedFlight,
      setSelectedFlight,
      isLoading,
      setIsLoading,
      error,
      setError,
    }}>
      {children}
    </FlightBookingContext.Provider>
  );
};

export const useFlightBooking = () => {
  const context = useContext(FlightBookingContext);
  if (context === undefined) {
    throw new Error('useFlightBooking must be used within a FlightBookingProvider');
  }
  return context;
};
