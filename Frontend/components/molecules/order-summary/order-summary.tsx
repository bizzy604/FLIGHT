import { Edit } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { formatCurrency } from "@/utils/currency-formatter"
import { 
  calculatePricingBreakdown, 
  calculateServiceFees, 
  extractFlightPricing,
  formatSeatSummary,
  getPassengerCountText,
  type SeatPrices,
  type ServiceInfo 
} from "@/utils/pricing-calculator"

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
  seatPrices?: SeatPrices
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

  // Extract pricing information using unified system
  const pricedOffer = booking?.flightOffer || {}
  const flightPricing = extractFlightPricing(pricedOffer)
  
  // Use unified pricing calculation
  const { serviceDetails } = calculateServiceFees(selectedServices || [], services || [])
  const pricingBreakdown = calculatePricingBreakdown(
    flightPricing.baseFare,
    flightPricing.taxes,
    seatPrices || { outbound: 0, return: 0 },
    selectedServices || [],
    services || [],
    null, // baggageSelection - to be added later
    35, // additionalBagPrice
    flightPricing.currency
  )
  
  const { currency, baseFare, taxes } = flightPricing
  const total = pricingBreakdown.total

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
      <div className="bg-white/95 dark:bg-background/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-primary-200 dark:border-primary-700">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-5 pb-3 border-b-2 border-primary-200 dark:border-primary-600">Booking Summary</h2>
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
            <div className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">PASSENGERS</div>
            {booking.passengers?.map((passenger: any, index: number) => (
              <div key={index} className="flex justify-between items-center py-1">
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {passenger.title} {passenger.firstName} {passenger.lastName}
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
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
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">SELECTED SEATS</div>
              {(selectedSeats && (selectedSeats.outbound.length > 0 || selectedSeats.return.length > 0)) ? (
                <div className="space-y-1">
                  {selectedSeats.outbound.length > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-700 dark:text-gray-300">Outbound: {selectedSeats.outbound.join(", ")}</span>
                      <span className="font-medium text-gray-900 dark:text-white">{formatCurrencyDisplay(seatPrices?.outbound || 0, currency)}</span>
                    </div>
                  )}
                  {selectedSeats.return.length > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-700 dark:text-gray-300">Return: {selectedSeats.return.join(", ")}</span>
                      <span className="font-medium text-gray-900 dark:text-white">{formatCurrencyDisplay(seatPrices?.return || 0, currency)}</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400">No seat selected</div>
              )}
            </div>

            {/* Selected Services */}
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-600 dark:text-gray-300">SELECTED SERVICES</div>
              {serviceDetails.length > 0 ? (
                <div className="space-y-1">
                  {serviceDetails.map((service) => (
                    <div key={service.objectKey} className="flex justify-between items-center text-sm">
                      <span className="text-gray-700 dark:text-gray-300">{service.name}</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {service.isFree ? (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-semibold rounded">FREE</span>
                        ) : (
                          formatCurrencyDisplay(service.price, service.currency)
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400">No services selected</div>
              )}
            </div>
          </div>

          {/* Price Breakdown */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900 dark:text-white">Price Breakdown</h3>
            <div className="space-y-2">
              {/* Show per-passenger pricing if available */}
              {pricedOffer.passengers && Array.isArray(pricedOffer.passengers) ? (
                <>
                  {pricedOffer.passengers.map((passenger: any, index: number) => (
                    <div key={index} className="space-y-1">
                      <div className="text-sm font-medium text-muted-foreground border-b pb-1">
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
                    <span>Flight fare ({booking.passengers?.length || 1} passenger{booking.passengers?.length !== 1 ? 's' : ''})</span>
                    <span>{formatCurrencyDisplay(flightPricing.total > 0 ? flightPricing.total * 0.8 : baseFare, currency)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Taxes and fees</span>
                    <span>{formatCurrencyDisplay(flightPricing.total > 0 ? flightPricing.total * 0.2 : taxes, currency)}</span>
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
              {pricingBreakdown.seatFees > 0 && (
                <div className="flex justify-between">
                  <span>Seat selection fees</span>
                  <span>{formatCurrencyDisplay(pricingBreakdown.seatFees, currency)}</span>
                </div>
              )}

              {/* Service Fees */}
              {pricingBreakdown.serviceFees > 0 && (
                <div className="flex justify-between">
                  <span>Additional services</span>
                  <span>{formatCurrencyDisplay(pricingBreakdown.serviceFees, currency)}</span>
                </div>
              )}

              <Separator />
              <div className="flex justify-between font-bold text-lg">
                <span className="text-gray-900 dark:text-white">Total Amount</span>
                <span className="text-purple-600 dark:text-purple-400">
                  {formatCurrencyDisplay(
                    flightPricing.total > 0 ? flightPricing.total + pricingBreakdown.seatFees + pricingBreakdown.serviceFees : 
                    pricingBreakdown.total, 
                    currency
                  )}
                </span>
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
