"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { ReactNode } from "react"

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

export default function PrivacyPolicy() {
  const lastUpdated = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto px-4 py-16">
        <AnimatedSection className="max-w-4xl mx-auto mb-12">
          <Link 
            href="/" 
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>
          
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Privacy Policy
          </h1>
          <p className="text-gray-600">
            Last updated: {lastUpdated}
          </p>
        </AnimatedSection>

        <AnimatedSection 
          className="max-w-4xl mx-auto prose prose-lg prose-gray prose-headings:text-gray-900 prose-p:text-gray-600"
          delay={0.2}
        >
          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <p>
                At Rea Travel, we take your privacy seriously. This Privacy Policy explains how we collect, use, disclose, and 
                safeguard your information when you visit our website or use our services. Please read this privacy policy 
                carefully. By using our services, you consent to the data practices described in this statement.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <h3 className="text-xl font-semibold">2.1 Personal Information</h3>
              <p>We may collect personal information that you provide to us, including but not limited to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Name and contact details</li>
                <li>Passport information</li>
                <li>Payment information</li>
                <li>Travel preferences and history</li>
                <li>Email communications</li>
              </ul>

              <h3 className="text-xl font-semibold">2.2 Automatically Collected Information</h3>
              <p>When you visit our website, we automatically collect certain information, including:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>IP address and browser type</li>
                <li>Device information</li>
                <li>Pages you view</li>
                <li>Time and date of your visits</li>
                <li>Cookies and tracking technologies</li>
              </ul>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>We use the information we collect for various purposes, including:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Processing your travel bookings</li>
                <li>Communicating with you about your bookings</li>
                <li>Sending promotional offers and newsletters</li>
                <li>Improving our services</li>
                <li>Complying with legal obligations</li>
                <li>Detecting and preventing fraud</li>
              </ul>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">4. Information Sharing</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>We may share your information with:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Travel service providers (airlines, hotels, etc.)</li>
                <li>Payment processors</li>
                <li>Marketing partners</li>
                <li>Legal authorities when required</li>
              </ul>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">5. Your Rights</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
              <p>You have the right to:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Access your personal data</li>
                <li>Correct inaccurate data</li>
                <li>Request deletion of your data</li>
                <li>Withdraw consent for marketing communications</li>
                <li>Request data portability</li>
              </ul>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-4">6. Contact Us</h2>
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <p className="mb-4">If you have any questions about this Privacy Policy, please contact us at:</p>
              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="font-semibold text-xl mb-4">Rea Travel</h3>
                <ul className="space-y-2">
                  <li className="flex items-center">
                    <span className="font-medium mr-2">Email:</span>
                    <a href="mailto:privacy@reatravel.com" className="text-blue-600 hover:text-blue-800">
                      privacy@reatravel.com
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
              This Privacy Policy was last updated on {lastUpdated}. We reserve the right to modify this policy at any time.
            </p>
          </AnimatedSection>
        </AnimatedSection>
      </div>
    </main>
  )
}