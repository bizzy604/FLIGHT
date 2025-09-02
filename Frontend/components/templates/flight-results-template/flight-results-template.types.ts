/**
 * Types for Flight Results Template
 */

import { ReactNode } from "react"

export interface FlightResultsTemplateProps {
  /** Search summary component showing search criteria */
  searchSummary?: ReactNode
  /** Flight filters sidebar or panel */
  filters?: ReactNode
  /** Sort options component */
  sortOptions?: ReactNode
  /** Main flight results list */
  flightResults: ReactNode
  /** Loading state indicator */
  loading?: boolean
  /** Empty state when no results */
  emptyState?: ReactNode
  /** Pagination component */
  pagination?: ReactNode
  /** Custom className for template styling */
  className?: string
}