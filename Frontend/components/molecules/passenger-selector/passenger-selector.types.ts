export type PassengerType = 'adults' | 'children' | 'infants'

export interface PassengerCounts {
  adults: number
  children: number
  infants: number
}

export interface PassengerSelectorProps {
  passengers: PassengerCounts
  onPassengersChange: (type: PassengerType, value: number) => void
  disabled?: boolean
  className?: string
  maxPassengers?: number
}

export interface PassengerTypeConfig {
  type: PassengerType
  label: string
  ageRange: string
  min: number
  max?: number
}