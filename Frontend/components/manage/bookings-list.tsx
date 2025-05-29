"use client"

import { useState } from "react"
import Link from "next/link"
import { format } from "date-fns"
import { Calendar, ChevronRight, Clock, MapPin, MoreHorizontal, Plane } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface Booking {
  bookingReference: string
  status: string
  createdAt: string
  totalAmount: number
  passengerDetails: Array<{
    firstName: string
    lastName: string
  }>
  flightDetails: {
    outbound: FlightDetail
    return?: FlightDetail
  }
}

interface FlightDetail {
  departure: {
    time: string
    date: string
    city: string
    airport: string
  }
  arrival: {
    time: string
    date: string
    city: string
    airport: string
  }
  duration: string
}

interface BookingsListProps {
  bookings: Booking[]
  onCancelBooking: (bookingReference: string) => void
  isPast?: boolean
}

export function BookingsList({ bookings, onCancelBooking, isPast = false }: BookingsListProps) {
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false)
  const [selectedBooking, setSelectedBooking] = useState<any>(null)

  const handleCancelClick = (booking: any) => {
    setSelectedBooking(booking)
    setCancelDialogOpen(true)
  }

  const confirmCancellation = () => {
    if (selectedBooking) {
      onCancelBooking(selectedBooking.bookingReference)
      setCancelDialogOpen(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "confirmed":
        return <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">Confirmed</Badge>
      case "pending":
        return (
          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">Pending</Badge>
        )
      case "cancelled":
        return <Badge className="bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">Cancelled</Badge>
      case "completed":
        return <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">Completed</Badge>
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

  return (
    <div className="space-y-4">
      {bookings.map((booking) => (
        <Card key={booking.bookingReference} className="overflow-hidden">
          <CardContent className="p-0">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto]">
              <div className="p-4 sm:p-6">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">Booking #{booking.bookingReference}</h3>
                    {getStatusBadge(booking.status)}
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <Calendar className="mr-1 h-4 w-4" />
                    <span>Booked on {formatDate(booking.createdAt || new Date().toISOString())}</span>
                  </div>
                </div>

                <div className="mb-4 grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <div className="flex items-center text-sm">
                      <Plane className="mr-2 h-4 w-4 rotate-45 text-muted-foreground" />
                      <span className="font-medium">Outbound Flight</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-lg font-bold">{booking.flightDetails?.outbound?.departure?.time}</p>
                        <p className="text-sm">
                          {booking.flightDetails?.outbound?.departure?.city} (
                          {booking.flightDetails?.outbound?.departure?.airport})
                        </p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      <div className="text-right">
                        <p className="text-lg font-bold">{booking.flightDetails?.outbound?.arrival?.time}</p>
                        <p className="text-sm">
                          {booking.flightDetails?.outbound?.arrival?.city} (
                          {booking.flightDetails?.outbound?.arrival?.airport})
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center text-xs text-muted-foreground">
                      <Calendar className="mr-1 h-3 w-3" />
                      <span>{formatDate(booking.flightDetails?.outbound?.departure?.date)}</span>
                      <Clock className="ml-2 mr-1 h-3 w-3" />
                      <span>{booking.flightDetails?.outbound?.duration}</span>
                    </div>
                  </div>

                  {booking.flightDetails?.return && (
                    <div className="space-y-2">
                      <div className="flex items-center text-sm">
                        <Plane className="mr-2 h-4 w-4 -rotate-45 text-muted-foreground" />
                        <span className="font-medium">Return Flight</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-lg font-bold">{booking.flightDetails?.return?.departure?.time}</p>
                          <p className="text-sm">
                            {booking.flightDetails?.return?.departure?.city} (
                            {booking.flightDetails?.return?.departure?.airport})
                          </p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        <div className="text-right">
                          <p className="text-lg font-bold">{booking.flightDetails?.return?.arrival?.time}</p>
                          <p className="text-sm">
                            {booking.flightDetails?.return?.arrival?.city} (
                            {booking.flightDetails?.return?.arrival?.airport})
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center text-xs text-muted-foreground">
                        <Calendar className="mr-1 h-3 w-3" />
                        <span>{formatDate(booking.flightDetails?.return?.departure?.date)}</span>
                        <Clock className="ml-2 mr-1 h-3 w-3" />
                        <span>{booking.flightDetails?.return?.duration}</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm">
                    <span className="font-medium">Passengers:</span> {booking.passengerDetails?.length || 1} •
                    <span className="ml-1 font-medium">Total:</span> $
                    {typeof booking.totalAmount === 'number' 
                      ? booking.totalAmount.toFixed(2) 
                      : 'N/A'}
                  </div>

                  <div className="flex items-center gap-2">
                    <Link href={`/manage/${booking.bookingReference}`}>
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                    </Link>

                    {!isPast && booking.status !== "cancelled" && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">More options</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <Link href={`/manage/${booking.bookingReference}/edit`}>
                            <DropdownMenuItem>Modify Booking</DropdownMenuItem>
                          </Link>
                          <DropdownMenuItem
                            className="text-destructive focus:text-destructive"
                            onClick={() => handleCancelClick(booking)}
                          >
                            Cancel Booking
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Booking</DialogTitle>
            <DialogDescription>
              Are you sure you want to cancel this booking? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          {selectedBooking && (
            <div className="rounded-md bg-muted p-3 text-sm">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span>
                  {selectedBooking.flightDetails?.outbound?.departure?.city} to{" "}
                  {selectedBooking.flightDetails?.outbound?.arrival?.city}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span>{formatDate(selectedBooking.flightDetails?.outbound?.departure?.date)}</span>
              </div>
              <div className="mt-1 font-medium">Booking Reference: {selectedBooking.bookingReference}</div>
            </div>
          )}

          <DialogFooter className="gap-2 sm:justify-end">
            <Button variant="outline" onClick={() => setCancelDialogOpen(false)}>
              Keep Booking
            </Button>
            <Button variant="destructive" onClick={confirmCancellation}>
              Cancel Booking
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

