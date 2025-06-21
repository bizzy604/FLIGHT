"use client"

import * as React from "react"
import { Users, Plus, Minus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

type PassengerType = 'adults' | 'children' | 'infants'

interface PassengersSelectorProps {
  passengers: {
    adults: number
    children: number
    infants: number
  }
  onPassengersChange: (type: PassengerType, value: number) => void
}

export function PassengersSelector({ passengers, onPassengersChange }: PassengersSelectorProps) {
  const totalPassengers = passengers.adults + passengers.children + passengers.infants

  const updatePassengers = (type: PassengerType, value: number) => {
    // Ensure we don't go below 0
    const newValue = Math.max(0, value)
    
    // For adults, ensure at least 1 if there are infants
    if (type === 'adults' && newValue === 0 && passengers.infants > 0) {
      onPassengersChange('adults', 1)
      return
    }
    
    // For infants, ensure not more than adults
    if (type === 'infants' && newValue > passengers.adults) {
      onPassengersChange('infants', passengers.adults)
      return
    }
    
    onPassengersChange(type, newValue)
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="w-full justify-start"
        >
          <Users className="mr-2 h-4 w-4" />
          {totalPassengers} {totalPassengers === 1 ? 'Passenger' : 'Passengers'}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-4">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Adults</p>
              <p className="text-xs text-muted-foreground">12+ years</p>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={() => updatePassengers('adults', passengers.adults - 1)}
                disabled={passengers.adults <= 1}
              >
                <Minus className="h-3 w-3" />
              </Button>
              <span className="w-6 text-center">{passengers.adults}</span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={() => updatePassengers('adults', passengers.adults + 1)}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Children</p>
              <p className="text-xs text-muted-foreground">2-11 years</p>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={() => updatePassengers('children', passengers.children - 1)}
                disabled={passengers.children <= 0}
              >
                <Minus className="h-3 w-3" />
              </Button>
              <span className="w-6 text-center">{passengers.children}</span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={() => updatePassengers('children', passengers.children + 1)}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Infants</p>
              <p className="text-xs text-muted-foreground">Under 2 years</p>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={() => updatePassengers('infants', passengers.infants - 1)}
                disabled={passengers.infants <= 0}
              >
                <Minus className="h-3 w-3" />
              </Button>
              <span className="w-6 text-center">{passengers.infants}</span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={() => updatePassengers('infants', passengers.infants + 1)}
                disabled={passengers.infants >= passengers.adults}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
