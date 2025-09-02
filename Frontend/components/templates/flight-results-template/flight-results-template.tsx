/**
 * Flight Results Template - Flight listing/results page layout
 * 
 * This template provides the layout structure for flight results pages.
 * It includes search summary, filters, sorting options, and flight listings
 * in a responsive layout optimized for browsing and comparing flights.
 */

import { ReactNode } from "react"

interface FlightResultsTemplateProps {
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

export function FlightResultsTemplate({
  searchSummary,
  filters,
  sortOptions,
  flightResults,
  loading = false,
  emptyState,
  pagination,
  className
}: FlightResultsTemplateProps) {
  return (
    <div className={`flight-results-template ${className || ''}`}>
      {/* Search Summary */}
      {searchSummary && (
        <section className="search-summary-section">
          <div className="container mx-auto px-4 py-4">
            {searchSummary}
          </div>
        </section>
      )}

      <div className="container mx-auto px-4 py-6">
        <div className="flight-results-layout grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          {filters && (
            <aside className="filters-sidebar lg:col-span-1">
              <div className="sticky top-4">
                {filters}
              </div>
            </aside>
          )}

          {/* Main Results Area */}
          <main className={`results-main ${filters ? 'lg:col-span-3' : 'lg:col-span-4'}`}>
            {/* Sort Options */}
            {sortOptions && (
              <div className="sort-section mb-6">
                {sortOptions}
              </div>
            )}

            {/* Results Content */}
            <div className="results-content">
              {loading ? (
                <div className="loading-state">
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">Searching for flights...</p>
                  </div>
                </div>
              ) : flightResults ? (
                <>
                  {flightResults}
                  {pagination && (
                    <div className="pagination-section mt-8">
                      {pagination}
                    </div>
                  )}
                </>
              ) : emptyState ? (
                <div className="empty-state">
                  {emptyState}
                </div>
              ) : null}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}