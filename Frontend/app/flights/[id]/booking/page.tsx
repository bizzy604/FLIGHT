"use client"

import { useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"
import { useUser } from "@clerk/nextjs"
import { Separator } from "@/components/ui/separator"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { BookingForm } from "@/components/booking-form"
import { LoadingSpinner } from "@/components/loading-spinner"

export default function BookingPage() {
  const { user, isLoaded } = useUser()
  const router = useRouter()
  const params = useParams()
  const flightId = params.id as string

  useEffect(() => {
    // If user is not authenticated, redirect to sign-in
    if (isLoaded && !user) {
      router.push(`/sign-in?redirect_url=${encodeURIComponent(`/flights/${flightId}/booking`)}`)
    }
  }, [isLoaded, user, router, flightId])

  if (!isLoaded || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
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
              href={`/flights/${flightId}`}
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Flight Details
            </Link>

            <h1 className="mt-4 text-2xl font-bold md:text-3xl">Complete Your Booking</h1>
            <p className="text-muted-foreground">
              Welcome, {user.firstName || user.username || "User"}! Please fill in the details to complete your booking.
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
            <BookingForm />

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
                    <span>$299.00</span>
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
                    <span>$344.60</span>
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

