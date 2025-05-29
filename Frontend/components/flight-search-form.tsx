"use client"

import * as React from "react"
import { format } from "date-fns"
import { CalendarIcon, MapPin, Users } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

import type { FlightSearchRequest } from "../types/flight-api";

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

// Helper function to get city from airport code
function getCity(code: string): string {
  const airport = airports.find((a) => a.code === code)
  return airport ? airport.city : code
}

// Helper function to parse ISO 8601 duration strings (e.g., "PT7H55M") into minutes
function parseISODuration(durationString: string): number {
  if (!durationString || !durationString.startsWith('PT')) {
    return 0;
  }
  let totalMinutes = 0;
  const timeString = durationString.substring(2); // Remove "PT"

  const hourMatch = timeString.match(/(\d+)H/);
  if (hourMatch) {
    totalMinutes += parseInt(hourMatch[1], 10) * 60;
  }

  const minuteMatch = timeString.match(/(\d+)M/);
  if (minuteMatch) {
    totalMinutes += parseInt(minuteMatch[1], 10);
  }

  return totalMinutes;
}

export function FlightSearchForm() {
  const [departDate, setDepartDate] = React.useState<Date>()
  const [returnDate, setReturnDate] = React.useState<Date>()
  const [origin, setOrigin] = React.useState("")
  const [destination, setDestination] = React.useState("")
  const [passengers, setPassengers] = React.useState(1)
  const [cabinType, setCabinType] = React.useState("Y")
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [results, setResults] = React.useState<any>(null)
  const [meta, setMeta] = React.useState<any>(null)

  // Handlers for select changes
  const handleOriginChange = (value: string) => setOrigin(value) // Updated for Shadcn Select
  const handleDestinationChange = (value: string) => setDestination(value) // Updated for Shadcn Select
  const handlePassengersChange = (value: string) => setPassengers(Number(value))
  const handleCabinTypeChange = (value: string) => setCabinType(value)

  // Reusable function to render From, To, Depart, Return inputs
  const renderFlightLegInputs = (showReturnDate: boolean, keyPrefix: string = 'leg') => {
    return (
      <div className={`grid gap-4 sm:grid-cols-2 ${showReturnDate ? 'md:grid-cols-4' : 'md:grid-cols-3'}`}> {/* Adjust grid cols based on return date */} 
        {/* From */}
        <div className="w-full sm:col-span-1">
          <Select onValueChange={handleOriginChange} value={origin}>
            <SelectTrigger>
              <MapPin className="mr-2 h-4 w-4 text-muted-foreground" />
              <SelectValue placeholder="From" />
            </SelectTrigger>
            <SelectContent>
              {airports.map((airport) => (
                <SelectItem key={`${keyPrefix}-from-${airport.code}`} value={airport.code}>
                  {airport.city} ({airport.code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* To */}
        <div className="w-full sm:col-span-1">
          <Select onValueChange={handleDestinationChange} value={destination}>
            <SelectTrigger>
              <MapPin className="mr-2 h-4 w-4 text-muted-foreground" />
              <SelectValue placeholder="To" />
            </SelectTrigger>
            <SelectContent>
              {airports.map((airport) => (
                <SelectItem key={`${keyPrefix}-to-${airport.code}`} value={airport.code}>
                  {airport.city} ({airport.code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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

  // Build and submit the advanced search request
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setResults(null)
    setMeta(null)
    setLoading(true)
    
    // Validate required fields
    if (!origin || !destination || !departDate) {
      setError("Please fill in all required fields")
      setLoading(false)
      return
    }
    
    try {
      // Build payload dynamically from form inputs
      const payload: FlightSearchRequest = {
        Preference: {
          CabinPreferences: {
            CabinType: [
              {
                PrefLevel: { PrefLevelCode: "Preferred" },
                OriginDestinationReferences: ["OD1"],
                Code: cabinType, // Dynamic cabin type from user selection
              },
            ],
          },
          FarePreferences: {
            Types: {
              Type: [{ Code: "PUBL" }],
            },
          },
          PricingMethodPreference: {
            BestPricingOption: "Y",
          },
        },
        ResponseParameters: {
          ResultsLimit: { value: 10 },
          SortOrder: [
            { Order: "ASCENDING", Parameter: "PRICE" },
            { Order: "ASCENDING", Parameter: "STOP" },
            { Order: "ASCENDING", Parameter: "DEPARTURE_TIME" },
          ],
          ShopResultPreference: "FULL",
        },
        Travelers: {
          Traveler: [
            {
              AnonymousTraveler: Array.from({ length: passengers }, () => ({
                PTC: { value: "ADT" }, // Could be made dynamic with passenger type selector
                Age: {
                  Value: { value: 30 }, // Could be made dynamic with age input
                  BirthDate: { value: "1995-01-01" }, // Could be made dynamic with DOB picker
                },
              })),
            },
          ],
        },
        CoreQuery: {
          OriginDestinations: {
            OriginDestination: [
              {
                Departure: {
                  AirportCode: { value: origin },
                  Date: departDate.toISOString().split('T')[0],
                },
                Arrival: {
                  AirportCode: { value: destination },
                },
                OriginDestinationKey: "OD1",
              },
              // If return date is selected, add a return flight
              ...(returnDate ? [
                {
                  Departure: {
                    AirportCode: { value: destination },
                    Date: returnDate.toISOString().slice(0, 10),
                  },
                  Arrival: {
                    AirportCode: { value: origin },
                  },
                  OriginDestinationKey: "OD2",
                }
              ] : []),
            ],
          },
        },
      }
      
      // Send search request to Flask backend
      const response = await fetch('http://localhost:5000/api/flights/search', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          // Add any required authentication headers here
        },
        body: JSON.stringify(payload),
        cache: 'no-store',
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Search failed:', response.status, errorData);
        throw new Error(errorData.message || `Search failed: ${response.statusText}`);
      }
      
      // Process response from Flask backend
      const data = await response.json();
      setResults(data.flights || [])
      setMeta({
        total: data.total || 0,
        // Add any other metadata from your Flask response
      })
      setLoading(false)
    } catch (error: any) {
      console.error("Error searching flights", error)
      setError(error.message || "Failed to search flights")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full px-2 sm:px-0">
      <Tabs defaultValue="round-trip" className="w-full">
        <TabsList className="grid w-full grid-cols-3 overflow-x-auto sm:grid-cols-3">
          <TabsTrigger value="round-trip" className="text-xs sm:text-sm">Round Trip</TabsTrigger>
          <TabsTrigger value="one-way" className="text-xs sm:text-sm">One Way</TabsTrigger>
          <TabsTrigger value="multi-city" className="text-xs sm:text-sm">Multi-City</TabsTrigger>
        </TabsList>
        <TabsContent value="round-trip" className="mt-4">
          {renderFlightLegInputs(true, 'rt')}
 
           {/* Common Fields Below */}
           <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-5">
            {/* Passengers */}
            <div className="w-full sm:col-span-1">
              <Select onValueChange={handlePassengersChange} value={String(passengers)}>
                <SelectTrigger>
                  <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                  <SelectValue placeholder="Passengers" />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                    <SelectItem key={num} value={String(num)}>
                      {num} Passenger{num > 1 ? "s" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Cabin Type */}
            <div className="w-full sm:col-span-1">
              <Select onValueChange={handleCabinTypeChange} value={cabinType}>
                <SelectTrigger>
                  {/* Consider an icon for cabin type */}
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
            
            {/* Add Another Flight Button */}
            <div className="w-full sm:col-span-1">
              <Button variant="outline" className="w-full">
                + Add Another Flight
              </Button>
            </div>
          </div>

          <div className="mt-4 flex justify-center">
            <Button 
              className="px-8" 
              onClick={handleSubmit} 
              disabled={loading || !origin || !destination || !departDate}
            >
              {loading ? "Searching..." : "Search Flights"}
            </Button>
          </div>
          
          {error && (
            <div className="mt-4 text-center text-red-500">{error}</div>
          )}
          
          {results && (
            <div className="mt-6 border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Search Results</h3>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto max-h-60">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          )}
        </TabsContent>

        <TabsContent value="one-way" className="mt-4">
          {renderFlightLegInputs(false, 'ow')}
 
           {/* Common Fields Below */}
           <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4"> {/* Adjusted grid cols */} 
            {/* Passengers */}
            <div className="w-full sm:col-span-1">
              <Select onValueChange={handlePassengersChange} value={String(passengers)}>
                <SelectTrigger>
                  <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                  <SelectValue placeholder="Passengers" />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                    <SelectItem key={num} value={String(num)}>
                      {num} Passenger{num > 1 ? "s" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Cabin Type */}
            <div className="w-full sm:col-span-1">
              <Select onValueChange={handleCabinTypeChange} value={cabinType}>
                <SelectTrigger>
                  {/* Consider an icon for cabin type */}
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
            
            {/* Add Another Flight Button */}
            <div className="w-full sm:col-span-1">
              <Button variant="outline" className="w-full">
                + Add Another Flight
              </Button>
            </div>
          </div>

          <div className="mt-4 flex justify-center">
            <Button 
              className="px-8" 
              onClick={handleSubmit} 
              disabled={loading || !origin || !destination || !departDate}
            >
              {loading ? "Searching..." : "Search Flights"}
            </Button>
          </div>
          
          {error && (
            <div className="mt-4 text-center text-red-500">{error}</div>
          )}
          
          {results && (
            <div className="mt-6 border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">Search Results</h3>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto max-h-60">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          )}
        </TabsContent>

        <TabsContent value="multi-city" className="mt-4">
           {/* Render first leg (no return date) */}
           {renderFlightLegInputs(false, 'mc-1')}
           {/* Render second leg (placeholder - needs proper state management) */}
           {renderFlightLegInputs(false, 'mc-2')}
 
           {/* Common Fields Below */}
           <div className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4"> {/* Adjusted grid cols */} 
             {/* Passengers */} 
             <div className="w-full sm:col-span-1">
               <Select onValueChange={handlePassengersChange} value={String(passengers)}>
                 <SelectTrigger>
                   <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                   <SelectValue placeholder="Passengers" />
                 </SelectTrigger>
                 <SelectContent>
                   {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                     <SelectItem key={num} value={String(num)}>
                       {num} Passenger{num > 1 ? "s" : ""}
                     </SelectItem>
                   ))}
                 </SelectContent>
               </Select>
             </div>

             {/* Cabin Type */} 
             <div className="w-full sm:col-span-1">
               <Select onValueChange={handleCabinTypeChange} value={cabinType}>
                 <SelectTrigger>
                   {/* Consider an icon for cabin type */}
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
               onClick={handleSubmit} 
               disabled={loading || !origin || !destination || !departDate}
             >
               {loading ? "Searching..." : "Search Flights"}
             </Button>
           </div>
         </TabsContent>
       </Tabs>
     </div>
   )
 }
