/**
 * Booking Template - Checkout/payment page layout
 * 
 * This template provides the layout structure for booking and payment pages.
 * It includes booking summary, passenger forms, payment options, and
 * confirmation steps in a secure, step-by-step layout.
 */

import { ReactNode } from "react"

interface BookingTemplateProps {
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

export function BookingTemplate({
  bookingSummary,
  bookingForm,
  progressIndicator,
  securityIndicators,
  legalInformation,
  className
}: BookingTemplateProps) {
  return (
    <div className={`booking-template ${className || ''}`}>
      {/* Progress Indicator */}
      {progressIndicator && (
        <section className="progress-section">
          <div className="container mx-auto px-4 py-4">
            {progressIndicator}
          </div>
        </section>
      )}

      <div className="container mx-auto px-4 py-6">
        <div className="booking-layout grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Booking Form */}
          <main className="booking-main lg:col-span-2">
            <div className="booking-form-content">
              {bookingForm}
            </div>

            {/* Legal Information */}
            {legalInformation && (
              <section className="legal-information-section mt-8">
                {legalInformation}
              </section>
            )}
          </main>

          {/* Booking Summary Sidebar */}
          {bookingSummary && (
            <aside className="booking-sidebar lg:col-span-1">
              <div className="sticky top-4">
                {bookingSummary}
                
                {/* Security Indicators */}
                {securityIndicators && (
                  <div className="security-indicators mt-6">
                    {securityIndicators}
                  </div>
                )}
              </div>
            </aside>
          )}
        </div>
      </div>
    </div>
  )
}