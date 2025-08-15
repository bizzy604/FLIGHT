import { Edit } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { formatCurrency } from "@/utils/currency-formatter"

// Helper function outside component to avoid parsing issues
const formatDateTime = (isoString: string): { time: string; date: string } => {
  if (!isoString) return { time: 'Unknown', date: 'Unknown' }
  const date = new Date(isoString)
  return {
    time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
    date: date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
  }
}

interface OrderSummaryProps {
  booking: any // Using any for brevity, but would use a proper type in a real app
  selectedSeats?: {
    outbound: string[]
    return: string[]
  }
  selectedServices?: string[]
  seatPrices?: {
    outbound: number
    return: number
  }
  servicePrices?: number
  services?: any[]
  onContinue?: () => void
}

function OrderSummary({ 
  booking, 
  selectedSeats = { outbound: [], return: [] }, 
  selectedServices = [], 
  seatPrices = { outbound: 0, return: 0 }, 
  servicePrices = 0, 
  services = [],
  onContinue 
}: OrderSummaryProps) {
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

  // Helper function to format currency with proper symbol (use imported utility)
  const formatCurrencyDisplay = (value: any, currencyCode: string = 'USD'): string => {
    const numericValue = typeof value === 'number' ? value : parseFloat(String(value)) || 0
    return formatCurrency(numericValue, currencyCode)
  }

  // Extract pricing information from the stored flight data
  const pricedOffer = booking?.flightOffer || {}

  // Extract pricing data using the same structure as flight details page
  let currency: string = 'USD'
  let totalPrice: number = 0
  let taxes: number = 0
  let baseFare: number = 0

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
  } else if (booking?.pricing) {
    // Fallback to booking pricing if available
    totalPrice = booking.pricing.total || 0
    baseFare = booking.pricing.baseFare || 0
    taxes = booking.pricing.taxes || 0
    currency = booking.pricing.currency || booking.currency || 'USD'
  }

  const total = totalPrice

  // Extract flight segments using the same structure as flight details page
  let outboundSegments: any[] = []
  let returnSegments: any[] = []

  const isRoundTrip = pricedOffer.direction === 'roundtrip'

  if (isRoundTrip && pricedOffer.flight_segments) {
    outboundSegments = pricedOffer.flight_segments.outbound || []
    returnSegments = pricedOffer.flight_segments.return || []
  } else if (pricedOffer.flight_segments) {
    outboundSegments = Array.isArray(pricedOffer.flight_segments) ? pricedOffer.flight_segments : []
  }

  // Get first and last segments for route display
  const firstSegment: any = outboundSegments[0] || {}
  const lastSegment: any = outboundSegments[outboundSegments.length - 1] || firstSegment

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

  return (
    <div className="sticky top-6">
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <h2 className="text-lg font-bold text-gray-900 mb-5 pb-3 border-b-2 border-gray-200">Booking Summary</h2>
        <div className="space-y-5">
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
                    Duration: {outboundFlight.duration} • {outboundFlight.totalSegments === 1 ? 'Direct' : `${outboundFlight.totalSegments - 1} stop`}
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
                      Duration: {returnSegments[0]?.duration} • {returnSegments.length === 1 ? 'Direct' : `${returnSegments.length - 1} stop`}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Passengers */}
          <div>
            <div className="text-sm font-semibold text-gray-600 mb-2">PASSENGERS</div>
            {booking.passengers?.map((passenger: any, index: number) => (
              <div key={index} className="flex justify-between items-center py-1">
                <span className="text-sm text-gray-700">
                  {passenger.title} {passenger.firstName} {passenger.lastName}
                </span>
                <span className="text-sm font-medium text-gray-900">
                  {passenger.type === 'ADULT' ? 'ADT' : passenger.type.substring(0, 3)}
                </span>
              </div>
            ))}
          </div>

          {/* Selected Extras */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Selected Extras</h3>
            </div>
            
            {/* Selected Seats */}
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-600">SELECTED SEATS</div>
              {(selectedSeats.outbound.length > 0 || selectedSeats.return.length > 0) ? (
                <div className="space-y-1">
                  {selectedSeats.outbound.length > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-700">Outbound: {selectedSeats.outbound.join(", ")}</span>
                      <span className="font-medium">{formatCurrencyDisplay(seatPrices.outbound, currency)}</span>
                    </div>
                  )}
                  {selectedSeats.return.length > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-700">Return: {selectedSeats.return.join(", ")}</span>
                      <span className="font-medium">{formatCurrencyDisplay(seatPrices.return, currency)}</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No seat selected</div>
              )}
            </div>

            {/* Selected Services */}
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-600">SELECTED SERVICES</div>
              {selectedServices.length > 0 ? (
                <div className="space-y-1">
                  {selectedServices.map((serviceKey, index) => {
                    const service = services.find(s => s.objectKey === serviceKey)
                    const serviceName = service?.name?.value || `Service ${index + 1}`
                    const servicePrice = service?.price?.[0]?.total?.value || 0
                    return (
                      <div key={serviceKey} className="flex justify-between items-center text-sm">
                        <span className="text-gray-700">{serviceName}</span>
                        <span className="font-medium">
                          {servicePrice === 0 ? (
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">FREE</span>
                          ) : (
                            formatCurrencyDisplay(servicePrice, service?.price?.[0]?.total?.code || currency)
                          )}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No services selected</div>
              )}
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
                          <span>{formatCurrencyDisplay(passenger.pricing.base_fare.amount, passenger.pricing.base_fare.currency || currency)}</span>
                        </div>
                      )}
                      {passenger.pricing?.taxes && (
                        <div className="flex justify-between text-sm">
                          <span className="ml-2">Taxes and fees</span>
                          <span>{formatCurrencyDisplay(passenger.pricing.taxes.amount, passenger.pricing.taxes.currency || currency)}</span>
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
                    <span>{formatCurrencyDisplay(baseFare, currency)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Taxes and fees</span>
                    <span>{formatCurrencyDisplay(taxes, currency)}</span>
                  </div>
                </>
              )}

              {/* Additional services */}
              {booking.pricing?.baggageFees !== undefined && (
                <div className="flex justify-between">
                  <span>Baggage fees</span>
                  <span>{formatCurrencyDisplay(booking.pricing.baggageFees, currency)}</span>
                </div>
              )}
              {booking.pricing?.seatSelection !== undefined && (
                <div className="flex justify-between">
                  <span>Seat selection</span>
                  <span>{formatCurrencyDisplay(booking.pricing.seatSelection, currency)}</span>
                </div>
              )}
              {booking.pricing?.mealSelection !== undefined && (
                <div className="flex justify-between">
                  <span>Meal selection</span>
                  <span>{formatCurrencyDisplay(booking.pricing.mealSelection, currency)}</span>
                </div>
              )}
              {booking.pricing?.priorityBoarding !== undefined && (
                <div className="flex justify-between">
                  <span>Priority boarding</span>
                  <span>{formatCurrencyDisplay(booking.pricing.priorityBoarding, currency)}</span>
                </div>
              )}
              {booking.pricing?.travelInsurance !== undefined && (
                <div className="flex justify-between">
                  <span>Travel insurance</span>
                  <span>{formatCurrencyDisplay(booking.pricing.travelInsurance, currency)}</span>
                </div>
              )}

              {/* Seat Selection Fees */}
              {(seatPrices.outbound > 0 || seatPrices.return > 0) && (
                <div className="flex justify-between">
                  <span>Seat selection fees</span>
                  <span>{formatCurrencyDisplay(seatPrices.outbound + seatPrices.return, currency)}</span>
                </div>
              )}

              {/* Service Fees */}
              {servicePrices > 0 && (
                <div className="flex justify-between">
                  <span>Additional services</span>
                  <span>{formatCurrencyDisplay(servicePrices, currency)}</span>
                </div>
              )}

              <Separator />
              <div className="flex justify-between font-bold text-lg">
                <span>Total Amount</span>
                <span className="text-purple-600">{formatCurrencyDisplay(total + seatPrices.outbound + seatPrices.return + servicePrices, currency)}</span>
              </div>
            </div>
          </div>

          {/* Continue Button */}
          {onContinue && (
            <div className="pt-4">
              <Button
                onClick={onContinue}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1 relative overflow-hidden group"
              >
                Continue to Payment
                <span className="absolute right-5 top-1/2 transform -translate-y-1/2 text-lg transition-transform group-hover:translate-x-1">
                  →
                </span>
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default OrderSummary
export { OrderSummary }
