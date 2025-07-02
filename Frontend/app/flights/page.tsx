'use client'

import { Suspense, useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft, ChevronRight, Filter } from "lucide-react"
import { useSearchParams } from "next/navigation"
import { api } from "@/utils/api-client"
import type { FlightSearchRequest } from "@/utils/api-client"
import type { FlightOffer } from "@/types/flight-api"

import { Button } from "@/components/ui/button"
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
}

const initialFilters: FlightFiltersState = {
  priceRange: [0, 100000], // Increased to accommodate higher price ranges in real data
  airlines: [],
  stops: [],
  departureTime: []
}

// Component that uses useSearchParams - needs to be wrapped in Suspense
function SearchParamsWrapper() {
  const [flights, setFlights] = useState<FlightOffer[]>([])
  const [allFlights, setAllFlights] = useState<FlightOffer[]>([])
  const [filters, setFilters] = useState<FlightFiltersState>(initialFilters)
  const [loading, setLoading] = useState(true)
  const searchParams = useSearchParams()
  const [sortOption, setSortOption] = useState('price_low')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Extract search parameters outside useEffect so they're available in component scope
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departDate = searchParams.get('departDate') || ''
  const returnDate = searchParams.get('returnDate') || ''
  const adults = Number(searchParams.get('adults')) || 1
  const children = Number(searchParams.get('children')) || 0
  const infants = Number(searchParams.get('infants')) || 0
  const cabinClass = searchParams.get('cabinClass') || 'Y'
  const outboundCabinClass = searchParams.get('outboundCabinClass') || 'Y'
  const returnCabinClass = searchParams.get('returnCabinClass') || 'Y'
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
      console.log('No flights available to filter');
      return;
    }
    
    console.log('Current filters:', filters);
    console.log('Available flights:', allFlights.length);
    
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
      if (filters.airlines.length > 0 && !filters.airlines.includes(flight.airline.name)) {
        return false;
      }
      
      // Stops filter - only apply if stops are selected
      if (filters.stops.length > 0 && !filters.stops.includes(flight.stops)) {
        return false;
      }
      
      // Departure time filter (would need to parse the time and check against time ranges)
      
      return true;
    });
    
    console.log('Filtered flights:', filteredFlights.length);
    
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
    console.log('Setting paginated flights:', paginatedFlights.length, 'displayed out of', sortedFlights.length);
    setFlights(paginatedFlights);
  }, [allFlights, filters.priceRange, filters.airlines, filters.stops, filters.departureTime, sortOption, currentPage]);

  // Load flight data from API based on search parameters
  useEffect(() => {
    console.log('Loading flight data...');
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
    
    // Fetch flights from the API
    const fetchFlights = async () => {
      try {
        const response = await api.searchFlights(flightSearchParams);
        
        // Transform API response to match the expected flight format
        // Backend returns response.data with nested data structure
        const apiResponse = response.data;
        let apiFlights: any[] = [];
        
        // Debug: Log response structure (remove in production)
        console.log('API response received with', apiResponse?.data?.data?.offers?.length || 0, 'offers');
        
        // The actual structure is response.data.data.data.offers (triple nested)
        if (apiResponse && apiResponse.data && apiResponse.data.data && apiResponse.data.data.offers) {
          apiFlights = apiResponse.data.data.offers;
          console.log('Found offers in apiResponse.data.data.offers:', apiFlights.length);
        } else if (apiResponse && apiResponse.data && apiResponse.data.offers) {
          // Fallback: response.data.data.offers
          apiFlights = apiResponse.data.offers;
          console.log('Found offers in apiResponse.data.offers:', apiFlights.length);
        } else if (Array.isArray(apiResponse)) {
          // Fallback: response.data is directly an array
          apiFlights = apiResponse;
          console.log('Using apiResponse as direct array:', apiFlights.length);
        } else {
          console.log('No offers found. API response structure:', {
            hasData: !!apiResponse.data,
            dataKeys: apiResponse.data ? Object.keys(apiResponse.data) : [],
            isArray: Array.isArray(apiResponse)
          });
        }

        // Debug: Log the first flight object to see its structure
        if (apiFlights && apiFlights.length > 0) {
          console.log('[DEBUG] First flight object structure:', {
            id: apiFlights[0].id,
            keys: Object.keys(apiFlights[0]),
            hasId: !!apiFlights[0].id
          });
        }
        
        // console.log('Extracted flights:', apiFlights.length, 'offers');
        
        // Store complete flight data in localStorage for flight details page
        // This includes the complete airShoppingResponse needed for pricing API calls
        const flightDataForStorage = {
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
          expiresAt: Date.now() + (24 * 60 * 60 * 1000) // 24 hours expiration
        };
        
        // Create a unique storage key based on search parameters
        const storageKey = `flightData_${origin}_${destination}_${departDate}_${tripType}_${adults}_${children}_${infants}_${cabinClass}_${outboundCabinClass}_${returnCabinClass}`;
        
        try {
          // Before setting a new item, check current storage size and clear old items if near quota
          // This is a simplified approach; a more robust LRU cache would be better for production
          const MAX_STORAGE_ITEMS = 10; // Limit to 10 stored searches
          const flightDataKeys = Object.keys(localStorage).filter(key => key.startsWith('flightData_'));

          if (flightDataKeys.length >= MAX_STORAGE_ITEMS) {
            // Sort by timestamp (oldest first) if available, or just remove some
            // For simplicity, remove the first few if no timestamps are easily parsable from keys
            // A more robust solution would store timestamps with the data and sort by that
            const keysToRemove = flightDataKeys.slice(0, flightDataKeys.length - MAX_STORAGE_ITEMS + 1);
            keysToRemove.forEach(key => {
              localStorage.removeItem(key);
              console.log('Removed older flight data to make space:', key);
            });
          }

          localStorage.setItem(storageKey, JSON.stringify(flightDataForStorage));
          // Store the current storage key for easy retrieval
          localStorage.setItem('currentFlightDataKey', storageKey);
          console.log('Flight data stored in localStorage with key:', storageKey);
          
          // Clean up old flight data (older than 24 hours)
          const now = Date.now();
          Object.keys(localStorage).forEach(key => {
            if (key.startsWith('flightData_')) {
              try {
                const data = JSON.parse(localStorage.getItem(key) || '{}');
                if (data.expiresAt && data.expiresAt < now) {
                  localStorage.removeItem(key);
                  console.log('Removed expired flight data:', key);
                }
              } catch (e) {
                // Remove corrupted data
                localStorage.removeItem(key);
              }
            }
          });
        } catch (storageError) {
          console.warn('Failed to store flight data in localStorage:', storageError);
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
        
        setAllFlights(directFlights);
      } catch (error) {
        console.error('Error fetching flights:', error);
        // You might want to show an error message to the user
      } finally {
        setLoading(false);
      }
    };
    
    fetchFlights();

    // Create a unique search key
    const searchKey = `flightResults_${origin}_${destination}_${departDate}_${adults}_${children}_${infants}_${tripType === 'round-trip' ? `${outboundCabinClass}_${returnCabinClass}` : cabinClass}`;

    // Log search parameters
    // console.log('Search params:', { origin, destination, departDate, returnDate, adults, children, infants, cabinClass, outboundCabinClass, returnCabinClass, tripType });
    
    // Clear session storage to force API fetch
    sessionStorage.removeItem(searchKey);
    console.log('Cleared stored flights for debugging');
    

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
            <span className="text-lg sm:text-xl lg:text-2xl font-bold">Rea Travel</span>
          </div>
          <MainNav />
          <UserNav />
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
              <div className="sticky top-24 rounded-lg border p-4 lg:p-6 bg-white shadow-sm">
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
                    <div className="rounded-lg border p-6 sm:p-8 lg:p-12 text-center bg-white shadow-sm">
                      <h3 className="mb-2 sm:mb-4 text-lg sm:text-xl lg:text-2xl font-semibold">No flights found</h3>
                      <p className="text-sm sm:text-base text-muted-foreground">Try adjusting your search criteria</p>
                    </div>
                  )}
                </div>
              </Suspense>

              {/* Pagination */}
              <div className="flex items-center justify-center space-x-2 sm:space-x-3 py-6 sm:py-8">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 sm:h-10 sm:w-10"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                >
                  <ChevronLeft className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="sr-only">Previous page</span>
                </Button>
                
                {/* Generate page buttons */}
                {Array.from({ length: Math.min(3, Math.ceil(allFlights.length / itemsPerPage)) }, (_, i) => (
                  <Button
                    key={i}
                    variant={currentPage === i + 1 ? "default" : "outline"}
                    size="sm"
                    className="h-8 w-8 sm:h-9 sm:w-9 p-0 text-sm sm:text-base"
                    onClick={() => setCurrentPage(i + 1)}
                  >
                    {i + 1}
                  </Button>
                ))}
                
                {Math.ceil(allFlights.length / itemsPerPage) > 3 && (
                  <>
                    <span className="text-sm text-muted-foreground">...</span>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 w-8 sm:h-9 sm:w-9 p-0 text-sm sm:text-base"
                      onClick={() => setCurrentPage(Math.ceil(allFlights.length / itemsPerPage))}
                    >
                      {Math.ceil(allFlights.length / itemsPerPage)}
                    </Button>
                  </>
                )}
                
                <Button
                  variant="outline"
                  size="icon"
                  className="h-9 w-9 sm:h-10 sm:w-10"
                  disabled={currentPage >= Math.ceil(allFlights.length / itemsPerPage)}
                  onClick={() => setCurrentPage(prev => Math.min(Math.ceil(allFlights.length / itemsPerPage), prev + 1))}
                >
                  <ChevronRight className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="sr-only">Next page</span>
                </Button>
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
