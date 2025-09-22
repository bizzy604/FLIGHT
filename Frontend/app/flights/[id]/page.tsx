'use client'

import { useState, useEffect, Suspense } from "react"
import Image from "next/image"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { ChevronLeft, AlertCircle, Loader2 } from "lucide-react"

import { api } from "@/utils/api-client"
import { logger } from "@/utils/logger"
import { 
  calculatePricingBreakdown,
  extractFlightPricing,
  type BaggageSelection 
} from "@/utils/pricing-calculator"


import { simpleCacheManager } from "@/utils/simple-cache-manager"
import { simpleApiManager } from "@/utils/simple-api-manager"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { MainNav, UserNav, BookingForm, FlightItineraryCard } from "@/components/organisms"
import { FlightRouteInfo, FareRulesTable } from "@/components/molecules"

// Airport code to name mapping for route display
const AIRPORT_NAMES: Record<string, string> = {
  'NBO': 'Nairobi',
  'FRA': 'Frankfurt',
  'AMS': 'Amsterdam',
  'CDG': 'Paris',
  'LHR': 'London',
  'DXB': 'Dubai',
  'JFK': 'New York',
  'LAX': 'Los Angeles',
  'BOM': 'Mumbai',
  'DEL': 'New Delhi',
  'DOH': 'Doha',
  'ZUR': 'Zurich',
  'IST': 'Istanbul',
  'CAI': 'Cairo',
  'ADD': 'Addis Ababa',
  'KGL': 'Kigali',
  'EBB': 'Entebbe',
  'DAR': 'Dar es Salaam',
  'JNB': 'Johannesburg',
  'CPT': 'Cape Town',
  'HND': 'Tokyo',
  'ICN': 'Seoul',
  'SIN': 'Singapore',
  'SYD': 'Sydney',
  'MEL': 'Melbourne',
  'YYZ': 'Toronto',
  'YVR': 'Vancouver',
  'ORD': 'Chicago',
  'MIA': 'Miami',
  'ATL': 'Atlanta',
  'DEN': 'Denver',
  'SEA': 'Seattle',
  'SFO': 'San Francisco',
  'LAS': 'Las Vegas',
  'PHX': 'Phoenix',
  'DFW': 'Dallas',
  'IAH': 'Houston',
  'BOS': 'Boston',
  'PHL': 'Philadelphia',
  'CLT': 'Charlotte',
  'MSP': 'Minneapolis',
  'DTW': 'Detroit',
  'BWI': 'Baltimore',
  'DCA': 'Washington DC',
  'IAD': 'Washington DC',
  'MDW': 'Chicago',
  'LGA': 'New York',
  'EWR': 'Newark',
  'SLC': 'Salt Lake City',
  'PDX': 'Portland',
  'SAN': 'San Diego',
  'TPA': 'Tampa',
  'MCO': 'Orlando',
  'FLL': 'Fort Lauderdale',
  'PBI': 'West Palm Beach',
  'JAX': 'Jacksonville',
  'RDU': 'Raleigh',
  'CHS': 'Charleston',
  'SAV': 'Savannah',
  'MEM': 'Memphis',
  'BNA': 'Nashville',
  'STL': 'St. Louis',
  'MCI': 'Kansas City',
  'OMA': 'Omaha',
  'DSM': 'Des Moines',
  'MSY': 'New Orleans',
  'AUS': 'Austin',
  'SAT': 'San Antonio',
  'HOU': 'Houston',
  'ELP': 'El Paso',
  'ABQ': 'Albuquerque',
  'TUS': 'Tucson',
  'COS': 'Colorado Springs',
  'BOI': 'Boise',
  'BIL': 'Billings',
  'FAR': 'Fargo',
  'GFK': 'Grand Forks',
  'BIS': 'Bismarck',
  'RAP': 'Rapid City',
  'CYS': 'Cheyenne',
  'COD': 'Cody',
  'JAC': 'Jackson',
  'IDA': 'Idaho Falls',
  'TWF': 'Twin Falls',
  'SUN': 'Sun Valley',
  'MSO': 'Missoula',
  'BZN': 'Bozeman',
  'GTF': 'Great Falls',
  'HLN': 'Helena',
  'BTM': 'Butte'
};

// Helper function to get airport display name
function getAirportDisplay(code: string): string {
  return AIRPORT_NAMES[code] || code;
}

// Define a strict type for the single offer you expect from your backend.
interface TransformedOffer {
  offer_id: string;
  fare_family: string;
  direction: 'oneway' | 'roundtrip';
  flight_segments: any[] | { outbound: any[], return: any[] };
  passengers: any[];
  total_price: {
    amount: number;
    currency: string;
  };
  time_limits: {
    offer_expiration: string | null;
    payment_deadline: string | null;
  }
}

function FlightDetailsPageContent() {
  const params = useParams()
  const searchParams = useSearchParams()
  const flightId = decodeURIComponent(params.id as string)

  // Extract passenger counts from URL parameters
  const adults = Number(searchParams.get('adults')) || 1
  const children = Number(searchParams.get('children')) || 0
  const infants = Number(searchParams.get('infants')) || 0

  // Check for invalid flight ID
  if (!flightId || flightId === 'null' || flightId === 'undefined') {
    // Invalid flight ID - will be handled in the component
  }

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pricedOffer, setPricedOffer] = useState<TransformedOffer | null>(null)
  const [cachedSearchParams, setCachedSearchParams] = useState<any>(null)
  
  // Pricing state for dynamic price summary
  const [selectedSeats, setSelectedSeats] = useState<{ outbound: string[], return: string[] }>({ outbound: [], return: [] })
  const [selectedServices, setSelectedServices] = useState<string[]>([])
  const [selectedBaggage, setSelectedBaggage] = useState<BaggageSelection>({ checkedBags: 0, specialEquipment: 'none' })
  const [services, setServices] = useState<any[]>([])
  const [seatPrices, setSeatPrices] = useState({ outbound: 0, return: 0 })
  
  // Direct pricing data from ServiceSelection (working data)
  const [directServicesPricing, setDirectServicesPricing] = useState({ 
    totalPrice: 0, 
    servicesCount: 0, 
    currency: 'INR' 
  })

  useEffect(() => {
    const fetchFlightPrice = async () => {
      setIsLoading(true)
      setError(null)
      try {
        // Simple cache check - KISS principle applied
        const sessionId = simpleCacheManager.getOrCreateSessionId();
        const cachedPriceResult = simpleCacheManager.getFlightPrice(sessionId);
        
        if (cachedPriceResult.success && cachedPriceResult.data) {
          const cachedPriceData = cachedPriceResult.data;
          if (cachedPriceData.pricedOffer) {
            setPricedOffer(cachedPriceData.pricedOffer);
            if (cachedPriceData.searchParams) {
              setCachedSearchParams(cachedPriceData.searchParams);
            }
            
            // 🚀 CRITICAL FIX: Include metadata in the stored flight price response
            const flightPriceResponseWithMetadata = {
              ...cachedPriceData.pricedOffer,
              metadata: cachedPriceData.metadata || {}
            };
            sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(flightPriceResponseWithMetadata));
            
            if (cachedPriceData.rawResponse) {
              sessionStorage.setItem('rawFlightPriceResponse', JSON.stringify(cachedPriceData.rawResponse));
            }
            setIsLoading(false);
            return;
          }
        }

        // Try to get flight pricing from cache first using backend API
        const flightIndex = parseInt(flightId);
        const shoppingResponseId = 'BACKEND_WILL_EXTRACT';

        if (isNaN(flightIndex) || flightIndex < 0) {
          throw new Error(`Invalid flight ID: ${flightId}. Please select a flight again.`);
        }

        try {
          // Check cache first via backend API
          logger.info(`🔍 Checking flight price cache for flight ID: ${flightId}`);
          const cacheCheckResponse = await api.checkFlightPriceCache(flightId, shoppingResponseId);
          
          if (cacheCheckResponse.data.status === 'success' && cacheCheckResponse.data.source === 'cache') {
            logger.info('🚀 Flight price cache hit! Using cached pricing data from backend');
            
            const cachedPricingData = cacheCheckResponse.data.data;
            
            // Extract the priced offer from cached response
            const pricedOfferData = cachedPricingData.priced_offers ? cachedPricingData.priced_offers[0] : cachedPricingData;
            
            if (pricedOfferData) {
              setPricedOffer(pricedOfferData);
              
              // 🚀 CRITICAL FIX: Include metadata in the stored flight price response
              const flightPriceResponseWithMetadata = {
                ...pricedOfferData,
                metadata: cachedPricingData.metadata || {}
              };
              
              // Store in sessionStorage for booking access WITH metadata
              sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(flightPriceResponseWithMetadata));
              
              if (cachedPricingData.metadata) {
                sessionStorage.setItem('flightPriceMetadata', JSON.stringify(cachedPricingData.metadata));
                
                // 🚀 CRITICAL FIX: Explicitly store flight_price_cache_key for seat/service retrieval
                if (cachedPricingData.metadata.flight_price_cache_key) {
                  sessionStorage.setItem('flight_price_cache_key', cachedPricingData.metadata.flight_price_cache_key);
                  logger.info(`💾 Stored cached flight_price_cache_key: ${cachedPricingData.metadata.flight_price_cache_key}`);
                }
              }
              
              // Try to get search params from URL parameters (more reliable than cache)
              const urlSearchParams = {
                origin: searchParams.get('origin'),
                destination: searchParams.get('destination'),
                departDate: searchParams.get('departDate'),
                returnDate: searchParams.get('returnDate'),
                tripType: searchParams.get('tripType'),
                adults: searchParams.get('adults'),
                children: searchParams.get('children'),
                infants: searchParams.get('infants'),
                cabinClass: searchParams.get('cabinClass')
              };

              // Only set cached params if we have the essential ones
              if (urlSearchParams.origin && urlSearchParams.destination && urlSearchParams.departDate) {
                setCachedSearchParams(urlSearchParams);
                logger.info('✅ Using search params from URL');
              } else {
                logger.warn('⚠️ Could not get search params from URL, will use flight data for route display');
              }
              
              setIsLoading(false);
              return; // Successfully loaded from cache
            }
          }
        } catch (cacheError) {
          logger.warn('⚠️ Flight price cache check failed, falling back to API:', cacheError);
        }

        // Cache miss - get flight search data for API call using new cache system
        logger.info(`💫 Cache miss for flight ID: ${flightId} - calling pricing API`);
        
        let airShoppingMetadata = {};
        
        // Try to get search parameters from URL first
        const urlSearchParams = {
          origin: searchParams.get('origin'),
          destination: searchParams.get('destination'),
          departDate: searchParams.get('departDate'),
          returnDate: searchParams.get('returnDate'),
          tripType: searchParams.get('tripType'),
          adults: Number(searchParams.get('adults')) || 1,
          children: Number(searchParams.get('children')) || 0,
          infants: Number(searchParams.get('infants')) || 0,
          cabinClass: searchParams.get('cabinClass') || 'ECONOMY'
        };

        // Set cached search params if available from URL
        if (urlSearchParams.origin && urlSearchParams.destination && urlSearchParams.departDate && !cachedSearchParams) {
          setCachedSearchParams(urlSearchParams);
        }

        // Try to get flight search data from new cache system
        if (urlSearchParams.origin && urlSearchParams.destination && urlSearchParams.departDate) {
          const flightSearchParams = {
            tripType: (urlSearchParams.tripType === 'round-trip' ? 'ROUND_TRIP' : 'ONE_WAY') as 'ROUND_TRIP' | 'ONE_WAY',
            odSegments: [{
              origin: urlSearchParams.origin,
              destination: urlSearchParams.destination,
              departureDate: urlSearchParams.departDate,
              ...(urlSearchParams.tripType === 'round-trip' && urlSearchParams.returnDate ? { returnDate: urlSearchParams.returnDate } : {})
            }],
            numAdults: Number(urlSearchParams.adults) || 1,
            numChildren: Number(urlSearchParams.children) || 0,
            numInfants: Number(urlSearchParams.infants) || 0,
            cabinPreference: urlSearchParams.cabinClass || 'ECONOMY',
            directOnly: false
          };

          try {
            // Check the new cache-first system for flight search data
            const cacheCheckResponse = await api.checkFlightSearchCache(flightSearchParams);
            
            if (cacheCheckResponse.data.status === 'success' && cacheCheckResponse.data.source === 'cache') {
              logger.info('✅ Found flight search data in new cache system for pricing API');
              
              const cachedFlightData = cacheCheckResponse.data.data;
              
              // Extract metadata if available
              if (cachedFlightData?.metadata) {
                airShoppingMetadata = cachedFlightData.metadata;
                logger.info('✅ Using metadata from new cache system for pricing API');
              } else if (cachedFlightData?.raw_response) {
                // Use raw response if metadata not available
                airShoppingMetadata = cachedFlightData.raw_response;
                logger.info('✅ Using raw response from new cache system for pricing API');
              } else {
                // Fallback to the whole cached data
                airShoppingMetadata = cachedFlightData;
                logger.info('✅ Using full cached data from new cache system for pricing API');
              }
            } else {
              logger.warn('⚠️ No flight search data found in new cache system, backend will handle cache retrieval');
            }
          } catch (cacheError) {
            logger.warn('⚠️ Failed to check new cache system for pricing API, backend will handle cache retrieval:', cacheError);
          }
        } else {
          logger.warn('⚠️ No search parameters available from URL, backend will handle cache retrieval');
        }

        // Check if we have valid air shopping data before making the API call
        if (!airShoppingMetadata || Object.keys(airShoppingMetadata).length === 0) {
          logger.warn('⚠️ No air shopping data available - flight search results may have expired');
          setError('Flight search results have expired. Please search for flights again.');
          setIsLoading(false);
          return;
        }

        // Make flight pricing API call
        const response = await api.getFlightPrice(
          flightIndex,
          shoppingResponseId,
          airShoppingMetadata
        );

        // Handle expired offers error specifically
        if (response.data?.status === 'expired_offer_error') {
          logger.warn('⚠️ Flight offers have expired, redirecting to search results');
          
          // Redirect back to search results page with a message
          alert('Flight offers have expired. You will be redirected to search for current flights.');
          
          // Build the search URL with current parameters
          const searchUrl = new URLSearchParams();
          if (urlSearchParams.origin) searchUrl.set('origin', urlSearchParams.origin);
          if (urlSearchParams.destination) searchUrl.set('destination', urlSearchParams.destination);
          if (urlSearchParams.departDate) searchUrl.set('departDate', urlSearchParams.departDate);
          if (urlSearchParams.returnDate) searchUrl.set('returnDate', urlSearchParams.returnDate);
          if (urlSearchParams.tripType) searchUrl.set('tripType', urlSearchParams.tripType);
          if (urlSearchParams.adults) searchUrl.set('adults', urlSearchParams.adults.toString());
          if (urlSearchParams.children) searchUrl.set('children', urlSearchParams.children.toString());
          if (urlSearchParams.infants) searchUrl.set('infants', urlSearchParams.infants.toString());
          if (urlSearchParams.cabinClass) searchUrl.set('cabinClass', urlSearchParams.cabinClass);
          
          // Redirect to flights page to trigger fresh search
          window.location.href = `/flights?${searchUrl.toString()}`;
          return;
        }

        // Handle cache/data expiration errors
        if (response.data?.status === 'error' && response.data?.error) {
          const errorMessage = response.data.error.toLowerCase();
          if (errorMessage.includes('expired') || errorMessage.includes('cache') || errorMessage.includes('search results')) {
            logger.warn('⚠️ Flight search data expired');
            setError('Flight search results have expired. Please search for flights again.');
            setIsLoading(false);
            return;
          }
        }

        if (!response.data || response.data.status !== 'success') {
          throw new Error(response.data?.error || 'Failed to get flight pricing');
        }

        // Extract the priced offer from the response
        const firstPricedOffer = response.data.data.priced_offers[0];
        if (!firstPricedOffer) {
          throw new Error("No valid offer found in the pricing response");
        }

        // Add metadata to the priced offer for order creation
        firstPricedOffer.metadata = response.data.data.metadata;

        // Add raw response if available (fallback when caching fails)
        if (response.data.data.raw_response) {
          firstPricedOffer.raw_flight_price_response = response.data.data.raw_response;
        }


        setPricedOffer(firstPricedOffer);

        // Note: Flight pricing data is now automatically cached by the backend Redis system
        // No need for client-side storage as backend handles caching with the new Redis implementation

        // 🚀 CRITICAL FIX: Include metadata in the stored flight price response
        const flightPriceResponseWithMetadata = {
          ...firstPricedOffer,
          metadata: response.data.data.metadata || {}
        };

        // Store in session storage for booking WITH metadata
        sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(flightPriceResponseWithMetadata));

        // Store raw flight price response for order creation
        if (response.data.data.raw_response) {
          sessionStorage.setItem('rawFlightPriceResponse', JSON.stringify(response.data.data.raw_response));
        }

        // Store metadata for order creation if available
        if (response.data.data.metadata) {
          sessionStorage.setItem('flightPriceMetadata', JSON.stringify(response.data.data.metadata));
          
          // 🚀 CRITICAL FIX: Explicitly store flight_price_cache_key for seat/service retrieval
          if (response.data.data.metadata.flight_price_cache_key) {
            sessionStorage.setItem('flight_price_cache_key', response.data.data.metadata.flight_price_cache_key);
            logger.info(`💾 Stored flight_price_cache_key: ${response.data.data.metadata.flight_price_cache_key}`);
          }
        }







      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to fetch flight price data";
        setError(errorMessage);

        // If it's a session/data error, provide helpful guidance
        if (errorMessage.includes('session may have expired') || errorMessage.includes('search data')) {
          logger.info('🔄 User needs to start a new search due to expired/missing data');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchFlightPrice();
  }, [flightId]);

  if (isLoading) {
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
          <div className="flex items-center justify-center min-h-[60vh] px-4">
            <div className="flex flex-col items-center space-y-4 text-center">
              <Loader2 className="h-8 w-8 sm:h-12 sm:w-12 animate-spin text-primary" />
              <p className="text-base sm:text-lg font-medium">Getting Live Prices and Fare Rules...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !pricedOffer) {
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
            <div className="container py-6 sm:py-8 md:py-12 px-4">
              <Alert variant="destructive" className="my-4 sm:my-8">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error Loading Flight</AlertTitle>
                <AlertDescription className="text-sm">{error || "Could not load the selected flight data."}</AlertDescription>
              </Alert>
              <Button asChild className="w-full sm:w-auto">
                <Link href="/flights">Back to Search Results</Link>
              </Button>
            </div>
        </main>
      </div>
    );
  }

  // Get all unique O&D pairs for table headers
  const allOds = new Set<string>();
  if (pricedOffer && pricedOffer.passengers) {
    pricedOffer.passengers.forEach(pax => {
      if (pax.fare_rules) {
        Object.values(pax.fare_rules).forEach((penalty: any) => {
          Object.values(penalty).forEach((rule: any) => {
            if (rule.od_pair) allOds.add(rule.od_pair);
          });
        });
      }
    });
  }
  const odHeaders = Array.from(allOds);
  
  // ## FIX 1 & 2: Type Guarding for Round-Trip Data Access ##
  // This structure helps TypeScript understand which type `flight_segments` is.
  const isRoundTrip = pricedOffer.direction === 'roundtrip';
  let outboundSegments: any[] = [];
  let returnSegments: any[] = [];

  if (isRoundTrip && typeof pricedOffer.flight_segments === 'object' && !Array.isArray(pricedOffer.flight_segments)) {
    // Inside this block, TypeScript knows `flight_segments` is an object.
    outboundSegments = (pricedOffer.flight_segments as { outbound: any[], return: any[] }).outbound;
    returnSegments = (pricedOffer.flight_segments as { outbound: any[], return: any[] }).return;
  } else {
    // Inside this block, TypeScript knows `flight_segments` is an array.
    outboundSegments = pricedOffer.flight_segments as any[];
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
              <div className="flex items-center gap-2">
                  <Image src="/logo1.png" alt="Rea Travel Logo" width={28} height={28} className="sm:w-8 sm:h-8" />
                  <span className="text-sm sm:text-base md:text-lg font-semibold">Rea Travel</span>
              </div>
              <div className="flex items-center gap-4">
                <MainNav />
                <UserNav />
              </div>
          </div>
      </header>

      <main className="flex-1">
        <div className="container py-3 sm:py-4 md:py-6">
          <div className="mb-4 sm:mb-6">
            <Link
              href={`/flights?${new URLSearchParams(cachedSearchParams || Object.fromEntries(searchParams.entries())).toString()}`}
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-4"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Search Results
            </Link>

            {/* ## FIX 3: Use original search parameters for route display instead of flight segments ## */}
            <FlightRouteInfo
              origin={getAirportDisplay(cachedSearchParams?.origin || outboundSegments[0]?.departure_airport)}
              originCode={cachedSearchParams?.origin || outboundSegments[0]?.departure_airport}
              destination={getAirportDisplay(cachedSearchParams?.destination || outboundSegments[outboundSegments.length - 1]?.arrival_airport)}
              destinationCode={cachedSearchParams?.destination || outboundSegments[outboundSegments.length - 1]?.arrival_airport}
              departDate={cachedSearchParams?.departDate || outboundSegments[0]?.departure_datetime}
              showPrice={false}
              adults={adults}
              children={children}
              infants={infants}
            />
          </div>

          <div className="grid gap-4 sm:gap-6 lg:gap-8 lg:grid-cols-[1fr_400px]">
            <div className="space-y-4 sm:space-y-6 lg:space-y-8">
              {isRoundTrip ? (
                <>
                  <div className="rounded-lg border">
                      <div className="p-3 sm:p-4 md:p-6">
                        <h2 className="text-lg sm:text-xl font-semibold">Outbound Flight</h2>
                      </div>
                      <Separator/>
                      <FlightItineraryCard flightSegments={outboundSegments} />
                  </div>
                  <div className="rounded-lg border">
                      <div className="p-3 sm:p-4 md:p-6">
                        <h2 className="text-lg sm:text-xl font-semibold">Return Flight</h2>
                      </div>
                      <Separator/>
                      <FlightItineraryCard flightSegments={returnSegments} />
                  </div>
                </>
              ) : (
                 <div className="rounded-lg border">
                      <div className="p-3 sm:p-4 md:p-6">
                        <h2 className="text-lg sm:text-xl font-semibold">Flight Details</h2>
                      </div>
                      <Separator/>
                      <FlightItineraryCard flightSegments={outboundSegments} />
                  </div>
              )}

              <div className="space-y-3 sm:space-y-4">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold">
                  Fare Rules & Baggage ({pricedOffer.fare_family})
                </h2>
                {pricedOffer.passengers.map(pax => (
                  <FareRulesTable key={pax.type} passenger={pax} allOds={odHeaders} />
                ))}
              </div>

              {/* Booking Form - Moved from sidebar to main content */}
              <div className="space-y-3 sm:space-y-4">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold">
                  Booking Details
                </h2>
                <div className="rounded-lg border">
                  <BookingForm
                    adults={adults}
                    children={children}
                    infants={infants}
                    onSeatChange={(seats) => {
                      setSelectedSeats(seats)
                    }}
                    onServiceChange={(servicesIds, servicesData) => {
                      setSelectedServices(servicesIds)
                      setServices(servicesData)
                    }}
                    onBaggageChange={(baggage) => {
                      setSelectedBaggage(baggage)
                    }}
                    onSeatPriceChange={(prices) => {
                      setSeatPrices(prices)
                    }}
                    onPricingUpdate={(totalPrice, servicesCount, currency) => {
                      setDirectServicesPricing({ totalPrice, servicesCount, currency })
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="h-fit rounded-lg border lg:sticky lg:top-24">
              <div className="p-4 sm:p-6">
                <h2 className="text-lg sm:text-xl font-semibold">Price Summary</h2>
              </div>
              <Separator />
              <div className="p-4 sm:p-6 space-y-4">
                {(() => {
                  // Calculate dynamic pricing
                  const flightPricing = extractFlightPricing(pricedOffer)
                  
                  // Use EXACT same logic as working ServiceSelection component
                  const getSelectedServicePrice = (service: any): number => {
                    return service.price?.[0]?.total?.value || 0;
                  };
                  
                  const getTotalServicesPrice = (): number => {
                    return selectedServices.reduce((total, serviceObjectKey) => {
                      const service = services.find(s => s.objectKey === serviceObjectKey);
                      return total + (service ? getSelectedServicePrice(service) : 0);
                    }, 0);
                  };
                  
                  const getCurrency = (): string => {
                    const firstService = services.find(s => s.price?.[0]?.total?.code);
                    return firstService?.price?.[0]?.total?.code || 'INR';
                  };
                  
                  // Calculate seat fees directly
                  const getSeatFees = (): number => {
                    return (seatPrices?.outbound || 0) + (seatPrices?.return || 0);
                  };
                  
                  // Debug logging for seat prices
                  console.log('🔍 Price Summary Debug - Seat Prices:', {
                    seatPrices,
                    outbound: seatPrices?.outbound || 0,
                    return: seatPrices?.return || 0,
                    total: getSeatFees()
                  });
                  
                  // Get selected baggage services (weight-based options like 25KG, 30KG, etc.)
                  const getSelectedBaggageServices = () => {
                    return services.filter(service => {
                      const serviceName = service.name?.value?.toLowerCase() || "";
                      const serviceCode = service.serviceId?.value?.toLowerCase() || "";
                      return (serviceName.includes("bag") || serviceName.includes("luggage") || serviceName.includes("weight") ||
                             serviceCode.includes("bag") || serviceCode.includes("xwbg") || serviceCode.includes("wbg")) &&
                             selectedServices.includes(service.objectKey);
                    });
                  };
                  
                  // Get price for basic baggage (+/- buttons) - use price from baggage services
                  const getBasicBaggagePrice = (): number => {
                    // Find the most appropriate baggage service price from actual API data
                    const baggageServices = services.filter(service => {
                      const serviceName = service.name?.value?.toLowerCase() || "";
                      const serviceCode = service.serviceId?.value?.toLowerCase() || "";
                      return (serviceName.includes("bag") || serviceName.includes("luggage") || serviceName.includes("weight") ||
                             serviceCode.includes("bag") || serviceCode.includes("xwbg") || serviceCode.includes("wbg"));
                    });
                    
                    const weightSystemService = baggageServices.find(s => s.name?.value?.toLowerCase().includes('weight system'));
                    const bagService = baggageServices.find(s => s.name?.value?.toLowerCase().includes('bag'));
                    const firstBaggageService = baggageServices[0];
                    
                    // Priority: weight system > bag > first service > 0 (no hardcoded fallback)
                    const selectedService = weightSystemService || bagService || firstBaggageService;
                    return selectedService?.price?.[0]?.total?.value || 0;
                  };
                  
                  // Calculate total baggage cost: basic bags + selected baggage services
                  const getTotalBaggageCost = (): number => {
                    const basicBaggageCost = selectedBaggage.checkedBags * getBasicBaggagePrice();
                    const selectedBaggageServicesCost = getSelectedBaggageServices()
                      .reduce((total, service) => total + (service.price?.[0]?.total?.value || 0), 0);
                    return basicBaggageCost + selectedBaggageServicesCost;
                  };
                  
                  // Calculate total baggage count: basic bags + selected baggage services  
                  const getTotalBaggageCount = (): number => {
                    return selectedBaggage.checkedBags + getSelectedBaggageServices().length;
                  };
                  
                  // Calculate non-baggage services total (exclude baggage from total services)
                  const getNonBaggageServicesPrice = (): number => {
                    const baggageServiceKeys = getSelectedBaggageServices().map(s => s.objectKey);
                    return selectedServices
                      .filter(serviceKey => !baggageServiceKeys.includes(serviceKey))
                      .reduce((total, serviceKey) => {
                        const service = services.find(s => s.objectKey === serviceKey);
                        return total + (service ? getSelectedServicePrice(service) : 0);
                      }, 0);
                  };
                  
                  // Calculate non-baggage services count
                  const getNonBaggageServicesCount = (): number => {
                    const baggageServiceKeys = getSelectedBaggageServices().map(s => s.objectKey);
                    return selectedServices.filter(serviceKey => !baggageServiceKeys.includes(serviceKey)).length;
                  };
                  
                  // Debug logging for services pricing
                  console.log('🔍 Price Summary Debug - Services:', {
                    selectedServices,
                    services: services.length,
                    directServicesPricing,
                    getTotalServicesPrice: getTotalServicesPrice(),
                    getNonBaggageServicesPrice: getNonBaggageServicesPrice(),
                    getTotalBaggageCost: getTotalBaggageCost()
                  });
                  
                  // Debug logging for baggage pricing
                  console.log('🔍 Price Summary Debug - Baggage:', {
                    selectedBaggage,
                    getBasicBaggagePrice: getBasicBaggagePrice(),
                    getTotalBaggageCost: getTotalBaggageCost(),
                    getTotalBaggageCount: getTotalBaggageCount(),
                    services: services.filter(s => {
                      const name = s.name?.value?.toLowerCase() || "";
                      return name.includes("bag") || name.includes("luggage") || name.includes("weight");
                    }).map(s => ({ name: s.name?.value, price: s.price?.[0]?.total?.value }))
                  });
                  
                  
                  return (
                    <>
                      {/* Price Breakdown */}
                      <div className="space-y-3">
                        {/* Base flight pricing */}
                        {pricedOffer.passengers && Array.isArray(pricedOffer.passengers) ? (
                          <>
                            {pricedOffer.passengers.map((passenger: any, index: number) => (
                              <div key={index} className="space-y-2">
                                <div className="text-sm font-medium text-muted-foreground border-b pb-1">
                                  {passenger.type} {index + 1}
                                </div>
                                {passenger.pricing?.base_fare && (
                                  <div className="flex justify-between text-sm">
                                    <span className="ml-2">Base fare</span>
                                    <span>{passenger.pricing.base_fare.amount?.toFixed(2)} {passenger.pricing.base_fare.currency || pricedOffer.total_price.currency}</span>
                                  </div>
                                )}
                                {passenger.pricing?.taxes && (
                                  <div className="flex justify-between text-sm">
                                    <span className="ml-2">Taxes and fees</span>
                                    <span>{passenger.pricing.taxes.amount?.toFixed(2)} {passenger.pricing.taxes.currency || pricedOffer.total_price.currency}</span>
                                  </div>
                                )}
                              </div>
                            ))}
                          </>
                        ) : (
                          <>
                            {/* Fallback to simple pricing display */}
                            <div className="flex justify-between text-sm">
                              <span>Flight fare ({adults + children + infants} passenger{adults + children + infants > 1 ? 's' : ''})</span>
                              <span>{(pricedOffer.total_price.amount * 0.8).toFixed(2)} {pricedOffer.total_price.currency}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span>Taxes and fees</span>
                              <span>{(pricedOffer.total_price.amount * 0.2).toFixed(2)} {pricedOffer.total_price.currency}</span>
                            </div>
                          </>
                        )}
                        
                        {/* Dynamic additional fees */}
                        <div className="space-y-1 text-sm border-t pt-3">
                          <div className="flex justify-between">
                            <span>Seat selection</span>
                            <span className={getSeatFees() > 0 ? 'font-medium text-primary' : 'text-muted-foreground'}>
                              {getSeatFees() > 0 ? 
                                `${getSeatFees().toFixed(2)} ${flightPricing.currency}` : 
                                (selectedSeats.outbound.length > 0 || selectedSeats.return.length > 0 ? 
                                  'Free seats selected' : 'Not selected')
                              }
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Baggage ({getTotalBaggageCount()} {getTotalBaggageCount() === 1 ? 'item' : 'items'})</span>
                            <span className={getTotalBaggageCost() > 0 ? 'font-medium text-primary' : 'text-muted-foreground'}>
                              {getTotalBaggageCost() > 0 ? 
                                `${getTotalBaggageCost().toFixed(2)} ${getCurrency()}` : 
                                'Not selected'
                              }
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Services ({getNonBaggageServicesCount()} selected)</span>
                            <span className={getNonBaggageServicesPrice() > 0 ? 'font-medium text-primary' : 'text-muted-foreground'}>
                              {getNonBaggageServicesPrice() > 0 ? 
                                `${getNonBaggageServicesPrice().toFixed(2)} ${getCurrency()}` : 
                                (selectedServices.length > 0 ? 'Free services selected' : 'Not selected')
                              }
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <Separator />
                      
                      {/* Dynamic Total Price */}
                      <div className="flex justify-between text-base sm:text-lg font-bold">
                        <span>Total Price</span>
                        <span className="text-primary">{(flightPricing.total + getSeatFees() + getTotalBaggageCost() + getNonBaggageServicesPrice()).toFixed(2)} {flightPricing.currency}</span>
                      </div>
                      
                      {/* Show additional costs if any */}
                      {(getSeatFees() + getTotalBaggageCost() + getNonBaggageServicesPrice()) > 0 && (
                        <div className="text-xs text-muted-foreground bg-primary/10 p-2 rounded">
                          Includes {(getSeatFees() + getTotalBaggageCost() + getNonBaggageServicesPrice()).toFixed(2)} {flightPricing.currency} in additional services
                        </div>
                      )}
                    </>
                  )
                })()}
                
                {/* Important timestamps */}
                <div className="space-y-2 text-xs sm:text-sm mt-4 border-t pt-4">
                  <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
                    <span className="text-muted-foreground">Offer expires:</span>
                    <span className="font-medium text-orange-600 text-xs sm:text-sm">
                      {pricedOffer.time_limits?.offer_expiration ? new Date(pricedOffer.time_limits.offer_expiration).toLocaleString() : "Not specified"}
                    </span>
                  </div>
                  <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
                    <span className="text-muted-foreground">Payment deadline:</span>
                    <span className="font-medium text-red-600 text-xs sm:text-sm">
                      {pricedOffer.time_limits?.payment_deadline ? new Date(pricedOffer.time_limits.payment_deadline).toLocaleString() : "Not specified"}
                    </span>
                  </div>
                </div>
                
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function FlightDetailsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background">
        <div className="border-b">
          <div className="flex h-16 items-center px-4">
            <MainNav />
            <div className="ml-auto flex items-center space-x-4">
              <UserNav />
            </div>
          </div>
        </div>
        <main className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-center min-h-[400px]">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        </main>
      </div>
    }>
      <FlightDetailsPageContent />
    </Suspense>
  )
}