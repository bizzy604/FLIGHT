"use client"

import { memo } from "react"
import { ArrowLeftRight } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  AirportSelector,
  DateRangeSelector,
  DateSelector,
  PassengerSelector,
  CabinSelector
} from "@/components/molecules"
import { FullscreenLoadingOverlay } from "@/components/atoms"
import { cn } from "@/utils/cn"
import { useFlightSearch } from "./use-flight-search"
import type { FlightSearchFormProps } from "./flight-search-form.types"

export const FlightSearchForm = memo(function FlightSearchForm({
  onSearch,
  onError,
  onSearchStart,
  initialValues,
  disabled = false,
  className,
}: FlightSearchFormProps) {
  const {
    formData,
    errors,
    loading,
    setFormData,
    handleSearch
  } = useFlightSearch(initialValues, onSearch, onError, onSearchStart)

  const handleTripTypeChange = (tripType: string) => {
    setFormData({ 
      tripType: tripType as 'round-trip' | 'one-way' | 'multi-city',
      returnDate: tripType === 'one-way' ? undefined : formData.returnDate
    })
  }

  const handleSwapAirports = () => {
    setFormData({
      origin: formData.destination,
      destination: formData.origin
    })
  }

  const handlePassengerChange = (type: 'adults' | 'children' | 'infants', value: number) => {
    setFormData({
      passengers: {
        ...formData.passengers,
        [type]: value
      }
    })
  }

  const isSubmitDisabled = loading || disabled || !formData.origin || !formData.destination || !formData.departDate

  return (
    <div className={cn("w-full", className)}>
      {/* Full-screen loading overlay */}
      <FullscreenLoadingOverlay 
        isVisible={loading} 
        message="Searching for flights..."
      />
      
      <div className="bg-card border border-border rounded-2xl p-2 shadow-2xl w-full animate-[slideUp_0.5s_ease-out]">
        {/* Trip Type - Horizontal Radio Buttons */}
        <div className="mb-2">
          <div className="flex bg-secondary rounded-lg p-1 w-fit">
            <button
              type="button"
              onClick={() => handleTripTypeChange('one-way')}
              disabled={disabled}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                formData.tripType === 'one-way'
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              )}
            >
              One way
            </button>
            <button
              type="button"
              onClick={() => handleTripTypeChange('round-trip')}
              disabled={disabled}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                formData.tripType === 'round-trip'
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              )}
            >
              Round trip
            </button>
          </div>
        </div>

        {/* Main Search Form */}
        <div className="flex gap-2 items-center flex-wrap">
          <style jsx>{`
            @keyframes slideUp {
              from {
                opacity: 0;
                transform: translateY(30px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
            @media (max-width: 1024px) {
              .search-form-container {
                flex-direction: column;
              }
              .swap-button-mobile {
                margin: -10px 0;
                transform: rotate(90deg);
              }
              .swap-button-mobile:hover {
                transform: rotate(270deg);
              }
            }
          `}</style>
          {/* From Airport */}
          <div className="bg-background border border-border rounded-xl px-5 py-4 flex-1 min-w-[180px] relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg group">
            <div className="text-xs font-medium text-muted-foreground mb-1 uppercase tracking-wider">FROM</div>
            <AirportSelector
              label=""
              value={formData.origin}
              onChange={(value) => setFormData({ origin: value })}
              placeholder="City or Airport"
              disabled={disabled}
              error={errors.origin}
              compact={true}
              inline={true}
              className="border-none shadow-none text-base font-medium text-foreground placeholder-muted-foreground bg-transparent focus:ring-0"
            />
          </div>

          {/* Swap Button */}
          <button
            onClick={handleSwapAirports}
            disabled={disabled}
            className="bg-background border-2 border-border rounded-full w-11 h-11 flex items-center justify-center cursor-pointer transition-all duration-300 flex-shrink-0 relative z-10 -mx-5 hover:bg-secondary hover:rotate-180 hover:border-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeftRight className="w-5 h-5 text-muted-foreground" />
          </button>

          {/* To Airport */}
          <div className="bg-background border border-border rounded-xl px-5 py-4 flex-1 min-w-[180px] relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg group">
            <div className="text-xs font-medium text-muted-foreground mb-1 uppercase tracking-wider">TO</div>
            <AirportSelector
              label=""
              value={formData.destination}
              onChange={(value) => setFormData({ destination: value })}
              placeholder="City or Airport"
              disabled={disabled}
              error={errors.destination}
              compact={true}
              inline={true}
              className="border-none shadow-none text-base font-medium text-foreground placeholder-muted-foreground bg-transparent focus:ring-0"
            />
          </div>

          {/* Depart Date */}
          <div className="bg-background border border-border rounded-xl px-5 py-4 flex-1 min-w-[160px] relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg group">
            <div className="text-xs font-medium text-muted-foreground mb-1 uppercase tracking-wider">DEPART</div>
            <DateSelector
              label=""
              value={formData.departDate}
              onChange={(date) => setFormData({ departDate: date })}
              placeholder="Departure Date"
              disabled={disabled}
              minDate={new Date()}
              className="border-none shadow-none text-base font-medium text-foreground bg-transparent focus:ring-0"
            />
          </div>

          {/* Return Date (if round trip) */}
          {formData.tripType === 'round-trip' && (
            <div className="bg-background border border-border rounded-xl px-5 py-4 flex-1 min-w-[160px] relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg group">
              <div className="text-xs font-medium text-muted-foreground mb-1 uppercase tracking-wider">RETURN</div>
              <DateSelector
                label=""
                value={formData.returnDate}
                onChange={(date) => setFormData({ returnDate: date })}
                placeholder="Return Date"
                disabled={disabled}
                minDate={formData.departDate ? (() => {
                  const nextDay = new Date(formData.departDate)
                  nextDay.setDate(nextDay.getDate() + 1)
                  return nextDay
                })() : new Date()}
                className="border-none shadow-none text-base font-medium text-foreground bg-transparent focus:ring-0"
              />
            </div>
          )}

          {/* Passengers */}
          <div className="bg-background border border-border rounded-xl px-5 py-4 flex-1 min-w-[160px] relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg group">
            <div className="text-xs font-medium text-muted-foreground mb-1 uppercase tracking-wider">TRAVELLERS</div>
            <PassengerSelector
              passengers={formData.passengers}
              onPassengersChange={handlePassengerChange}
              disabled={disabled}
            />
          </div>

          {/* Cabin Class */}
          <div className="bg-background border border-border rounded-xl px-5 py-4 flex-1 min-w-[140px] relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg group">
            <div className="text-xs font-medium text-muted-foreground mb-1 uppercase tracking-wider">CABIN CLASS</div>
            <CabinSelector
              value={formData.cabinType}
              onChange={(value) => setFormData({ cabinType: value })}
              disabled={disabled}
              error={errors.cabinType}
              label=""
              className="border-none shadow-none text-base font-medium text-foreground bg-transparent focus:ring-0"
            />
          </div>

          {/* Search Button */}
          <button
            onClick={handleSearch}
            disabled={isSubmitDisabled}
            className="px-8 py-5 flex-shrink-0 rounded-xl bg-primary text-primary-foreground font-semibold text-base cursor-pointer transition-all duration-300 uppercase tracking-wide shadow-lg hover:-translate-y-0.5 hover:shadow-xl hover:bg-primary/90 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2 inline-block"></div>
                Searching...
              </>
            ) : (
              'Search'
            )}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {errors.general && (
        <Alert variant="destructive" className="mt-4 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
          <AlertDescription className="text-sm text-red-700 dark:text-red-300">{errors.general}</AlertDescription>
        </Alert>
      )}
    </div>
  )
})


FlightSearchForm.displayName = "FlightSearchForm"