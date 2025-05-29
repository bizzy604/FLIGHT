"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 }
}

// Create a separate layout component for animations
import { ReactNode } from "react";

const AnimatedSection = ({ children, className = "", delay = 0 }: { children: ReactNode, className?: string, delay?: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className={className}
  >
    {children}
  </motion.div>
)

export default function TermsAndConditions() {
  const lastUpdated = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto px-4 py-16">
        {/* Header Section */}
        <AnimatedSection className="max-w-4xl mx-auto mb-12">
          <Link 
            href="/" 
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>
          
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Terms and Conditions
          </h1>
          <p className="text-gray-600">
            Last updated: {lastUpdated}
          </p>
        </AnimatedSection>

        {/* Main Content */}
        <AnimatedSection 
          className="max-w-4xl mx-auto prose prose-lg prose-gray prose-headings:text-gray-900 prose-p:text-gray-600"
          delay={0.2}
        >
          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <p>
                Welcome to Rea Travels. By accessing or using our website, mobile application, or any of our services, you
                agree to comply with and be bound by these Terms and Conditions. If you do not agree to these terms, please
                do not use our services.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">2. Definitions</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p><strong>Travello:</strong> "Rea Travel," "we," "us," or "our" refers to Rea Travel Agency.</p>
              <p><strong>User:</strong> "You" or "your" refers to the user or viewer of our website or services.</p>
              <p><strong>Services:</strong> Refers to all travel-related services, including but not limited to bookings for flights,
                accommodations, tours, and transportation.</p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">3. Booking and Payments</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>3.1. All bookings are subject to availability and confirmation.</p>
              <p>3.2. Prices are subject to change without notice until a booking is confirmed and paid for.</p>
              <p>
                3.3. Payment methods accepted include credit cards, debit cards, and other forms as specified on our
                website.
              </p>
              <p>3.4. Full payment is required to confirm and secure your booking unless otherwise stated.</p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">4. Cancellations and Refunds</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>4.1. Cancellation policies vary depending on the service provider and type of booking.</p>
              <p>
                4.2. Refunds, if applicable, will be processed according to the cancellation policy of each specific
                booking.
              </p>
              <p>
                4.3. Rea Travel reserves the right to charge an administrative fee for processing cancellations and refunds.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">5. Travel Documents and Requirements</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>
                5.1. You are responsible for ensuring that you have all necessary travel documents, including valid
                passports, visas, and health certificates.
              </p>
              <p>5.2. Rea Travel is not liable for any issues arising from inadequate or improper travel documentation.</p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">6. Liability and Insurance</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>
                6.1. Rea Travel acts as an intermediary between you and service providers (airlines, hotels, tour operators,
                etc.) and is not liable for their actions or omissions.
              </p>
              <p>
                6.2. We strongly recommend that you obtain comprehensive travel insurance to cover potential risks and
                losses.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">7. Privacy and Data Protection</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>7.1. We collect and process your personal data in accordance with our Privacy Policy.</p>
              <p>
                7.2. By using our services, you consent to the collection and use of your information as described in our
                Privacy Policy.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">8. Intellectual Property</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>
                8.1. All content on our website and mobile application is the property of Rea Travel or its content suppliers
                and is protected by international copyright laws.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">9. Modifications to Services and Terms</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>9.1. Rea Travel reserves the right to modify or discontinue any part of its services without notice.</p>
              <p>
                9.2. We may update these Terms and Conditions from time to time. Continued use of our services after any
                changes constitutes your acceptance of the new Terms and Conditions.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">10. Governing Law and Jurisdiction</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>
                10.1. These Terms and Conditions are governed by and construed in accordance with the laws of Your
                Country/State.
              </p>
              <p>
                10.2. Any disputes arising from these terms will be subject to the exclusive jurisdiction of the courts in
                Your City/State.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">11. Contact Information</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <p className="mb-4">If you have any questions about these Terms and Conditions, please contact us at:</p>
              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="font-semibold text-xl mb-4">Travello Travel Agency</h3>
                <ul className="space-y-2">
                  <li className="flex items-center">
                    <span className="font-medium mr-2">Email:</span>
                    <a href="mailto:support@reatravel.com" className="text-blue-600 hover:text-blue-800">
                      support@reatravel.com
                    </a>
                  </li>
                  <li className="flex items-center">
                    <span className="font-medium mr-2">Phone:</span>
                    <a href="tel:+254729582121" className="text-blue-600 hover:text-blue-800">
                      +254 (729) 582-121
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <AnimatedSection 
            className="mt-12 p-6 bg-gray-50 rounded-lg border border-gray-200"
            delay={0.4}
          >
            <p className="text-center text-gray-600">
              By using our services, you acknowledge that you have read, understood, and agree to be bound by these Terms
              and Conditions.
            </p>
          </AnimatedSection>
        </AnimatedSection>
      </div>
    </main>
  )
}