"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft, Download, Mail, Printer } from "lucide-react"

import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { LoadingSpinner } from "@/components/loading-spinner"
import { LoadingButton } from "@/components/ui/button"
import { toast } from "@/components/ui/use-toast"
import OfficialItinerary from "@/components/itinerary/OfficialItinerary"
import BoardingPassItinerary from "@/components/itinerary/BoardingPassItinerary"
import { transformOrderCreateToItinerary, ItineraryData } from "@/utils/itinerary-data-transformer"
import { generatePDFFromComponent } from "@/utils/download-utils"

export default function BookingItineraryPage() {
  const router = useRouter()
  const params = useParams()
  const bookingId = params.bookingId as string
  const { user, isLoaded } = useUser()

  const [isLoading, setIsLoading] = useState(true)
  const [booking, setBooking] = useState<any>(null)
  const [itineraryData, setItineraryData] = useState<ItineraryData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)
  const [isEmailing, setIsEmailing] = useState(false)

  useEffect(() => {
    if (!isLoaded) return

    const fetchBooking = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Fetch booking from database
        const { api } = await import('@/utils/api-client')
        const response = await api.get(`/api/verteil/booking/${bookingId}`)
        
        if (response.data.status === 'success') {
          const bookingData = response.data.data
          setBooking(bookingData)

          // Parse originalFlightOffer if available (declare outside if block)
          let originalFlightOffer = bookingData.originalFlightOffer
            ? (typeof bookingData.originalFlightOffer === 'string'
                ? JSON.parse(bookingData.originalFlightOffer)
                : bookingData.originalFlightOffer)
            : null

          // Transform stored booking data to itinerary format
          if (bookingData.orderCreateResponse) {
            try {
              const parsedOrderCreate = typeof bookingData.orderCreateResponse === 'string'
                ? JSON.parse(bookingData.orderCreateResponse)
                : bookingData.orderCreateResponse

              // Also check session storage for flightPriceResponseForBooking
              let sessionFlightData = null;
              try {
                const sessionData = sessionStorage.getItem('flightPriceResponseForBooking');

                if (sessionData) {
                  sessionFlightData = JSON.parse(sessionData);

                  // Use session data if originalFlightOffer doesn't have fare rules
                  if (!originalFlightOffer?.passengers?.[0]?.fare_rules && sessionFlightData.passengers?.[0]?.fare_rules) {
                    originalFlightOffer = sessionFlightData;
                  }
                }
              } catch (e) {
                // Silently handle session storage errors
              }



              // Prepare basic booking data for fallback
              const basicBookingData = {
                bookingReference: bookingData.bookingReference,
                createdAt: bookingData.createdAt,
                passengerDetails: bookingData.passengerDetails,
                contactInfo: bookingData.contactInfo,
                documentNumbers: bookingData.documentNumbers
              };

              const transformedData = transformOrderCreateToItinerary(parsedOrderCreate, originalFlightOffer, basicBookingData)
              setItineraryData(transformedData)
            } catch (transformError) {
              setError('Unable to display itinerary. Booking data may be corrupted.')
            }
          } else if (originalFlightOffer) {
            // Fallback: Use originalFlightOffer when orderCreateResponse is missing
            try {
              const basicBookingData = {
                bookingReference: bookingData.bookingReference,
                createdAt: bookingData.createdAt,
                passengerDetails: bookingData.passengerDetails,
                contactInfo: bookingData.contactInfo,
                documentNumbers: bookingData.documentNumbers
              };

              const transformedData = transformOrderCreateToItinerary(null, originalFlightOffer, basicBookingData)
              setItineraryData(transformedData)
            } catch (fallbackError) {
              setError('Unable to display itinerary. Limited booking data available.')
            }
          } else {
            setError('Itinerary data not available for this booking.')
          }
        } else {
          throw new Error(response.data.error || 'Booking not found')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load booking")
        
        toast({
          title: "Error Loading Booking",
          description: "Unable to load booking details. Please try again.",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchBooking()
  }, [bookingId, isLoaded])

  const handleDownloadItinerary = async () => {
    if (!itineraryData) {
      toast({
        title: "Download Failed",
        description: "Itinerary data is not available.",
        variant: "destructive",
      })
      return
    }

    if (!itineraryData.bookingInfo || !itineraryData.bookingInfo.bookingReference) {
      toast({
        title: "Download Failed",
        description: "Booking reference is not available.",
        variant: "destructive",
      })
      return
    }

    setIsDownloading(true)
    try {
      await generatePDFFromComponent(
        'booking-itinerary',
        `flight-itinerary-${itineraryData.bookingInfo.bookingReference}.pdf`
      )
      toast({
        title: "Download Successful",
        description: "PDF has been generated successfully.",
        variant: "default",
      })
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Unable to generate PDF. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsDownloading(false)
    }
  }

  const handleEmailItinerary = async () => {
    setIsEmailing(true)
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      // In a real app, this would trigger an API call to send an email
      toast({
        title: "Email Sent",
        description: `Itinerary sent to ${booking?.contactEmail || 'your email'}`,
        variant: "default",
      })
    } finally {
      setIsEmailing(false)
    }
  }

  // Show loading spinner while checking authentication or loading data
  if (!isLoaded || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner className="h-12 w-12" />
      </div>
    )
  }

  // If booking not found or error occurred
  if (error || !booking || !itineraryData) {
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
                href="/bookings"
                className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Back to Bookings
              </Link>

              <div className="mt-6 rounded-lg border p-6 text-center">
                <h1 className="mb-4 text-2xl font-bold">Itinerary Not Available</h1>
                <p className="mb-6 text-muted-foreground">
                  {error || "We couldn't load the itinerary for this booking."}
                </p>
                <div className="flex justify-center gap-4">
                  <Link href="/bookings">
                    <button className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90">
                      Back to Bookings
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
              href="/bookings"
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Back to Bookings
            </Link>

            <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="text-2xl font-bold md:text-3xl">Flight Itinerary</h1>
                <p className="text-muted-foreground">
                  Booking Reference: {itineraryData.bookingInfo.bookingReference}
                </p>
              </div>
              
              <div className="flex flex-wrap gap-2">
                <LoadingButton
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-1"
                  onClick={handleEmailItinerary}
                  loading={isEmailing}
                  loadingText="Sending..."
                  aria-label="Email itinerary"
                >
                  <Mail className="h-4 w-4" />
                  <span>Email</span>
                </LoadingButton>
                
                <LoadingButton
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-1"
                  onClick={handleDownloadItinerary}
                  loading={isDownloading}
                  loadingText="Generating..."
                  aria-label="Download itinerary"
                >
                  <Download className="h-4 w-4" />
                  <span>Download PDF</span>
                </LoadingButton>
              </div>
            </div>
          </div>

          {/* Boarding Pass Itinerary Display */}
          <div className="mb-8">
            <div id="booking-itinerary">
              <BoardingPassItinerary data={itineraryData} />
            </div>
          </div>
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
