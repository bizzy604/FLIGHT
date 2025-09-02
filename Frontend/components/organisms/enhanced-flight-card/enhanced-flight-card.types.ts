import type { FlightOffer } from "@/types/flight-api"

export interface EnhancedFlightCardProps {
  flight: FlightOffer
  showExtendedDetails?: boolean
  searchParams?: {
    adults?: number
    children?: number
    infants?: number
    tripType?: string
    origin?: string
    destination?: string
    departDate?: string
    returnDate?: string
    cabinClass?: string
  }
}

export interface FlightSelectionSearchParams {
  adults?: number
  children?: number
  infants?: number
  tripType?: string
  origin?: string
  destination?: string
  departDate?: string
  returnDate?: string
  cabinClass?: string
}