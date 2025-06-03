import { CalendarIcon, MapPin, Users } from "lucide-react"

interface FlightSearchSummaryProps {
  origin: string
  destination: string
  departDate: string
  returnDate?: string
  passengers: number
}

export function FlightSearchSummary({
  origin,
  destination,
  departDate,
  returnDate,
  passengers,
}: FlightSearchSummaryProps) {
  return (
    <div className="mt-4">
      <h1 className="text-2xl font-bold md:text-3xl">Flight Search Results</h1>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
        <div className="flex items-center">
          <MapPin className="mr-1 h-4 w-4" />
          <span>
            {origin} to {destination}
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
      </div>
    </div>
  )
}

