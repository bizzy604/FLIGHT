import { Edit } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

interface OrderSummaryProps {
  booking: any // Using any for brevity, but would use a proper type in a real app
}

function OrderSummary({ booking }: OrderSummaryProps) {
  // Helper function to safely convert values to numbers and format them
  const formatPrice = (value: any): string => {
    if (value === null || value === undefined) return '0.00'

    // If it's already a number, use it directly
    if (typeof value === 'number') {
      return value.toFixed(2)
    }

    // If it's a string, try to parse it
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      return isNaN(parsed) ? '0.00' : parsed.toFixed(2)
    }

    // For any other type, try to convert to string then parse
    const parsed = parseFloat(String(value))
    return isNaN(parsed) ? '0.00' : parsed.toFixed(2)
  }

  // Helper function to format currency with proper symbol
  const formatCurrency = (value: any, currencyCode: string = 'USD'): string => {
    const amount = formatPrice(value)
    const currencySymbols: { [key: string]: string } = {
      'USD': '$',
      'EUR': '€',
      'GBP': '£',
      'INR': '₹',
      'JPY': '¥',
      'CAD': 'C$',
      'AUD': 'A$'
    }

    const symbol = currencySymbols[currencyCode] || currencyCode
    return `${symbol}${amount}`
  }

  // Extract pricing information from the stored flight data
  // The flight data should be the priced offer from the flight details page
  const pricedOffer = booking?.flightOffer || {}

  console.log('Order Summary - Complete Priced Offer:', pricedOffer)
  console.log('Order Summary - Booking Object:', booking)

  // Extract pricing data using the same structure as flight details page
  let currency = 'USD'
  let totalPrice = 0
  let taxes = 0
  let baseFare = 0

  // Use the same pricing structure as flight details page
  if (pricedOffer.total_price) {
    totalPrice = pricedOffer.total_price.amount || 0
    currency = pricedOffer.total_price.currency || 'USD'

    // Extract base fare and taxes from passengers pricing
    if (pricedOffer.passengers && Array.isArray(pricedOffer.passengers)) {
      const firstPassenger = pricedOffer.passengers[0]
      if (firstPassenger?.pricing) {
        baseFare = firstPassenger.pricing.base_fare?.amount || 0
        taxes = firstPassenger.pricing.taxes?.amount || 0
      }
    }
    console.log('Order Summary - Using priced offer structure')
  }
  // Fallback to booking pricing if available
  else if (booking?.pricing) {
    totalPrice = booking.pricing.total || 0
    baseFare = booking.pricing.baseFare || 0
    taxes = booking.pricing.taxes || 0
    currency = booking.pricing.currency || booking.currency || 'USD'
    console.log('Order Summary - Using booking pricing fallback')
  }

  const total = totalPrice

  // Extract flight segments using the same structure as flight details page
  let outboundSegments = []
  let returnSegments = []

  const isRoundTrip = pricedOffer.direction === 'roundtrip'

  if (isRoundTrip && pricedOffer.flight_segments) {
    outboundSegments = pricedOffer.flight_segments.outbound || []
    returnSegments = pricedOffer.flight_segments.return || []
  } else if (pricedOffer.flight_segments) {
    outboundSegments = Array.isArray(pricedOffer.flight_segments) ? pricedOffer.flight_segments : []
  }

  // Get first and last segments for route display
  const firstSegment = outboundSegments[0] || {}
  const lastSegment = outboundSegments[outboundSegments.length - 1] || firstSegment

  // Format datetime helper function (same as flight details page)
  const formatDateTime = (isoString: string) => {
    if (!isoString) return { time: 'Unknown', date: 'Unknown' }
    const date = new Date(isoString)
    return {
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
      date: date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
    }
  }

  const departure = formatDateTime(firstSegment.departure_datetime)
  const arrival = formatDateTime(lastSegment.arrival_datetime)

  // Extract flight details using the same field mapping as flight details page
  const outboundFlight = {
    departure: {
      airport: firstSegment?.departure_airport || 'Unknown',
      time: departure.time,
      date: departure.date
    },
    arrival: {
      airport: lastSegment?.arrival_airport || 'Unknown',
      time: arrival.time,
      date: arrival.date
    },
    airline: {
      name: firstSegment?.airline_name || 'Unknown Airline',
      code: firstSegment?.airline_code || 'XX',
      flightNumber: firstSegment?.flight_number || 'Unknown'
    },
    duration: firstSegment?.duration || 'Unknown',
    totalSegments: outboundSegments.length,
    isRoundTrip: isRoundTrip
  }

  console.log('Order Summary - Extracted flight details:', outboundFlight)
  console.log('Order Summary - Pricing details:', { totalPrice, baseFare, taxes, currency })

  return (
    <div className="rounded-lg border">
      <div className="p-4 sm:p-6">
        <h2 className="text-xl font-semibold">Order Summary</h2>
      </div>
      <Separator />
      <div className="p-4 sm:p-6 space-y-6">
        {/* Flight Details */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Flight Details</h3>
            <Button variant="ghost" size="sm">
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>
          <div className="space-y-3">
            {/* Outbound Flight */}
            <div className="flex justify-between items-start">
              <div className="space-y-2">
                <p className="font-medium">{outboundFlight.departure.date}</p>
                <p className="text-sm text-muted-foreground">
                  {outboundFlight.departure.airport} → {outboundFlight.arrival.airport}
                </p>
                <p className="text-sm text-muted-foreground">
                  {outboundFlight.departure.time} - {outboundFlight.arrival.time}
                </p>
                <p className="text-sm text-muted-foreground">
                  {outboundFlight.airline.name} • {outboundFlight.airline.flightNumber}
                </p>
                <p className="text-sm text-muted-foreground">
                  Duration: {outboundFlight.duration} • {outboundFlight.totalSegments === 1 ? 'Direct' : `${outboundFlight.totalSegments - 1} stop${outboundFlight.totalSegments > 2 ? 's' : ''}`}
                </p>
              </div>
            </div>

            {/* Return Flight (if round-trip) */}
            {outboundFlight.isRoundTrip && returnSegments.length > 0 && (
              <div className="flex justify-between items-start pt-3 border-t">
                <div className="space-y-2">
                  <p className="font-medium">{formatDateTime(returnSegments[0]?.departure_datetime).date}</p>
                  <p className="text-sm text-muted-foreground">
                    {returnSegments[returnSegments.length - 1]?.arrival_airport} → {returnSegments[0]?.departure_airport}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {formatDateTime(returnSegments[0]?.departure_datetime).time} - {formatDateTime(returnSegments[returnSegments.length - 1]?.arrival_datetime).time}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {returnSegments[0]?.airline_name} • {returnSegments[0]?.flight_number}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Duration: {returnSegments[0]?.duration} • {returnSegments.length === 1 ? 'Direct' : `${returnSegments.length - 1} stop${returnSegments.length > 2 ? 's' : ''}`}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Passengers */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Passengers</h3>
            <Button variant="ghost" size="sm">
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>
          <div className="space-y-2">
            {booking.passengers?.map((passenger: any, index: number) => (
              <div key={index} className="text-sm">
                <span className="font-medium">{passenger.title} {passenger.firstName} {passenger.lastName}</span>
                <span className="text-muted-foreground ml-2">({passenger.type})</span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Extras */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Selected Extras</h3>
            <Button variant="ghost" size="sm">
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>
          <div className="space-y-2 text-sm text-muted-foreground">
            <div>Seats:</div>
            <div>Baggage:</div>
            <div>Meals:</div>
          </div>
        </div>

        {/* Price Breakdown */}
        <div className="space-y-4">
          <h3 className="font-medium">Price Breakdown</h3>
          <div className="space-y-2">
            {/* Show per-passenger pricing if available */}
            {pricedOffer.passengers && Array.isArray(pricedOffer.passengers) ? (
              <>
                {pricedOffer.passengers.map((passenger: any, index: number) => (
                  <div key={index} className="space-y-1">
                    <div className="text-sm font-medium text-muted-foreground">
                      {passenger.type} {index + 1}
                    </div>
                    {passenger.pricing?.base_fare && (
                      <div className="flex justify-between text-sm">
                        <span className="ml-2">Base fare</span>
                        <span>{formatCurrency(passenger.pricing.base_fare.amount, passenger.pricing.base_fare.currency || currency)}</span>
                      </div>
                    )}
                    {passenger.pricing?.taxes && (
                      <div className="flex justify-between text-sm">
                        <span className="ml-2">Taxes and fees</span>
                        <span>{formatCurrency(passenger.pricing.taxes.amount, passenger.pricing.taxes.currency || currency)}</span>
                      </div>
                    )}
                  </div>
                ))}
              </>
            ) : (
              <>
                {/* Fallback to aggregated pricing */}
                <div className="flex justify-between">
                  <span>Base fare ({booking.passengers?.length || 1} passenger{booking.passengers?.length !== 1 ? 's' : ''})</span>
                  <span>{formatCurrency(baseFare, currency)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Taxes and fees</span>
                  <span>{formatCurrency(taxes, currency)}</span>
                </div>
              </>
            )}

            {/* Additional services */}
            {booking.pricing?.baggageFees !== undefined && (
              <div className="flex justify-between">
                <span>Baggage fees</span>
                <span>{formatCurrency(booking.pricing.baggageFees, currency)}</span>
              </div>
            )}
            {booking.pricing?.seatSelection !== undefined && (
              <div className="flex justify-between">
                <span>Seat selection</span>
                <span>{formatCurrency(booking.pricing.seatSelection, currency)}</span>
              </div>
            )}
            {booking.pricing?.mealSelection !== undefined && (
              <div className="flex justify-between">
                <span>Meal selection</span>
                <span>{formatCurrency(booking.pricing.mealSelection, currency)}</span>
              </div>
            )}
            {booking.pricing?.priorityBoarding !== undefined && (
              <div className="flex justify-between">
                <span>Priority boarding</span>
                <span>{formatCurrency(booking.pricing.priorityBoarding, currency)}</span>
              </div>
            )}
            {booking.pricing?.travelInsurance !== undefined && (
              <div className="flex justify-between">
                <span>Travel insurance</span>
                <span>{formatCurrency(booking.pricing.travelInsurance, currency)}</span>
              </div>
            )}

            <Separator />
            <div className="flex justify-between font-bold">
              <span>Total</span>
              <span>{formatCurrency(total, currency)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Export both default and named
export default OrderSummary
export { OrderSummary }
