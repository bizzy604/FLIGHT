export interface Airport {
  code: string
  name: string
  city: string
  country?: string
}

export interface AirportSelectorProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  airports?: Airport[]
  className?: string
  error?: string
  icon?: React.ReactNode
}

export const DEFAULT_AIRPORTS: Airport[] = [
  { code: "JFK", name: "John F. Kennedy International Airport", city: "New York", country: "USA" },
  { code: "LAX", name: "Los Angeles International Airport", city: "Los Angeles", country: "USA" },
  { code: "LHR", name: "Heathrow Airport", city: "London", country: "UK" },
  { code: "CDG", name: "Charles de Gaulle Airport", city: "Paris", country: "France" },
  { code: "HND", name: "Haneda Airport", city: "Tokyo", country: "Japan" },
  { code: "BOM", name: "Chhatrapati Shivaji Maharaj International Airport", city: "Mumbai", country: "India" },
  { code: "DXB", name: "Dubai International Airport", city: "Dubai", country: "UAE" },
  { code: "SIN", name: "Singapore Changi Airport", city: "Singapore", country: "Singapore" },
  { code: "FRA", name: "Frankfurt Airport", city: "Frankfurt", country: "Germany" },
  { code: "AMS", name: "Amsterdam Airport Schiphol", city: "Amsterdam", country: "Netherlands" },
]