import Image from "next/image"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { FlightDetailsHeader } from "@/components/flight-details-header"
import { FlightDetailsCard } from "@/components/flight-details-card"
import { BookingForm } from "@/components/booking-form"

// Mock data for the selected flight
const selectedFlight = {
  id: "fl-001",
  airline: {
    name: "SkyWay Airlines",
    logo: "/placeholder.svg?height=40&width=40",
    code: "SW",
    flightNumber: "1234",
  },
  departure: {
    airport: "JFK",
    terminal: "4",
    city: "New York",
    time: "08:30",
    date: "2025-04-15",
    fullDate: "Tuesday, April 15, 2025",
  },
  arrival: {
    airport: "LAX",
    terminal: "B",
    city: "Los Angeles",
    time: "11:45",
    date: "2025-04-15",
    fullDate: "Tuesday, April 15, 2025",
  },
  returnFlight: {
    airline: {
      name: "SkyWay Airlines",
      logo: "/placeholder.svg?height=40&width=40",
      code: "SW",
      flightNumber: "4321",
    },
    departure: {
      airport: "LAX",
      terminal: "B",
      city: "Los Angeles",
      time: "14:30",
      date: "2025-04-22",
      fullDate: "Tuesday, April 22, 2025",
    },
    arrival: {
      airport: "JFK",
      terminal: "4",
      city: "New York",
      time: "22:45",
      date: "2025-04-22",
      fullDate: "Tuesday, April 22, 2025",
    },
    duration: "5h 15m",
    stops: 0,
    aircraft: "Boeing 737-800",
    amenities: ["Wi-Fi", "Power outlets", "In-flight entertainment"],
  },
  duration: "6h 15m",
  stops: 0,
  aircraft: "Boeing 787-9",
  amenities: ["Wi-Fi", "Power outlets", "In-flight entertainment"],
  baggageAllowance: {
    carryOn: "1 bag (8 kg)",
    checked: "1 bag (23 kg)",
  },
  price: 299,
  seatsAvailable: 12,
  refundable: true,
  fareClass: "Economy",
}

export default function FlightDetailsPage({ params }: { params: { id: string } }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/logo1.png" alt="Rea Travel Logo" width={32} height={32} />
            <span className="text-xl font-bold">Rea Travel</span>
          </div>
          <MainNav />
          <UserNav />
        </div>
      </header>

      <main className="flex-1">
        <div className="container py-6">
          <div className="mb-6">
            <Link
              href="/flights"
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Search Results
            </Link>

            <FlightDetailsHeader
              origin={selectedFlight.departure.city}
              originCode={selectedFlight.departure.airport}
              destination={selectedFlight.arrival.city}
              destinationCode={selectedFlight.arrival.airport}
              departDate={selectedFlight.departure.fullDate}
              returnDate={selectedFlight.returnFlight?.departure.fullDate}
              passengers={1}
              price={selectedFlight.price}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
            {/* Flight Details and Booking Form */}
            <div className="space-y-6">
              <div className="rounded-lg border">
                <div className="p-4 sm:p-6">
                  <h2 className="text-xl font-semibold">Outbound Flight</h2>
                  <p className="text-sm text-muted-foreground">{selectedFlight.departure.fullDate}</p>
                </div>
                <Separator />
                <FlightDetailsCard flight={selectedFlight} />
              </div>

              {selectedFlight.returnFlight && (
                <div className="rounded-lg border">
                  <div className="p-4 sm:p-6">
                    <h2 className="text-xl font-semibold">Return Flight</h2>
                    <p className="text-sm text-muted-foreground">{selectedFlight.returnFlight.departure.fullDate}</p>
                  </div>
                  <Separator />
                  <FlightDetailsCard
                    flight={{
                      ...selectedFlight.returnFlight,
                      id: selectedFlight.id,
                      price: selectedFlight.price,
                      seatsAvailable: selectedFlight.seatsAvailable,
                      baggageAllowance: selectedFlight.baggageAllowance,
                      refundable: selectedFlight.refundable,
                      fareClass: selectedFlight.fareClass,
                    }}
                  />
                </div>
              )}

              <BookingForm />
            </div>

            {/* Price Summary */}
            <div className="h-fit rounded-lg border">
              <div className="p-4 sm:p-6">
                <h2 className="text-xl font-semibold">Price Summary</h2>
              </div>
              <Separator />
              <div className="p-4 sm:p-6">
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Base fare (1 passenger)</span>
                    <span>${selectedFlight.price}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Taxes and fees</span>
                    <span>$45.60</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Baggage fees</span>
                    <span>Included</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between font-bold">
                    <span>Total</span>
                    <span>${(selectedFlight.price + 45.6).toFixed(2)}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    <p>Fare rules:</p>
                    <ul className="mt-1 list-inside list-disc">
                      <li>{selectedFlight.refundable ? "Refundable" : "Non-refundable"}</li>
                      <li>Changes allowed (fee may apply)</li>
                      <li>Fare class: {selectedFlight.fareClass}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

