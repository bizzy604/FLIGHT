"use client"

import { Plane, CalendarX } from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

interface EmptyBookingsProps {
  message?: string
  description?: string
  showBookButton?: boolean
}

export function EmptyBookings({ 
  message = "No bookings found", 
  description = "Your bookings will appear here",
  showBookButton = false 
}: EmptyBookingsProps) {
  return (
    <Card className="w-full">
      <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <div className="mb-4 rounded-full bg-gray-100 p-4">
          <CalendarX className="h-8 w-8 text-gray-400" />
        </div>
        
        <h3 className="mb-2 text-lg font-semibold text-gray-900">
          {message}
        </h3>
        
        <p className="mb-6 text-sm text-gray-600 max-w-sm">
          {description}
        </p>

        {showBookButton && (
          <Link href="/">
            <Button className="flex items-center gap-2">
              <Plane className="w-4 h-4" />
              Book a Flight
            </Button>
          </Link>
        )}
      </CardContent>
    </Card>
  )
}