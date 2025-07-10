"use client"

import { useState, useEffect } from 'react'
import Link from "next/link"
import Image from "next/image"
import {
  ArrowRight,
  Clock,
  Luggage,
  ChevronDown,
  ChevronUp,
  Wifi,
  Power,
  Utensils,
  Tv,
  Briefcase,
  MapPin,
  Plane,
  Users,
  CreditCard,
  AlertCircle
} from "lucide-react"

import { Button, LoadingButton } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { FlightOffer, FlightSegmentDetails, Penalty } from "@/types/flight-api"

import { logger } from "@/utils/logger"
import { flightStorageManager } from "@/utils/flight-storage-manager"
import { redisFlightStorage } from "@/utils/redis-flight-storage"
import { api } from "@/utils/api-client"

interface EnhancedFlightCardProps {
  flight: FlightOffer
  showExtendedDetails?: boolean
  searchParams?: {
    adults?: number
    children?: number
    infants?: number
    tripType?: string
    origin?: string
    destination?: string
    departDate?: string
    returnDate?: string
    cabinClass?: string
  }
}

export function EnhancedFlightCard({ flight, showExtendedDetails = false, searchParams }: EnhancedFlightCardProps) {
  const [isSelecting, setIsSelecting] = useState(false)

  // Check if offer is expiring soon (within 10 minutes)
  const getOfferExpirationStatus = () => {
    if (!flight.time_limits?.offer_expiration) return null;

    try {
      const expirationTime = new Date(flight.time_limits.offer_expiration);
      const currentTime = new Date();
      const timeUntilExpiration = expirationTime.getTime() - currentTime.getTime();
      const minutesUntilExpiration = Math.floor(timeUntilExpiration / (1000 * 60));

      if (timeUntilExpiration <= 0) {
        return { status: 'expired', message: 'Offer expired' };
      } else if (minutesUntilExpiration <= 10) {
        return { status: 'expiring', message: `Expires in ${minutesUntilExpiration}m` };
      } else if (minutesUntilExpiration <= 30) {
        return { status: 'warning', message: `Expires in ${minutesUntilExpiration}m` };
      }
    } catch (error) {
    }

    return null;
  };

  const expirationStatus = getOfferExpirationStatus();
  // Store flight data in localStorage when flight is selected
  const handleFlightSelect = async (e: React.MouseEvent) => {
    setIsSelecting(true);

    try {
      // Store the complete flight data with a timestamp
      const flightData = {
        flight,
        timestamp: new Date().toISOString(),
        expiresAt: Date.now() + (30 * 60 * 1000), // 30 minutes expiry
        searchParams: searchParams || {}
      };

      // Store selected flight data using robust storage manager
      const storeResult = await flightStorageManager.storeSelectedFlight(flightData);

      if (!storeResult.success) {
        logger.warn('⚠️ Failed to store selected flight data:', storeResult.error);
        // Continue anyway - don't block user flow
      } else {
        logger.info('✅ Selected flight data stored successfully');
      }

      // If this is a roundtrip, store the return flight data as well
      if (flight.returnFlight) {
        const returnFlightData = {
          flight: flight.returnFlight,
          timestamp: new Date().toISOString(),
          expiresAt: Date.now() + (30 * 60 * 1000), // 30 minutes expiry
          searchParams: searchParams || {}
        };

        const returnStoreResult = await flightStorageManager.storeSelectedFlight(returnFlightData);
        if (!returnStoreResult.success) {
          logger.warn('⚠️ Failed to store return flight data:', returnStoreResult.error);
        }
      }

      // Call flight pricing API to get detailed pricing and store in Redis
      logger.info('🔄 Calling flight pricing API for selected flight...');

      // Get flight search data to extract metadata for API call
      const flightSearchResult = await redisFlightStorage.getFlightSearch();

      let airShoppingData = {};
      let shoppingResponseId = 'BACKEND_WILL_EXTRACT';

      if (flightSearchResult.success && flightSearchResult.data) {
        const rawAirShoppingResponse = flightSearchResult.data.airShoppingResponse;

        // Check if we have metadata (for Redis-enabled backend) or need full response (for Redis-disabled backend)
        if (rawAirShoppingResponse?.data?.metadata) {
          // Use metadata for Redis-enabled backend
          airShoppingData = rawAirShoppingResponse.data.metadata;
          logger.info('✅ Using metadata from cached air shopping response');
        } else if (rawAirShoppingResponse?.metadata) {
          // Use metadata for legacy format
          airShoppingData = rawAirShoppingResponse.metadata;
          logger.info('✅ Using metadata from legacy air shopping response');
        } else {
          // Fallback: send full response for Redis-disabled backend
          airShoppingData = rawAirShoppingResponse;
          logger.info('✅ Using full air shopping response as fallback');
        }
      } else {
        logger.warn('⚠️ No flight search data found, backend will handle cache retrieval');
      }

      // Call flight pricing API
      const flightIndex = parseInt(flight.id); // flight.id is the index
      const response = await api.getFlightPrice(
        flightIndex,
        shoppingResponseId,
        airShoppingData
      );

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

      logger.info('✅ Flight pricing API call successful');

      // Store flight price data in Redis for the details page
      const flightPriceData = {
        flightId: flight.id,
        pricedOffer: firstPricedOffer,
        rawResponse: response.data.data.raw_response, // This will be null when caching works
        metadata: response.data.data.metadata, // Store metadata with cache keys
        searchParams: searchParams || {},
        timestamp: Date.now(),
        expiresAt: Date.now() + (30 * 60 * 1000) // 30 minutes
      };

      const redisStoreResult = await redisFlightStorage.storeFlightPrice(flightPriceData);
      if (redisStoreResult.success) {
        logger.info('✅ Flight price data stored successfully in Redis');
      } else {
        logger.warn('⚠️ Failed to store flight price data in Redis:', redisStoreResult.error);
        // Continue anyway - the details page will handle this
      }

      // Store metadata for order creation if available
      if (response.data.data.metadata) {
        sessionStorage.setItem('flightPriceMetadata', JSON.stringify(response.data.data.metadata));
        logger.info('✅ Stored flight price metadata for order creation');
      }

      // Store priced offer in session storage for immediate access
      sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(firstPricedOffer));

      // Store raw flight price response for order creation
      if (response.data.data.raw_response) {
        sessionStorage.setItem('rawFlightPriceResponse', JSON.stringify(response.data.data.raw_response));
        logger.info('✅ Stored raw flight price response for order creation');
      }

      // Add a small delay to show the loading state
      await new Promise(resolve => setTimeout(resolve, 500));

    } catch (error) {
      console.error('❌ Error during flight selection:', error);

      // Show user-friendly error message
      const errorMessage = error instanceof Error ? error.message : 'Failed to get flight pricing';
      alert(`Unable to select flight: ${errorMessage}. Please try again or select a different flight.`);

      setIsSelecting(false);
      return; // Don't navigate if there's an error
    } finally {
      setIsSelecting(false);
    }
  };

  // Build query string with search parameters
  const buildFlightUrl = () => {
    const params = new URLSearchParams({ from: 'search' });

    if (searchParams) {
      if (searchParams.adults) params.set('adults', searchParams.adults.toString());
      if (searchParams.children) params.set('children', searchParams.children.toString());
      if (searchParams.infants) params.set('infants', searchParams.infants.toString());
      if (searchParams.tripType) params.set('tripType', searchParams.tripType);
      if (searchParams.origin) params.set('origin', searchParams.origin);
      if (searchParams.destination) params.set('destination', searchParams.destination);
      if (searchParams.departDate) params.set('departDate', searchParams.departDate);
      if (searchParams.returnDate) params.set('returnDate', searchParams.returnDate);
      if (searchParams.cabinClass) params.set('cabinClass', searchParams.cabinClass);
    }

    if (!flight.id) {
      return '/flights/error';
    }

    return `/flights/${encodeURIComponent(flight.id)}?${params.toString()}`;
  }
  const [expanded, setExpanded] = useState(showExtendedDetails)

  useEffect(() => {
  }, [flight]);

  // Note: Data formatting is now handled by the backend
  // Frontend components should use FlightOffer data directly

  return (
    <Card className="overflow-hidden transition-all hover:shadow-md">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto]">
          {/* Flight Details */}
          <div className="p-4 md:p-6">
            <div className="mb-4 flex items-center">
              <div className="flex items-center">
                <Image
                  src={flight.airline?.logo || "/placeholder-logo.svg"}
                  alt={flight.airline?.name || "Airline"}
                  width={32}
                  height={32}
                  className="mr-3 rounded"
                />
                <div>
                  <div className="font-semibold text-sm">{flight.airline?.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {flight.segments?.map((segment, index) => (
                      <span key={`flight-${flight.id}-segment-${index}-${segment.airline?.flightNumber || 'unknown'}`}>
                        {segment.airline?.flightNumber}
                        {index < (flight.segments?.length || 0) - 1 && ", "}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {flight.fare?.fareFamily && (
                <Badge variant="secondary" className="ml-auto">
                  {flight.fare.fareFamily}
                </Badge>
              )}
              {searchParams?.tripType === 'round-trip' && (
                <Badge variant="outline" className="ml-2">
                  Round Trip
                </Badge>
              )}
            </div>

            {/* Route and Time */}
            <div className="mb-4">
              {searchParams?.tripType === 'round-trip' ? (
                // Round-trip display: show both outbound and return journeys
                (() => {
                  const segments = flight.segments || [];

                  // Determine outbound and return segments
                  let outboundSegments: any[] = [];
                  let returnSegments: any[] = [];

                  if (segments.length > 0) {
                    // Find the turnaround point (where we reach the destination)
                    const searchDestination = searchParams?.destination || '';
                    let turnaroundIndex = -1;

                    // Look for the first occurrence of the destination airport
                    for (let i = 0; i < segments.length; i++) {
                      if (segments[i].arrival?.airport === searchDestination) {
                        turnaroundIndex = i;
                        break;
                      }
                    }

                    if (turnaroundIndex > -1) {
                      outboundSegments = segments.slice(0, turnaroundIndex + 1);
                      returnSegments = segments.slice(turnaroundIndex + 1);
                    } else {
                      // Fallback: split in half
                      const midPoint = Math.ceil(segments.length / 2);
                      outboundSegments = segments.slice(0, midPoint);
                      returnSegments = segments.slice(midPoint);
                    }
                  }

                  // Outbound journey details
                  const outboundOrigin = outboundSegments[0]?.departure?.airport || searchParams?.origin || '';
                  const outboundDestination = outboundSegments[outboundSegments.length - 1]?.arrival?.airport || searchParams?.destination || '';
                  const outboundDepartureTime = outboundSegments[0]?.departure?.time || '--:--';
                  const outboundArrivalTime = outboundSegments[outboundSegments.length - 1]?.arrival?.time || '--:--';
                  const outboundStops = outboundSegments.length > 1 ? outboundSegments.length - 1 : 0;

                  // Return journey details
                  const returnOrigin = returnSegments[0]?.departure?.airport || searchParams?.destination || '';
                  const returnDestination = returnSegments[returnSegments.length - 1]?.arrival?.airport || searchParams?.origin || '';
                  const returnDepartureTime = returnSegments[0]?.departure?.time || '--:--';
                  const returnArrivalTime = returnSegments[returnSegments.length - 1]?.arrival?.time || '--:--';
                  const returnStops = returnSegments.length > 1 ? returnSegments.length - 1 : 0;

                  return (
                    <div className="space-y-4">
                      {/* Outbound Journey */}
                      <div className="flex items-center justify-between">
                        <div className="text-center">
                          <div className="text-xl font-bold">
                            {outboundDepartureTime}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {outboundOrigin}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Departure
                          </div>
                        </div>

                        <div className="flex flex-col items-center px-4">
                          <div className="text-xs text-muted-foreground mb-1">
                            Outbound
                          </div>
                          <div className="flex items-center">
                            <div className="h-px bg-border flex-1 w-12"></div>
                            <ArrowRight className="mx-2 h-3 w-3 text-muted-foreground" />
                            <div className="h-px bg-border flex-1 w-12"></div>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {outboundStops > 0 ? `${outboundStops} stop${outboundStops > 1 ? 's' : ''}` : 'Direct'}
                          </div>
                        </div>

                        <div className="text-center">
                          <div className="text-xl font-bold">
                            {outboundArrivalTime}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {outboundDestination}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Arrival
                          </div>
                        </div>
                      </div>

                      {/* Return Journey */}
                      {returnSegments.length > 0 && (
                        <div className="flex items-center justify-between border-t pt-3">
                          <div className="text-center">
                            <div className="text-xl font-bold">
                              {returnDepartureTime}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {returnOrigin}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Departure
                            </div>
                          </div>

                          <div className="flex flex-col items-center px-4">
                            <div className="text-xs text-muted-foreground mb-1">
                              Return
                            </div>
                            <div className="flex items-center">
                              <div className="h-px bg-border flex-1 w-12"></div>
                              <ArrowRight className="mx-2 h-3 w-3 text-muted-foreground" />
                              <div className="h-px bg-border flex-1 w-12"></div>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {returnStops > 0 ? `${returnStops} stop${returnStops > 1 ? 's' : ''}` : 'Direct'}
                            </div>
                          </div>

                          <div className="text-center">
                            <div className="text-xl font-bold">
                              {returnArrivalTime}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {returnDestination}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Arrival
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })()
              ) : (
                // One-way display: show user's searched route
                (() => {
                  // Use route_display if available, otherwise fallback to segment logic
                  const routeDisplay = flight.route_display;
                  const useSearchRoute = routeDisplay && searchParams?.origin && searchParams?.destination;

                  let originAirport: string, destinationAirport: string, originTime: string, destinationTime: string, stopInfo: string;

                  if (useSearchRoute) {
                    // Use search parameters as authoritative source
                    originAirport = searchParams.origin || '';
                    destinationAirport = searchParams.destination || '';

                    // Find corresponding segment times
                    const firstSegment = flight.segments?.find(seg => seg.departure?.airport === originAirport);
                    const lastSegment = flight.segments?.find(seg => seg.arrival?.airport === destinationAirport);

                    originTime = firstSegment?.departure?.time || '--:--';
                    destinationTime = lastSegment?.arrival?.time || '--:--';

                    // Show stops information
                    const stops = routeDisplay.stops || [];
                    stopInfo = stops.length > 0 ? `${stops.length} stop${stops.length > 1 ? 's' : ''} (via ${stops.join(', ')})` : 'Direct';
                  } else {
                    // Fallback to original segment logic
                    originAirport = flight.segments?.[0]?.departure?.airport || '';
                    destinationAirport = flight.segments?.[flight.segments.length - 1]?.arrival?.airport || '';
                    originTime = flight.segments?.[0]?.departure?.time || '--:--';
                    destinationTime = flight.segments?.[flight.segments.length - 1]?.arrival?.time || '--:--';
                    stopInfo = flight.segments && flight.segments.length > 1 ? `${flight.segments.length - 1} stop${flight.segments.length > 2 ? 's' : ''}` : 'Direct';
                  }

                  return (
                    <div className="flex items-center justify-between">
                      <div className="text-center">
                        <div className="text-2xl font-bold">
                          {originTime}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {originAirport}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {useSearchRoute ? 'Origin' : 'Departure'}
                        </div>
                      </div>

                      <div className="flex flex-col items-center px-4">
                        <div className="text-xs text-muted-foreground mb-1">
                          {flight.duration}
                        </div>
                        <div className="flex items-center">
                          <div className="h-px bg-border flex-1 w-16"></div>
                          <ArrowRight className="mx-2 h-4 w-4 text-muted-foreground" />
                          <div className="h-px bg-border flex-1 w-16"></div>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {stopInfo}
                        </div>
                      </div>

                      <div className="text-center">
                        <div className="text-2xl font-bold">
                          {destinationTime}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {destinationAirport}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {useSearchRoute ? 'Destination' : 'Arrival'}
                        </div>
                      </div>
                    </div>
                  );
                })()
              )}
            </div>


            {/* Expandable Details */}
            {expanded && (
              <div className="space-y-4">
                <Separator />

                <Tabs defaultValue="segments" className="w-full">
                  <TabsList className="grid w-full grid-cols-1">
                    <TabsTrigger value="segments">Flight Details</TabsTrigger>
                  </TabsList>

                  <TabsContent value="segments" className="space-y-4">
                    {searchParams?.tripType === 'round-trip' ? (
                      // Round-trip: Group segments by outbound and return
                      (() => {
                        const segments = flight.segments || [];

                        // Determine outbound and return segments (same logic as above)
                        let outboundSegments: any[] = [];
                        let returnSegments: any[] = [];

                        if (segments.length > 0) {
                          const searchDestination = searchParams?.destination || '';
                          let turnaroundIndex = -1;

                          for (let i = 0; i < segments.length; i++) {
                            if (segments[i].arrival?.airport === searchDestination) {
                              turnaroundIndex = i;
                              break;
                            }
                          }

                          if (turnaroundIndex > -1) {
                            outboundSegments = segments.slice(0, turnaroundIndex + 1);
                            returnSegments = segments.slice(turnaroundIndex + 1);
                          } else {
                            const midPoint = Math.ceil(segments.length / 2);
                            outboundSegments = segments.slice(0, midPoint);
                            returnSegments = segments.slice(midPoint);
                          }
                        }

                        return (
                          <div className="space-y-6">
                            {/* Outbound Segments */}
                            {outboundSegments.length > 0 && (
                              <div>
                                <h4 className="font-semibold text-sm text-muted-foreground mb-3 flex items-center">
                                  <ArrowRight className="w-4 h-4 mr-2" />
                                  Outbound Journey
                                </h4>
                                <div className="space-y-3">
                                  {outboundSegments.map((segment, index) => (
                                    <div key={`outbound-${index}-${segment.airline?.flightNumber}`} className="border rounded-lg p-4">
                                      <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center">
                                          <Image
                                            src={flight.airline?.logo || "/airlines/default.svg"}
                                            alt={segment.airline?.name || flight.airline?.name || "Airline"}
                                            width={24}
                                            height={24}
                                            className="mr-2 rounded"
                                          />
                                          <span className="font-medium">{segment.airline?.name}</span>
                                        </div>
                                        <Badge variant="outline">{segment.airline?.flightNumber}</Badge>
                                      </div>

                                      <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                          <div className="font-medium">Departure</div>
                                          <div className="text-lg font-semibold">{segment.departure?.time || '--:--'}</div>
                                          <div className="text-xs text-muted-foreground">
                                            {segment.departure?.datetime ? new Date(segment.departure.datetime).toLocaleDateString() : ''}
                                          </div>
                                          <div className="text-muted-foreground">
                                            {segment.departure?.airportName || segment.departure?.airport || 'Unknown'} ({segment.departure?.airport})
                                          </div>
                                          {segment.departure?.terminal && (
                                            <div className="text-xs text-muted-foreground">Terminal {segment.departure.terminal}</div>
                                          )}
                                        </div>
                                        <div>
                                          <div className="font-medium">Arrival</div>
                                          <div className="text-lg font-semibold">{segment.arrival?.time || '--:--'}</div>
                                          <div className="text-xs text-muted-foreground">
                                            {segment.arrival?.datetime ? new Date(segment.arrival.datetime).toLocaleDateString() : ''}
                                          </div>
                                          <div className="text-muted-foreground">
                                            {segment.arrival?.airportName || segment.arrival?.airport || 'Unknown'} ({segment.arrival?.airport})
                                          </div>
                                          {segment.arrival?.terminal && (
                                            <div className="text-xs text-muted-foreground">Terminal {segment.arrival.terminal}</div>
                                          )}
                                        </div>
                                      </div>

                                      <div className="mt-2 text-sm text-muted-foreground">
                                        Duration: {segment.duration && segment.duration !== 'Unknown' ? segment.duration : 'Not available'}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Return Segments */}
                            {returnSegments.length > 0 && (
                              <div>
                                <h4 className="font-semibold text-sm text-muted-foreground mb-3 flex items-center">
                                  <ArrowRight className="w-4 h-4 mr-2 rotate-180" />
                                  Return Journey
                                </h4>
                                <div className="space-y-3">
                                  {returnSegments.map((segment, index) => (
                                    <div key={`return-${index}-${segment.airline?.flightNumber}`} className="border rounded-lg p-4">
                                      <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center">
                                          <Image
                                            src={flight.airline?.logo || "/airlines/default.svg"}
                                            alt={segment.airline?.name || flight.airline?.name || "Airline"}
                                            width={24}
                                            height={24}
                                            className="mr-2 rounded"
                                          />
                                          <span className="font-medium">{segment.airline?.name}</span>
                                        </div>
                                        <Badge variant="outline">{segment.airline?.flightNumber}</Badge>
                                      </div>

                                      <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                          <div className="font-medium">Departure</div>
                                          <div className="text-lg font-semibold">{segment.departure?.time || '--:--'}</div>
                                          <div className="text-xs text-muted-foreground">
                                            {segment.departure?.datetime ? new Date(segment.departure.datetime).toLocaleDateString() : ''}
                                          </div>
                                          <div className="text-muted-foreground">
                                            {segment.departure?.airportName || segment.departure?.airport || 'Unknown'} ({segment.departure?.airport})
                                          </div>
                                          {segment.departure?.terminal && (
                                            <div className="text-xs text-muted-foreground">Terminal {segment.departure.terminal}</div>
                                          )}
                                        </div>
                                        <div>
                                          <div className="font-medium">Arrival</div>
                                          <div className="text-lg font-semibold">{segment.arrival?.time || '--:--'}</div>
                                          <div className="text-xs text-muted-foreground">
                                            {segment.arrival?.datetime ? new Date(segment.arrival.datetime).toLocaleDateString() : ''}
                                          </div>
                                          <div className="text-muted-foreground">
                                            {segment.arrival?.airportName || segment.arrival?.airport || 'Unknown'} ({segment.arrival?.airport})
                                          </div>
                                          {segment.arrival?.terminal && (
                                            <div className="text-xs text-muted-foreground">Terminal {segment.arrival.terminal}</div>
                                          )}
                                        </div>
                                      </div>

                                      <div className="mt-2 text-sm text-muted-foreground">
                                        Duration: {segment.duration && segment.duration !== 'Unknown' ? segment.duration : 'Not available'}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })()
                    ) : (
                      // One-way: Show all segments in sequence
                      flight.segments?.map((segment, index) => (
                        <div key={`flight-${flight.id}-detail-segment-${index}-${segment.airline?.flightNumber || 'unknown'}-${segment.departure?.airport || 'unknown'}`} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center">
                              <Image
                                src={flight.airline?.logo || "/airlines/default.svg"}
                                alt={segment.airline?.name || flight.airline?.name || "Airline"}
                                width={24}
                                height={24}
                                className="mr-2 rounded"
                              />
                              <span className="font-medium">{segment.airline?.flightNumber}</span>
                            </div>
                            <Badge variant="outline">{segment.aircraft?.name || segment.aircraft?.code}</Badge>
                          </div>

                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <div className="font-medium">Departure</div>
                              <div className="text-lg font-semibold">{segment.departure?.time || '--:--'}</div>
                              <div className="text-xs text-muted-foreground">
                                {segment.departure?.datetime ? new Date(segment.departure.datetime).toLocaleDateString() : ''}
                              </div>
                              <div className="text-muted-foreground">
                                {segment.departure?.airportName || segment.departure?.airport || 'Unknown'} ({segment.departure?.airport})
                              </div>
                              {segment.departure?.terminal && (
                                <div className="text-xs text-muted-foreground">Terminal {segment.departure.terminal}</div>
                              )}
                            </div>
                            <div>
                              <div className="font-medium">Arrival</div>
                              <div className="text-lg font-semibold">{segment.arrival?.time || '--:--'}</div>
                              <div className="text-xs text-muted-foreground">
                                {segment.arrival?.datetime ? new Date(segment.arrival.datetime).toLocaleDateString() : ''}
                              </div>
                              <div className="text-muted-foreground">
                                {segment.arrival?.airportName || segment.arrival?.airport || 'Unknown'} ({segment.arrival?.airport})
                              </div>
                              {segment.arrival?.terminal && (
                                <div className="text-xs text-muted-foreground">Terminal {segment.arrival.terminal}</div>
                              )}
                            </div>
                          </div>

                          <div className="mt-2 text-sm text-muted-foreground">
                            Duration: {segment.duration && segment.duration !== 'Unknown' ? segment.duration : 'Not available'}
                          </div>
                        </div>
                      ))
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            )}

            {/* Toggle Button */}
            <div className="mt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
                className="w-full"
              >
                {expanded ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-2" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-2" />
                    Show More Details
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Price and Book Button */}
          <div className="bg-muted/50 p-4 md:p-6 flex flex-col justify-between min-w-[200px]">
            <div className="text-center mb-4">
              <div className="text-2xl font-bold">
                {flight.currency} {flight.price}
              </div>
              <div className="text-sm text-muted-foreground">
                for all passengers
              </div>
            </div>

            <Link href={buildFlightUrl()} className="w-full">
              <LoadingButton
                className="w-full"
                onClick={handleFlightSelect}
                loading={isSelecting}
                loadingText="Selecting..."
              >
                Select Flight
              </LoadingButton>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
