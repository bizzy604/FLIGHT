"use client"

import { memo } from "react"
import { Search, ArrowLeftRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import {
  AirportSelector,
  DateRangeSelector,
  PassengerSelector,
  CabinSelector
} from "@/components/molecules"
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
    <Card className={cn("w-full max-w-6xl mx-auto", className)}>
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">
          Search Flights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Trip Type Selection */}
        <Tabs 
          value={formData.tripType} 
          onValueChange={handleTripTypeChange}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="round-trip">Round Trip</TabsTrigger>
            <TabsTrigger value="one-way">One Way</TabsTrigger>
            <TabsTrigger value="multi-city">Multi City</TabsTrigger>
          </TabsList>

          <TabsContent value="round-trip" className="space-y-6">
            <FlightSearchContent
              formData={formData}
              errors={errors}
              onFormDataChange={setFormData}
              onSwapAirports={handleSwapAirports}
              onPassengerChange={handlePassengerChange}
              showReturnDate={true}
              disabled={disabled}
            />
          </TabsContent>

          <TabsContent value="one-way" className="space-y-6">
            <FlightSearchContent
              formData={formData}
              errors={errors}
              onFormDataChange={setFormData}
              onSwapAirports={handleSwapAirports}
              onPassengerChange={handlePassengerChange}
              showReturnDate={false}
              disabled={disabled}
            />
          </TabsContent>

          <TabsContent value="multi-city" className="space-y-6">
            {/* Multi-city implementation would go here */}
            <div className="text-center py-8 text-muted-foreground">
              Multi-city search coming soon...
            </div>
          </TabsContent>
        </Tabs>

        {/* Error Display */}
        {errors.general && (
          <Alert variant="destructive">
            <AlertDescription>{errors.general}</AlertDescription>
          </Alert>
        )}

        {/* Search Button */}
        <div className="flex justify-center pt-4">
          <Button
            size="lg"
            onClick={handleSearch}
            disabled={isSubmitDisabled}
            className="w-full max-w-md"
          >
            {loading ? (
              "Searching..."
            ) : (
              <>
                <Search className="mr-2 h-5 w-5" />
                Search Flights
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
})

// Extracted content component for reusability
interface FlightSearchContentProps {
  formData: any
  errors: any
  onFormDataChange: (data: any) => void
  onSwapAirports: () => void
  onPassengerChange: (type: 'adults' | 'children' | 'infants', value: number) => void
  showReturnDate: boolean
  disabled: boolean
}

const FlightSearchContent = memo(function FlightSearchContent({
  formData,
  errors,
  onFormDataChange,
  onSwapAirports,
  onPassengerChange,
  showReturnDate,
  disabled
}: FlightSearchContentProps) {
  return (
    <>
      {/* Origin and Destination */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
        <AirportSelector
          label="From"
          value={formData.origin}
          onChange={(value) => onFormDataChange({ origin: value })}
          placeholder="Select departure airport"
          disabled={disabled}
          error={errors.origin}
        />
        
        {/* Swap Button */}
        <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
          <Button
            variant="outline"
            size="icon"
            onClick={onSwapAirports}
            disabled={disabled}
            className="rounded-full bg-background border-2"
          >
            <ArrowLeftRight className="h-4 w-4" />
          </Button>
        </div>
        
        <AirportSelector
          label="To"
          value={formData.destination}
          onChange={(value) => onFormDataChange({ destination: value })}
          placeholder="Select destination airport"
          disabled={disabled}
          error={errors.destination}
        />
      </div>

      {/* Dates */}
      <DateRangeSelector
        departDate={formData.departDate}
        returnDate={formData.returnDate}
        onDepartDateChange={(date) => onFormDataChange({ departDate: date })}
        onReturnDateChange={(date) => onFormDataChange({ returnDate: date })}
        showReturnDate={showReturnDate}
        disabled={disabled}
        minDate={new Date()}
      />

      <Separator />

      {/* Passengers and Cabin */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <PassengerSelector
          passengers={formData.passengers}
          onPassengersChange={onPassengerChange}
          disabled={disabled}
        />
        
        <CabinSelector
          value={formData.cabinType}
          onChange={(value) => onFormDataChange({ cabinType: value })}
          disabled={disabled}
          error={errors.cabinType}
        />
      </div>
    </>
  )
})

FlightSearchForm.displayName = "FlightSearchForm"