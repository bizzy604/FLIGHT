/**
 * Flight Search Template - Landing/Home page layout
 * 
 * This template provides the layout structure for the main flight search page.
 * It combines the flight search form organism with supporting sections in a
 * responsive layout optimized for search functionality.
 */

"use client"

import { ReactNode } from "react"
import { useRouter } from "next/navigation"
import { FlightSearchForm } from "@/components/organisms"
import type { FlightOffer } from "@/types/flight-api"

interface FlightSearchTemplateProps {
  /** Optional hero content above search form */
  heroContent?: ReactNode
  /** Optional promotional sections below search */
  promotionalSections?: ReactNode
  /** Optional partner/destination sections */
  supportingSections?: ReactNode
  /** Custom className for template styling */
  className?: string
}

export function FlightSearchTemplate({
  heroContent,
  promotionalSections,
  supportingSections,
  className
}: FlightSearchTemplateProps) {
  const router = useRouter()

  const handleSearch = (results: FlightOffer[], meta: any, formData?: any) => {
    // This callback now only handles successful results from the API
    // Immediate redirection is handled by the form itself
    console.log('Search completed with results:', results.length, 'offers')
  }

  // New function to handle immediate redirection when search button is clicked
  const handleSearchStart = (formData: any) => {
    // Validate that we have the minimum required data
    if (!formData.origin || !formData.destination || !formData.departDate) {
      return false // Let form handle validation errors
    }

    // Build URL with search parameters for immediate redirect
    const searchParams = new URLSearchParams({
      origin: formData.origin || '',
      destination: formData.destination || '',
      departDate: formData.departDate ? formData.departDate.toISOString().split('T')[0] : '',
      tripType: formData.tripType === 'round-trip' ? 'round-trip' : 'one-way',
      adults: formData.passengers?.adults?.toString() || '1',
      children: formData.passengers?.children?.toString() || '0',
      infants: formData.passengers?.infants?.toString() || '0',
      cabinClass: formData.cabinType || 'ECONOMY'
    })
    
    // Add return date for round-trip
    if (formData.tripType === 'round-trip' && formData.returnDate) {
      searchParams.set('returnDate', formData.returnDate.toISOString().split('T')[0])
    }
    
    // Immediately redirect to results page - this provides instant feedback to user
    router.push(`/flights?${searchParams.toString()}`)
    return true // Indicate successful redirection
  }

  const handleError = (error: string) => {
    // Handle search errors (could add toast notification here)
    console.error('Flight search error:', error)
  }

  return (
    <div className={`flight-search-template ${className || ''}`}>
      {/* Hero Section */}
      {heroContent && (
        <section className="hero-section">
          {heroContent}
        </section>
      )}

      {/* Main Search Section */}
      <section className="search-section">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <FlightSearchForm 
              onSearch={handleSearch}
              onError={handleError}
              onSearchStart={handleSearchStart}
            />
          </div>
        </div>
      </section>

      {/* Promotional Content */}
      {promotionalSections && (
        <section className="promotional-section">
          {promotionalSections}
        </section>
      )}

      {/* Supporting Sections (destinations, partners, etc.) */}
      {supportingSections && (
        <section className="supporting-sections">
          {supportingSections}
        </section>
      )}
    </div>
  )
}