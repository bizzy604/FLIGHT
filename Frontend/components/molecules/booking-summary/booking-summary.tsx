"use client"

import * as React from "react"
import { cn } from "@/utils/cn"
import { Button } from "@/components/ui/button"

interface BookingSummaryProps {
  passengers: Array<{
    objectKey: string
    name: string
    type: string
  }>
  selectedSeats: {
    outbound: string[]
    return: string[]
  }
  selectedServices: string[]
  seatPrices: {
    outbound: number
    return: number
  }
  servicePrices: number
  currency?: string
  className?: string
  onContinue: () => void
}

export function BookingSummary({
  passengers,
  selectedSeats,
  selectedServices,
  seatPrices,
  servicePrices,
  currency = 'INR',
  className,
  onContinue
}: BookingSummaryProps) {
  const totalSeatCost = seatPrices.outbound + seatPrices.return
  const totalAmount = totalSeatCost + servicePrices
  
  const getSeatSummary = () => {
    const outboundSeats = selectedSeats.outbound.length
    const returnSeats = selectedSeats.return.length
    const totalSeats = outboundSeats + returnSeats
    
    if (totalSeats === 0) return "No seat selected"
    
    const segments = []
    if (outboundSeats > 0) segments.push(`${selectedSeats.outbound.join(", ")}`)
    if (returnSeats > 0) segments.push(`Return: ${selectedSeats.return.join(", ")}`)
    
    return segments.join(" | ")
  }

  return (
    <div className={cn("sticky top-6", className)}>
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <h3 className="text-lg font-bold text-gray-900 mb-5 pb-3 border-b-2 border-gray-200">
          Booking Summary
        </h3>
        
        {/* Passengers */}
        <div className="mb-5">
          <div className="text-sm font-semibold text-gray-600 mb-2">PASSENGERS</div>
          {passengers.map((passenger, index) => (
            <div key={passenger.objectKey} className="flex justify-between items-center py-1">
              <span className="text-sm text-gray-700">
                {passenger.type === 'ADULT' ? '1 Adult' : passenger.type} (PAX{index + 1})
              </span>
              <span className="text-sm font-medium text-gray-900">
                {passenger.type === 'ADULT' ? 'ADT' : passenger.type.substring(0, 3)}
              </span>
            </div>
          ))}
        </div>

        {/* Selected Seats */}
        <div className="mb-5">
          <div className="text-sm font-semibold text-gray-600 mb-2">SELECTED SEATS</div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-700 flex-1 pr-4">
              {getSeatSummary()}
            </span>
            <span className="text-sm font-medium text-gray-900">
              ₹{totalSeatCost.toLocaleString('en-IN')}
            </span>
          </div>
        </div>

        {/* Selected Services */}
        <div className="mb-5">
          <div className="text-sm font-semibold text-gray-600 mb-2">SELECTED SERVICES</div>
          {selectedServices.length === 0 ? (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-700">No services selected</span>
              <span className="text-sm font-medium text-gray-900">₹0</span>
            </div>
          ) : (
            <div className="space-y-1">
              {selectedServices.map((serviceKey, index) => (
                <div key={serviceKey} className="flex justify-between items-center">
                  <span className="text-sm text-gray-700">Service {index + 1}</span>
                  <span className="text-sm font-medium text-gray-900">
                    ₹{(servicePrices / selectedServices.length).toLocaleString('en-IN')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Total Amount */}
        <div className="flex justify-between items-center pt-4 border-t-2 border-gray-200 mt-4">
          <span className="text-base font-semibold text-gray-900">Total Amount</span>
          <span className="text-2xl font-bold text-purple-600">
            ₹{totalAmount.toLocaleString('en-IN')}
          </span>
        </div>

        {/* Continue Button */}
        <Button
          className="w-full mt-6 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1 relative overflow-hidden"
          onClick={onContinue}
        >
          Continue to Payment
          <span className="absolute right-5 top-1/2 transform -translate-y-1/2 text-lg transition-transform group-hover:translate-x-1">
            →
          </span>
        </Button>
      </div>
    </div>
  )
}

