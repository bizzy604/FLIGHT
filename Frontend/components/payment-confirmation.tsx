"use client"

import Link from "next/link"
import Image from "next/image"
import { Check, Download, Mail, Printer, Share2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import { downloadBookingConfirmation } from "@/lib/download-utils"

interface PaymentConfirmationProps {
  booking: any // Using any for brevity, but would use a proper type in a real app
}

export function PaymentConfirmation({ booking }: PaymentConfirmationProps) {
  const handleDownload = () => {
    downloadBookingConfirmation(booking)
  }

  const handleEmailItinerary = () => {
    // In a real app, this would trigger an API call to send an email
    alert(`Itinerary sent to ${booking.contactInfo.email}`)
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-8 rounded-lg border bg-green-50 p-6 text-center dark:bg-green-950">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
          <Check className="h-6 w-6 text-green-600 dark:text-green-400" />
        </div>
        <h1 className="mb-2 text-2xl font-bold text-green-800 dark:text-green-300">Booking Confirmed!</h1>
        <p className="text-green-700 dark:text-green-400">
          Your payment has been processed successfully and your booking is confirmed.
        </p>
      </div>

      <div className="mb-6 rounded-lg border p-6">
        <div className="mb-4 flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div>
            <h2 className="text-xl font-bold">Booking Reference: {booking.id}</h2>
            <p className="text-sm text-muted-foreground">Please save this reference number for future inquiries</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={handleEmailItinerary}
              aria-label="Email itinerary"
            >
              <Mail className="h-4 w-4" />
              <span>Email</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={handleDownload}
              aria-label="Download itinerary"
            >
              <Download className="h-4 w-4" />
              <span>Download</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={() => window.print()}
              aria-label="Print itinerary"
            >
              <Printer className="h-4 w-4" />
              <span>Print</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
              onClick={() => {
                if (navigator.share) {
                  navigator.share({
                    title: `Flight Booking - ${booking.id}`,
                    text: `My flight from ${booking.flightDetails.outbound.departure.city} to ${booking.flightDetails.outbound.arrival.city} is confirmed!`,
                    url: window.location.href,
                  })
                } else {
                  alert("Sharing is not supported on this browser")
                }
              }}
              aria-label="Share booking details"
            >
              <Share2 className="h-4 w-4" />
              <span>Share</span>
            </Button>
          </div>
        </div>

        <Separator className="my-4" />

        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-lg font-medium">Flight Details</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardContent className="p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <h4 className="font-medium">Outbound Flight</h4>
                    <span className="text-sm text-muted-foreground">{booking.flightDetails.outbound.duration}</span>
                  </div>
                  <div className="mb-2 flex items-center">
                    <Image
                      src={booking.flightDetails.outbound.airline.logo || "/placeholder.svg"}
                      alt={booking.flightDetails.outbound.airline.name}
                      width={24}
                      height={24}
                      className="mr-2 rounded-full"
                    />
                    <span className="text-sm">
                      {booking.flightDetails.outbound.airline.name} {booking.flightDetails.outbound.airline.code}
                      {booking.flightDetails.outbound.airline.flightNumber}
                    </span>
                  </div>
                  <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                    <div>
                      <p className="text-lg font-bold">{booking.flightDetails.outbound.departure.time}</p>
                      <p className="text-sm">{booking.flightDetails.outbound.departure.airport}</p>
                      <p className="text-xs text-muted-foreground">
                        {booking.flightDetails.outbound.departure.fullDate}
                      </p>
                    </div>
                    <div className="text-center text-xs text-muted-foreground">
                      <div className="relative h-0.5 w-16 bg-muted">
                        <div className="absolute -right-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                        <div className="absolute -left-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                      </div>
                      <p className="mt-1">Direct</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">{booking.flightDetails.outbound.arrival.time}</p>
                      <p className="text-sm">{booking.flightDetails.outbound.arrival.airport}</p>
                      <p className="text-xs text-muted-foreground">{booking.flightDetails.outbound.arrival.fullDate}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <h4 className="font-medium">Return Flight</h4>
                    <span className="text-sm text-muted-foreground">{booking.flightDetails.return.duration}</span>
                  </div>
                  <div className="mb-2 flex items-center">
                    <Image
                      src={booking.flightDetails.return.airline.logo || "/placeholder.svg"}
                      alt={booking.flightDetails.return.airline.name}
                      width={24}
                      height={24}
                      className="mr-2 rounded-full"
                    />
                    <span className="text-sm">
                      {booking.flightDetails.return.airline.name} {booking.flightDetails.return.airline.code}
                      {booking.flightDetails.return.airline.flightNumber}
                    </span>
                  </div>
                  <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
                    <div>
                      <p className="text-lg font-bold">{booking.flightDetails.return.departure.time}</p>
                      <p className="text-sm">{booking.flightDetails.return.departure.airport}</p>
                      <p className="text-xs text-muted-foreground">{booking.flightDetails.return.departure.fullDate}</p>
                    </div>
                    <div className="text-center text-xs text-muted-foreground">
                      <div className="relative h-0.5 w-16 bg-muted">
                        <div className="absolute -right-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                        <div className="absolute -left-1 -top-1 h-3 w-3 rounded-full border border-muted bg-background"></div>
                      </div>
                      <p className="mt-1">Direct</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">{booking.flightDetails.return.arrival.time}</p>
                      <p className="text-sm">{booking.flightDetails.return.arrival.airport}</p>
                      <p className="text-xs text-muted-foreground">{booking.flightDetails.return.arrival.fullDate}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-medium">Passenger Information</h3>
            <div className="rounded-md border p-4">
              {booking.passengers && booking.passengers.length > 0 ? (
                booking.passengers.map((passenger: any, index: number) => (
                  <div key={index} className="mb-2 last:mb-0">
                    <p className="font-medium">
                      {passenger.firstName} {passenger.lastName}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {passenger.type} • {passenger.documentType}: {passenger.documentNumber}
                    </p>
                  </div>
                ))
              ) : (
                <p>No passenger information available</p>
              )}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-medium">Contact Information</h3>
            <div className="rounded-md border p-4">
              <p className="mb-1">
                <span className="font-medium">Email:</span> {booking.contactInfo.email}
              </p>
              <p>
                <span className="font-medium">Phone:</span> {booking.contactInfo.phone}
              </p>
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-medium">Selected Extras</h3>
            <div className="rounded-md border p-4">
              <div className="mb-2">
                <p className="font-medium">Seats</p>
                <p className="text-sm">Outbound: {booking.extras.seats.outbound}</p>
                <p className="text-sm">Return: {booking.extras.seats.return}</p>
              </div>
              <div className="mb-2">
                <p className="font-medium">Baggage</p>
                <p className="text-sm">Included: {booking.extras.baggage.included}</p>
                <p className="text-sm">Additional: {booking.extras.baggage.additional}</p>
              </div>
              <div className="mb-2">
                <p className="font-medium">Meals</p>
                <p className="text-sm">Outbound: {booking.extras.meals.outbound}</p>
                <p className="text-sm">Return: {booking.extras.meals.return}</p>
              </div>
              <div>
                <p className="font-medium">Additional Services</p>
                <p className="text-sm">{booking.extras.additionalServices.join(", ")}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-lg font-medium">Payment Summary</h3>
            <div className="rounded-md border p-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Base fare ({booking.passengers?.length || 1} passenger{(booking.passengers?.length || 1) > 1 ? 's' : ''})</span>
                  <span>${booking.pricing?.baseFare?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Taxes and fees</span>
                  <span>${booking.pricing?.taxes?.toFixed(2) || '0.00'}</span>
                </div>
                {booking.pricing?.seatSelection !== undefined && (
                  <div className="flex justify-between">
                    <span>Seat selection</span>
                    <span>${booking.pricing?.seatSelection?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                {booking.pricing?.extraBaggage !== undefined && (
                  <div className="flex justify-between">
                    <span>Extra baggage</span>
                    <span>${booking.pricing?.extraBaggage?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                {booking.pricing?.priorityBoarding !== undefined && (
                  <div className="flex justify-between">
                    <span>Priority boarding</span>
                    <span>${booking.pricing?.priorityBoarding?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                {booking.pricing?.travelInsurance !== undefined && (
                  <div className="flex justify-between">
                    <span>Travel insurance</span>
                    <span>${booking.pricing?.travelInsurance?.toFixed(2) || '0.00'}</span>
                  </div>
                )}
                <Separator />
                <div className="flex justify-between font-bold">
                  <span>Total paid</span>
                  <span>${booking.pricing?.total?.toFixed(2) || (booking.totalAmount ? parseFloat(String(booking.totalAmount)).toFixed(2) : '0.00')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-8 space-y-4 rounded-lg border bg-muted/30 p-6">
        <h3 className="text-lg font-medium">What's Next?</h3>
        <div className="space-y-2">
          <p className="text-sm">
            <span className="font-medium">Check-in:</span> Online check-in opens 24 hours before your flight. You'll
            receive an email reminder.
          </p>
          <p className="text-sm">
            <span className="font-medium">Manage your booking:</span> You can make changes to your booking, select
            seats, or add extras through your account.
          </p>
          <p className="text-sm">
            <span className="font-medium">Need help?:</span> Our customer service team is available 24/7 to assist you
            with any questions.
          </p>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/manage">
            <Button>Manage Booking</Button>
          </Link>
          <Link href="/support">
            <Button variant="outline">Contact Support</Button>
          </Link>
        </div>
      </div>

      <div className="text-center">
        <Link href="/">
          <Button variant="outline">Return to Home</Button>
        </Link>
      </div>
    </div>
  )
}

