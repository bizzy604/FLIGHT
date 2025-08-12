/**
 * Types for Flight Search Template
 */

import { ReactNode } from "react"

export interface FlightSearchTemplateProps {
  /** Optional hero content above search form */
  heroContent?: ReactNode
  /** Optional promotional sections below search */
  promotionalSections?: ReactNode
  /** Optional partner/destination sections */
  supportingSections?: ReactNode
  /** Custom className for template styling */
  className?: string
}