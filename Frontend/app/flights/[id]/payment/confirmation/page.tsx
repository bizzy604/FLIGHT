"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams, useSearchParams } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

import { Separator } from "@/components/ui/separator"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { PaymentConfirmation } from "@/components/payment-confirmation"
import { LoadingSpinner } from "@/components/loading-spinner"
import { toast } from "@/components/ui/use-toast"

export default function ConfirmationPage() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const flightId = params.id as string
  const { user, isLoaded } = useUser()

  const [isLoading, setIsLoading] = useState(true)
  const [booking, setBooking] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch booking data from session storage or API
  useEffect(() => {
    const fetchBooking = async () => {
      try {
        setIsLoading(true)

        // Get the booking reference from URL query parameter
        const bookingReference = searchParams.get("reference")

        if (!bookingReference) {
          throw new Error("Booking reference not found")
        }

        // First try to get booking from session storage
        const bookingData = sessionStorage.getItem("bookingData")

        if (bookingData) {
          const parsedBooking = JSON.parse(bookingData)
          if (parsedBooking.bookingReference === bookingReference) {
            setBooking(parsedBooking)
            setIsLoading(false)
            return
          }
        }

        // If not in session storage, fetch from API
        const response = await fetch(`/api/bookings?reference=${bookingReference}`)

        if (!response.ok) {
          throw new Error("Failed to fetch booking")
        }

        const data = await response.json()

        if (data.bookings && data.bookings.length > 0) {
          setBooking(data.bookings[0])
        } else {
          throw new Error("Booking not found")
        }
      } catch (err) {
        console.error("Error fetching booking:", err)
        setError(err instanceof Error ? err.message : "An unknown error occurred")
      } finally {
        setIsLoading(false)
      }
    }

    fetchBooking()
  }, [searchParams, flightId])

  // Show loading spinner while checking authentication or loading data
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner className="h-12 w-12" />
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
                href={`/flights/${flightId}`}
                className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Back to Flight Details
              </Link>

              <div className="mt-6 rounded-lg border p-6 text-center">
                <h1 className="mb-4 text-2xl font-bold">Booking Not Found</h1>
                <p className="mb-6 text-muted-foreground">
                  {error || "We couldn't find the booking you're looking for."}
                </p>
                <div className="flex justify-center gap-4">
                  <Link href={`/flights/${flightId}/booking`}>
                    <button className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90">
                      Make a New Booking
                    </button>
                  </Link>
                  <Link href="/">
                    <button className="rounded-md border px-4 py-2 hover:bg-muted">
                      Return to Home
                    </button>
                  </Link>
                </div>
              </div>
            </div>
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
              href="/"
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Home
            </Link>

            <h1 className="mt-4 text-2xl font-bold md:text-3xl">Booking Confirmation</h1>
          </div>

          <PaymentConfirmation booking={booking} />
        </div>
      </main>

      <footer className="border-t bg-background">
        <div className="container py-6 text-center text-sm text-muted-foreground">
          <p>u00a9 {new Date().getFullYear()} Rea Travel. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
