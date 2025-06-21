"use client"

import * as React from "react"
import { ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"

// Mock data for airlines
const airlineOptions = [
  { id: "sw", name: "SkyWay Airlines" },
  { id: "ga", name: "Global Airways" },
  { id: "pa", name: "Pacific Air" },
  { id: "ae", name: "Atlantic Express" },
  { id: "ua", name: "United Airlines" },
  { id: "dl", name: "Delta Air Lines" },
  { id: "ac", name: "Air Canada" }
]

// Define props interface for the FlightFilters component
interface FlightFiltersProps {
  priceRange: [number, number]
  onPriceRangeChange: (range: [number, number]) => void
  airlines: string[]
  onAirlinesChange: (airlines: string[]) => void
  stops: number[]
  onStopsChange: (stops: number[]) => void
  departureTime: string[]
  onDepartureTimeChange: (time: string[]) => void
  onResetFilters: () => void
}

export function FlightFilters({
  priceRange,
  onPriceRangeChange,
  airlines,
  onAirlinesChange,
  stops,
  onStopsChange,
  departureTime,
  onDepartureTimeChange,
  onResetFilters
}: FlightFiltersProps) {
  // Local UI state variables
  const [localPriceRange, setLocalPriceRange] = React.useState(priceRange)
  const [departureTimeRange, setDepartureTimeRange] = React.useState([0, 24])
  const [arrivalTimeRange, setArrivalTimeRange] = React.useState([0, 24])

  // Data formatting is now handled by the backend
  // Frontend components should use FlightOffer data directly

  return (
    <div className="space-y-6">
      {/* Stops Filter */}
      <div>
        <h3 className="mb-2 text-sm font-medium">Stops</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="stops-direct"
              checked={stops.includes(0)}
              onCheckedChange={(checked) => {
                if (checked) {
                  onStopsChange([...stops, 0])
                } else {
                  onStopsChange(stops.filter((stop) => stop !== 0))
                }
              }}
            />
            <label
              htmlFor="stops-direct"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Direct flights only
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="stops-1"
              checked={stops.includes(1)}
              onCheckedChange={(checked) => {
                if (checked) {
                  onStopsChange([...stops, 1])
                } else {
                  onStopsChange(stops.filter((stop) => stop !== 1))
                }
              }}
            />
            <label
              htmlFor="stops-1"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              1 stop
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="stops-2"
              checked={stops.includes(2)}
              onCheckedChange={(checked) => {
                if (checked) {
                  onStopsChange([...stops, 2])
                } else {
                  onStopsChange(stops.filter((stop) => stop !== 2))
                }
              }}
            />
            <label
              htmlFor="stops-2"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              2+ stops
            </label>
          </div>
        </div>
      </div>

      <Separator />

      {/* Price Range Filter */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-medium">Price Range</h3>
          <span className="text-xs text-muted-foreground">
            ${priceRange[0]} - ${priceRange[1]}
          </span>
        </div>
        <Slider
          defaultValue={priceRange}
          min={0}
          max={100000}
          step={1000}
          value={localPriceRange}
          onValueChange={(value) => {
            setLocalPriceRange(value as [number, number])
          }}
          className="py-4"
        />
      </div>

      <Separator />

      {/* Departure Time Filter */}
      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between">
          <h3 className="text-sm font-medium">Departure Time</h3>
          <ChevronDown className="h-4 w-4" />
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {Math.floor(departureTimeRange[0]).toString().padStart(2, '0')}:00 - {Math.floor(departureTimeRange[1]).toString().padStart(2, '0')}:00
            </span>
          </div>
          <Slider
            defaultValue={[0, 24]}
            min={0}
            max={24}
            step={0.5}
            value={departureTimeRange}
            onValueChange={setDepartureTimeRange}
            className="py-4"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>12 AM</span>
            <span>12 PM</span>
            <span>11:59 PM</span>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Separator />

      {/* Arrival Time Filter */}
      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between">
          <h3 className="text-sm font-medium">Arrival Time</h3>
          <ChevronDown className="h-4 w-4" />
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {Math.floor(arrivalTimeRange[0]).toString().padStart(2, '0')}:00 - {Math.floor(arrivalTimeRange[1]).toString().padStart(2, '0')}:00
            </span>
          </div>
          <Slider
            defaultValue={[0, 24]}
            min={0}
            max={24}
            step={0.5}
            value={arrivalTimeRange}
            onValueChange={setArrivalTimeRange}
            className="py-4"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>12 AM</span>
            <span>12 PM</span>
            <span>11:59 PM</span>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Separator />

      {/* Airlines Filter */}
      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between">
          <h3 className="text-sm font-medium">Airlines</h3>
          <ChevronDown className="h-4 w-4" />
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2">
          <div className="space-y-2">
            {airlineOptions.map((airline) => (
              <div key={airline.id} className="flex items-center space-x-2">
                <Checkbox
                  id={`airline-${airline.id}`}
                  checked={airlines.includes(airline.name)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      onAirlinesChange([...airlines, airline.name])
                    } else {
                      onAirlinesChange(airlines.filter((name) => name !== airline.name))
                    }
                  }}
                />
                <label
                  htmlFor={`airline-${airline.id}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {airline.name}
                </label>
              </div>
            ))}
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Separator />

      <div className="flex gap-2">
        <Button 
          className="flex-1"
          onClick={() => {
            // Apply the local price range to parent state
            onPriceRangeChange(localPriceRange as [number, number])
          }}
        >Apply Filters</Button>
        <Button 
          variant="outline"
          className="flex-1"
          onClick={onResetFilters}
        >Reset</Button>
      </div>
    </div>
  )
}