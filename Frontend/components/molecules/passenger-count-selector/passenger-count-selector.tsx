"use client"

import { memo } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface PassengerCountSelectorProps {
  value: string
  onChange: (value: string) => void
}

export const PassengerCountSelector = memo(function PassengerCountSelector({
  value,
  onChange
}: PassengerCountSelectorProps) {
  return (
    <Select
      value={value}
      onValueChange={onChange}
    >
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Number of Passengers" />
      </SelectTrigger>
      <SelectContent>
        {Array.from({ length: Number(value) }, (_, i) => (
          <SelectItem key={i + 1} value={(i + 1).toString()}>
            {i + 1} {i === 0 ? 'Passenger' : 'Passengers'}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
})