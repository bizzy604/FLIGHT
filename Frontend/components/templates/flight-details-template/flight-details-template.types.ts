/**
 * Types for Flight Details Template
 */

import { ReactNode } from "react"

export interface FlightDetailsTemplateProps {
  /** Flight route information header */
  flightHeader?: ReactNode
  /** Main flight details content */
  flightDetails: ReactNode
  /** Booking/selection panel */
  bookingPanel?: ReactNode
  /** Additional flight information (baggage, meals, etc.) */
  additionalServices?: ReactNode
  /** Terms and conditions, fare rules */
  fareInformation?: ReactNode
  /** Related flights or alternatives */
  relatedFlights?: ReactNode
  /** Custom className for template styling */
  className?: string
}