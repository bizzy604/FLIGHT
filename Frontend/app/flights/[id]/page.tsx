'use client'

import { useState, useEffect, Suspense } from "react"
import Image from "next/image"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { ChevronLeft, AlertCircle, Loader2 } from "lucide-react"

import { api } from "@/utils/api-client"
import { logger } from "@/utils/logger"

import { debugFlightStorage } from "@/utils/debug-storage"
import { flightStorageManager, FlightPriceData } from "@/utils/flight-storage-manager"
import { redisFlightStorage } from "@/utils/redis-flight-storage"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { FlightDetailsHeader } from "@/components/flight-details-header"
import { BookingForm } from "@/components/booking-form"
import { FareRulesTable } from "@/components/fare-rules-table"
import { FlightItineraryCard } from "@/components/flight-itinerary-card"

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
        // Debug storage before validation
        console.log('🔍 Debugging storage before flight data validation...');
        debugFlightStorage();

        // Enhanced debugging for storage retrieval
        console.log('🔍 Checking for existing flight price data first...');

        // Try to get existing flight price data from Redis first
        let flightPriceResult = await redisFlightStorage.getFlightPrice();

        console.log('🔍 Redis flight price result:', {
          success: flightPriceResult.success,
          hasData: !!flightPriceResult.data,
          error: flightPriceResult.error,
          session_id: redisFlightStorage.getCurrentSessionId()
        });

        // If Redis has flight price data, use it directly
        if (flightPriceResult.success && flightPriceResult.data) {
          console.log('✅ Found existing flight price data in Redis, using it directly');
          const cachedPriceData = flightPriceResult.data;

          if (cachedPriceData.pricedOffer) {
            setPricedOffer(cachedPriceData.pricedOffer);

            // Store search parameters for back button navigation
            if (cachedPriceData.searchParams) {
              setCachedSearchParams(cachedPriceData.searchParams);
            }

            // Store in sessionStorage for booking and faster future access
            sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(cachedPriceData.pricedOffer));
            if (cachedPriceData.rawResponse) {
              sessionStorage.setItem('rawFlightPriceResponse', JSON.stringify(cachedPriceData.rawResponse));
            }

            setIsLoading(false);
            return; // Data found and loaded, no need to fetch from API
          }
        }

        // If no flight price data found, try to make API call as fallback
        console.log('⚠️ No flight price data found in Redis, attempting API call as fallback...');

        // Get flight search data for API call
        const flightSearchResult = await redisFlightStorage.getFlightSearch();

        if (!flightSearchResult.success || !flightSearchResult.data) {
          console.log('❌ No flight search data available for API call');
          throw new Error('Flight data not found. Your session may have expired. Please start a new search.');
        }

        const rawAirShoppingResponse = flightSearchResult.data.airShoppingResponse;
        let airShoppingMetadata = {};
        let shoppingResponseId = 'BACKEND_WILL_EXTRACT';

        // Extract metadata for backend cache retrieval
        if (rawAirShoppingResponse?.data?.metadata) {
          airShoppingMetadata = rawAirShoppingResponse.data.metadata;
          console.log('✅ Using metadata from cached air shopping response');
        } else if (rawAirShoppingResponse?.metadata) {
          airShoppingMetadata = rawAirShoppingResponse.metadata;
          console.log('✅ Using metadata from legacy air shopping response');
        } else {
          console.log('⚠️ No metadata found, backend will use cached response');
        }

        // Make flight pricing API call
        console.log('🔄 Making flight pricing API call...');
        const flightIndex = parseInt(flightId);

        if (isNaN(flightIndex) || flightIndex < 0) {
          throw new Error(`Invalid flight ID: ${flightId}. Please select a flight again.`);
        }

        const response = await api.getFlightPrice(
          flightIndex,
          shoppingResponseId,
          airShoppingMetadata
        );

        if (!response.data || response.data.status !== 'success') {
          throw new Error(response.data?.error || 'Failed to get flight pricing');
        }

        // Extract the priced offer from the response
        const firstPricedOffer = response.data.data.priced_offers[0];
        if (!firstPricedOffer) {
          throw new Error("No valid offer found in the pricing response");
        }

        console.log('✅ Flight pricing API call successful');
        setPricedOffer(firstPricedOffer);

        // Store the data in Redis for future use
        const flightPriceData = {
          flightId: flightId,
          pricedOffer: firstPricedOffer,
          rawResponse: response.data.data.raw_response,
          searchParams: cachedSearchParams || {},
          timestamp: Date.now(),
          expiresAt: Date.now() + (30 * 60 * 1000) // 30 minutes
        };

        const redisStoreResult = await redisFlightStorage.storeFlightPrice(flightPriceData);
        if (redisStoreResult.success) {
          console.log('✅ Flight price data stored successfully in Redis');
        } else {
          console.warn('⚠️ Failed to store flight price data in Redis:', redisStoreResult.error);
        }

        // Store in session storage for booking
        sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(firstPricedOffer));

        // Store metadata for order creation if available
        if (response.data.data.metadata) {
          sessionStorage.setItem('flightPriceMetadata', JSON.stringify(response.data.data.metadata));
          console.log('✅ Stored flight price metadata for order creation');
        }







      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to fetch flight price data";
        setError(errorMessage);
        console.error('Error fetching flight price:', err);

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

            {/* ## FIX 3: Added all required props to FlightDetailsHeader ## */}
            <FlightDetailsHeader
              origin={outboundSegments[0]?.departure_airport}
              originCode={outboundSegments[0]?.departure_airport}
              destination={outboundSegments[outboundSegments.length - 1]?.arrival_airport}
              destinationCode={outboundSegments[outboundSegments.length - 1]?.arrival_airport}
              departDate={outboundSegments[0]?.departure_datetime}
              returnDate={returnSegments[0]?.departure_datetime} // Safely access for round-trip
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