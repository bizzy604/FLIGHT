/**
 * Types for Admin Template
 */

import { ReactNode } from "react"

export interface AdminTemplateProps {
  /** Admin sidebar navigation */
  sidebar?: ReactNode
  /** Page header with title and actions */
  pageHeader?: ReactNode
  /** Main admin content */
  children: ReactNode
  /** Page-level actions (export, settings, etc.) */
  pageActions?: ReactNode
  /** Breadcrumb navigation */
  breadcrumbs?: ReactNode
  /** Custom className for template styling */
  className?: string
}