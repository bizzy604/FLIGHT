"use client"

import { memo } from "react"
import { DateSelector } from "./date-selector"
import { cn } from "@/utils/cn"
import type { DateRangeProps } from "./date-selector.types"

export const DateRangeSelector = memo(function DateRangeSelector({
  departDate,
  returnDate,
  onDepartDateChange,
  onReturnDateChange,
  disabled = false,
  minDate,
  maxDate,
  className,
  showReturnDate = true,
}: DateRangeProps) {
  // Ensure return date is after departure date
  const handleDepartDateChange = (date: Date | undefined) => {
    onDepartDateChange(date)
    // If return date is before new depart date, clear it
    if (returnDate && date && returnDate <= date) {
      onReturnDateChange(undefined)
    }
  }

  const getReturnMinDate = (): Date | undefined => {
    if (departDate) {
      // Return date must be at least 1 day after departure
      const nextDay = new Date(departDate)
      nextDay.setDate(nextDay.getDate() + 1)
      return minDate ? new Date(Math.max(nextDay.getTime(), minDate.getTime())) : nextDay
    }
    return minDate
  }

  return (
    <div className={cn("grid gap-4", showReturnDate ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1", className)}>
      <DateSelector
        label="Departure Date"
        value={departDate}
        onChange={handleDepartDateChange}
        placeholder="Select departure date"
        disabled={disabled}
        minDate={minDate}
        maxDate={maxDate}
      />
      
      {showReturnDate && (
        <DateSelector
          label="Return Date"
          value={returnDate}
          onChange={onReturnDateChange}
          placeholder="Select return date"
          disabled={disabled || !departDate}
          minDate={getReturnMinDate()}
          maxDate={maxDate}
        />
      )}
    </div>
  )
})

DateRangeSelector.displayName = "DateRangeSelector"