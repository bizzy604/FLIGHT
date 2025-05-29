import Link from "next/link"
import { Edit } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

interface OrderSummaryProps {
  booking: any // Using any for brevity, but would use a proper type in a real app
}

export function OrderSummary({ booking }: OrderSummaryProps) {
  return (
    <div className="rounded-lg border">
      <div className="p-4 sm:p-6">
        <h2 className="text-xl font-semibold">Order Summary</h2>
      </div>
      <Separator />
      <div className="p-4 sm:p-6">
        <div className="space-y-4">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-medium">Flight Details</h3>
              <Link href={`/flights/${booking.id}`}>
                <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">
                  <Edit className="mr-1 h-3 w-3" />
                  Edit
                </Button>
              </Link>
            </div>
            <div className="rounded-md bg-muted p-3 text-sm">
              <div className="mb-2">
                <p className="font-medium">Outbound</p>
                <p>{booking.flightDetails.outbound.departure.fullDate}</p>
                <p>
                  {booking.flightDetails.outbound.departure.city} ({booking.flightDetails.outbound.departure.airport}) →{" "}
                  {booking.flightDetails.outbound.arrival.city} ({booking.flightDetails.outbound.arrival.airport})
                </p>
                {booking.flightDetails.outbound.airline && (
                  <p>
                    {booking.flightDetails.outbound.airline.name} {booking.flightDetails.outbound.airline.code}
                    {booking.flightDetails.outbound.airline.flightNumber}
                  </p>
                )}
              </div>
              {booking.flightDetails.return && (
                <div>
                  <p className="font-medium">Return</p>
                  <p>{booking.flightDetails.return.departure.fullDate}</p>
                  <p>
                    {booking.flightDetails.return.departure.city} ({booking.flightDetails.return.departure.airport}) →{" "}
                    {booking.flightDetails.return.arrival.city} ({booking.flightDetails.return.arrival.airport})
                  </p>
                  {booking.flightDetails.return.airline && (
                    <p>
                      {booking.flightDetails.return.airline.name} {booking.flightDetails.return.airline.code}
                      {booking.flightDetails.return.airline.flightNumber}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-medium">Passengers</h3>
              <Link href={`/flights/${booking.id}`}>
                <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">
                  <Edit className="mr-1 h-3 w-3" />
                  Edit
                </Button>
              </Link>
            </div>
            <div className="rounded-md bg-muted p-3 text-sm">
              {booking.passengers ? (
                booking.passengers.map((passenger: any, index: number) => (
                  <div key={index}>
                    <p>
                      {passenger.firstName} {passenger.lastName} ({passenger.type})
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {passenger.documentType}: {passenger.documentNumber}
                    </p>
                  </div>
                ))
              ) : (
                <p>No passenger information available</p>
              )}
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-medium">Selected Extras</h3>
              <Link href={`/flights/${booking.id}`}>
                <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">
                  <Edit className="mr-1 h-3 w-3" />
                  Edit
                </Button>
              </Link>
            </div>
            <div className="rounded-md bg-muted p-3 text-sm">
              {booking.extras ? (
                <>
                  {booking.extras.seats && (
                    <p>
                      <span className="font-medium">Seats:</span>{" "}
                      {booking.extras.seats.outbound && `${booking.extras.seats.outbound} (Outbound)`}
                      {booking.extras.seats.outbound && booking.extras.seats.return && ", "}
                      {booking.extras.seats.return && `${booking.extras.seats.return} (Return)`}
                    </p>
                  )}
                  
                  {booking.extras.baggage && (
                    <p>
                      <span className="font-medium">Baggage:</span>{" "}
                      {booking.extras.baggage.included}
                      {booking.extras.baggage.included && booking.extras.baggage.additional && ", "}
                      {booking.extras.baggage.additional}
                    </p>
                  )}
                  
                  {booking.extras.meals && (
                    <p>
                      <span className="font-medium">Meals:</span>{" "}
                      {booking.extras.meals.outbound && `${booking.extras.meals.outbound} (Outbound)`}
                      {booking.extras.meals.outbound && booking.extras.meals.return && ", "}
                      {booking.extras.meals.return && `${booking.extras.meals.return} (Return)`}
                    </p>
                  )}
                  
                  {booking.extras.additionalServices && booking.extras.additionalServices.length > 0 && (
                    <p>
                      <span className="font-medium">Additional Services:</span>{" "}
                      {booking.extras.additionalServices.join(", ")}
                    </p>
                  )}
                </>
              ) : (
                <p>No extras information available</p>
              )}
            </div>
          </div>

          <Separator />

          <div className="space-y-2">
            {booking.pricing ? (
              <>
                <div className="flex justify-between">
                  <span>Base fare ({booking.passengers?.length || 1} passenger)</span>
                  <span>${booking.pricing.baseFare?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Taxes and fees</span>
                  <span>${booking.pricing.taxes?.toFixed(2) || '0.00'}</span>
                </div>
                {booking.pricing.seatSelection !== undefined && (
                  <div className="flex justify-between">
                    <span>Seat selection</span>
                    <span>${booking.pricing.seatSelection.toFixed(2)}</span>
                  </div>
                )}
                {booking.pricing.extraBaggage !== undefined && (
                  <div className="flex justify-between">
                    <span>Extra baggage</span>
                    <span>${booking.pricing.extraBaggage.toFixed(2)}</span>
                  </div>
                )}
                {booking.pricing.priorityBoarding !== undefined && (
                  <div className="flex justify-between">
                    <span>Priority boarding</span>
                    <span>${booking.pricing.priorityBoarding.toFixed(2)}</span>
                  </div>
                )}
                {booking.pricing.travelInsurance !== undefined && (
                  <div className="flex justify-between">
                    <span>Travel insurance</span>
                    <span>${booking.pricing.travelInsurance.toFixed(2)}</span>
                  </div>
                )}
                <Separator />
                <div className="flex justify-between font-bold">
                  <span>Total</span>
                  <span>${booking.pricing.total?.toFixed(2) || booking.totalAmount?.toFixed(2) || '0.00'}</span>
                </div>
              </>
            ) : (
              <>
                <div className="flex justify-between">
                  <span>Total</span>
                  <span>${booking.totalAmount?.toFixed(2) || '0.00'}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

