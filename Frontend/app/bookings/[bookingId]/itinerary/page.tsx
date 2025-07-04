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

          // Transform stored booking data to itinerary format
          if (bookingData.orderCreateResponse) {
            try {
              console.log('📋 Raw orderCreateResponse type:', typeof bookingData.orderCreateResponse)
              console.log('📋 Raw orderCreateResponse preview:',
                typeof bookingData.orderCreateResponse === 'string'
                  ? bookingData.orderCreateResponse.substring(0, 200) + '...'
                  : Object.keys(bookingData.orderCreateResponse || {})
              )

              const parsedOrderCreate = typeof bookingData.orderCreateResponse === 'string'
                ? JSON.parse(bookingData.orderCreateResponse)
                : bookingData.orderCreateResponse

              console.log('📋 Parsed orderCreateResponse keys:', Object.keys(parsedOrderCreate || {}))

              // Parse originalFlightOffer if available
              let originalFlightOffer = bookingData.originalFlightOffer
                ? (typeof bookingData.originalFlightOffer === 'string'
                    ? JSON.parse(bookingData.originalFlightOffer)
                    : bookingData.originalFlightOffer)
                : null

              // Also check session storage for flightPriceResponseForBooking
              let sessionFlightData = null;
              console.log('📋 Checking session storage for flightPriceResponseForBooking...');
              try {
                const sessionData = sessionStorage.getItem('flightPriceResponseForBooking');
                console.log('📋 Session storage raw data:', sessionData ? 'Found' : 'Not found');

                if (sessionData) {
                  sessionFlightData = JSON.parse(sessionData);
                  console.log('📋 Found flightPriceResponseForBooking in session storage');
                  console.log('📋 Session flight data structure:', {
                    hasPassengers: !!sessionFlightData.passengers,
                    passengerCount: sessionFlightData.passengers?.length || 0,
                    hasFareRules: !!sessionFlightData.passengers?.[0]?.fare_rules,
                    fareRulesKeys: sessionFlightData.passengers?.[0]?.fare_rules ? Object.keys(sessionFlightData.passengers[0].fare_rules) : []
                  });

                  // Use session data if originalFlightOffer doesn't have fare rules
                  if (!originalFlightOffer?.passengers?.[0]?.fare_rules && sessionFlightData.passengers?.[0]?.fare_rules) {
                    originalFlightOffer = sessionFlightData;
                    console.log('📋 Using session storage data for fare rules');
                  } else {
                    console.log('📋 Not using session data:', {
                      originalHasFareRules: !!originalFlightOffer?.passengers?.[0]?.fare_rules,
                      sessionHasFareRules: !!sessionFlightData.passengers?.[0]?.fare_rules
                    });
                  }
                } else {
                  console.log('📋 No flightPriceResponseForBooking in session storage');
                }
              } catch (e) {
                console.log('📋 Error accessing session storage:', e);
              }

              console.log('📋 Original flight offer available:', !!originalFlightOffer)
              if (originalFlightOffer) {
                console.log('📋 Original flight offer keys:', Object.keys(originalFlightOffer))
                console.log('📋 Has raw_flight_price_response:', !!originalFlightOffer.raw_flight_price_response)
                console.log('📋 Has processed fare_rules:', !!originalFlightOffer.passengers?.[0]?.fare_rules)
              }

              const transformedData = transformOrderCreateToItinerary(parsedOrderCreate, originalFlightOffer)
              setItineraryData(transformedData)
              console.log('✅ Successfully transformed itinerary data')
            } catch (transformError) {
              console.error('❌ Error transforming booking data:', transformError)
              console.error('❌ Transform error details:', {
                message: transformError instanceof Error ? transformError.message : 'Unknown error',
                stack: transformError instanceof Error ? transformError.stack : undefined
              })
              setError('Unable to display itinerary. Booking data may be corrupted.')
            }
          } else {
            console.warn('⚠️ No orderCreateResponse found in booking data')
            console.log('📋 Available booking data keys:', Object.keys(bookingData || {}))
            setError('Itinerary data not available for this booking.')
          }
        } else {
          throw new Error(response.data.error || 'Booking not found')
        }
      } catch (err) {
        console.error('Error fetching booking:', err)
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
      console.error('Error generating PDF:', error)
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

          {/* Official Itinerary Display */}
          <div className="mb-8">
            <div id="booking-itinerary">
              <OfficialItinerary data={itineraryData} />
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
