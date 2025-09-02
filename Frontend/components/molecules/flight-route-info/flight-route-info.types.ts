export interface FlightRouteInfoProps {
  origin: string
  originCode: string
  destination: string
  destinationCode: string
  departDate: string
  returnDate?: string
  adults: number
  children: number
  infants: number
  price?: number
  currency?: string
  compact?: boolean
  showPrice?: boolean
  className?: string
}

export interface PassengerCounts {
  adults: number
  children: number
  infants: number
}