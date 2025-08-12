/**
 * Organisms - Complex components that form distinct sections
 * 
 * Organisms combine molecules and atoms into complex UI sections.
 * They can manage complex state, side effects, API calls, and business logic.
 * These represent major sections of the flight booking interface.
 */

// Flight Search Components
export { FlightSearchForm } from "./flight-search-form"
export type { 
  FlightSearchFormProps, 
  FlightSearchFormData, 
  SearchFormErrors 
} from "./flight-search-form"

// Flight Display Components
export { EnhancedFlightCard } from "./enhanced-flight-card"
export type { 
  EnhancedFlightCardProps, 
  FlightSelectionSearchParams 
} from "./enhanced-flight-card"

export { FlightItineraryCard } from "./flight-itinerary-card"

// Navigation Components
export { MainNav } from "./main-nav"
export { UserNav } from "./user-nav"

// Footer Components
export { Footer } from "./footer"
export { SimpleFooter } from "./simple-footer"
export { ConditionalFooter } from "./conditional-footer"

// Booking Components
export { BookingForm } from "./booking-form"

// Booking Management Components
export { BookingsList } from "./bookings-list"
export { EmptyBookings } from "./empty-bookings"

// Itinerary Components
export { OfficialItinerary } from "./official-itinerary"
export { BoardingPassItinerary } from "./boarding-pass-itinerary"

// Admin Components
export { BookingsTable } from "./bookings-table"
export { BookingsFilter } from "./bookings-filter"
export { AdminGeneralSettings } from "./admin-general-settings"
export { AdminApiSettings } from "./admin-api-settings"
export { AdminUserManagement } from "./admin-user-management"

// Section Components
// Removed exports for missing section components