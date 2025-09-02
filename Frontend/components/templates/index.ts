/**
 * Templates - Page-level layout structures
 * 
 * Templates define page layouts and component positioning without actual content.
 * They focus on layout, spacing, and responsive design while remaining reusable
 * across similar page types in the flight booking portal.
 */

// Flight Booking Templates
export { FlightSearchTemplate } from "./flight-search-template"
export type { FlightSearchTemplateProps } from "./flight-search-template"

export { FlightResultsTemplate } from "./flight-results-template"
export type { FlightResultsTemplateProps } from "./flight-results-template"

export { FlightDetailsTemplate } from "./flight-details-template"
export type { FlightDetailsTemplateProps } from "./flight-details-template"

export { BookingTemplate } from "./booking-template"
export type { BookingTemplateProps } from "./booking-template"

// Admin Templates
export { AdminTemplate } from "./admin-template"
export type { AdminTemplateProps } from "./admin-template"