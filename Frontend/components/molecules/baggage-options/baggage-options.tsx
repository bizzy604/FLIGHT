"use client"
import { Minus, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { formatCurrency } from "@/utils/currency-formatter"

interface BaggageSelection {
  checkedBags: number
  specialEquipment: 'none'
}

interface BaggageOptionsProps {
  selectedBaggage: BaggageSelection
  onBaggageChange: (updatedBaggage: BaggageSelection) => void
  flightBaggageAllowance?: {
    carryOn?: string
    checked?: string
    additionalBagPrice?: number
    currency?: string
  }
  currency?: string
}

export function BaggageOptions({ 
  selectedBaggage, 
  onBaggageChange, 
  flightBaggageAllowance,
  currency = 'USD'
}: BaggageOptionsProps) {
  const checkedBags = selectedBaggage?.checkedBags ?? 0
  const specialEquipment = selectedBaggage?.specialEquipment ?? 'none'
  
  // Pricing constants from API or props - no hardcoded fallbacks
  const additionalBagPrice = flightBaggageAllowance?.additionalBagPrice ?? 0
  const specialEquipmentPrices = {
    none: 0
  }

  const incrementBags = () => {
    const newCount = Math.min(checkedBags + 1, 5) // Ensure max 5
    onBaggageChange({ ...selectedBaggage, checkedBags: newCount })
  }

  const decrementBags = () => {
    const newCount = Math.max(checkedBags - 1, 0) // Ensure min 0
    onBaggageChange({ ...selectedBaggage, checkedBags: newCount })
  }

  const handleSpecialEquipmentChange = (value: string) => {
    onBaggageChange({ 
      ...selectedBaggage, 
      specialEquipment: 'none'
    })
  }
  
  // Calculate total cost
  const baggageCost = checkedBags * additionalBagPrice
  const specialEquipmentCost = specialEquipmentPrices[specialEquipment]
  const totalCost = baggageCost + specialEquipmentCost

  return (
    <div className="space-y-6">
      <div className="rounded-md border p-4">
        <h4 className="mb-2 text-sm font-medium">Included in Your Fare</h4>
        <div className="space-y-2 text-sm">
          <p>• 1 personal item (must fit under the seat)</p>
          {flightBaggageAllowance?.carryOn ? (
            <p>• Carry-on: {flightBaggageAllowance.carryOn}</p>
          ) : (
            <p>• Carry-on allowance as per airline policy</p>
          )}
          {flightBaggageAllowance?.checked ? (
            <p>• Checked baggage: {flightBaggageAllowance.checked}</p>
          ) : (
            <p>• Checked baggage allowance as per airline policy</p>
          )}
        </div>
      </div>

      <div className="rounded-md border p-4">
        <h4 className="mb-4 text-sm font-medium">Additional Checked Baggage</h4>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Additional Checked Bags</p>
            <p className="text-sm text-muted-foreground">
              {formatCurrency(additionalBagPrice, currency)} per bag
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 border-primary-300 text-primary-600 hover:bg-primary-50 hover:border-primary-500"
              onClick={decrementBags}
              disabled={checkedBags === 0}
            >
              <Minus className="h-4 w-4" />
              <span className="sr-only">Decrease</span>
            </Button>
            <span className="w-8 text-center font-semibold text-primary-800">{checkedBags}</span>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 border-primary-300 text-primary-600 hover:bg-primary-50 hover:border-primary-500"
              onClick={incrementBags}
              disabled={checkedBags === 5}
            >
              <Plus className="h-4 w-4" />
              <span className="sr-only">Increase</span>
            </Button>
          </div>
        </div>

        {checkedBags > 0 && (
          <div className="mt-4 text-sm">
            <p className="font-medium text-primary-700">
              Subtotal: {formatCurrency(baggageCost, currency)}
            </p>
          </div>
        )}
      </div>

      
      {/* Total Cost Summary */}
      {totalCost > 0 && (
        <div className="rounded-md border border-primary-200 p-4 bg-primary-50">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-primary-800">
              Total Baggage Cost
            </span>
            <span className="font-bold text-lg text-primary-800">
              {formatCurrency(totalCost, currency)}
            </span>
          </div>
          {baggageCost > 0 && (
            <div className="text-sm text-primary-600 mt-1">
              {checkedBags} bag{checkedBags > 1 ? 's' : ''}: {formatCurrency(baggageCost, currency)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export type { BaggageSelection }
