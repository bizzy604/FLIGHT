"use client"
import { SlidersHorizontal } from "lucide-react"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export function FlightSortOptions() {
  return (
    <div className="flex items-center">
      <SlidersHorizontal className="mr-2 h-4 w-4 text-muted-foreground" />
      <Select defaultValue="price-asc">
        <SelectTrigger className="h-8 w-[180px]">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="price-asc">Price: Low to High</SelectItem>
          <SelectItem value="price-desc">Price: High to Low</SelectItem>
          <SelectItem value="duration-asc">Duration: Shortest</SelectItem>
          <SelectItem value="departure-asc">Departure: Earliest</SelectItem>
          <SelectItem value="arrival-asc">Arrival: Earliest</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}

