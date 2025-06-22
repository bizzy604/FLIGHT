"use client"

import * as React from "react"
import { format } from "date-fns"
import { CalendarIcon, MapPin, Users } from "lucide-react"
import { api } from "@/utils/api-client"
import { useLoading } from "@/utils/loading-state"
import { FlightOffer, FlightSearchRequest } from "@/utils/api-client"

import { cn } from "@/utils/cn"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PassengersSelector } from "@/components/passengers-selector"
import { Input } from "@/components/ui/input";

// Constants moved outside the component
const cabinTypes = [
  { value: "Y", label: "Economy" },
  { value: "W", label: "Premium Economy" },
  { value: "C", label: "Business Class" },
  { value: "F", label: "First Class" },
]

const airports = [
  { code: "JFK", name: "John F. Kennedy International Airport", city: "New York" },
  { code: "LAX", name: "Los Angeles International Airport", city: "Los Angeles" },
  { code: "LHR", name: "Heathrow Airport", city: "London" },
  { code: "CDG", name: "Charles de Gaulle Airport", city: "Paris" },
  { code: "HND", name: "Haneda Airport", city: "Tokyo" },
  { code: "BOM", name: "Chhatrapati Shivaji Maharaj International Airport", city: "Mumbai" },
  { code: "DXB", name: "Dubai International Airport", city: "Dubai" },
]

// Helper function to get airport display name
function getAirportDisplay(code: string): string {
  const airport = airports.find((a) => a.code === code);
  return airport ? `${airport.city} (${airport.code})` : code;
}

export function FlightSearchForm() {
  const [departDate, setDepartDate] = React.useState<Date>()
  const [returnDate, setReturnDate] = React.useState<Date>()
  const [origin, setOrigin] = React.useState("")
  const [destination, setDestination] = React.useState("")
  const [originQuery, setOriginQuery] = React.useState("");
  const [destinationQuery, setDestinationQuery] = React.useState("");
  const [passengers, setPassengers] = React.useState({
    adults: 1,
    children: 0,
    infants: 0
  })
  const [cabinType, setCabinType] = React.useState("Y")
  const [outboundCabinType, setOutboundCabinType] = React.useState("Y")
  const [returnCabinType, setReturnCabinType] = React.useState("Y")
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [results, setResults] = React.useState<FlightOffer[]>([])
  const [meta, setMeta] = React.useState<any>(null)
  const { setLoadingState } = useLoading()
  const [activeTab, setActiveTab] = React.useState('round-trip')
  const [segments, setSegments] = React.useState([{ origin: '', destination: '', departureDate: undefined as Date | undefined }])
  
  // Calculate total passengers
  const totalPassengers = passengers.adults + passengers.children + passengers.infants
  
  // Handle passenger count changes
  const handlePassengersChange = (type: 'adults' | 'children' | 'infants', value: number) => {
    setPassengers(prev => {
      const newPassengers = { ...prev, [type]: value }
      
      // Ensure infants don't exceed adults
      if (type === 'adults' && newPassengers.infants > value) {
        newPassengers.infants = value
      } else if (type === 'infants' && value > newPassengers.adults) {
        newPassengers.infants = newPassengers.adults
      }
      
      return newPassengers
    })
  }

  // Handlers for input changes
  const handleCabinTypeChange = (value: string) => setCabinType(value);
  const handleOutboundCabinTypeChange = (value: string) => setOutboundCabinType(value);
  const handleReturnCabinTypeChange = (value: string) => setReturnCabinType(value);

  const handleOriginChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setOrigin(value);
    setOriginQuery(value);
  };

  const handleDestinationChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setDestination(value);
    setDestinationQuery(value);
  };

  // Reusable function to render From, To, Depart, Return inputs
  const renderFlightLegInputs = (showReturnDate: boolean, keyPrefix: string = 'leg') => {
    return (
      <div className={`grid gap-4 sm:grid-cols-2 ${showReturnDate ? 'md:grid-cols-4' : 'md:grid-cols-3'}`}>
        {/* From */}
        <div className="w-full sm:col-span-1">
          <Label htmlFor={`${keyPrefix}-origin-input`}>From</Label>
          <div className="relative mt-1">
            <div className="flex items-center">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                id={`${keyPrefix}-origin-input`}
                type="text"
                placeholder="City or airport code"
                value={originQuery}
                onChange={handleOriginChange}
                className="pl-10"
              />
            </div>
          </div>
        </div>

        {/* To */}
        <div className="w-full sm:col-span-1">
          <Label htmlFor={`${keyPrefix}-destination-input`}>To</Label>
          <div className="relative mt-1">
            <div className="flex items-center">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                id={`${keyPrefix}-destination-input`}
                type="text"
                placeholder="City or airport code"
                value={destinationQuery}
                onChange={handleDestinationChange}
                className="pl-10"
              />
            </div>
          </div>
        </div>

        {/* Depart Date */}
        <div className="w-full sm:col-span-1">
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant={"outline"}
                className={cn(
                  "w-full justify-start text-left font-normal",
                  !departDate && "text-muted-foreground",
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {departDate ? format(departDate, "PPP") : <span>Depart Date</span>}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar mode="single" selected={departDate} onSelect={setDepartDate} initialFocus />
            </PopoverContent>
          </Popover>
        </div>

        {/* Return Date (Conditional) */}
        {showReturnDate && (
          <div className="w-full sm:col-span-1">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant={"outline"}
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !returnDate && "text-muted-foreground",
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {returnDate ? format(returnDate, "PPP") : <span>Return Date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar mode="single" selected={returnDate} onSelect={setReturnDate} initialFocus />
              </PopoverContent>
            </Popover>
          </div>
        )}
      </div>
    );
  }

  // Function to handle search logic
  const performSearch = async () => {
    setError(null)
    setLoading(true)
    setLoadingState({ isLoading: true, error: undefined, data: undefined })

    try {
      const tripType = 
        activeTab === 'round-trip' ? 'round-trip' :
        activeTab === 'one-way' ? 'one-way' :
        'multi-city';

      // Create URLSearchParams object to build the query string
      const searchParams = new URLSearchParams();
      
      // Add basic search parameters
      searchParams.append('origin', origin.toUpperCase());
      searchParams.append('destination', destination.toUpperCase());
      searchParams.append('departDate', departDate ? format(departDate, 'yyyy-MM-dd') : '');
      searchParams.append('adults', passengers.adults.toString());
      searchParams.append('children', passengers.children.toString());
      searchParams.append('infants', passengers.infants.toString());
      // Use appropriate cabin type based on trip type
      if (tripType === 'round-trip') {
        searchParams.append('outboundCabinClass', outboundCabinType);
        searchParams.append('returnCabinClass', returnCabinType);
      } else {
        searchParams.append('cabinClass', cabinType);
      }
      
      // Add return date for round trips
      if (tripType === 'round-trip' && returnDate) {
        searchParams.append('returnDate', format(returnDate, 'yyyy-MM-dd'));
      }
      
      // Add trip type
      searchParams.append('tripType', tripType);
      
      // For multi-city trips, add each segment
      if (tripType === 'multi-city') {
        segments.forEach((segment, index) => {
          if (segment.origin && segment.destination && segment.departureDate) {
            searchParams.append(`segments[${index}].origin`, segment.origin.toUpperCase());
            searchParams.append(`segments[${index}].destination`, segment.destination.toUpperCase());
            searchParams.append(
              `segments[${index}].departureDate`,
              format(segment.departureDate, 'yyyy-MM-dd')
            );
          }
        });
      }
      
      // Navigate to the results page with the search parameters
      window.location.href = `/flights?${searchParams.toString()}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setLoadingState({ isLoading: false, error: err, data: undefined })
    } finally {
      setLoading(false)
      setLoadingState({ isLoading: false, error: undefined, data: undefined })
    }
  }

  // Handle form submission
  const handleFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    await performSearch()
  }

  // Handle button click
  const handleSearchButtonClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    await performSearch()
  }

  const addSegment = () => {
    setSegments([...segments, { origin: '', destination: '', departureDate: undefined }]);
  };
  
  const removeSegment = (index: number) => {
    if (segments.length > 1) {
      setSegments(segments.filter((_, i) => i !== index));
    }
  };
  
  const updateSegment = (index: number, field: string, value: any) => {
    const updated = [...segments];
    updated[index] = { ...updated[index], [field]: value };
    setSegments(updated);
  };

  return (
    <div className="w-full px-2 sm:px-0">
      <div className="backdrop-blur-md bg-white/30 dark:bg-gray-900/30 rounded-2xl p-6 shadow-xl border border-white/20">
      <Tabs className="w-full" value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 overflow-x-auto sm:grid-cols-3">
          <TabsTrigger value="round-trip" className="text-xs sm:text-sm">Round Trip</TabsTrigger>
          <TabsTrigger value="one-way" className="text-xs sm:text-sm">One Way</TabsTrigger>
          <TabsTrigger value="multi-city" className="text-xs sm:text-sm">Multi-City</TabsTrigger>
        </TabsList>
        
        {/* Round Trip Tab */}
        <TabsContent value="round-trip" className="mt-4">
          {renderFlightLegInputs(true, 'rt')}

          {/* Common Fields */}
          <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
            {/* Passengers */}
            <div className="w-full sm:col-span-1">
              <PassengersSelector 
                passengers={passengers} 
                onPassengersChange={handlePassengersChange} 
              />
            </div>

            {/* Outbound Cabin Type */}
            <div className="w-full sm:col-span-1">
              <Label className="text-sm font-medium mb-2 block">Outbound Cabin</Label>
              <Select onValueChange={handleOutboundCabinTypeChange} value={outboundCabinType}>
                <SelectTrigger>
                  <SelectValue placeholder="Outbound Cabin" />
                </SelectTrigger>
                <SelectContent>
                  {cabinTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Return Cabin Type */}
            <div className="w-full sm:col-span-1">
              <Label className="text-sm font-medium mb-2 block">Return Cabin</Label>
              <Select onValueChange={handleReturnCabinTypeChange} value={returnCabinType}>
                <SelectTrigger>
                  <SelectValue placeholder="Return Cabin" />
                </SelectTrigger>
                <SelectContent>
                  {cabinTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="mt-4 flex justify-center">
            <Button 
              className="px-8" 
              onClick={handleSearchButtonClick} 
              disabled={
                loading || 
                !origin || 
                !destination || 
                !departDate || 
                (activeTab === 'round-trip' && !returnDate)
              }
            >
              {loading ? "Searching..." : "Search Flights"}
            </Button>
          </div>
        </TabsContent>

        {/* One Way Tab */}
        <TabsContent value="one-way" className="mt-4">
          {renderFlightLegInputs(false, 'ow')}
          
          {/* Common Fields */}
          <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
            {/* Passengers */}
            <div className="w-full sm:col-span-1">
              <PassengersSelector 
                passengers={passengers} 
                onPassengersChange={handlePassengersChange} 
              />
            </div>

            {/* Cabin Type */}
            <div className="w-full sm:col-span-1">
              <Select onValueChange={handleCabinTypeChange} value={cabinType}>
                <SelectTrigger>
                  <SelectValue placeholder="Cabin Type" />
                </SelectTrigger>
                <SelectContent>
                  {cabinTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Placeholder for grid alignment */}
            <div className="sm:col-span-1"></div>
          </div>

          <div className="mt-4 flex justify-center">
            <Button 
              className="px-8" 
              onClick={handleSearchButtonClick} 
              disabled={
                loading || 
                !origin || 
                !destination || 
                !departDate
              }
            >
              {loading ? "Searching..." : "Search Flights"}
            </Button>
          </div>
        </TabsContent>

        {/* Multi-City Tab */}
        <TabsContent value="multi-city" className="mt-4">
          <div className="space-y-4">
            {segments.map((segment, index) => (
              <div key={index} className="space-y-4 border-b pb-4 mb-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium">Flight {index + 1}</h3>
                  {segments.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeSegment(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      Remove
                    </Button>
                  )}
                </div>
                
                <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
                  {/* From */}
                  <div className="w-full">
                    <Select 
                      value={segment.origin}
                      onValueChange={(value) => updateSegment(index, 'origin', value)}
                    >
                      <SelectTrigger>
                        <MapPin className="mr-2 h-4 w-4 text-muted-foreground" />
                        <SelectValue placeholder="From" />
                      </SelectTrigger>
                      <SelectContent>
                        {airports.map((airport) => (
                          <SelectItem key={`mci-from-${index}-${airport.code}`} value={airport.code}>
                            {airport.city} ({airport.code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* To */}
                  <div className="w-full">
                    <Select 
                      value={segment.destination}
                      onValueChange={(value) => updateSegment(index, 'destination', value)}
                    >
                      <SelectTrigger>
                        <MapPin className="mr-2 h-4 w-4 text-muted-foreground" />
                        <SelectValue placeholder="To" />
                      </SelectTrigger>
                      <SelectContent>
                        {airports.map((airport) => (
                          <SelectItem key={`mci-to-${index}-${airport.code}`} value={airport.code}>
                            {airport.city} ({airport.code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Depart Date */}
                  <div className="w-full">
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className={cn(
                            "w-full justify-start text-left font-normal",
                            !segment.departureDate && "text-muted-foreground",
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {segment.departureDate ? (
                            format(segment.departureDate, "PPP")
                          ) : (
                            <span>Depart Date</span>
                          )}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={segment.departureDate}
                          onSelect={(date) => updateSegment(index, 'departureDate', date)}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>

                  {/* Remove button for small screens */}
                  {segments.length > 1 && (
                    <div className="sm:hidden w-full">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeSegment(index)}
                        className="w-full text-red-500 hover:text-red-700"
                      >
                        Remove Flight
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Add Flight Button */}
            <Button
              type="button"
              variant="outline"
              className="w-full mt-2"
              onClick={addSegment}
            >
              + Add Another Flight
            </Button>

            {/* Common Fields */}
            <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
              {/* Passengers */}
              <div className="w-full sm:col-span-1">
                <PassengersSelector 
                  passengers={passengers} 
                  onPassengersChange={handlePassengersChange} 
                />
              </div>

              {/* Cabin Type */}
              <div className="w-full sm:col-span-1">
                <Select onValueChange={handleCabinTypeChange} value={cabinType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Cabin Type" />
                  </SelectTrigger>
                  <SelectContent>
                    {cabinTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="mt-4 flex justify-center">
              <Button 
                className="px-8" 
                onClick={handleSearchButtonClick}
                disabled={
                  (() => {
                    const isAnySegmentInvalid = segments.some(s => !s.origin || !s.destination || !s.departureDate);
                    return loading || isAnySegmentInvalid;
                  })()
                }
              >
                {loading ? "Searching..." : "Search Flights"}
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
      </div>
    </div>
  )
}