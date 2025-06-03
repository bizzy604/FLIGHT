"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft, Lock, Shield } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { StripeProvider } from "@/components/stripe-provider"
import { StripePaymentForm } from "@/components/stripe-payment-form"
import { PaymentConfirmation } from "@/components/payment-confirmation"
import { OrderSummary } from "@/components/order-summary"
import { ErrorBoundary } from "@/components/error-boundary"
import { LoadingSpinner } from "@/components/loading-spinner"
import { toast } from "@/components/ui/use-toast"

export default function PaymentPage() {
  const router = useRouter()
  const params = useParams()
  const flightId = params.id as string
  const { user, isLoaded, isSignedIn } = useUser()

  const [paymentStatus, setPaymentStatus] = useState<"pending" | "processing" | "success" | "error">("pending")
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [booking, setBooking] = useState<any>(null)

  // Fetch booking data from session storage or API
  useEffect(() => {
    const fetchBooking = async () => {
      try {
        setIsLoading(true)

        // First try to get booking from session storage
        const bookingReference = sessionStorage.getItem("bookingReference")
        const bookingData = sessionStorage.getItem("bookingData")

        if (bookingReference && bookingData) {
          setBooking(JSON.parse(bookingData))
          setIsLoading(false)
          return
        }

        // If not in session storage, try to get from URL query param
        const urlParams = new URLSearchParams(window.location.search)
        const refParam = urlParams.get("ref")

        if (refParam) {
          // Try to fetch booking by reference
          const response = await fetch(`/api/bookings?reference=${refParam}`)

          if (!response.ok) {
            throw new Error("Failed to fetch booking")
          }

          const data = await response.json()

          if (data.bookings && data.bookings.length > 0) {
            setBooking(data.bookings[0])
            setIsLoading(false)
            return
          }
        }

        // If we still don't have a booking, try to fetch by flight ID
        const response = await fetch(`/api/bookings?flightId=${flightId}`)

        if (!response.ok) {
          throw new Error("Failed to fetch booking")
        }

        const data = await response.json()

        if (data.bookings && data.bookings.length > 0) {
          setBooking(data.bookings[0])
        } else {
          // No booking found, redirect to booking page
          toast({
            title: "No booking found",
            description: "Please complete the booking process first",
            variant: "destructive",
          })
          router.push(`/flights/${flightId}/booking`)
        }
      } catch (err) {
        console.error("Error fetching booking:", err)
        setError("Failed to load booking details. Please try again.")
      } finally {
        setIsLoading(false)
      }
    }

    fetchBooking()
  }, [flightId, router])

  const handlePaymentSuccess = () => {
    setPaymentStatus("success")
    // Clear session storage after successful payment
    sessionStorage.removeItem("bookingReference")
    sessionStorage.removeItem("bookingData")
  }

  const handlePaymentError = (errorMessage: string) => {
    setPaymentStatus("error")
    setError(errorMessage)
  }

  // Show loading spinner while checking authentication or loading data
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // If no booking was found
  if (!booking && !isLoading) {
    return (
      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-16 items-center justify-between">
            <div className="flex items-center gap-2">
              <Image src="/logo1.png" alt="SkyWay Logo" width={32} height={32} />
              <span className="text-xl font-bold">Rea Travel</span>
            </div>
            <MainNav />
            <UserNav />
          </div>
        </header>

        <main className="flex-1 container py-12">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">No Booking Found</h1>
            <p className="mb-6 text-muted-foreground">
              You don't have an active booking for this flight. Please complete the booking process first.
            </p>
            <Link
              href={`/flights/${flightId}/booking`}
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Go to Booking
            </Link>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/placeholder.svg?height=32&width=32" alt="SkyWay Logo" width={32} height={32} />
            <span className="text-xl font-bold">SkyWay</span>
          </div>
          <MainNav />
          <UserNav />
        </div>
      </header>

      <main className="flex-1">
        <ErrorBoundary>
          <div className="container py-6">
            {paymentStatus !== "success" && (
              <div className="mb-6">
                <Link
                  href={`/flights/${params.id}`}
                  className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
                >
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Back to Flight Details
                </Link>

                <h1 className="mt-4 text-2xl font-bold md:text-3xl">Payment</h1>
                <div className="mt-2 flex items-center text-sm text-muted-foreground">
                  <Lock className="mr-1 h-4 w-4" />
                  <span>Secure payment processing with Stripe</span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Please complete your payment to confirm your booking {booking.bookingReference}.
                </p>
              </div>
            )}

            {error && (
              <div className="mb-6 rounded-md bg-destructive/10 p-4 text-destructive">
                <p>{error}</p>
              </div>
            )}

            {paymentStatus === "success" ? (
              <PaymentConfirmation booking={booking} />
            ) : (
              <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
                {/* Payment Form */}
                <div className="space-y-6">
                  <div className="rounded-lg border">
                    <div className="flex items-center justify-between p-4 sm:p-6">
                      <h2 className="text-xl font-semibold">Payment Method</h2>
                      <div className="flex items-center space-x-2">
                        <Image
                          src="/placeholder.svg?height=24&width=36"
                          alt="Visa"
                          width={36}
                          height={24}
                          className="rounded"
                        />
                        <Image
                          src="/placeholder.svg?height=24&width=36"
                          alt="Mastercard"
                          width={36}
                          height={24}
                          className="rounded"
                        />
                        <Image
                          src="/placeholder.svg?height=24&width=36"
                          alt="American Express"
                          width={36}
                          height={24}
                          className="rounded"
                        />
                      </div>
                    </div>
                    <Separator />
                    <StripeProvider>
                      <StripePaymentForm
                        bookingReference={booking.bookingReference}
                        amount={booking.totalAmount}
                        currency="usd"
                        flightDetails={{
                          id: flightId,
                          from: booking.flightDetails.outbound.departure.city,
                          to: booking.flightDetails.outbound.arrival.city,
                          departureDate: booking.flightDetails.outbound.departure.fullDate,
                          returnDate: booking.flightDetails.return?.departure.fullDate,
                        }}
                        onPaymentSuccess={handlePaymentSuccess}
                        onPaymentError={handlePaymentError}
                      />
                    </StripeProvider>
                  </div>

                  <div className="rounded-lg border bg-muted/50 p-4">
                    <div className="flex items-start space-x-4">
                      <Shield className="mt-0.5 h-6 w-6 text-muted-foreground" />
                      <div>
                        <h3 className="font-medium">Secure Payment</h3>
                        <p className="text-sm text-muted-foreground">
                          Your payment information is securely processed by Stripe. Your card details never touch our
                          servers.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Order Summary */}
                <div>
                  <OrderSummary booking={booking} />
                </div>
              </div>
            )}
          </div>
        </ErrorBoundary>
      </main>

      <footer className="border-t bg-background">
        <div className="container py-6 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} Rea Travel. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
