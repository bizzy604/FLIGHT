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
      <h1 className="text-2xl font-bold md:text-3xl">Flight Details & Booking</h1>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
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
          <span>
            {formatPassengerCount()}
          </span>
        </div>
        <div className="ml-auto font-medium text-foreground">Total: {price.toFixed(2)} {currency}</div>
      </div>
    </div>
  )
}

