/**
 * Flight Details Template - Individual flight details page layout
 * 
 * This template provides the layout structure for detailed flight views.
 * It displays comprehensive flight information, booking options, and
 * related content in an organized, scannable layout.
 */

import { ReactNode } from "react"

interface FlightDetailsTemplateProps {
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

export function FlightDetailsTemplate({
  flightHeader,
  flightDetails,
  bookingPanel,
  additionalServices,
  fareInformation,
  relatedFlights,
  className
}: FlightDetailsTemplateProps) {
  return (
    <div className={`flight-details-template ${className || ''}`}>
      {/* Flight Header */}
      {flightHeader && (
        <section className="flight-header-section">
          <div className="container mx-auto px-4 py-4">
            {flightHeader}
          </div>
        </section>
      )}

      <div className="container mx-auto px-4 py-6">
        <div className="flight-details-layout grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Area */}
          <main className="flight-main-content lg:col-span-2">
            {/* Primary Flight Details */}
            <section className="flight-details-section mb-8">
              {flightDetails}
            </section>

            {/* Additional Services */}
            {additionalServices && (
              <section className="additional-services-section mb-8">
                <h2 className="text-xl font-semibold mb-4">Additional Services</h2>
                {additionalServices}
              </section>
            )}

            {/* Fare Information */}
            {fareInformation && (
              <section className="fare-information-section mb-8">
                <h2 className="text-xl font-semibold mb-4">Fare Details</h2>
                {fareInformation}
              </section>
            )}
          </main>

          {/* Booking Sidebar */}
          {bookingPanel && (
            <aside className="booking-sidebar lg:col-span-1">
              <div className="sticky top-4">
                {bookingPanel}
              </div>
            </aside>
          )}
        </div>

        {/* Related Flights */}
        {relatedFlights && (
          <section className="related-flights-section mt-12">
            <h2 className="text-2xl font-semibold mb-6">Similar Flights</h2>
            {relatedFlights}
          </section>
        )}
      </div>
    </div>
  )
}