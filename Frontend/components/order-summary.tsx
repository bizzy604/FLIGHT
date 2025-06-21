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

  // Extract pricing information from the stored flight data
  const flightData = booking?.flightOffer || {}
  
  // Extract priced offer and pricing data from the correct path
  const pricedOffer = flightData?.data?.raw_response?.data?.priced_offers?.[0] || {}
  const pricingData = pricedOffer?.pricing || {}

  // console.log('Order Summary - Flight Data:', flightData)
  // console.log('Order Summary - Priced Offer:', pricedOffer)
  // console.log('Order Summary - Pricing Data:', pricingData)
  
  const totalPrice = pricingData?.total_price || pricingData?.total_price_per_traveler || 0
  const currency = pricingData?.currency || 'INR'
  const taxes = pricingData?.taxes_per_traveler || 0
  const baseFare = pricingData?.base_fare_per_traveler || 0
  const total = totalPrice
  
  // Extract flight details from segments
  const segments = pricedOffer?.segments || []
  const firstSegment = segments[0] || {}
  const lastSegment = segments[segments.length - 1] || firstSegment
  
  const outboundFlight = {
    departure: {
      airport: firstSegment?.origin || 'Unknown',
      city: firstSegment?.origin || 'Unknown',
      time: firstSegment?.departure_time || 'Unknown',
      date: firstSegment?.departure_date || 'Unknown'
    },
    arrival: {
      airport: lastSegment?.destination || 'Unknown',
      city: lastSegment?.destination || 'Unknown', 
      time: lastSegment?.arrival_time || 'Unknown',
      date: lastSegment?.arrival_date || 'Unknown'
    },
    airline: {
      name: firstSegment?.airline_name || 'Unknown Airline',
      code: firstSegment?.flight_number?.substring(0, 2) || 'XX',
      flightNumber: firstSegment?.flight_number || 'Unknown'
    },
    duration: firstSegment?.flight_duration || 'Unknown',
    totalSegments: segments.length
  }

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
                  Duration: {outboundFlight.duration} • {outboundFlight.totalSegments} stop{outboundFlight.totalSegments > 1 ? 's' : ''}
                </p>
              </div>
            </div>
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
          <h3 className="font-medium">Base fare</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Base fare ({booking.passengers?.length || 1} passenger{booking.passengers?.length !== 1 ? 's' : ''})</span>
              <span>₹{baseFare?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex justify-between">
              <span>Taxes and fees</span>
              <span>₹{taxes?.toLocaleString() || '0'}</span>
            </div>
            {booking.pricing?.baggageFees !== undefined && (
              <div className="flex justify-between">
                <span>Baggage fees ({booking.passengers?.length || 1} passenger{booking.passengers?.length !== 1 ? 's' : ''})</span>
                <span>${formatPrice(booking.pricing.baggageFees)}</span>
              </div>
            )}
            {booking.pricing?.seatSelection !== undefined && (
              <div className="flex justify-between">
                <span>Seat selection</span>
                <span>${formatPrice(booking.pricing.seatSelection)}</span>
              </div>
            )}
            {booking.pricing?.mealSelection !== undefined && (
              <div className="flex justify-between">
                <span>Meal selection</span>
                <span>${formatPrice(booking.pricing.mealSelection)}</span>
              </div>
            )}
            {booking.pricing?.priorityBoarding !== undefined && (
              <div className="flex justify-between">
                <span>Priority boarding</span>
                <span>${formatPrice(booking.pricing.priorityBoarding)}</span>
              </div>
            )}
            {booking.pricing?.travelInsurance !== undefined && (
              <div className="flex justify-between">
                <span>Travel insurance</span>
                <span>${formatPrice(booking.pricing.travelInsurance)}</span>
              </div>
            )}
            <Separator />
            <div className="flex justify-between font-bold">
              <span>Total</span>
              <span>₹{total?.toLocaleString() || '0'}</span>
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
