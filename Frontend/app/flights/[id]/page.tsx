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
import { FlightDetailsCard } from "@/components/flight-details-card"
import { BookingForm } from "@/components/booking-form"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function FlightDetailsPage() {
  const searchParams = useSearchParams()
  const params = useParams()
  const flightId = params.id as string
  
  // State management
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [flightOffer, setFlightOffer] = useState<any>(null)
  const [pricedOffer, setPricedOffer] = useState<any>(null)
  const [airShoppingResponse, setAirShoppingResponse] = useState<any>(null)

  useEffect(() => {
    // Function to fetch flight price
    const fetchFlightPrice = async () => {
      setIsLoading(true)
      setError(null)

      try {
        // Get the air shopping response from URL state or localStorage
        const airShoppingResponseStr = searchParams.get('airShoppingResponse') || localStorage.getItem('airShoppingResponse')
        
        if (!airShoppingResponseStr) {
          throw new Error("No flight search data found. Please go back to search results.")
        }

        // Parse the air shopping response
        const airShoppingResponseData = JSON.parse(airShoppingResponseStr)
        setAirShoppingResponse(airShoppingResponseData)

        // Find the selected offer by ID
        const selectedOffer = airShoppingResponseData.data.offers.find(
          (offer: any) => offer.id === flightId
        )

        if (!selectedOffer) {
          throw new Error("Selected flight offer not found")
        }

        setFlightOffer(selectedOffer)

        // Call the flight-price API endpoint
        const response = await api.getFlightPrice(
          selectedOffer.id,
          airShoppingResponseData.data.shopping_response_id,
          airShoppingResponseData.data
        )

        // Set the priced offer data
        setPricedOffer(response.data)
      } catch (err) {
        console.error("Error fetching flight price:", err)
        setError(err instanceof Error ? err.message : "Failed to fetch flight price data")
      } finally {
        setIsLoading(false)
      }
    }

    fetchFlightPrice()
  }, [flightId, searchParams])

  // Helper function to format date
  const formatDate = (dateString: string) => {
    if (!dateString) return ""
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

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
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            
            <Button asChild>
              <Link href="/flights">Return to Flight Search</Link>
            </Button>
          </div>
        </main>
      </div>
    )
  }

  // If we have flight data, render the flight details
  if (flightOffer && pricedOffer) {
    // Extract data from API response
    const outboundSegment = flightOffer.segments[0]
    const returnSegment = flightOffer.segments.length > 1 ? flightOffer.segments[1] : null
    
    // Price data
    const totalPrice = pricedOffer.data.priced_offer?.total_amount || flightOffer.price?.amount
    const currency = pricedOffer.data.priced_offer?.currency || flightOffer.price?.currency || "USD"
    const taxes = pricedOffer.data.priced_offer?.breakdown?.[0]?.taxes || 0
    const baseFare = pricedOffer.data.priced_offer?.breakdown?.[0]?.base || (totalPrice - taxes)
    
    // Format flight data for the components
    const formattedFlight = {
      id: flightOffer.id,
      airline: {
        name: outboundSegment?.marketingCarrier?.name || "Airline",
        logo: "/placeholder.svg?height=40&width=40", // Default logo
        code: outboundSegment?.marketingCarrier?.iataCode || "",
        flightNumber: outboundSegment?.marketingFlightNumber || "",
      },
      departure: {
        airport: outboundSegment?.departure?.airport || "",
        terminal: outboundSegment?.departure?.terminal || "",
        city: outboundSegment?.departure?.cityName || "",
        time: new Date(outboundSegment?.departure?.time || "").toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        date: new Date(outboundSegment?.departure?.time || "").toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          year: 'numeric' 
        }),
        fullDate: formatDate(outboundSegment?.departure?.time),
      },
      arrival: {
        airport: outboundSegment?.arrival?.airport || "",
        terminal: outboundSegment?.arrival?.terminal || "",
        city: outboundSegment?.arrival?.cityName || "",
        time: new Date(outboundSegment?.arrival?.time || "").toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        date: new Date(outboundSegment?.arrival?.time || "").toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          year: 'numeric' 
        }),
        fullDate: formatDate(outboundSegment?.arrival?.time),
      },
      returnFlight: returnSegment ? {
        airline: {
          name: returnSegment?.marketingCarrier?.name || "Airline",
          logo: "/placeholder.svg?height=40&width=40", // Default logo
          code: returnSegment?.marketingCarrier?.iataCode || "",
          flightNumber: returnSegment?.marketingFlightNumber || "",
        },
        departure: {
          airport: returnSegment?.departure?.airport || "",
          terminal: returnSegment?.departure?.terminal || "",
          city: returnSegment?.departure?.cityName || "",
          time: new Date(returnSegment?.departure?.time || "").toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          date: new Date(returnSegment?.departure?.time || "").toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
          }),
          fullDate: formatDate(returnSegment?.departure?.time),
        },
        arrival: {
          airport: returnSegment?.arrival?.airport || "",
          terminal: returnSegment?.arrival?.terminal || "",
          city: returnSegment?.arrival?.cityName || "",
          time: new Date(returnSegment?.arrival?.time || "").toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          date: new Date(returnSegment?.arrival?.time || "").toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
          }),
          fullDate: formatDate(returnSegment?.arrival?.time),
        },
        duration: returnSegment?.duration || "",
        stops: 0, // Default value, adjust based on API response
        aircraft: returnSegment?.equipment || "Aircraft",
        amenities: [], // Default value, adjust based on API response
      } : null,
      duration: outboundSegment?.duration || flightOffer.duration || "",
      stops: (outboundSegment?.stops?.length || 0),
      aircraft: outboundSegment?.equipment || "Aircraft",
      amenities: [], // Default value, adjust based on API response
      baggageAllowance: {
        carryOn: "1 bag (8 kg)", // Default value, adjust based on API response
        checked: "1 bag (23 kg)", // Default value, adjust based on API response
      },
      price: totalPrice,
      currency: currency,
      seatsAvailable: flightOffer.seatsAvailable || 9,
      refundable: flightOffer.refundable || false,
      fareClass: flightOffer.cabinType || "Economy",
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
                origin={formattedFlight.departure.city}
                originCode={formattedFlight.departure.airport}
                destination={formattedFlight.arrival.city}
                destinationCode={formattedFlight.arrival.airport}
                departDate={formattedFlight.departure.fullDate}
                returnDate={formattedFlight.returnFlight?.departure.fullDate}
                passengers={1} // Update with actual passenger count from search
                price={formattedFlight.price}
                currency={formattedFlight.currency}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
              {/* Flight Details and Booking Form */}
              <div className="space-y-6">
                <div className="rounded-lg border">
                  <div className="p-4 sm:p-6">
                    <h2 className="text-xl font-semibold">Outbound Flight</h2>
                    <p className="text-sm text-muted-foreground">{formattedFlight.departure.fullDate}</p>
                  </div>
                  <Separator />
                  <FlightDetailsCard flight={formattedFlight} />
                </div>

                {formattedFlight.returnFlight && (
                  <div className="rounded-lg border">
                    <div className="p-4 sm:p-6">
                      <h2 className="text-xl font-semibold">Return Flight</h2>
                      <p className="text-sm text-muted-foreground">{formattedFlight.returnFlight.departure.fullDate}</p>
                    </div>
                    <Separator />
                    <FlightDetailsCard
                      flight={{
                        ...formattedFlight.returnFlight,
                        id: formattedFlight.id,
                        price: formattedFlight.price,
                        currency: formattedFlight.currency,
                        seatsAvailable: formattedFlight.seatsAvailable,
                        baggageAllowance: formattedFlight.baggageAllowance,
                        refundable: formattedFlight.refundable,
                        fareClass: formattedFlight.fareClass,
                      }}
                    />
                  </div>
                )}

                <BookingForm 
                  flightOffer={flightOffer} 
                  pricedOffer={pricedOffer} 
                  airShoppingResponse={airShoppingResponse} 
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
                      <span>Base fare (1 passenger)</span>
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
                    <Separator />
                    <div className="flex justify-between font-bold">
                      <span>Total</span>
                      <span>{totalPrice.toFixed(2)} {currency}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      <p>Fare rules:</p>
                      <ul className="mt-1 list-inside list-disc">
                        <li>{formattedFlight.refundable ? "Refundable" : "Non-refundable"}</li>
                        <li>Changes allowed (fee may apply)</li>
                        <li>Fare class: {formattedFlight.fareClass}</li>
                      </ul>
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
