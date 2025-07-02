import { Calendar as CalendarIcon, MapPin, Users } from "lucide-react"

interface FlightDetailsHeaderProps {
  origin: string
  originCode: string
  destination: string
  destinationCode: string
  departDate: string
  returnDate?: string
  adults: number
  children: number
  infants: number
  price: number
  currency: string
}

export function FlightDetailsHeader({
  origin,
  originCode,
  destination,
  destinationCode,
  departDate,
  returnDate,
  adults,
  children,
  infants,
  price,
  currency,
}: FlightDetailsHeaderProps) {
  const totalPassengers = adults + children + infants
  
  const formatPassengerCount = () => {
    const parts = []
    if (adults > 0) parts.push(`${adults} ${adults === 1 ? 'adult' : 'adults'}`)
    if (children > 0) parts.push(`${children} ${children === 1 ? 'child' : 'children'}`)
    if (infants > 0) parts.push(`${infants} ${infants === 1 ? 'infant' : 'infants'}`)
    
    const breakdown = parts.join(', ')
    return `${breakdown} (total ${totalPassengers} ${totalPassengers === 1 ? 'passenger' : 'passengers'})`
  }
  return (
    <div className="mt-4">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold">Flight Details & Booking</h1>

      {/* Mobile Layout - Stacked */}
      <div className="mt-3 space-y-3 sm:hidden">
        <div className="flex items-center text-sm text-muted-foreground">
          <MapPin className="mr-2 h-4 w-4 flex-shrink-0" />
          <span className="break-words">
            {origin} ({originCode}) to {destination} ({destinationCode})
          </span>
        </div>
        <div className="flex items-center text-sm text-muted-foreground">
          <CalendarIcon className="mr-2 h-4 w-4 flex-shrink-0" />
          <span>
            {departDate}
            {returnDate && ` - ${returnDate}`}
          </span>
        </div>
        <div className="flex items-center text-sm text-muted-foreground">
          <Users className="mr-2 h-4 w-4 flex-shrink-0" />
          <span className="text-xs">
            {formatPassengerCount()}
          </span>
        </div>
        <div className="bg-muted/50 rounded-lg p-3">
          <div className="text-lg font-bold text-foreground">
            Total: {price.toFixed(2)} {currency}
          </div>
        </div>
      </div>

      {/* Desktop Layout - Horizontal */}
      <div className="mt-2 hidden sm:flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
        <div className="flex items-center">
          <MapPin className="mr-1 h-4 w-4" />
          <span>
            {origin} ({originCode}) to {destination} ({destinationCode})
          </span>
        </div>
        <div className="flex items-center">
          <CalendarIcon className="mr-1 h-4 w-4" />
          <span>
            {departDate}
            {returnDate && ` - ${returnDate}`}
          </span>
        </div>
        <div className="flex items-center">
          <Users className="mr-1 h-4 w-4" />
          <span className="text-xs lg:text-sm">
            {formatPassengerCount()}
          </span>
        </div>
        <div className="ml-auto font-medium text-foreground text-base lg:text-lg">
          Total: {price.toFixed(2)} {currency}
        </div>
      </div>
    </div>
  )
}

