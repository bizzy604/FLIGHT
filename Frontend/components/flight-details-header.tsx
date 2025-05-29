import { CalendarIcon, MapPin, Users } from "lucide-react"

interface FlightDetailsHeaderProps {
  origin: string
  originCode: string
  destination: string
  destinationCode: string
  departDate: string
  returnDate?: string
  passengers: number
  price: number
}

export function FlightDetailsHeader({
  origin,
  originCode,
  destination,
  destinationCode,
  departDate,
  returnDate,
  passengers,
  price,
}: FlightDetailsHeaderProps) {
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
            {passengers} {passengers === 1 ? "passenger" : "passengers"}
          </span>
        </div>
        <div className="ml-auto font-medium text-foreground">Total: ${(price + 45.6).toFixed(2)}</div>
      </div>
    </div>
  )
}

