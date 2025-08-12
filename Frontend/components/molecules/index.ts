/**
 * Molecules - Component combinations that form functional UI units
 * 
 * Molecules combine atoms to create reusable flight booking components
 * with specific purposes. They accept data via props and manage minimal
 * internal state for functionality.
 */

// Price Display Components
export { PriceDisplay } from "./price-display"
export type { PriceDisplayProps } from "./price-display"

// Flight Route Information
export { FlightRouteInfo } from "./flight-route-info"
export type { FlightRouteInfoProps } from "./flight-route-info"

// Passenger Selection Components
export { PassengerSelector } from "./passenger-selector"
export type { PassengerSelectorProps, PassengerCounts } from "./passenger-selector"

export { PassengerCountSelector } from "./passenger-count-selector"
export { PassengerForm } from "./passenger-form"

// Date Selection Components
export { DateSelector, DateRangeSelector } from "./date-selector"
export type { DateSelectorProps, DateRangeProps } from "./date-selector"

// Cabin Selection Components
export { CabinSelector } from "./cabin-selector"
export type { CabinSelectorProps, CabinType } from "./cabin-selector"

// Airport Selection Components
export { AirportSelector } from "./airport-selector"
export type { AirportSelectorProps, Airport } from "./airport-selector"

// Flight Display Components
export { FlightHeader } from "./flight-header"
export { FlightRouteDisplay } from "./flight-route-display" 
export { FlightSegmentDetails } from "./flight-segment-details"
export { FlightPricePanel } from "./flight-price-panel"

// Search & Filter Components
export { FlightFilters } from "./flight-filters"
export { FlightSortOptions } from "./flight-sort-options"  
export { FlightSearchSummary } from "./flight-search-summary"

// Display Components
export { DestinationCard } from "./destination-card"
export { OrderSummary } from "./order-summary"

// Service Components
export { BaggageInfo } from "./baggage-info"
export { BaggageOptions } from "./baggage-options"
export { MealOptions } from "./meal-options"
export { SeatSelection } from "./seat-selection"
export { AdditionalServices } from "./additional-services"

// Payment Components
export { PaymentForm } from "./payment-form"
export { CardPaymentForm } from "./card-payment-form"
export { PaymentConfirmation } from "./payment-confirmation"

// Form Components
export { FareRulesTable } from "./fare-rules-table"