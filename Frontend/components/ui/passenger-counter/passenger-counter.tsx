"use client"

import { memo } from "react"
import { Plus, Minus } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface PassengerCounterProps {
  label: string
  description: string
  value: number
  onIncrement: () => void
  onDecrement: () => void
  canIncrement: boolean
  canDecrement: boolean
  disabled?: boolean
}

export const PassengerCounter = memo(function PassengerCounter({
  label,
  description,
  value,
  onIncrement,
  onDecrement,
  canIncrement,
  canDecrement,
  disabled = false,
}: PassengerCounterProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 rounded-full"
          onClick={onDecrement}
          disabled={disabled || !canDecrement}
        >
          <Minus className="h-3 w-3" />
        </Button>
        <span className="w-6 text-center font-medium">
          {value}
        </span>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 rounded-full"
          onClick={onIncrement}
          disabled={disabled || !canIncrement}
        >
          <Plus className="h-3 w-3" />
        </Button>
      </div>
    </div>
  )
})

PassengerCounter.displayName = "PassengerCounter"