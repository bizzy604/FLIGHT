"use client"

import * as React from "react"

import { cn } from "@/utils/cn"

// Mock data for seat map
const seatMap = {
  rows: 30,
  columns: ["A", "B", "C", "", "D", "E", "F"],
  unavailableSeats: ["1A", "1F", "5C", "5D", "10A", "10B", "10C", "15D", "15E", "15F", "20B", "25A"],
  premiumSeats: ["1B", "1C", "1D", "1E", "2A", "2B", "2C", "2D", "2E", "2F"],
  exitRowSeats: ["15A", "15B", "15C", "16D", "16E", "16F"],
}

interface SeatSelectionProps {
  flightType: 'outbound' | 'return';
  selectedSeats: string[];
  onSeatChange: (flightType: 'outbound' | 'return', updatedSeats: string[]) => void;
}

export function SeatSelection({ flightType, selectedSeats, onSeatChange }: SeatSelectionProps) {
  const isSeatAvailable = (seat: string) => {
    return !seatMap.unavailableSeats.includes(seat)
  }

  const isSeatPremium = (seat: string) => {
    return seatMap.premiumSeats.includes(seat)
  }

  const isSeatExitRow = (seat: string) => {
    return seatMap.exitRowSeats.includes(seat)
  }

  const getSeatPrice = (seat: string) => {
    if (isSeatPremium(seat)) return 49.99
    if (isSeatExitRow(seat)) return 29.99
    return 14.99
  }

  const handleSeatSelect = (seat: string) => {
    if (isSeatAvailable(seat)) {
      const currentlySelected = selectedSeats.includes(seat);
      let newSelectedSeats;

      if (currentlySelected) {
        // Deselect: Remove the seat from the array
        newSelectedSeats = selectedSeats.filter(s => s !== seat);
      } else {
        // Select: Add the seat to the array
        newSelectedSeats = [...selectedSeats, seat];
      }
      // Call the callback with the updated array
      onSeatChange(flightType, newSelectedSeats);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-center space-x-6 text-sm">
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded border border-muted-foreground/50"></div>
          <span>Available</span>
        </div>
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded bg-primary/20"></div>
          <span>Premium ($49.99)</span>
        </div>
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded bg-amber-500/20"></div>
          <span>Exit Row ($29.99)</span>
        </div>
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded bg-muted"></div>
          <span>Unavailable</span>
        </div>
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded bg-primary"></div>
          <span>Selected</span>
        </div>
      </div>

      <div className="mx-auto max-w-md overflow-x-auto">
        <div className="relative mb-8 w-full rounded-t-xl bg-muted p-4 text-center">
          <div className="absolute left-0 top-1/2 h-8 w-4 -translate-y-1/2 rounded-r-md bg-muted-foreground/20"></div>
          <div className="absolute right-0 top-1/2 h-8 w-4 -translate-y-1/2 rounded-l-md bg-muted-foreground/20"></div>
          <span className="font-medium">Front of Aircraft</span>
        </div>

        <div className="grid grid-cols-7 gap-1 text-center text-xs">
          {seatMap.columns.map((col, colIndex) => (
            <div key={colIndex} className="py-2 font-medium">
              {col}
            </div>
          ))}

          {Array.from({ length: seatMap.rows }).map((_, rowIndex) => {
            const rowNum = rowIndex + 1
            return (
              <React.Fragment key={rowNum}>
                {seatMap.columns.map((col, colIndex) => {
                  if (col === "") return <div key={`${rowNum}-${colIndex}`}></div>

                  const seat = `${rowNum}${col}`
                  const isAvailable = isSeatAvailable(seat)
                  const isPremium = isSeatPremium(seat)
                  const isExitRow = isSeatExitRow(seat)
                  const isSelected = selectedSeats.includes(seat)

                  return (
                    <button
                      key={seat}
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded",
                        isAvailable ? "cursor-pointer" : "cursor-not-allowed bg-muted",
                        isPremium && isAvailable && "bg-primary/20 hover:bg-primary/30",
                        isExitRow && isAvailable && "bg-amber-500/20 hover:bg-amber-500/30",
                        isSelected && "bg-primary text-primary-foreground",
                        !isPremium &&
                          !isExitRow &&
                          isAvailable &&
                          !isSelected &&
                          "border border-muted-foreground/50 hover:border-primary/50",
                      )}
                      onClick={() => handleSeatSelect(seat)}
                      disabled={!isAvailable}
                    >
                      {seat}
                    </button>
                  )
                })}
              </React.Fragment>
            )
          })}
        </div>

        <div className="mt-8 rounded-b-xl bg-muted p-4 text-center">
          <span className="font-medium">Rear of Aircraft</span>
        </div>
      </div>

      <div className="mt-4 rounded-md border p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium">Selected Seats ({selectedSeats.length})</h4>
            {selectedSeats.length > 0 ? (
              <p className="text-sm text-muted-foreground">
                {selectedSeats.join(", ")} - Total: ${selectedSeats.reduce((total, seat) => total + getSeatPrice(seat), 0).toFixed(2)}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">No seats selected</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
