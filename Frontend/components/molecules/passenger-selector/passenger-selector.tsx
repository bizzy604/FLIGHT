"use client"

import { memo } from "react"
import { Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { PassengerCounter } from "@/components/ui/passenger-counter/passenger-counter"
import { cn } from "@/utils/cn"
import { usePassengerRules } from "./use-passenger-rules"
import type { PassengerSelectorProps, PassengerTypeConfig } from "./passenger-selector.types"

const passengerConfigs: PassengerTypeConfig[] = [
  { type: 'adults', label: 'Adults', ageRange: '12+ years', min: 1, max: 9 },
  { type: 'children', label: 'Children', ageRange: '2-11 years', min: 0, max: 8 },
  { type: 'infants', label: 'Infants', ageRange: 'Under 2 years', min: 0, max: 4 },
]

export const PassengerSelector = memo(function PassengerSelector({
  passengers,
  onPassengersChange,
  disabled = false,
  className,
  maxPassengers = 9,
}: PassengerSelectorProps) {
  const passengerRules = usePassengerRules(passengers, { maxPassengers })

  const handlePassengerChange = (type: PassengerTypeConfig['type'], change: number) => {
    const newValue = passengers[type] + change
    const updatedPassengers = passengerRules.updatePassengers(type, newValue)
    
    // Only call onChange if the value actually changed
    if (updatedPassengers[type] !== passengers[type]) {
      onPassengersChange(type, updatedPassengers[type])
    }
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn("w-full justify-start", className)}
          disabled={disabled}
        >
          <Users className="mr-2 h-4 w-4" />
          {passengerRules.totalPassengers} {passengerRules.totalPassengers === 1 ? 'Passenger' : 'Passengers'}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-4">
        <div className="space-y-4">
          {passengerConfigs.map((config) => (
            <PassengerCounter
              key={config.type}
              label={config.label}
              description={config.ageRange}
              value={passengers[config.type]}
              onIncrement={() => handlePassengerChange(config.type, 1)}
              onDecrement={() => handlePassengerChange(config.type, -1)}
              canIncrement={passengerRules.canIncrement(config.type)}
              canDecrement={passengerRules.canDecrement(config.type)}
              disabled={disabled}
            />
          ))}
          
          {passengerRules.totalPassengers >= maxPassengers && (
            <p className="text-xs text-amber-600 mt-2">
              Maximum {maxPassengers} passengers allowed
            </p>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
})

PassengerSelector.displayName = "PassengerSelector"