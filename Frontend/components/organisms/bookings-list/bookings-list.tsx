"use client"

import { useState } from "react"
import { format } from "date-fns"
import { Calendar, Clock, MapPin, Plane, Edit, Trash2, Eye } from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

interface BookingsListProps {
  bookings: any[]
  onCancelBooking?: (bookingReference: string) => Promise<void>
  isPast?: boolean
}

export function BookingsList({ bookings, onCancelBooking, isPast = false }: BookingsListProps) {
  const [cancelling, setCancelling] = useState<string | null>(null)

  const handleCancel = async (bookingReference: string) => {
    if (!onCancelBooking) return
    
    try {
      setCancelling(bookingReference)
      await onCancelBooking(bookingReference)
    } catch (error) {
      console.error("Error cancelling booking:", error)
    } finally {
      setCancelling(null)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "confirmed":
        return <Badge className="bg-green-100 text-green-800">Confirmed</Badge>
      case "pending":
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>
      case "cancelled":
        return <Badge className="bg-red-100 text-red-800">Cancelled</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM d, yyyy")
    } catch (e) {
      return dateString
    }
  }

  const formatTime = (dateString: string) => {
    try {
      return format(new Date(dateString), "h:mm a")
    } catch (e) {
      return dateString
    }
  }

  const getFlightRoute = (booking: any) => {
    // Try to get from new structure first
    if (booking.routeSegments?.segments?.[0]) {
      const segment = booking.routeSegments.segments[0]
      return {
        from: segment.departure_airport || 'Unknown',
        to: segment.arrival_airport || 'Unknown',
        departureTime: segment.departure_datetime,
        flightNumber: segment.flight_number
      }
    }

    // Fallback to legacy structure
    if (booking.flightDetails?.outbound) {
      return {
        from: booking.flightDetails.outbound.departure?.city || 'Unknown',
        to: booking.flightDetails.outbound.arrival?.city || 'Unknown',
        departureTime: booking.flightDetails.outbound.departure?.date,
        flightNumber: booking.flightDetails.outbound.flightNumber
      }
    }

    return {
      from: 'Unknown',
      to: 'Unknown',
      departureTime: null,
      flightNumber: null
    }
  }

  if (bookings.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No bookings found</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {bookings.map((booking) => {
        const route = getFlightRoute(booking)
        
        return (
          <Card key={booking.bookingReference} className="w-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Plane className="w-5 h-5 text-blue-600" />
                  <CardTitle className="text-lg">
                    Booking Reference: {booking.bookingReference}
                  </CardTitle>
                </div>
                {getStatusBadge(booking.status)}
              </div>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-4">
                {/* Flight Route */}
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium">{route.from}</span>
                  </div>
                  <div className="flex-1 border-t border-dashed"></div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium">{route.to}</span>
                  </div>
                </div>

                {/* Flight Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span>
                      {route.departureTime ? formatDate(route.departureTime) : 'Date not available'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span>
                      {route.departureTime ? formatTime(route.departureTime) : 'Time not available'}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">
                      Total: ${booking.totalAmount || 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 pt-4 border-t">
                  <Link href={`/manage/${booking.bookingReference}`}>
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4 mr-1" />
                      View Details
                    </Button>
                  </Link>

                  {!isPast && booking.status !== "cancelled" && (
                    <>
                      <Link href={`/manage/${booking.bookingReference}/edit`}>
                        <Button variant="outline" size="sm">
                          <Edit className="w-4 h-4 mr-1" />
                          Modify
                        </Button>
                      </Link>

                      {onCancelBooking && (
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="outline" size="sm" disabled={cancelling === booking.bookingReference}>
                              <Trash2 className="w-4 h-4 mr-1" />
                              Cancel
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Cancel Booking</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to cancel booking {booking.bookingReference}? 
                                This action cannot be undone and cancellation fees may apply.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Keep Booking</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleCancel(booking.bookingReference)}
                                className="bg-red-600 hover:bg-red-700"
                              >
                                Cancel Booking
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      )}
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}