'use client'

import { Suspense, useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft, ChevronRight, Filter } from "lucide-react"
import { useSearchParams } from "next/navigation"
import { api } from "@/utils/api-client"
import type { FlightSearchRequest } from "@/utils/api-client"
import type { FlightOffer } from "@/types/flight-api"
import { flightStorageManager, FlightSearchData } from "@/utils/flight-storage-manager"
import { setupRobustStorage } from "@/utils/storage-integration-example"

import { Button, LoadingButton } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { FlightFilters } from "@/components/flight-filters"
import { EnhancedFlightCard } from "@/components/enhanced-flight-card"
import { FlightSortOptions } from "@/components/flight-sort-options"
import { FlightSearchSummary } from "@/components/flight-search-summary"

// Define interfaces for flight data types
interface StopDetail {
  airport: string
  city: string
  duration: string
}

// Helper function to safely get airport display name
function getAirportDisplay(airport: string, airportName?: string): string {
  return airportName || airport || 'Unknown';
}

// This interface matches the FlightCard component's expectations
interface Flight {
  id: string
  airline: {
    name: string
    logo: string
    code: string
    flightNumber: string
  }
  departure: {
    airport: string
    datetime: string
    terminal?: string
    airportName?: string
  }
  arrival: {
    airport: string
    datetime: string
    terminal?: string
    airportName?: string
  }
  duration: string
  stops: number
  stopDetails: string[]
  price: number
  currency: string
  baggage: any // Using any for now to match FlightOffer structure
}

// This interface matches the API response format
interface ApiFlightResponse {
  id: string
  airline: {
    name: string
    logo: string
    code: string
    flightNumber: string
  }
  departure: {
    airport: string
    datetime: string
    time: string
    terminal?: string
    airportName?: string
  }
  arrival: {
    airport: string
    datetime: string
    time: string
    terminal?: string
    airportName?: string
  }
  duration: string
  stops: number
  stopDetails?: string[]
  price: number
}

interface FlightFiltersState {
  priceRange: [number, number]
  airlines: string[]
  stops: number[]
  departureTime: string[]
  airports: string[]
}

const initialFilters: FlightFiltersState = {
  priceRange: [0, 100000], // Increased to accommodate higher price ranges in real data
  airlines: [],
  stops: [],
  departureTime: [],
  airports: []
}

// Component that uses useSearchParams - needs to be wrapped in Suspense
function SearchParamsWrapper() {
  const [flights, setFlights] = useState<FlightOffer[]>([])
  const [allFlights, setAllFlights] = useState<FlightOffer[]>([])
  const [availableAirlines, setAvailableAirlines] = useState<{id: string, name: string}[]>([])
  const [availableAirports, setAvailableAirports] = useState<{id: string, name: string, city?: string}[]>([])
  const [filters, setFilters] = useState<FlightFiltersState>(initialFilters)
  const [loading, setLoading] = useState(true)
  const searchParams = useSearchParams()
  const [sortOption, setSortOption] = useState('price_low')
  const [currentPage, setCurrentPage] = useState(1)
  const [isChangingPage, setIsChangingPage] = useState(false)
  const itemsPerPage = 10

  const handlePageChange = async (newPage: number) => {
    setIsChangingPage(true)
    try {
      // Add a small delay to show loading state
      await new Promise(resolve => setTimeout(resolve, 300))
      setCurrentPage(newPage)
    } finally {
      setIsChangingPage(false)
    }
  }

  // Extract search parameters outside useEffect so they're available in component scope
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departDate = searchParams.get('departDate') || ''
  const returnDate = searchParams.get('returnDate') || ''
  const adults = Number(searchParams.get('adults')) || 1
  const children = Number(searchParams.get('children')) || 0
  const infants = Number(searchParams.get('infants')) || 0
  const cabinClass = searchParams.get('cabinClass') || 'ECONOMY'
  const outboundCabinClass = searchParams.get('outboundCabinClass') || 'ECONOMY'
  const returnCabinClass = searchParams.get('returnCabinClass') || 'ECONOMY'
  const tripType = searchParams.get('tripType') || 'one-way'

  const handleFilterChange = (newFilters: Partial<FlightFiltersState>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters
    }))
  }

  function handleResetFilters() {
    setFilters(initialFilters)
  }
  
  // Apply filters and pagination to flight data
  useEffect(() => {
    if (allFlights.length === 0) {
      return;
    }

    // First apply filters
    const filteredFlights = allFlights.filter(flight => {
      // Only apply price filter if it's been explicitly set (not the default values)
      const usingDefaultPriceRange = 
        filters.priceRange[0] === initialFilters.priceRange[0] && 
        filters.priceRange[1] === initialFilters.priceRange[1];
      
      if (!usingDefaultPriceRange && 
          (flight.price < filters.priceRange[0] || flight.price > filters.priceRange[1])) {
        return false;
      }
      
      // Airlines filter - only apply if airlines are selected
      if (filters.airlines.length > 0 && flight.airline && flight.airline.name && !filters.airlines.includes(flight.airline.name)) {
        return false;
      }
      
      // Stops filter - only apply if stops are selected
      if (filters.stops.length > 0 && !filters.stops.includes(flight.stops)) {
        return false;
      }

      // Airports filter - only apply if airports are selected
      if (filters.airports.length > 0) {
        const arrivalAirport = flight.arrival?.airport;
        if (!arrivalAirport || !filters.airports.includes(arrivalAirport)) {
          return false;
        }
      }

      // Departure time filter (would need to parse the time and check against time ranges)

      return true;
    });
    

    
    // Apply sorting
    const sortedFlights = [...filteredFlights].sort((a, b) => {
      if (sortOption === 'price_low') {
        return a.price - b.price;
      } else if (sortOption === 'price_high') {
        return b.price - a.price;
      } else if (sortOption === 'duration_short') {
        // Would need to parse duration for proper comparison
        return a.duration.localeCompare(b.duration);
      }
      return 0;
    });
    
    // Calculate pagination offsets
    const startIdx = (currentPage - 1) * itemsPerPage;
    const endIdx = startIdx + itemsPerPage;
    
    // Set the paginated flights
    const paginatedFlights = sortedFlights.slice(startIdx, endIdx);
    setFlights(paginatedFlights);
  }, [allFlights, filters.priceRange, filters.airlines, filters.stops, filters.departureTime, filters.airports, sortOption, currentPage]);

  // Load flight data from API based on search parameters
  useEffect(() => {
    // Setup robust storage on component mount
    setupRobustStorage();

    // Reset pagination when loading new data
    setCurrentPage(1);
    setLoading(true);

    // Clear old data
    setAllFlights([]);

    // Search parameters are now extracted at component level

    // Validate required parameters
    if (!origin || !destination || !departDate) {
      setLoading(false);
      return;
    }
    
    // Convert trip type to backend format
    const convertTripType = (type: string): 'ONE_WAY' | 'ROUND_TRIP' | 'MULTI_CITY' => {
      switch (type.toLowerCase()) {
        case 'round-trip':
        case 'roundtrip':
          return 'ROUND_TRIP';
        case 'multi-city':
        case 'multicity':
          return 'MULTI_CITY';
        case 'one-way':
        case 'oneway':
        default:
          return 'ONE_WAY';
      }
    };

    // Prepare search parameters for the API
    const flightSearchParams: FlightSearchRequest = {
      tripType: convertTripType(tripType),
      odSegments: [{
        origin,
        destination,
        departureDate: departDate,
        ...(tripType === 'round-trip' && returnDate ? { returnDate } : {})
      }],
      numAdults: adults,
      numChildren: children,
      numInfants: infants,
      // Use separate cabin classes for round trips, single cabin class for others
      ...(tripType === 'round-trip' ? {
        outboundCabinClass,
        returnCabinClass,
        enableRoundtrip: true
      } : {
        cabinPreference: cabinClass,
        enableRoundtrip: false
      }),
      directOnly: false
    };
    
    // Create a unique storage key based on search parameters
    const storageKey = `flightData_${origin}_${destination}_${departDate}_${tripType}_${adults}_${children}_${infants}_${cabinClass}_${outboundCabinClass}_${returnCabinClass}`;

    // Check for cached data using robust storage manager
    const checkCachedData = async () => {
      try {
        console.log('🔍 Checking for cached flight data with robust storage...');
        const result = await flightStorageManager.getFlightSearch();

        if (result.success && result.data) {
          const cachedData = result.data;
          const cachedParams = cachedData.searchParams;

          console.log('🔍 Comparing search parameters:');
          console.log('Current:', { origin, destination, departDate, tripType, adults, children, infants });
          console.log('Cached:', cachedParams);

          if (cachedParams &&
              cachedParams.origin === origin &&
              cachedParams.destination === destination &&
              cachedParams.departDate === departDate &&
              cachedParams.tripType === tripType &&
              cachedParams.passengers?.adults === adults &&
              cachedParams.passengers?.children === children &&
              cachedParams.passengers?.infants === infants) {

            console.log('✅ Using cached flight data from robust storage');
            if (result.recovered) {
              console.log('🔄 Data was recovered from backup storage');
            }
            console.log('📊 Cached data structure:', cachedData);
            console.log('📊 Air shopping response:', cachedData.airShoppingResponse);

            // Extract flights from cached data
            const cachedFlights = cachedData.airShoppingResponse?.offers || [];
            console.log('✈️ Cached flights count:', cachedFlights.length);
            const directFlights = cachedFlights.map((offer: any) => ({
              id: offer.id,
              offer_index: offer.offer_index,
              original_offer_id: offer.original_offer_id,
              airline: offer.airline,
              departure: offer.departure,
              arrival: offer.arrival,
              duration: offer.duration,
              stops: offer.stops,
              stopDetails: offer.stopDetails || [],
              price: offer.price,
              currency: offer.currency,
              baggage: offer.baggage,
              fare: offer.fare,
              aircraft: offer.aircraft,
              segments: offer.segments,
              priceBreakdown: offer.priceBreakdown,
              additionalServices: offer.additionalServices,
              fareRules: offer.fareRules,
              penalties: offer.penalties,
              time_limits: offer.time_limits || {}
            }));

            // Extract unique airlines
            const uniqueAirlines = new Map<string, {id: string, name: string}>();
            directFlights.forEach(flight => {
              if (flight.airline && flight.airline.code && flight.airline.name) {
                uniqueAirlines.set(flight.airline.code, {
                  id: flight.airline.code,
                  name: flight.airline.name
                });
              }
            });
            const airlineOptions = Array.from(uniqueAirlines.values()).sort((a, b) => a.name.localeCompare(b.name));

            // Extract unique arrival airports
            const uniqueAirports = new Map<string, {id: string, name: string, city?: string}>();
            directFlights.forEach(flight => {
              if (flight.arrival && flight.arrival.airport) {
                const airportCode = flight.arrival.airport;
                const airportName = flight.arrival.airportName || airportCode;

                const displayName = flight.arrival.airportName
                  ? `${airportCode} - ${flight.arrival.airportName}`
                  : airportCode;

                uniqueAirports.set(airportCode, {
                  id: airportCode,
                  name: displayName
                });
              }
            });
            const airportOptions = Array.from(uniqueAirports.values()).sort((a, b) => a.id.localeCompare(b.id));

            setAvailableAirlines(airlineOptions);
            setAvailableAirports(airportOptions);
            setAllFlights(directFlights);
            setLoading(false);
            return true; // Data found and loaded
          }
        } else {
          console.log('❌ No valid cached flight data found:', result.error);
        }
      } catch (error) {
        console.warn('Error checking cached data:', error);
      }
      return false; // No valid cached data found
    };

    // Try to load cached data first (async)
    const loadData = async () => {
      const hasCachedData = await checkCachedData();
      console.log('🔍 Cache check result:', hasCachedData);

      // Only fetch from API if no valid cached data exists
      if (!hasCachedData) {
      console.log('🔄 No cached data found, fetching from API');

      // Fetch flights from the API
      const fetchFlights = async () => {
        try {
          const response = await api.searchFlights(flightSearchParams);
        
        // Transform API response to match the expected flight format
        // Backend returns response.data with nested data structure
        const apiResponse = response.data;
        let apiFlights: any[] = [];

        // The actual structure is response.data.data.offers
        if (apiResponse && apiResponse.data && apiResponse.data.offers) {
          apiFlights = apiResponse.data.offers;
        } else if (Array.isArray(apiResponse)) {
          // Fallback: response.data is directly an array
          apiFlights = apiResponse;
        }
        
        // Clear ALL previous flight data before storing new search results
        // This prevents conflicts with old search data
        console.log('🧹 Clearing all previous flight data before storing new search...');
        Object.keys(localStorage).forEach(key => {
          if (key.startsWith('flightData_') || key.startsWith('flight_') || key === 'currentFlightDataKey' || key === 'currentFlightKey' || key === 'returnFlightKey') {
            localStorage.removeItem(key);
            console.log(`🧹 Cleared previous data: ${key}`);
          }
        });

        // Store complete flight data using robust storage manager
        const flightSearchData: FlightSearchData = {
          airShoppingResponse: apiResponse.data, // Backend response data (contains status, data with offers and raw_response)
          searchParams: {
            origin,
            destination,
            departDate,
            returnDate,
            tripType,
            passengers: {
              adults,
              children,
              infants
            },
            cabinClass,
            outboundCabinClass,
            returnCabinClass
          },
          timestamp: Date.now(),
          expiresAt: Date.now() + (30 * 60 * 1000) // 30 minutes expiration
        };

        // Store flight data using robust storage manager
        try {
          const storeResult = await flightStorageManager.storeFlightSearch(flightSearchData);

          if (storeResult.success) {
            console.log('✅ Flight data stored successfully with robust storage manager');
          } else {
            console.warn('⚠️ Failed to store flight data:', storeResult.error);
          }
        } catch (storageError) {
          console.warn('Failed to store flight data:', storageError);
          // Continue execution even if storage fails
        }
        
        // Use backend-provided FlightOffer data directly
        const directFlights = apiFlights.map((offer: any) => ({
          id: offer.id, // This is now the index (string)
          offer_index: offer.offer_index, // Explicit index property
          original_offer_id: offer.original_offer_id, // Store original OfferID for reference
          airline: offer.airline,
          departure: offer.departure,
          arrival: offer.arrival,
          duration: offer.duration,
          stops: offer.stops,
          stopDetails: offer.stopDetails || [],
          price: offer.price,
          currency: offer.currency,
          baggage: offer.baggage,
          fare: offer.fare,
          aircraft: offer.aircraft,
          segments: offer.segments,
          priceBreakdown: offer.priceBreakdown,
          additionalServices: offer.additionalServices,
          fareRules: offer.fareRules,
          penalties: offer.penalties,
          time_limits: offer.time_limits || {} // Include offer expiration information
        }));

        // Extract unique airlines from the real flight data
        const uniqueAirlines = new Map<string, {id: string, name: string}>();
        directFlights.forEach(flight => {
          if (flight.airline && flight.airline.code && flight.airline.name) {
            uniqueAirlines.set(flight.airline.code, {
              id: flight.airline.code,
              name: flight.airline.name
            });
          }
        });

        // Convert to array and sort by name
        const airlineOptions = Array.from(uniqueAirlines.values()).sort((a, b) => a.name.localeCompare(b.name));

        // Extract unique arrival airports from the real flight data
        const uniqueAirports = new Map<string, {id: string, name: string, city?: string}>();
        directFlights.forEach(flight => {
          if (flight.arrival && flight.arrival.airport) {
            const airportCode = flight.arrival.airport;
            const airportName = flight.arrival.airportName || airportCode;

            // Create a display name that includes both code and name if available
            const displayName = flight.arrival.airportName
              ? `${airportCode} - ${flight.arrival.airportName}`
              : airportCode;

            uniqueAirports.set(airportCode, {
              id: airportCode,
              name: displayName
            });
          }
        });

        // Convert to array and sort by airport code
        const airportOptions = Array.from(uniqueAirports.values()).sort((a, b) => a.id.localeCompare(b.id));

        setAvailableAirlines(airlineOptions);
        setAvailableAirports(airportOptions);
        setAllFlights(directFlights);
      } catch (error) {
        console.error('Error fetching flights:', error);
        // You might want to show an error message to the user
      } finally {
        setLoading(false);
      }
    };

        fetchFlights();
      } // Close the conditional block for !hasCachedData
    };

    // Call the async function
    loadData();

  }, [searchParams]);

  // Note: Removed convertApiResponseToFlights function as we now use backend-transformed data directly

  // Note: Data transformation is now handled by the backend
  // Frontend components should use FlightOffer data directly

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 sm:gap-3">
            <Image
              src="/logo1.png"
              alt="Rea Travel Logo"
              width={32}
              height={32}
              className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12"
            />
            <span className="text-sm sm:text-base md:text-lg font-semibold">Rea Travel</span>
          </div>
          <div className="flex items-center gap-4">
            <MainNav />
            <UserNav />
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="container py-4 sm:py-6 lg:py-8 px-3 sm:px-6 lg:px-8">
          <div className="mb-4 sm:mb-6">
            <Link
              href="/"
              className="inline-flex items-center text-sm sm:text-base font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronLeft className="mr-1 h-4 w-4 sm:h-5 sm:w-5" />
              Back to Home
            </Link>

            <Suspense fallback={<Skeleton className="h-8 w-full max-w-md" />}>
              <FlightSearchSummary
                origin={`${getAirportDisplay(searchParams.get('origin') || 'JFK')} (${searchParams.get('origin') || 'JFK'})`}
                destination={`${getAirportDisplay(searchParams.get('destination') || 'CDG')} (${searchParams.get('destination') || 'CDG'})`}
                departDate={searchParams.get('departDate') ?? '2025-04-20'}
                returnDate={searchParams.get('returnDate') || undefined}
                adults={Number(searchParams.get('adults')) || 1}
                children={Number(searchParams.get('children')) || 0}
                infants={Number(searchParams.get('infants')) || 0}
              />
            </Suspense>
          </div>

          <div className="grid gap-4 sm:gap-6 lg:gap-8 lg:grid-cols-[300px_1fr] xl:grid-cols-[320px_1fr]">
            {/* Filters Sidebar */}
            <div className="hidden lg:block">
              <div className="sticky top-24 rounded-lg border p-4 lg:p-6 bg-card shadow-sm">
                <div className="mb-4 lg:mb-6 flex items-center justify-between">
                  <h2 className="text-lg lg:text-xl font-semibold">Filters</h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 lg:h-9 px-2 lg:px-3 text-xs lg:text-sm"
                    onClick={handleResetFilters}
                  >
                    Reset All
                  </Button>
                </div>
                <Suspense
                  fallback={
                    <div className="space-y-4">
                      <Skeleton className="h-8 w-full" />
                      <Skeleton className="h-24 w-full" />
                      <Skeleton className="h-32 w-full" />
                    </div>
                  }
                >
                  <FlightFilters
                    priceRange={filters.priceRange}
                    onPriceRangeChange={(range) => handleFilterChange({ priceRange: range })}
                    airlines={filters.airlines}
                    onAirlinesChange={(airlines) => handleFilterChange({ airlines })}
                    availableAirlines={availableAirlines}
                    airports={filters.airports}
                    onAirportsChange={(airports) => handleFilterChange({ airports })}
                    availableAirports={availableAirports}
                    stops={filters.stops}
                    onStopsChange={(stops) => handleFilterChange({ stops })}
                    departureTime={filters.departureTime}
                    onDepartureTimeChange={(departureTime) => handleFilterChange({ departureTime })}
                    onResetFilters={handleResetFilters}
                  />
                </Suspense>
              </div>
            </div>

            {/* Mobile Filters Button */}
            <div className="flex items-center justify-between gap-3 lg:hidden mb-4 sm:mb-6">
              <Button variant="outline" size="sm" className="h-10 sm:h-11 px-3 sm:px-4 text-sm sm:text-base">
                <Filter className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                Filters
              </Button>
              <FlightSortOptions />
            </div>

            {/* Results */}
            <div className="space-y-4 sm:space-y-6">
              <div className="hidden items-center justify-between lg:flex">
                <p className="text-sm lg:text-base text-muted-foreground">
                  Showing <strong>{flights.length}</strong> of <strong>{allFlights.length}</strong> flights
                </p>
                <FlightSortOptions />
              </div>

              <Suspense
                fallback={
                  <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                      <Skeleton key={i} className="h-48 w-full rounded-lg" />
                    ))}
                  </div>
                }
              >
                <div className="space-y-3 sm:space-y-4 lg:space-y-6">
                  {loading ? (
                    <div className="space-y-3 sm:space-y-4 lg:space-y-6">
                      {[...Array(3)].map((_, i) => (
                        <Skeleton key={i} className="h-40 sm:h-48 lg:h-56 w-full rounded-lg" />
                      ))}
                    </div>
                  ) : flights.length > 0 ? (
                    flights.map((flight) => (
                      <EnhancedFlightCard
                        key={flight.id}
                        flight={flight}
                        searchParams={{
                          adults,
                          children,
                          infants,
                          tripType,
                          origin,
                          destination,
                          departDate,
                          returnDate,
                          cabinClass
                        }}
                      />
                    ))
                  ) : (
                    <div className="rounded-lg border p-6 sm:p-8 lg:p-12 text-center bg-card shadow-sm">
                      <h3 className="mb-2 sm:mb-4 text-lg sm:text-xl lg:text-2xl font-semibold">No flights found</h3>
                      <p className="text-sm sm:text-base text-muted-foreground">Try adjusting your search criteria</p>
                    </div>
                  )}
                </div>
              </Suspense>

              {/* Pagination */}
              <div className="flex items-center justify-center space-x-2 sm:space-x-3 py-6 sm:py-8">
                <LoadingButton
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 sm:h-10 sm:w-10"
                  disabled={currentPage === 1}
                  loading={isChangingPage}
                  onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                >
                  <ChevronLeft className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="sr-only">Previous page</span>
                </LoadingButton>
                
                {/* Generate page buttons */}
                {Array.from({ length: Math.min(3, Math.ceil(allFlights.length / itemsPerPage)) }, (_, i) => (
                  <LoadingButton
                    key={i}
                    variant={currentPage === i + 1 ? "default" : "outline"}
                    size="sm"
                    className="h-8 w-8 sm:h-9 sm:w-9 p-0 text-sm sm:text-base"
                    loading={isChangingPage && currentPage !== i + 1}
                    onClick={() => handlePageChange(i + 1)}
                  >
                    {i + 1}
                  </LoadingButton>
                ))}
                
                {Math.ceil(allFlights.length / itemsPerPage) > 3 && (
                  <>
                    <span className="text-sm text-muted-foreground">...</span>
                    <LoadingButton
                      variant="outline"
                      size="sm"
                      className="h-8 w-8 sm:h-9 sm:w-9 p-0 text-sm sm:text-base"
                      loading={isChangingPage}
                      onClick={() => handlePageChange(Math.ceil(allFlights.length / itemsPerPage))}
                    >
                      {Math.ceil(allFlights.length / itemsPerPage)}
                    </LoadingButton>
                  </>
                )}
                
                <LoadingButton
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 sm:h-10 sm:w-10"
                  disabled={currentPage >= Math.ceil(allFlights.length / itemsPerPage)}
                  loading={isChangingPage}
                  onClick={() => handlePageChange(Math.min(Math.ceil(allFlights.length / itemsPerPage), currentPage + 1))}
                >
                  <ChevronRight className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="sr-only">Next page</span>
                </LoadingButton>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

// Main component that wraps SearchParamsWrapper in Suspense
export default function FlightsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50">
        <div className="border-b">
          <div className="flex h-16 items-center px-4">
            <MainNav className="mx-6" />
            <div className="ml-auto flex items-center space-x-4">
              <UserNav />
            </div>
          </div>
        </div>
        <main className="container mx-auto px-4 py-8">
          <div className="space-y-6">
            <Skeleton className="h-8 w-64" />
            <div className="grid gap-6 lg:grid-cols-4">
              <div className="lg:col-span-1">
                <Skeleton className="h-96 w-full" />
              </div>
              <div className="lg:col-span-3">
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-32 w-full" />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    }>
      <SearchParamsWrapper />
    </Suspense>
  )
}
