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
        <SelectItem value="1">1 Passenger</SelectItem>
        <SelectItem value="2">2 Passengers</SelectItem>
        <SelectItem value="3">3 Passengers</SelectItem>
        <SelectItem value="4">4 Passengers</SelectItem>
        <SelectItem value="5">5 Passengers</SelectItem>
      </SelectContent>
    </Select>
  )
})