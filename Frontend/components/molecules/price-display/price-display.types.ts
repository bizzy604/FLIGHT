import { PriceBreakdown } from "@/types/flight-api"

export interface PriceDisplayProps {
  priceBreakdown: PriceBreakdown
  detailed?: boolean
  compact?: boolean
  className?: string
}

export interface TaxDetail {
  code: string
  amount: number
  description?: string
}

export interface FeeDetail {
  code: string
  amount: number
  description?: string
}