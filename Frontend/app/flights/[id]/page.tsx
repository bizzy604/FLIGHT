'use client'

import { useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"
import { useSearchParams, useParams } from "next/navigation"
import { api } from "@/utils/api-client"
import { Separator } from "@/components/ui/separator"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { FlightDetailsHeader } from "@/components/flight-details-header"
import { EnhancedFlightCard } from "@/components/enhanced-flight-card"
import { BookingForm } from "@/components/booking-form"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import type { FlightOffer } from "@/types/flight-api"
import { AlertCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function FlightDetailsPage() {
  const searchParams = useSearchParams()
  const params = useParams()
  const flightId = decodeURIComponent(params.id as string)
  
  // Get trip type from search parameters
  const tripType = searchParams.get('tripType') || 'one-way'
  
  // State management
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [flightOffer, setFlightOffer] = useState<any>(null)
  const [returnFlightOffer, setReturnFlightOffer] = useState<any>(null)
  const [pricedOffer, setPricedOffer] = useState<any>(null)
  const [airShoppingResponse, setAirShoppingResponse] = useState<any>(null)

  useEffect(() => {
    // Function to fetch flight price
    const fetchFlightPrice = async () => {
      setIsLoading(true)
      setError(null)

      try {
        // Enhanced data retrieval with multiple fallback strategies
        let airShoppingResponseData = null;
        let flightDataSource = 'unknown';
        
        // Strategy 1: Try to get from new localStorage storage system
        try {
          const currentFlightDataKey = localStorage.getItem('currentFlightDataKey');
          if (currentFlightDataKey) {
            const storedFlightDataStr = localStorage.getItem(currentFlightDataKey);
            if (storedFlightDataStr) {
              const storedFlightData = JSON.parse(storedFlightDataStr);
              
              // Check if data is not expired
              if (storedFlightData.expiresAt && storedFlightData.expiresAt > Date.now()) {
                airShoppingResponseData = storedFlightData.airShoppingResponse;
                flightDataSource = 'localStorage-new';
                console.log('Flight data retrieved from new localStorage system');
              } else {
                console.log('Stored flight data has expired, removing...');
                localStorage.removeItem(currentFlightDataKey);
                localStorage.removeItem('currentFlightDataKey');
              }
            }
          }
        } catch (storageError) {
          console.warn('Failed to retrieve from new localStorage system:', storageError);
        }
        
        // Strategy 2: Fallback to URL parameters (legacy)
        if (!airShoppingResponseData) {
          const airShoppingResponseStr = searchParams.get('airShoppingResponse');
          if (airShoppingResponseStr) {
            airShoppingResponseData = JSON.parse(airShoppingResponseStr);
            flightDataSource = 'url-params';
            console.log('Flight data retrieved from URL parameters');
          }
        }
        
        // Strategy 3: Fallback to old localStorage (legacy)
        if (!airShoppingResponseData) {
          const legacyDataStr = localStorage.getItem('airShoppingResponse');
          if (legacyDataStr) {
            airShoppingResponseData = JSON.parse(legacyDataStr);
            flightDataSource = 'localStorage-legacy';
            console.log('Flight data retrieved from legacy localStorage');
          }
        }
        
        // Strategy 4: Try to find any flightData_ keys in localStorage
        if (!airShoppingResponseData) {
          const flightDataKeys = Object.keys(localStorage).filter(key => key.startsWith('flightData_'));
          for (const key of flightDataKeys) {
            try {
              const data = JSON.parse(localStorage.getItem(key) || '{}');
              if (data.airShoppingResponse && data.expiresAt && data.expiresAt > Date.now()) {
                airShoppingResponseData = data.airShoppingResponse;
                flightDataSource = 'localStorage-search';
                console.log('Flight data retrieved from localStorage search:', key);
                break;
              }
            } catch (e) {
              // Remove corrupted data
              localStorage.removeItem(key);
            }
          }
        }
        
        if (!airShoppingResponseData) {
          throw new Error("No flight search data found. Please go back to search results and try again.")
        }
        
        console.log('Flight data source:', flightDataSource);
        console.log('airShoppingResponseData structure:', {
          hasData: !!airShoppingResponseData.data,
          dataKeys: airShoppingResponseData.data ? Object.keys(airShoppingResponseData.data) : [],
          hasNestedData: !!(airShoppingResponseData.data && airShoppingResponseData.data.data),
          nestedDataKeys: (airShoppingResponseData.data && airShoppingResponseData.data.data) ? Object.keys(airShoppingResponseData.data.data) : []
        });
        
        setAirShoppingResponse(airShoppingResponseData)

        // Find the offers array - handle multiple possible structures
        let offers = null;
        if (airShoppingResponseData.data && airShoppingResponseData.data.data && airShoppingResponseData.data.data.offers) {
          // Triple nested structure: response.data.data.data.offers
          offers = airShoppingResponseData.data.data.offers;
          console.log('Using triple nested structure, found', offers.length, 'offers');
        } else if (airShoppingResponseData.data && airShoppingResponseData.data.offers) {
          // Double nested structure: response.data.data.offers
          offers = airShoppingResponseData.data.offers;
          console.log('Using double nested structure, found', offers.length, 'offers');
        } else if (Array.isArray(airShoppingResponseData.offers)) {
          // Direct offers array: response.offers
          offers = airShoppingResponseData.offers;
          console.log('Using direct offers array, found', offers.length, 'offers');
        }

        if (!offers || !Array.isArray(offers)) {
          throw new Error(`airShoppingResponseData.data.offers is undefined. Available structure: ${JSON.stringify({
            hasData: !!airShoppingResponseData.data,
            dataKeys: airShoppingResponseData.data ? Object.keys(airShoppingResponseData.data) : [],
            hasNestedData: !!(airShoppingResponseData.data && airShoppingResponseData.data.data),
            nestedDataKeys: (airShoppingResponseData.data && airShoppingResponseData.data.data) ? Object.keys(airShoppingResponseData.data.data) : []
          }, null, 2)}`);
        }

        // Find the selected offer by ID
        const selectedOffer = offers.find(
          (offer: any) => offer.id === flightId
        );

        if (!selectedOffer) {
          throw new Error(`Selected flight offer not found. Available offer IDs: ${offers.map((o: any) => o.id).join(', ')}`);
        }

        setFlightOffer(selectedOffer)

        // Handle return flight for round-trip
        if (tripType === 'round-trip' && offers.length > 1) {
          // Find return flight by looking for corresponding return ID or by direction
          let returnOffer;
          
          // Current selectedOffer.id might be BASE_ID, BASE_ID_outbound, or BASE_ID_return
          // We need the base ID to find its counterpart
          const baseOfferId = selectedOffer.id.replace('_outbound', '').replace('_return', '');
          
          // First try to find return flight by replacing 'outbound' with 'return' in the ID or vice-versa
          // This logic needs to handle if selectedOffer.id is already a return or an outbound flight
          if (selectedOffer.id.includes('_outbound')) {
            const potentialReturnId = selectedOffer.id.replace('_outbound', '_return');
            returnOffer = offers.find((offer: any) => offer.id === potentialReturnId);
          } else if (selectedOffer.id.includes('_return')) {
            // If the selected offer is already a return, this logic might be for finding its outbound pair if needed
            // For now, let's assume we are primarily looking for the return flight if selected is outbound
          } else {
            // If selectedOffer.id is a base ID (no suffix), look for its suffixed counterparts
            const potentialReturnId = `${baseOfferId}_return`;
            returnOffer = offers.find((offer: any) => offer.id === potentialReturnId);
          }
          
          // If not found by direct ID manipulation, try to find by direction or other criteria
          if (!returnOffer) {
            returnOffer = offers.find(
              (offer: any) => offer.id !== flightId && (
                offer.direction === 'return' || 
                offer.segments?.some((seg: any) => seg.direction === 'return') ||
                offer.id.includes('-return')
              )
            ) || offers[1]; // Fallback to second offer
          }
          
          if (returnOffer) {
            console.log('[DEBUG] Return flight offer found:', returnOffer);
            console.log('[DEBUG] Return flight segments:', returnOffer.segments);
            setReturnFlightOffer(returnOffer)
          } else {
            console.log('[DEBUG] No return flight offer found. Available offers:', offers.map(o => ({ id: o.id, direction: o.direction })));
          }
        }

        // Find shopping_response_id - handle multiple possible structures
        let shoppingResponseId = null;
        let airShoppingRsData = null;

        // Based on the data structure, check all possible locations
        // The data is stored as airShoppingResponse: apiResponse where apiResponse = response.data
        // So the actual shopping_response_id is in airShoppingResponseData.data.data.shopping_response_id
        if (airShoppingResponseData.data?.data?.data?.shopping_response_id) {
          shoppingResponseId = airShoppingResponseData.data.data.data.shopping_response_id;
          airShoppingRsData = airShoppingResponseData.data.data.data;
          console.log('Found shopping_response_id in triple nested structure');
        } else if (airShoppingResponseData.data?.data?.shopping_response_id) {
          shoppingResponseId = airShoppingResponseData.data.data.shopping_response_id;
          airShoppingRsData = airShoppingResponseData.data.data;
          console.log('Found shopping_response_id in double nested structure');
        } else if (airShoppingResponseData.data?.shopping_response_id) {
          shoppingResponseId = airShoppingResponseData.data.shopping_response_id;
          airShoppingRsData = airShoppingResponseData.data;
          console.log('Found shopping_response_id in single nested structure');
        } else if (airShoppingResponseData.shopping_response_id) {
          shoppingResponseId = airShoppingResponseData.shopping_response_id;
          airShoppingRsData = airShoppingResponseData;
          console.log('Found shopping_response_id in direct structure');
        }
        
        console.log('Shopping response ID found:', shoppingResponseId);
        console.log('Air shopping RS data keys:', airShoppingRsData ? Object.keys(airShoppingRsData) : 'null');
        
        if (!shoppingResponseId) {
          throw new Error(`Shopping response ID not found. Available data structure: ${JSON.stringify({
            hasData: !!airShoppingResponseData.data,
            dataKeys: airShoppingResponseData.data ? Object.keys(airShoppingResponseData.data) : [],
            hasNestedData: !!(airShoppingResponseData.data && airShoppingResponseData.data.data),
            nestedDataKeys: (airShoppingResponseData.data && airShoppingResponseData.data.data) ? Object.keys(airShoppingResponseData.data.data) : [],
            directKeys: Object.keys(airShoppingResponseData)
          }, null, 2)}`);
        }
        
        // Log the data we're sending to the API
        console.log('Sending to flight-price API:', {
          offerId: selectedOffer.id,
          shoppingResponseId,
          hasAirShoppingRsData: !!airShoppingRsData,
          airShoppingRsDataKeys: airShoppingRsData ? Object.keys(airShoppingRsData) : []
        });
        
        // Call the flight-price API endpoint with the complete air shopping response
        const response = await api.getFlightPrice(
          selectedOffer.id,
          shoppingResponseId,
          airShoppingResponseData // Pass the complete response data
        )
        
        // Set the priced offer data
        setPricedOffer(response.data)
        
        // Store the raw flight price response for backend order creation
        // Backend expects the raw response to bypass cache issues
        const dataToStore = {
          ...response.data,
          raw_response: response.data.raw_response || response.data,
          data: {
            raw_response: response.data.raw_response || response.data
          }
        }
        
        sessionStorage.setItem('selectedFlightOffer', JSON.stringify(dataToStore))
        console.log('[[ DEBUG ]] Stored flight data with raw response:', {
          hasRawResponse: !!(response.data.raw_response || response.data),
          dataStructure: Object.keys(dataToStore),
          rawResponseKeys: response.data.raw_response ? Object.keys(response.data.raw_response) : 'Using response.data as fallback'
        })
      } catch (err) {
        console.error("Error fetching flight price:", err)
        setError(err instanceof Error ? err.message : "Failed to fetch flight price data")
      } finally {
        setIsLoading(false)
      }
    }

    fetchFlightPrice()
  }, [flightId]) // Removed searchParams to prevent duplicate calls on URL parameter changes

  // Note: Date formatting is now handled by the backend
  // Frontend should display dates directly from FlightOffer interface

  // Show loading state
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
          <div className="container py-6">
            <div className="mb-6">
              <Link
                href="/flights"
                className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Back to Search Results
              </Link>
            </div>
            
            <div className="flex flex-col items-center justify-center space-y-4 py-12">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <p className="text-lg font-medium">Loading flight pricing details...</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // Show error state
  if (error) {
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
                href="/flights"
                className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Back to Search Results
              </Link>
            </div>
            
            <Alert variant="destructive" className="my-8">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Flight Data Not Found</AlertTitle>
              <AlertDescription>
                {error}
                <br /><br />
                This usually happens when:
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>You navigated directly to this page without searching for flights first</li>
                  <li>Your flight search data has expired (older than 24 hours)</li>
                  <li>Your browser storage was cleared</li>
                </ul>
              </AlertDescription>
            </Alert>
            
            <div className="space-y-4">
              <Button asChild>
                <Link href="/">Start New Flight Search</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/flights">Back to Search Results</Link>
              </Button>
            </div>
          </div>
        </main>
      </div>
    )
  }
  console.log(pricedOffer)

  // If we have flight data, render the flight details
  if (pricedOffer) {
    // Price data from priced offer or fallback to flight offer
    // Note: pricedOffer is already the data from response.data, so no need for .data
    const totalPrice = pricedOffer?.data?.priced_offers?.[0]?.pricing?.total_price || flightOffer.price || 0
    const currency = pricedOffer?.data?.priced_offers?.[0]?.pricing?.currency || flightOffer.currency || "USD"
    const taxes = pricedOffer?.data?.priced_offers?.[0]?.pricing?.taxes_per_traveler || flightOffer.priceBreakdown?.taxes || 0
    const baseFare = pricedOffer?.data?.priced_offers?.[0]?.pricing?.base_fare_per_traveler || flightOffer.priceBreakdown?.baseFare || (totalPrice - taxes)
    
    // Extract penalties from the API response data
    const penalties = pricedOffer?.data?.priced_offers?.[0]?.penalties || null
    
    // Format flight data for the components using the actual API response structure
    const formattedFlight: FlightOffer = {
      id: flightOffer.id,
      airline: {
        name: flightOffer.airline?.name || "Unknown Airline",
        logo: flightOffer.airline?.logo || "/placeholder.svg?height=40&width=40",
        code: flightOffer.airline?.code || "",
        flightNumber: flightOffer.airline?.flightNumber || "",
      },
      departure: {
        airport: flightOffer.departure?.airport || "",
        datetime: flightOffer.departure?.datetime || "",
        time: flightOffer.departure?.time || "",
        terminal: flightOffer.departure?.terminal || "",
        airportName: flightOffer.departure?.airportName || "",
      },
      arrival: {
        airport: flightOffer.arrival?.airport || "",
        datetime: flightOffer.arrival?.datetime || "",
        time: flightOffer.arrival?.time || "",
        terminal: flightOffer.arrival?.terminal || "",
        airportName: flightOffer.arrival?.airportName || "",
      },
      duration: flightOffer.duration && flightOffer.duration !== "0h 0m" 
        ? flightOffer.duration 
        : flightOffer.segments?.reduce((total: number, segment: any) => {
            if (segment.duration && segment.duration.startsWith('PT')) {
              // Parse ISO 8601 duration format (PT1H15M)
              const hours = segment.duration.match(/PT(\d+)H/) ? parseInt(segment.duration.match(/PT(\d+)H/)![1]) : 0;
              const minutes = segment.duration.match(/(\d+)M/) ? parseInt(segment.duration.match(/(\d+)M/)![1]) : 0;
              return total + (hours * 60) + minutes;
            }
            return total;
          }, 0) ? (() => {
            const totalMinutes = flightOffer.segments?.reduce((total: number, segment: any) => {
              if (segment.duration && segment.duration.startsWith('PT')) {
                const hours = segment.duration.match(/PT(\d+)H/) ? parseInt(segment.duration.match(/PT(\d+)H/)![1]) : 0;
                const minutes = segment.duration.match(/(\d+)M/) ? parseInt(segment.duration.match(/(\d+)M/)![1]) : 0;
                return total + (hours * 60) + minutes;
              }
              return total;
            }, 0) || 0;
            const hours = Math.floor(totalMinutes / 60);
            const mins = totalMinutes % 60;
            return `${hours}h ${mins}m`;
          })() : "0h 0m",
      stops: flightOffer.segments?.length > 1 ? flightOffer.segments.length - 1 : 0,
      stopDetails: flightOffer.stopDetails || [],
      price: totalPrice,
      currency: currency,
      baggage: {
        carryOn: { 
          description: flightOffer.baggage?.carryOn || "Not specified"
        },
        checkedBaggage: { 
          description: flightOffer.baggage?.checked || "Not specified",
          policyType: 'WEIGHT_BASED' as const
        }
      },
      fare: flightOffer.fare,
      aircraft: flightOffer.aircraft,
      segments: flightOffer.segments?.map((segment: any) => ({
        ...segment,
        airlineName: flightOffer.airline?.name || segment.airlineName || "Unknown Airline"
      })) || [],
      priceBreakdown: flightOffer.priceBreakdown,
      additionalServices: flightOffer.additionalServices,
      fareRules: flightOffer.fareRules,
      penalties: flightOffer.penalties,
      fareDescription: flightOffer.fareDescription,
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
                href="/flights"
                className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Back to Search Results
              </Link>

              <FlightDetailsHeader
                origin={formattedFlight.departure.airportName || ''}
                originCode={formattedFlight.departure.airport || ''}
                destination={formattedFlight.arrival.airportName || ''}
                destinationCode={formattedFlight.arrival.airport || ''}
                departDate={formattedFlight.departure.datetime}
                returnDate={returnFlightOffer?.departure?.datetime}
                adults={Number(searchParams.get('adults')) || 1}
                children={Number(searchParams.get('children')) || 0}
                infants={Number(searchParams.get('infants')) || 0}
                price={totalPrice}
                currency={formattedFlight.currency}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
              {/* Flight Details and Booking Form */}
              <div className="space-y-6">
                {/* Dynamic flight display based on trip type */}
                {tripType === 'one-way' && (
                  <div className="rounded-lg border">
                    <div className="p-4 sm:p-6">
                      <h2 className="text-xl font-semibold">Flight Details</h2>
                      <p className="text-sm text-muted-foreground">{formattedFlight.departure.datetime}</p>
                    </div>
                    <Separator />
                    <EnhancedFlightCard flight={formattedFlight} />
                  </div>
                )}

                {tripType === 'round-trip' && (
                  <>
                    <div className="rounded-lg border">
                      <div className="p-4 sm:p-6">
                        <h2 className="text-xl font-semibold">Outbound Flight</h2>
                        <p className="text-sm text-muted-foreground">{formattedFlight.departure.datetime}</p>
                      </div>
                      <Separator />
                      <EnhancedFlightCard flight={formattedFlight} />
                    </div>

                    {returnFlightOffer && (
                      <div className="rounded-lg border">
                        <div className="p-4 sm:p-6">
                          <h2 className="text-xl font-semibold">Return Flight</h2>
                          <p className="text-sm text-muted-foreground">{returnFlightOffer.departure?.datetime}</p>
                        </div>
                        <Separator />
                        <EnhancedFlightCard
                          flight={{
                            ...returnFlightOffer,
                            stopDetails: returnFlightOffer.stopDetails || [],
                            baggage: returnFlightOffer.baggage || {
                              carryOn: { description: "Not specified" },
                              checkedBaggage: { description: "Not specified" }
                            },
                            fareRules: returnFlightOffer.fareRules,
                            penalties: returnFlightOffer.penalties,
                            fareDescription: returnFlightOffer.fareDescription,
                          } as FlightOffer}
                        />
                      </div>
                    )}
                  </>
                )}

                {tripType === 'multi-city' && (
                  <div className="space-y-4">
                    <div className="rounded-lg border">
                      <div className="p-4 sm:p-6">
                        <h2 className="text-xl font-semibold">Flight Segment 1</h2>
                        <p className="text-sm text-muted-foreground">{formattedFlight.departure.datetime}</p>
                      </div>
                      <Separator />
                      <EnhancedFlightCard flight={formattedFlight} />
                    </div>
                    {/* Additional segments would be rendered here based on the flight data */}
                  </div>
                )}

                <BookingForm 
                  adults={Number(searchParams.get('adults')) || 1}
                  children={Number(searchParams.get('children')) || 0}
                  infants={Number(searchParams.get('infants')) || 0}
                />
              </div>

              {/* Price Summary */}
              <div className="h-fit rounded-lg border">
                <div className="p-4 sm:p-6">
                  <h2 className="text-xl font-semibold">Price Summary</h2>
                </div>
                <Separator />
                <div className="p-4 sm:p-6">
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Base fare ({airShoppingResponse?.data?.data?.travelers?.length || 1} {airShoppingResponse?.data?.data?.travelers?.length === 1 ? 'passenger' : 'passengers'})</span>
                      <span>{baseFare.toFixed(2)} {currency}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Taxes and fees</span>
                      <span>{taxes.toFixed(2)} {currency}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Baggage fees</span>
                      <span>Included</span>
                    </div>
                    
                    {/* Penalty Fees */}
                    {penalties && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium text-muted-foreground">Penalty Fees:</div>
                        {(penalties.change_fee_min > 0 || penalties.change_fee_max > 0) && (
                          <div className="flex justify-between text-sm">
                            <span>Change fee:</span>
                            <span>
                              {penalties.change_fee_min === penalties.change_fee_max 
                                ? `${penalties.change_fee_min} ${currency}`
                                : `${penalties.change_fee_min} - ${penalties.change_fee_max} ${currency}`
                              }
                            </span>
                          </div>
                        )}
                        {(penalties.cancel_fee_min > 0 || penalties.cancel_fee_max > 0) && (
                          <div className="flex justify-between text-sm">
                            <span>Cancel fee:</span>
                            <span>
                              {penalties.cancel_fee_min === penalties.cancel_fee_max 
                                ? `${penalties.cancel_fee_min} ${currency}`
                                : `${penalties.cancel_fee_min} - ${penalties.cancel_fee_max} ${currency}`
                              }
                            </span>
                          </div>
                        )}
                        {penalties.change_fee_min === 0 && penalties.change_fee_max === 0 && 
                         penalties.cancel_fee_min === 0 && penalties.cancel_fee_max === 0 && (
                          <div className="text-sm text-green-600">
                            <span>No penalty fees</span>
                          </div>
                        )}
                      </div>
                    )}
                    <Separator />
                    <div className="flex justify-between font-bold">
                      <span>Total</span>
                      <span>{totalPrice.toFixed(2)} {currency}</span>
                    </div>
                    
                    {/* Offer and Payment Expiry Times */}
                    <Separator />
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Offer expires:</span>
                        <span className="font-medium text-orange-600">
                          {pricedOffer?.data?.priced_offers?.[0]?.offer_expiration_utc 
                            ? new Date(pricedOffer.data.priced_offers[0].offer_expiration_utc).toLocaleString()
                            : "Not specified"
                          }
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Payment deadline:</span>
                        <span className="font-medium text-red-600">
                          {pricedOffer?.data?.priced_offers?.[0]?.payment_expiration_utc 
                            ? new Date(pricedOffer.data.priced_offers[0].payment_expiration_utc).toLocaleString()
                            : "Not specified"
                          }
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      <p>Fare rules:</p>
                      <ul className="mt-1 list-inside list-disc">
                        <li>{flightOffer?.fareRules?.refundable ? "Refundable" : "Non-refundable"}</li>
                        <li>Changes allowed (fee may apply)</li>
                        <li>Fare class: {flightOffer?.cabinType || "Economy"}</li>
                      </ul>
                      
                      {/* Debug: Always show penalties section for testing */}
                      <div className="mt-3 border border-red-200 p-2">
                        {penalties && (
                          <div className="mt-2">
                            <p className="font-medium">Penalty Fees:</p>
                            <div className="mt-1 space-y-1">
                              {(penalties.change_fee_min > 0 || penalties.change_fee_max > 0) && (
                                <div className="flex justify-between">
                                  <span>Change fee:</span>
                                  <span>
                                    {penalties.change_fee_min === penalties.change_fee_max 
                                      ? `${penalties.change_fee_min} ${currency}`
                                      : `${penalties.change_fee_min} - ${penalties.change_fee_max} ${currency}`
                                    }
                                  </span>
                                </div>
                              )}
                              {(penalties.cancel_fee_min > 0 || penalties.cancel_fee_max > 0) && (
                                <div className="flex justify-between">
                                  <span>Cancel fee:</span>
                                  <span>
                                    {penalties.cancel_fee_min === penalties.cancel_fee_max 
                                      ? `${penalties.cancel_fee_min} ${currency}`
                                      : `${penalties.cancel_fee_min} - ${penalties.cancel_fee_max} ${currency}`
                                  }
                                </span>
                              </div>
                            )}
                            {penalties.change_fee_min === 0 && penalties.change_fee_max === 0 && 
                             penalties.cancel_fee_min === 0 && penalties.cancel_fee_max === 0 && (
                              <div className="text-green-600">
                                <span>No penalty fees</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </main>
      </div>
    )
  }

  // Fallback if we somehow get here without data or errors
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
              href="/flights"
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Search Results
            </Link>
          </div>
          
          <Alert className="my-8">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>No flight data available</AlertTitle>
            <AlertDescription>
              Please return to the search results and select a flight.
            </AlertDescription>
          </Alert>
          
          <Button asChild>
            <Link href="/flights">Return to Flight Search</Link>
          </Button>
        </div>
      </main>
    </div>
  )
}
