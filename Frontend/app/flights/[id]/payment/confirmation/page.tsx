"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams, useSearchParams } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"


import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { PaymentConfirmation } from "@/components/payment-confirmation"
import { LoadingSpinner } from "@/components/loading-spinner"
import { toast } from "@/components/ui/use-toast"
import { getBookingData, getStorageInfo } from "@/utils/booking-storage"

export default function ConfirmationPage() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const flightId = params.id as string
  const { user, isLoaded } = useUser()

  const [isLoading, setIsLoading] = useState(true)
  const [booking, setBooking] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [dataRecovered, setDataRecovered] = useState(false)
  const [isHydrated, setIsHydrated] = useState(false)

  // Helper function to validate and ensure booking data structure
  const validateBookingData = (data: any) => {

    
    // Check if data is nested under 'data' property (backend response structure)
    const actualData = data?.data || data
    
    // If the data is already in the correct format (from backend), use it directly
    if (actualData && (actualData.bookingReference || actualData.booking_reference) && actualData.flightDetails) {

      return actualData
    }
    
    // If data needs basic structure validation, ensure required fields exist
    const validatedData = {
      bookingReference: actualData?.bookingReference || actualData?.booking_reference || actualData?.order_id || data?.data?.bookingReference || 'N/A',
      id: actualData?.order_id || actualData?.id || actualData?.bookingReference || 'N/A',
      flightDetails: actualData?.flightDetails || {
        outbound: null,
        return: null
      },
      passengers: actualData?.passengers || actualData?.passengerDetails || [],
      contactInfo: actualData?.contactInfo || {},
      pricing: actualData?.pricing || {},
      totalAmount: actualData?.totalAmount || actualData?.total || 0,
      passengerDetails: actualData?.passengerDetails || {},
      seatSelection: actualData?.seatSelection || {},
      raw_response: data
    }
    

    return validatedData
  }

  // Handle client-side hydration
  useEffect(() => {
    setIsHydrated(true)
  }, [])

  // Development-only: Auto-recovery mechanism for hot reloads
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development' || !isHydrated || booking) return

    const checkForRecovery = () => {
      const bookingReference = searchParams.get("reference")
      if (!bookingReference) return

      const completedBookingData = getBookingData()
      if (completedBookingData) {
        const backendBookingRef = completedBookingData.data?.bookingReference ||
                                 completedBookingData.booking_reference ||
                                 completedBookingData.order_id ||
                                 completedBookingData.OrderID

        if (backendBookingRef === bookingReference) {

          const validatedBooking = validateBookingData(completedBookingData)
          setBooking(validatedBooking)
          setDataRecovered(true)
          setIsLoading(false)
        }
      }
    }

    // Check immediately and then periodically
    checkForRecovery()
    const interval = setInterval(checkForRecovery, 500)

    // Clean up after 5 seconds
    const timeout = setTimeout(() => {
      clearInterval(interval)
    }, 5000)

    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [isHydrated, booking, searchParams])

  // Enhanced data recovery mechanism that handles hot reloads
  useEffect(() => {
    // Don't run until hydrated to prevent SSR/client mismatch
    if (!isHydrated) return
    const fetchBooking = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Get the booking reference from URL query parameter
        const bookingReference = searchParams.get("reference")

        if (!bookingReference) {
          throw new Error("Booking reference not found")
        }

        // Enhanced storage recovery with multiple attempts
        let completedBookingData = null
        let recoveryMethod = "none"

        // Attempt 1: Try immediate retrieval
        const storageInfo = getStorageInfo()


        completedBookingData = getBookingData()

        // Attempt 2: If no data found, wait a bit and try again (handles hot reload timing)
        if (!completedBookingData && process.env.NODE_ENV === 'development') {

          await new Promise(resolve => setTimeout(resolve, 100))
          completedBookingData = getBookingData()
          if (completedBookingData) {
            recoveryMethod = "delayed_retry"
          }
        }

        if (completedBookingData) {


          // Determine recovery method for user feedback
          if (!storageInfo.hasSessionData && storageInfo.hasLocalData && !storageInfo.localDataExpired) {
            recoveryMethod = "localStorage"
          } else if (!storageInfo.hasSessionData && !storageInfo.hasLocalData && storageInfo.hasPersistentData && !storageInfo.persistentDataExpired) {
            recoveryMethod = "persistent_backup"
          } else if (storageInfo.hasSessionData) {
            recoveryMethod = "sessionStorage"
          }

          // Show appropriate user feedback
          if (recoveryMethod === "localStorage") {
            setDataRecovered(true)
            toast({
              title: "Booking Data Recovered",
              description: "Your booking details were successfully restored after the page refresh.",
              variant: "default",
            })
          } else if (recoveryMethod === "persistent_backup") {
            setDataRecovered(true)
            toast({
              title: "Booking Data Restored",
              description: "Your booking details were restored from development backup after hot reload.",
              variant: "default",
            })
          } else if (recoveryMethod === "delayed_retry") {
            setDataRecovered(true)
            toast({
              title: "Data Synchronized",
              description: "Your booking details have been synchronized successfully.",
              variant: "default",
            })
          }
          
          // Check if this is the right booking by reference
        // Updated to check the correct data structure from backend response
        const backendBookingRef = completedBookingData.data?.bookingReference || 
                                 completedBookingData.booking_reference || 
                                 completedBookingData.order_id ||
                                 completedBookingData.OrderID
        
        if (backendBookingRef === bookingReference) {
          
          // Use the structured data directly from hybrid storage
          const validatedBooking = validateBookingData(completedBookingData)

          setBooking(validatedBooking)
          setIsLoading(false)
          return
        }
        }

        // If not in session storage, try to fetch from backend API
        try {
          const { api } = await import('@/utils/api-client')
          const response = await api.get(`/api/verteil/booking/${bookingReference}`)
          
          if (response.data.status === 'success') {
            // Use the structured data directly from backend API
            const validatedBooking = validateBookingData(response.data.data)
            setBooking(validatedBooking)
          } else {
            throw new Error(response.data.error || 'Booking not found')
          }
        } catch (apiError) {

          throw new Error("Booking not found. Please check your booking reference.")
        }
      } catch (err) {

        
        // Check if localStorage data was expired and provide helpful message
        const storageInfo = getStorageInfo()
        let errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
        
        if ((storageInfo.hasLocalData && storageInfo.localDataExpired) || 
            (storageInfo.hasPersistentData && storageInfo.persistentDataExpired)) {
          errorMessage = "Your booking session has expired. Please check your email for booking confirmation or contact support."
        } else if (!storageInfo.hasSessionData && !storageInfo.hasLocalData && 
                   (!storageInfo.hasPersistentData || storageInfo.persistentDataExpired)) {
          errorMessage = "Booking details not found. Please check your booking reference or contact support."
        }
        
        setError(errorMessage)
        
        toast({
          title: "Error Loading Booking",
          description: errorMessage,
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchBooking()
  }, [searchParams, flightId, isHydrated])

  // Show loading spinner while checking authentication, hydrating, or loading data
  if (!isHydrated || isLoading) {
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
          <div className="container flex h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
            <div className="flex items-center gap-2">
              <Image src="/logo1.png" alt="Rea Travel Logo" width={32} height={32} />
              <span className="text-sm sm:text-base md:text-lg font-semibold">Rea Travel</span>
            </div>
            <div className="flex items-center gap-4">
              <MainNav />
              <UserNav />
            </div>
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
                  <Link href={`/flights/${flightId}`}>
                    <button className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90">
                      View Flight Details
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
        <div className="container flex h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <Image src="/logo1.png" alt="Rea Travel Logo" width={32} height={32} />
            <span className="text-sm sm:text-base md:text-lg font-semibold">Rea Travel</span>
          </div>
          <div className="flex items-center gap-4">
            <MainNav />
            <UserNav />
          </div>
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

            {dataRecovered && (
              <div className="mt-4 rounded-md bg-green-50 border border-green-200 p-3">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-green-800">
                      Booking data successfully recovered and synchronized.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <PaymentConfirmation booking={booking} />
        </div>
      </main>

      <footer className="border-t bg-background">
        <div className="container py-6 text-center text-sm text-muted-foreground">
          <p>{new Date().getFullYear()} Rea Travel. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
