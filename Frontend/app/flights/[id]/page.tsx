'use client'

import { useState, useEffect, Suspense } from "react"
import Image from "next/image"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { ChevronLeft, AlertCircle, Loader2 } from "lucide-react"

import { api } from "@/utils/api-client"
import { logger } from "@/utils/logger"


import { flightStorageManager, FlightPriceData } from "@/utils/flight-storage-manager"
import { redisFlightStorage } from "@/utils/redis-flight-storage"
import { navigationCacheManager } from "@/utils/navigation-cache-manager"
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

  useEffect(() => {
    const fetchFlightPrice = async () => {
      setIsLoading(true)
      setError(null)
      try {
        // Update navigation state
        navigationCacheManager.updateNavigationState('details', { flightId });

        // Check if we should skip API call based on navigation context
        if (navigationCacheManager.shouldSkipApiCall('details', { flightId })) {
          const cacheValidation = await navigationCacheManager.validateFlightPriceCache(flightId);
          if (cacheValidation.isValid && cacheValidation.data) {
            const cachedPriceData = cacheValidation.data;
            setPricedOffer(cachedPriceData.pricedOffer);
            if (cachedPriceData.searchParams) {
              setCachedSearchParams(cachedPriceData.searchParams);
            }
            sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(cachedPriceData.pricedOffer));
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
              
              // Store in sessionStorage for booking access
              sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(pricedOfferData));
              
              if (cachedPricingData.metadata) {
                sessionStorage.setItem('flightPriceMetadata', JSON.stringify(cachedPricingData.metadata));
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
            tripType: urlSearchParams.tripType === 'round-trip' ? 'ROUND_TRIP' : 'ONE_WAY',
            odSegments: [{
              origin: urlSearchParams.origin,
              destination: urlSearchParams.destination,
              departureDate: urlSearchParams.departDate,
              ...(urlSearchParams.tripType === 'round-trip' && urlSearchParams.returnDate ? { returnDate: urlSearchParams.returnDate } : {})
            }],
            numAdults: urlSearchParams.adults,
            numChildren: urlSearchParams.children,
            numInfants: urlSearchParams.infants,
            cabinPreference: urlSearchParams.cabinClass,
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

        // Store in session storage for booking
        sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(firstPricedOffer));

        // Store raw flight price response for order creation
        if (response.data.data.raw_response) {
          sessionStorage.setItem('rawFlightPriceResponse', JSON.stringify(response.data.data.raw_response));
        }

        // Store metadata for order creation if available
        if (response.data.data.metadata) {
          sessionStorage.setItem('flightPriceMetadata', JSON.stringify(response.data.data.metadata));
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
              price={pricedOffer.total_price.amount}
              currency={pricedOffer.total_price.currency}
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
                <div className="flex justify-between text-base sm:text-lg font-bold">
                  <span>Total Price</span>
                  <span>{pricedOffer.total_price.amount.toFixed(2)} {pricedOffer.total_price.currency}</span>
                </div>
                 <div className="space-y-2 text-xs sm:text-sm mt-4 border-t pt-4">
                    <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
                      <span className="text-muted-foreground">Offer expires:</span>
                      <span className="font-medium text-orange-600 text-xs sm:text-sm">
                        {pricedOffer.time_limits.offer_expiration ? new Date(pricedOffer.time_limits.offer_expiration).toLocaleString() : "Not specified"}
                      </span>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
                      <span className="text-muted-foreground">Payment deadline:</span>
                      <span className="font-medium text-red-600 text-xs sm:text-sm">
                        {pricedOffer.time_limits.payment_deadline ? new Date(pricedOffer.time_limits.payment_deadline).toLocaleString() : "Not specified"}
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