/**
 * Unified pricing calculation system for flight booking
 * Handles seats, services, and total pricing across all components
 */

export interface PricingBreakdown {
  baseFare: number
  taxes: number
  seatFees: number
  serviceFees: number
  baggageFees: number
  total: number
  currency: string
}

export interface SeatPrices {
  outbound: number
  return: number
}

export interface ServiceInfo {
  objectKey: string
  name: string
  price: number
  currency: string
  isFree: boolean
}

export interface BaggageSelection {
  checkedBags: number
  specialEquipment: 'none'
}

/**
 * Calculate total seat fees from seat prices
 */
export function calculateSeatFees(seatPrices: SeatPrices): number {
  return (seatPrices.outbound || 0) + (seatPrices.return || 0)
}

/**
 * Calculate total service fees from selected services
 */
export function calculateServiceFees(
  selectedServices: string[], 
  services: any[]
): { total: number; currency: string; serviceDetails: ServiceInfo[] } {
  let total = 0
  let currency = 'USD'
  const serviceDetails: ServiceInfo[] = []

  // Ensure services is an array
  const servicesArray = Array.isArray(services) ? services : []

  selectedServices.forEach(serviceKey => {
    const service = servicesArray.find(s => s.objectKey === serviceKey)
    if (service) {
      const price = service.price?.[0]?.total?.value || 0
      const serviceCurrency = service.price?.[0]?.total?.code || 'USD'
      
      total += price
      currency = serviceCurrency // Use the last service's currency as fallback
      
      serviceDetails.push({
        objectKey: service.objectKey,
        name: service.name?.value || 'Unknown Service',
        price,
        currency: serviceCurrency,
        isFree: price === 0
      })
    }
  })

  return { total, currency, serviceDetails }
}

/**
 * Calculate baggage fees from baggage selection
 */
export function calculateBaggageFees(
  baggageSelection: BaggageSelection | null,
  additionalBagPrice: number = 0, // No hardcoded fallback - use actual API prices
  currency: string = 'USD'
): { total: number; currency: string } {
  if (!baggageSelection) {
    return { total: 0, currency }
  }

  const specialEquipmentPrices = {
    none: 0
  }

  const baggageCost = baggageSelection.checkedBags * additionalBagPrice
  const specialEquipmentCost = specialEquipmentPrices[baggageSelection.specialEquipment]
  
  return {
    total: baggageCost + specialEquipmentCost,
    currency
  }
}

/**
 * Calculate complete pricing breakdown
 */
export function calculatePricingBreakdown(
  baseFare: number,
  taxes: number,
  seatPrices: SeatPrices,
  selectedServices: string[],
  services: any[],
  baggageSelection: BaggageSelection | null = null,
  additionalBagPrice: number = 0,
  currency: string = 'USD'
): PricingBreakdown {
  const seatFees = calculateSeatFees(seatPrices)
  const { total: serviceFees } = calculateServiceFees(selectedServices, services)
  const { total: baggageFees } = calculateBaggageFees(baggageSelection, additionalBagPrice, currency)
  
  const total = baseFare + taxes + seatFees + serviceFees + baggageFees

  return {
    baseFare,
    taxes,
    seatFees,
    serviceFees,
    baggageFees,
    total,
    currency
  }
}

/**
 * Extract pricing information from flight offer data
 */
export function extractFlightPricing(flightOffer: any): {
  baseFare: number
  taxes: number
  total: number
  currency: string
  passengerBreakdown?: any[]
} {
  let currency = 'USD'
  let totalPrice = 0
  let taxes = 0
  let baseFare = 0
  let passengerBreakdown: any[] = []

  // Use the same pricing structure as order-summary component
  if (flightOffer.total_price) {
    totalPrice = flightOffer.total_price.amount || 0
    currency = flightOffer.total_price.currency || 'USD'

    // Extract base fare and taxes from passengers pricing
    if (flightOffer.passengers && Array.isArray(flightOffer.passengers)) {
      passengerBreakdown = flightOffer.passengers
      const firstPassenger = flightOffer.passengers[0]
      if (firstPassenger?.pricing) {
        baseFare = firstPassenger.pricing.base_fare?.amount || 0
        taxes = firstPassenger.pricing.taxes?.amount || 0
      }
    }
  } else if (flightOffer.pricing) {
    // Fallback to booking pricing if available
    totalPrice = flightOffer.pricing.total || 0
    baseFare = flightOffer.pricing.baseFare || 0
    taxes = flightOffer.pricing.taxes || 0
    currency = flightOffer.pricing.currency || flightOffer.currency || 'USD'
  }

  return {
    baseFare,
    taxes,
    total: totalPrice,
    currency,
    passengerBreakdown: passengerBreakdown.length > 0 ? passengerBreakdown : undefined
  }
}

/**
 * Format seat summary for display
 */
export function formatSeatSummary(selectedSeats: { outbound: string[]; return: string[] }): string {
  const outboundSeats = selectedSeats.outbound.length
  const returnSeats = selectedSeats.return.length
  const totalSeats = outboundSeats + returnSeats
  
  if (totalSeats === 0) return "No seat selected"
  
  const segments = []
  if (outboundSeats > 0) segments.push(`${selectedSeats.outbound.join(", ")}`)
  if (returnSeats > 0) segments.push(`Return: ${selectedSeats.return.join(", ")}`)
  
  return segments.join(" | ")
}

/**
 * Get passenger count display text
 */
export function getPassengerCountText(passengers: any[]): string {
  if (!passengers || passengers.length === 0) return "0 passengers"
  if (passengers.length === 1) return "1 passenger"
  return `${passengers.length} passengers`
}

/**
 * Validate pricing data consistency
 */
export function validatePricingConsistency(
  flightPricing: ReturnType<typeof extractFlightPricing>,
  seatPrices: SeatPrices,
  serviceFees: number,
  baggageFees: number = 0
): { isValid: boolean; warnings: string[] } {
  const warnings: string[] = []
  
  // Check for negative values
  if (flightPricing.baseFare < 0) warnings.push("Base fare is negative")
  if (flightPricing.taxes < 0) warnings.push("Taxes are negative")
  if (seatPrices.outbound < 0) warnings.push("Outbound seat price is negative")
  if (seatPrices.return < 0) warnings.push("Return seat price is negative")
  if (serviceFees < 0) warnings.push("Service fees are negative")
  if (baggageFees < 0) warnings.push("Baggage fees are negative")
  
  // Check for missing required data
  if (!flightPricing.currency) warnings.push("Currency is missing")
  if (flightPricing.total === 0 && flightPricing.baseFare === 0) {
    warnings.push("Both total and base fare are zero")
  }
  
  return {
    isValid: warnings.length === 0,
    warnings
  }
}