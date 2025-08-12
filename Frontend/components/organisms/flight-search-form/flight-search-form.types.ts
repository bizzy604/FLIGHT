import type { FlightSearchRequest } from "@/utils/api-client"
import type { FlightOffer } from "@/types/flight-api"
import type { PassengerCounts } from "@/components/molecules/passenger-selector"

export interface FlightSearchFormProps {
  onSearch?: (results: FlightOffer[], meta: any) => void
  onError?: (error: string) => void
  onSearchStart?: (formData: FlightSearchFormData) => boolean
  initialValues?: Partial<FlightSearchFormData>
  disabled?: boolean
  className?: string
}

export interface FlightSearchFormData {
  tripType: 'round-trip' | 'one-way' | 'multi-city'
  origin: string
  destination: string
  departDate: Date | undefined
  returnDate: Date | undefined
  passengers: PassengerCounts
  cabinType: string
  segments: FlightSegment[]
}

export interface FlightSegment {
  origin: string
  destination: string
  departureDate: Date | undefined
}

export interface SearchFormErrors {
  origin?: string
  destination?: string
  departDate?: string
  returnDate?: string
  passengers?: string
  cabinType?: string
  general?: string
}