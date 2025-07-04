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
  }> | { names?: string }
  flightDetails?: {
    outbound: FlightDetail
    return?: FlightDetail
  }
  // New database structure fields
  airlineCode?: string
  flightNumbers?: string[]
  routeSegments?: {
    origin?: string
    destination?: string
    departureTime?: string
    arrivalTime?: string
    segments?: Array<{
      duration?: string
      airline_code?: string
      airline_name?: string
      flight_number?: string
      arrival_airport?: string
      departure_airport?: string
      arrival_datetime?: string
      departure_datetime?: string
    }>
  }
  originalFlightOffer?: {
    total_price?: {
      amount?: number
      currency?: string
    }
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

  // Helper function to clean values
  const cleanValue = (value: any, fallback = 'N/A') => {
    if (!value || value === 'Unknown' || value === 'undefined' || value === 'null') {
      return fallback;
    }
    return value;
  };

  // Helper function to format time from string
  const formatTimeFromString = (timeString: string) => {
    if (!timeString || timeString === 'N/A' || timeString === 'Unknown') return 'N/A';

    try {
      if (timeString.includes('T')) {
        const date = new Date(timeString);
        return date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });
      }
      return timeString;
    } catch {
      return 'N/A';
    }
  };

  // Helper function to get formatted price from booking data
  const getFormattedPrice = (booking: Booking) => {
    // Try to get price from originalFlightOffer first
    if (booking.originalFlightOffer && booking.originalFlightOffer.total_price) {
      const price = booking.originalFlightOffer.total_price
      const amount = price.amount || 0
      const currency = price.currency || 'USD'

      // Convert currency symbols
      const currencySymbol = currency === 'INR' ? '₹' :
                           currency === 'USD' ? '$' :
                           currency === 'EUR' ? '€' :
                           currency === 'GBP' ? '£' : currency

      return `${currencySymbol}${amount.toLocaleString()}`
    }

    // Fallback to totalAmount from booking
    if (booking.totalAmount && booking.totalAmount > 0) {
      return `$${booking.totalAmount.toFixed(2)}`
    }

    // Default fallback
    return 'N/A'
  }

  // Helper function to normalize flight data structure
  const getFlightInfo = (booking: Booking) => {
    // PRIORITY 1: Extract from routeSegments.segments array (new structure)
    const routeSegments = booking.routeSegments;
    const flightNumbers = booking.flightNumbers;
    const airlineCode = booking.airlineCode;

    if (routeSegments && routeSegments.segments && routeSegments.segments.length > 0) {
      const segment = routeSegments.segments[0]; // Get first segment
      const origin = cleanValue(segment.departure_airport, 'Unknown Airport');
      const destination = cleanValue(segment.arrival_airport, 'Unknown Airport');
      const airline = cleanValue(segment.airline_code, 'Unknown');
      const outboundFlightNumber = cleanValue(segment.flight_number, 'N/A');
      const returnFlightNumber = routeSegments.segments[1] ? cleanValue(routeSegments.segments[1].flight_number) : undefined;

      return {
        outbound: {
          departure: {
            time: formatTimeFromString(segment.departure_datetime || ''),
            city: origin,
            airport: origin,
            date: segment.departure_datetime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(segment.arrival_datetime || ''),
            city: destination,
            airport: destination,
            date: segment.arrival_datetime || new Date().toISOString()
          },
          duration: cleanValue(segment.duration, 'N/A'),
          flightNumber: outboundFlightNumber,
          airline: {
            code: airline,
            name: cleanValue(segment.airline_name, airline === 'Unknown' ? 'Unknown Airline' : airline)
          }
        },
        return: returnFlightNumber && returnFlightNumber !== 'N/A' ? {
          departure: {
            time: formatTimeFromString(routeSegments.segments[1]?.departure_datetime || ''),
            city: destination,
            airport: destination,
            date: routeSegments.segments[1]?.departure_datetime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(routeSegments.segments[1]?.arrival_datetime || ''),
            city: origin,
            airport: origin,
            date: routeSegments.segments[1]?.arrival_datetime || new Date().toISOString()
          },
          duration: cleanValue(routeSegments.segments[1]?.duration, 'N/A'),
          flightNumber: returnFlightNumber,
          airline: {
            code: airline,
            name: cleanValue(routeSegments.segments[1]?.airline_name, airline === 'Unknown' ? 'Unknown Airline' : airline)
          }
        } : undefined
      }
    }

    // PRIORITY 2: Fallback to routeSegments top-level fields if segments array is empty
    if (routeSegments && (routeSegments.origin || routeSegments.destination) &&
        routeSegments.origin !== 'Unknown' && routeSegments.destination !== 'Unknown') {
      const origin = cleanValue(routeSegments.origin, 'Unknown Airport')
      const destination = cleanValue(routeSegments.destination, 'Unknown Airport')
      const airline = cleanValue(airlineCode, 'Unknown')
      const outboundFlightNumber = flightNumbers && flightNumbers[0] ? cleanValue(flightNumbers[0], 'N/A') : 'N/A'
      const returnFlightNumber = flightNumbers && flightNumbers[1] ? cleanValue(flightNumbers[1]) : undefined

      return {
        outbound: {
          departure: {
            time: formatTimeFromString(routeSegments.departureTime || ''),
            city: origin,
            airport: origin,
            date: routeSegments.departureTime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(routeSegments.arrivalTime || ''),
            city: destination,
            airport: destination,
            date: routeSegments.arrivalTime || new Date().toISOString()
          },
          duration: 'N/A',
          flightNumber: outboundFlightNumber,
          airline: {
            code: airline,
            name: airline === 'Unknown' ? 'Unknown Airline' : airline
          }
        },
        return: returnFlightNumber && returnFlightNumber !== 'N/A' ? {
          departure: {
            time: formatTimeFromString(routeSegments.arrivalTime || ''),
            city: destination,
            airport: destination,
            date: routeSegments.arrivalTime || new Date().toISOString()
          },
          arrival: {
            time: formatTimeFromString(routeSegments.departureTime || ''),
            city: origin,
            airport: origin,
            date: routeSegments.departureTime || new Date().toISOString()
          },
          duration: 'N/A',
          flightNumber: returnFlightNumber,
          airline: {
            code: airline,
            name: airline === 'Unknown' ? 'Unknown Airline' : airline
          }
        } : undefined
      }
    }

    // PRIORITY 3: Extract from flightDetails (legacy structure)
    if (booking.flightDetails) {
      return booking.flightDetails;
    }

    // FALLBACK: Return default structure
    return {
      outbound: {
        departure: {
          time: 'N/A',
          city: 'Unknown',
          airport: 'Unknown',
          date: new Date().toISOString()
        },
        arrival: {
          time: 'N/A',
          city: 'Unknown',
          airport: 'Unknown',
          date: new Date().toISOString()
        },
        duration: 'N/A',
        flightNumber: 'N/A',
        airline: {
          code: 'Unknown',
          name: 'Unknown Airline'
        }
      }
    };
  };

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
      {bookings.map((booking) => {
        const flightInfo = getFlightInfo(booking);

        return (
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
                        <p className="text-lg font-bold">{flightInfo?.outbound?.departure?.time}</p>
                        <p className="text-sm">
                          {flightInfo?.outbound?.departure?.city} (
                          {flightInfo?.outbound?.departure?.airport})
                        </p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      <div className="text-right">
                        <p className="text-lg font-bold">{flightInfo?.outbound?.arrival?.time}</p>
                        <p className="text-sm">
                          {flightInfo?.outbound?.arrival?.city} (
                          {flightInfo?.outbound?.arrival?.airport})
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center text-xs text-muted-foreground">
                      <Calendar className="mr-1 h-3 w-3" />
                      <span>{formatDate(flightInfo?.outbound?.departure?.date)}</span>
                      <Clock className="ml-2 mr-1 h-3 w-3" />
                      <span>{flightInfo?.outbound?.duration}</span>
                    </div>
                  </div>

                  {flightInfo?.return && (
                    <div className="space-y-2">
                      <div className="flex items-center text-sm">
                        <Plane className="mr-2 h-4 w-4 -rotate-45 text-muted-foreground" />
                        <span className="font-medium">Return Flight</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-lg font-bold">{flightInfo?.return?.departure?.time}</p>
                          <p className="text-sm">
                            {flightInfo?.return?.departure?.city} (
                            {flightInfo?.return?.departure?.airport})
                          </p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        <div className="text-right">
                          <p className="text-lg font-bold">{flightInfo?.return?.arrival?.time}</p>
                          <p className="text-sm">
                            {flightInfo?.return?.arrival?.city} (
                            {flightInfo?.return?.arrival?.airport})
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center text-xs text-muted-foreground">
                        <Calendar className="mr-1 h-3 w-3" />
                        <span>{formatDate(flightInfo?.return?.departure?.date)}</span>
                        <Clock className="ml-2 mr-1 h-3 w-3" />
                        <span>{flightInfo?.return?.duration}</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm">
                    <span className="font-medium">Passengers:</span> {Array.isArray(booking.passengerDetails) ? booking.passengerDetails.length : 1} •
                    <span className="ml-1 font-medium">Total:</span> {getFormattedPrice(booking)}
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
        );
      })}

      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Booking</DialogTitle>
            <DialogDescription>
              Are you sure you want to cancel this booking? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          {selectedBooking && (() => {
            const selectedFlightInfo = getFlightInfo(selectedBooking);
            return (
              <div className="rounded-md bg-muted p-3 text-sm">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span>
                    {selectedFlightInfo?.outbound?.departure?.city} to{" "}
                    {selectedFlightInfo?.outbound?.arrival?.city}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>{formatDate(selectedFlightInfo?.outbound?.departure?.date)}</span>
                </div>
                <div className="mt-1 font-medium">Booking Reference: {selectedBooking.bookingReference}</div>
              </div>
            );
          })()}

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

