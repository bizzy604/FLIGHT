/**
 * Types for Booking Template
 */

import { ReactNode } from "react"

export interface BookingTemplateProps {
  /** Flight/booking summary sidebar */
  bookingSummary?: ReactNode
  /** Main booking form content */
  bookingForm: ReactNode
  /** Progress indicator for multi-step booking */
  progressIndicator?: ReactNode
  /** Payment security badges/trust indicators */
  securityIndicators?: ReactNode
  /** Terms and conditions, policy links */
  legalInformation?: ReactNode
  /** Custom className for template styling */
  className?: string
}