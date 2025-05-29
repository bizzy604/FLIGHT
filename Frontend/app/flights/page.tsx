'use client'

import { Suspense, useState, useEffect, useCallback } from "react"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft, ChevronRight, Filter } from "lucide-react"
import { useSearchParams } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { FlightFilters } from "@/components/flight-filters"
import { EnhancedFlightCard } from "@/components/enhanced-flight-card"
import { FlightCard } from "@/components/flight-card"
import { FlightSortOptions } from "@/components/flight-sort-options"
import { FlightSearchSummary } from "@/components/flight-search-summary"

// Define interfaces for flight data types
interface StopDetail {
  airport: string
  city: string
  duration: string
}

// Helper functions for formatting display data
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function getAirportCity(code: string): string {
  const airports = {
    'JFK': 'New York',
    'LAX': 'Los Angeles',
    'CDG': 'Paris',
    'LHR': 'London',
    'HND': 'Tokyo',
    'DXB': 'Dubai',
    'SYD': 'Sydney',
    'YYZ': 'Toronto',
    'YUL': 'Montreal',
    'MUC': 'Munich',
    'FRA': 'Frankfurt',
    'ZRH': 'Zurich'
  };
  return airports[code as keyof typeof airports] || code;
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
    city: string
    time: string
    date: string
  }
  arrival: {
    airport: string
    city: string
    time: string
    date: string
  }
  duration: string
  stops: number
  stopDetails?: StopDetail[]
  price: number
  seatsAvailable: number
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
    city: string
    time: string
    date: string
  }
  arrival: {
    airport: string
    city: string
    time: string
    date: string
  }
  duration: string
  stops: number
  stopDetails?: string[]
  price: number
  seatsAvailable: number
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

export default function FlightsPage() {
  // State management
  const [flights, setFlights] = useState<Flight[]>([])
  const [allFlights, setAllFlights] = useState<Flight[]>([])
  const [filteredFlights, setFilteredFlights] = useState<Flight[]>([])
  const [filters, setFilters] = useState<FlightFiltersState>(initialFilters)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [sortOption, setSortOption] = useState<string>('price_low')
  const [currentPage, setCurrentPage] = useState<number>(1)
  const itemsPerPage = 10
  
  // Get search parameters from URL
  const searchParams = useSearchParams()
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departDate = searchParams.get('departDate') || ''
  const returnDate = searchParams.get('returnDate') || ''
  const passengers = searchParams.get('passengers') || '1'
  const cabinClass = searchParams.get('cabinClass') || 'Y'
  
  // Memoized function to handle filter changes
  const handleFilterChange = useCallback((newFilters: Partial<FlightFiltersState>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters
    }))
  }, [])

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

  // Load flight data from sessionStorage or API
  useEffect(() => {
    console.log('Loading flight data...');
    // Reset pagination when loading new data
    setCurrentPage(1);
    setLoading(true);
    
    // Maximum number of retry attempts for failed API calls
    const MAX_RETRIES = 2;
    const RETRY_DELAY = 1000; // 1 second delay between retries

    // Function to fetch flight data with retry logic
    const fetchWithRetry = async (url: string, options: RequestInit, retries = MAX_RETRIES): Promise<Response> => {
      try {
        const response = await fetch(url, options);
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.message || `Request failed with status ${response.status}`);
        }
        return response;
      } catch (error) {
        if (retries <= 0) throw error;
        console.log(`Retrying... ${retries} attempts left`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        return fetchWithRetry(url, options, retries - 1);
      }
    };

    // Fetch flight data when search params change
    async function fetchFlightData() {
      // Validation function
      const validateSearchParams = () => {
        if (!origin || !destination || !departDate) {
          setError('Please fill in all required fields (origin, destination, and departure date)');
          return false;
        }
        
        // Validate date format (YYYY-MM-DD)
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateRegex.test(departDate) || (returnDate && !dateRegex.test(returnDate))) {
          setError('Invalid date format. Please use YYYY-MM-DD');
          return false;
        }
        
        // Validate passenger count
        const passengerCount = Number(passengers);
        if (isNaN(passengerCount) || passengerCount < 1 || passengerCount > 9) {
          setError('Number of passengers must be between 1 and 9');
          return false;
        }
        
        return true;
      };

      if (!validateSearchParams()) {
        setLoading(false);
        return;
      }
      
      // Create a unique search key
      const searchKey = `flightResults_${origin}_${destination}_${departDate}_${passengers}_${cabinClass}`;

      // Log search parameters
      console.log('Search params:', { origin, destination, departDate, returnDate, passengers, cabinClass });
      
      try {
        setLoading(true);
        setError(null);
        
        // Prepare request payload for Flask backend
        const payload = {
          origin: origin,
          destination: destination,
          departDate: departDate,
          returnDate: returnDate || undefined,
          passengers: Number(passengers) || 1,
          cabinClass: cabinClass || 'Y',
        };
        
        console.log('Fetching flights from Flask backend with payload:', payload);
        
        // Use fetchWithRetry for the API call
        const response = await fetchWithRetry('http://localhost:5000/api/flights/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Add any required authentication headers here
          },
          body: JSON.stringify(payload),
          cache: 'no-store'
        });
        
        const data = await response.json();
        console.log('Received response from Flask backend:', data);
        
        // Transform the response to match our Flight interface
        const flights = Array.isArray(data) ? data : data.flights || [];
        
        if (!flights.length) {
          setError('No flights found for the selected criteria. Please try different dates or routes.');
          setAllFlights([]);
          setFilteredFlights([]);
          return;
        }
        
        const processedFlights = flights.map((flight: any) => ({
          id: flight.id || `flight-${Math.random().toString(36).substr(2, 9)}`,
          airline: {
            name: flight.airline?.name || 'Unknown Airline',
            logo: flight.airline?.logo || '/placeholder-airline.png',
            code: flight.airline?.code || '--',
            flightNumber: flight.airline?.flightNumber || '--'
          },
          departure: {
            airport: flight.departure?.airport || origin,
            city: flight.departure?.city || getAirportCity(origin),
            time: flight.departure?.time || '--:--',
            date: flight.departure?.date || ''
          },
          arrival: {
            airport: flight.arrival?.airport || destination,
            city: flight.arrival?.city || getAirportCity(destination),
            time: flight.arrival?.time || '--:--',
            date: flight.arrival?.date || ''
          },
          duration: flight.duration || '--',
          stops: flight.stops || 0,
          stopDetails: flight.stopDetails || [],
          price: flight.price || 0,
          seatsAvailable: flight.seatsAvailable || 0
        }));
        
        console.log(`Processed ${processedFlights.length} flights`);
        setAllFlights(processedFlights);
        setFilteredFlights(processedFlights);
      } catch (error) {
        console.error('Error fetching flight data:', error);
        setError(`Failed to load flights: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`);
        setAllFlights([]);
        setFilteredFlights([]);
      } finally {
        setLoading(false);
      }
    }
    
    // Clear any existing flights and fetch new ones
    setAllFlights([]);
    setFilteredFlights([]);
    fetchFlightData();
    
    // Cleanup function
    return () => {
      // Any cleanup if needed
    };
  }, [origin, destination, departDate, returnDate, passengers, cabinClass]);

  // Convert API response to Flight interface
  function convertApiResponseToFlights(apiFlights: any[], origin: string, destination: string): Flight[] {
    if (!apiFlights || !Array.isArray(apiFlights)) {
      console.error('Invalid flights data:', apiFlights);
      return [];
    }
    
    return apiFlights.map(flight => {
      // Handle the time format from the API
      const extractTime = (dateTimeStr: string) => {
        if (!dateTimeStr) return '--:--';
        
        try {
          // Handle the specific format "2025-04-23T00:00:00.000T13:30"
          if (dateTimeStr.includes('.000T')) {
            return dateTimeStr.split('T')[2]?.substring(0, 5) || '--:--';
          }
          
          // Handle standard ISO format "2025-04-23T13:30:00"
          if (dateTimeStr.includes('T')) {
            return dateTimeStr.split('T')[1]?.substring(0, 5) || '--:--';
          }
          
          // If we get here, return the original string or a default value
          return dateTimeStr;
        } catch (error) {
          console.error('Error parsing date:', dateTimeStr, error);
          return '--:--';
        }
      };
      
      // Extract required fields or provide defaults
      const departureTime = extractTime(flight.departure.datetime);
      const arrivalTime = extractTime(flight.arrival.datetime);
      
      // Extract date parts
      const departureDate = flight.departure.datetime.split('T')[0] || '';
      const arrivalDate = flight.arrival.datetime.split('T')[0] || '';
      
      // Create stopDetails in the format expected by Flight interface
      const stopDetails = flight.stops > 0 && flight.stopDetails ? flight.stopDetails.map((stop: string) => {
        return {
          airport: stop,
          city: getAirportCity(stop),
          duration: "2h 0m" // Default duration as it's not in the API response
        };
      }) : [];
      
      return {
        id: flight.id,
        airline: {
          name: flight.airline.name,
          logo: flight.airline.logo || `/airlines/${flight.airline.code.toLowerCase()}.png`,
          code: flight.airline.code,
          flightNumber: flight.airline.flightNumber
        },
        departure: {
          airport: flight.departure.airport,
          city: (flight.departure.airportName ? flight.departure.airportName.split(',')[0] : getAirportCity(flight.departure.airport)),
          time: departureTime,
          date: departureDate
        },
        arrival: {
          airport: flight.arrival.airport,
          city: (flight.arrival.airportName ? flight.arrival.airportName.split(',')[0] : getAirportCity(flight.arrival.airport)),
          time: arrivalTime,
          date: arrivalDate
        },
        duration: flight.duration,
        stops: flight.stops,
        stopDetails: stopDetails,
        price: flight.price,
        seatsAvailable: typeof flight.seatsAvailable === 'string' ? 
          parseInt(flight.seatsAvailable.replace(/\D/g, '')) || 5 : 
          flight.seatsAvailable
      };
    });
  }

  // Helper function to convert Flight data to FlightOffer format
  function convertToFlightOffer(flight: Flight): any {
    // Generate a fare class based on price range
    const getFareClass = (price: number) => {
      if (price > 80000) return "First";
      if (price > 50000) return "Business";
      if (price > 30000) return "Premium Economy";
      return "Economy";
    };
    
    // Generate price breakdown
    const baseFare = Math.round(flight.price * 0.75);
    const taxes = Math.round(flight.price * 0.15);
    const fees = Math.round(flight.price * 0.1);
    
    const fareClass = getFareClass(flight.price);

    return {
      id: flight.id,
      airline: flight.airline,
      departure: {
        airport: flight.departure.airport,
        datetime: `${flight.departure.date.split('T')[0]}T${flight.departure.time}:00`,
        airportName: flight.departure.city,
      },
      arrival: {
        airport: flight.arrival.airport,
        datetime: `${flight.arrival.date.split('T')[0]}T${flight.arrival.time}:00`,
        airportName: flight.arrival.city,
      },
      duration: flight.duration,
      stops: flight.stops,
      stopDetails: flight.stopDetails ? flight.stopDetails.map(stop => stop.airport) : [],
      price: flight.price,
      currency: "USD",
      seatsAvailable: flight.seatsAvailable,
      
      // Enhanced fare information
      fare: {
        fareBasisCode: `${flight.airline.code}${fareClass.substring(0, 1)}${Math.floor(Math.random() * 100)}`,
        fareClass: fareClass,
        fareName: `${fareClass} ${flight.price > 30000 ? "Flex" : "Standard"}`,
        fareFamily: flight.price > 50000 ? "Premium" : "Standard",
        rules: {
          refundable: flight.price > 40000,
          changeFee: flight.price <= 40000,
          changeBeforeDeparture: {
            allowed: true,
            fee: flight.price > 40000 ? 0 : 15000,
            currency: "USD"
          },
          changeAfterDeparture: {
            allowed: flight.price > 30000,
            fee: flight.price > 50000 ? 0 : 25000,
            currency: "USD"
          },
          cancelBeforeDeparture: {
            allowed: true,
            fee: flight.price > 50000 ? 0 : 20000,
            currency: "USD"
          }
        }
      },
      
      // Enhanced baggage information
      baggage: {
        carryOn: {
          description: "1 carry-on bag included",
          quantity: 1,
          weight: {
            value: 7,
            unit: "kg"
          },
          dimensions: "56 x 36 x 23 cm",
          personalItem: {
            description: "1 personal item (small bag)",
            dimensions: "40 x 30 x 15 cm",
            weight: {
              value: 2,
              unit: "kg"
            }
          }
        },
        checkedBaggage: {
          description: `${fareClass === "Economy" ? "Not included" : "Included"} checked baggage allowance`,
          pieces: fareClass === "Economy" ? 0 : (fareClass === "Premium Economy" ? 1 : 2),
          weight: {
            value: 23,
            unit: "kg"
          },
          dimensions: "158 cm (length + width + height)",
          policyType: "PIECE_BASED",
          additionalBaggagePrices: [
            {
              amount: 5000,
              currency: "USD"
            }
          ],
          prepaidDiscount: {
            percentage: 20,
            description: "Save 20% when adding bags during booking"
          }
        }
      },
      
      // Enhanced price breakdown
      priceBreakdown: {
        baseFare,
        taxes,
        fees,
        totalPrice: flight.price,
        currency: "USD",
        taxBreakdown: [
          { code: "YQ", description: "Fuel Surcharge", amount: Math.round(taxes * 0.6) },
          { code: "XF", description: "Passenger Facility Charge", amount: Math.round(taxes * 0.2) },
          { code: "AY", description: "Security Fee", amount: Math.round(taxes * 0.2) }
        ],
        feeBreakdown: [
          { code: "OT", description: "Service Fee", amount: Math.round(fees * 0.8) },
          { code: "XA", description: "Airport Fee", amount: Math.round(fees * 0.2) }
        ]
      },
      
      // Additional services
      additionalServices: {
        wifiAvailable: true,
        powerOutlets: true,
        entertainmentSystem: flight.price > 30000,
        meals: {
          available: true,
          complimentary: flight.price > 30000,
          description: flight.price > 50000 ? "Premium multi-course meals" : "Standard meals",
          options: flight.price > 50000 ? ["Western", "Asian", "Vegetarian", "Religious"] : ["Standard", "Vegetarian"]
        },
        seatSelection: {
          available: true,
          complimentary: flight.price > 40000,
          cost: 1000,
          currency: "USD",
          description: flight.price > 40000 ? "Complimentary seat selection" : "Seat selection available for purchase"
        },
        priorityBoarding: {
          available: true,
          complimentary: flight.price > 50000,
          cost: 1500,
          currency: "USD"
        }
      },
      
      // Aircraft information
      aircraft: {
        code: flight.airline.code === "LH" ? "32Q" : (flight.airline.code === "AC" ? "789" : "77W"),
        name: flight.airline.code === "LH" ? "Airbus A321neo" : (flight.airline.code === "AC" ? "Boeing 787-9" : "Boeing 777-300ER")
      }
    };
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/logo1.png" alt="Rea Travel Logo" width={32} height={32} />
            <span className="text-xl font-bold">Rea Travel</span>
          </div>
          <MainNav />
          <UserNav />
        </div>
      </header>

      <main className="flex-1">
        <div className="container py-6">
          <div className="mb-6">
            <Link
              href="/"
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Home
            </Link>

            <Suspense fallback={<Skeleton className="h-8 w-full max-w-md" />}>
              <FlightSearchSummary
                origin={`${getAirportCity(searchParams.get('origin') || 'JFK')} (${searchParams.get('origin') || 'JFK'})`}
                destination={`${getAirportCity(searchParams.get('destination') || 'CDG')} (${searchParams.get('destination') || 'CDG'})`}
                departDate={formatDate(searchParams.get('departDate') ?? '2025-04-20')}
                returnDate={searchParams.get('returnDate') ? formatDate(searchParams.get('returnDate') ?? '') : undefined}
                passengers={Number(searchParams.get('passengers')) || 1}
              />
            </Suspense>
          </div>

          <div className="grid gap-6 md:grid-cols-[280px_1fr]">
            {/* Filters Sidebar */}
            <div className="hidden md:block">
              <div className="sticky top-24 rounded-lg border p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-semibold">Filters</h2>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-8 px-2 text-xs"
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
            <div className="flex items-center justify-between md:hidden">
              <Button variant="outline" size="sm" className="mb-4">
                <Filter className="mr-2 h-4 w-4" />
                Filters
              </Button>
              <FlightSortOptions />
            </div>

            {/* Results */}
            <div className="space-y-4">
              <div className="hidden items-center justify-between md:flex">
                <p className="text-sm text-muted-foreground">
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
                <div className="space-y-4">
                  {loading ? (
                    <div className="space-y-4">
                      {[...Array(3)].map((_, i) => (
                        <Skeleton key={i} className="h-48 w-full rounded-lg" />
                      ))}
                    </div>
                  ) : flights.length > 0 ? (
                    flights.map((flight) => (
                      <EnhancedFlightCard key={flight.id} flight={convertToFlightOffer(flight)} />
                    ))
                  ) : (
                    <div className="rounded-lg border p-8 text-center">
                      <h3 className="mb-2 text-lg font-semibold">No flights found</h3>
                      <p className="text-sm text-muted-foreground">Try adjusting your search criteria</p>
                    </div>
                  )}
                </div>
              </Suspense>

              {/* Pagination */}
              <div className="flex items-center justify-center space-x-2 py-4">
                <Button 
                  variant="outline" 
                  size="icon" 
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span className="sr-only">Previous page</span>
                </Button>
                
                {/* Generate page buttons */}
                {Array.from({ length: Math.min(3, Math.ceil(allFlights.length / itemsPerPage)) }, (_, i) => (
                  <Button 
                    key={i}
                    variant={currentPage === i + 1 ? "default" : "outline"} 
                    size="sm" 
                    className="h-8 w-8 p-0"
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
                      className="h-8 w-8 p-0"
                      onClick={() => setCurrentPage(Math.ceil(allFlights.length / itemsPerPage))}
                    >
                      {Math.ceil(allFlights.length / itemsPerPage)}
                    </Button>
                  </>
                )}
                
                <Button 
                  variant="outline" 
                  size="icon"
                  disabled={currentPage >= Math.ceil(allFlights.length / itemsPerPage)}
                  onClick={() => setCurrentPage(prev => Math.min(Math.ceil(allFlights.length / itemsPerPage), prev + 1))}
                >
                  <ChevronRight className="h-4 w-4" />
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
