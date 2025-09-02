export interface CabinType {
  value: string
  label: string
  description?: string
}

export interface CabinSelectorProps {
  value: string
  onChange: (value: string) => void
  cabinTypes?: CabinType[]
  disabled?: boolean
  className?: string
  error?: string
  label?: string
}

export const DEFAULT_CABIN_TYPES: CabinType[] = [
  { value: "ECONOMY", label: "Economy", description: "Standard seating and service" },
  { value: "PREMIUM_ECONOMY", label: "Premium Economy", description: "Extra legroom and enhanced service" },
  { value: "BUSINESS", label: "Business Class", description: "Priority service and lie-flat seats" },
  { value: "FIRST", label: "First Class", description: "Luxury service and private suites" },
]