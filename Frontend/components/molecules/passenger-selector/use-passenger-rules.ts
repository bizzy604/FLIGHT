import { useMemo } from "react"
import type { PassengerCounts, PassengerType } from "./passenger-selector.types"

interface PassengerRulesConfig {
  maxPassengers?: number
}

interface PassengerValidation {
  canIncrement: (type: PassengerType) => boolean
  canDecrement: (type: PassengerType) => boolean
  updatePassengers: (type: PassengerType, value: number) => PassengerCounts
  totalPassengers: number
}

export function usePassengerRules(
  passengers: PassengerCounts,
  config: PassengerRulesConfig = {}
): PassengerValidation {
  const { maxPassengers = 9 } = config
  
  const totalPassengers = useMemo(() => 
    passengers.adults + passengers.children + passengers.infants,
    [passengers]
  )

  const canDecrement = (type: PassengerType): boolean => {
    const currentValue = passengers[type]
    
    switch (type) {
      case 'adults':
        // Must have at least 1 adult, or at least as many adults as infants
        return currentValue > Math.max(1, passengers.infants)
      case 'children':
        return currentValue > 0
      case 'infants':
        return currentValue > 0
      default:
        return false
    }
  }

  const canIncrement = (type: PassengerType): boolean => {
    const currentValue = passengers[type]
    
    // Check total passenger limit first
    if (totalPassengers >= maxPassengers) {
      return false
    }
    
    switch (type) {
      case 'adults':
        return currentValue < 9
      case 'children':
        return currentValue < 8
      case 'infants':
        // Infants can't exceed adults
        return currentValue < passengers.adults && currentValue < 4
      default:
        return false
    }
  }

  const updatePassengers = (type: PassengerType, value: number): PassengerCounts => {
    const newValue = Math.max(0, value)
    
    switch (type) {
      case 'adults': {
        // Ensure at least 1 adult, and at least as many as infants
        const minAdults = Math.max(1, passengers.infants)
        const finalValue = Math.max(minAdults, Math.min(9, newValue))
        return { ...passengers, adults: finalValue }
      }
      case 'children': {
        const finalValue = Math.min(8, newValue)
        // Check if total would exceed limit
        const newTotal = passengers.adults + finalValue + passengers.infants
        if (newTotal > maxPassengers) {
          return passengers // Don't change if it would exceed limit
        }
        return { ...passengers, children: finalValue }
      }
      case 'infants': {
        // Infants can't exceed adults
        const maxInfants = Math.min(passengers.adults, 4)
        const finalValue = Math.min(maxInfants, newValue)
        return { ...passengers, infants: finalValue }
      }
      default:
        return passengers
    }
  }

  return {
    canIncrement,
    canDecrement,
    updatePassengers,
    totalPassengers,
  }
}