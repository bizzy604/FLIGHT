"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import Link from "next/link"
import { ChevronLeft, Lock, Shield } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { LoadingButton } from "@/components/ui/button"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { CardPaymentForm } from "@/components/card-payment-form"
import { PaymentConfirmation } from "@/components/payment-confirmation"
import { OrderSummary } from "@/components/order-summary"
import { ErrorBoundary } from "@/components/error-boundary"
import { LoadingSpinner } from "@/components/loading-spinner"
import { toast } from "@/components/ui/use-toast"
import { storeBookingData } from "@/utils/booking-storage"
import { flightStorageManager } from "@/utils/flight-storage-manager"
import { navigationCacheManager } from "@/utils/navigation-cache-manager"

export default function PaymentPage() {
  const router = useRouter()
  const params = useParams()
  const flightId = decodeURIComponent(params.id as string)
  const { user, isLoaded, isSignedIn } = useUser()

  const [paymentStatus, setPaymentStatus] = useState<"pending" | "processing" | "success" | "error">("pending")
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [booking, setBooking] = useState<any>(null)
  const [flightOffer, setFlightOffer] = useState<any>(null)
  const [isProcessingPayment, setIsProcessingPayment] = useState(false)

  // Fetch booking data using robust storage manager
  useEffect(() => {
    const fetchBookingData = async () => {
      setIsLoading(true)
      try {
        // Update navigation state
        navigationCacheManager.updateNavigationState('payment', { flightId });
        let storedPendingBooking = sessionStorage.getItem("pendingBookingData")
        if (!storedPendingBooking) {
          // Try to recover from robust storage as fallback
          const bookingResult = await flightStorageManager.getBookingData()
          if (bookingResult.success && bookingResult.data) {
            storedPendingBooking = JSON.stringify(bookingResult.data)
          } else {
            router.push(`/flights/${flightId}`)
            return
          }
        } else {
        }

        const pendingBooking = JSON.parse(storedPendingBooking)

        // Get flight offer data - prioritize session storage since that's where booking form stores it
        let flightOfferData = null;
        let storedFlightOffer = sessionStorage.getItem("selectedFlightOffer")

        if (storedFlightOffer) {
          flightOfferData = JSON.parse(storedFlightOffer);
          setFlightOffer(flightOfferData);
        } else {
          // Fallback to robust storage
          const selectedFlightResult = await flightStorageManager.getSelectedFlight()
          if (selectedFlightResult.success && selectedFlightResult.data) {
            flightOfferData = selectedFlightResult.data;
            setFlightOffer(flightOfferData);
          } else {
            router.push(`/flights/${flightId}`)
            return
          }
        }

        // The stored flight offer should be the priced offer from flight details page
        const pricedOffer = flightOfferData;

        // Extract pricing from the priced offer structure (same as flight details page)
        let currency = "USD"
        let totalPrice = 0

        if (pricedOffer.total_price) {
          totalPrice = pricedOffer.total_price.amount || 0
          currency = pricedOffer.total_price.currency || "USD"
        }

        // Create pricing object for backward compatibility
        const pricing = {
          total_price: totalPrice,
          total_price_per_traveler: totalPrice,
          currency: currency
        }
        
        // The booking form now stores the complete flight offer data with optimized metadata
        // Check if the data is already properly structured from the booking form
        let flightOfferWithOptimizedData;

        if ((pricedOffer.metadata && pricedOffer.metadata.flight_price_cache_key) ||
            (pricedOffer.raw_flight_price_response && pricedOffer.shopping_response_id)) {
          // Data is already properly structured from the booking form (either optimized or fallback)
          flightOfferWithOptimizedData = pricedOffer;
        } else {
          // Fallback: extract from old structure (for backward compatibility)
          const rawFlightPriceResponse = pricedOffer?.data?.raw_response

          // Extract ShoppingResponseID and OrderID from raw response for backend
          let shoppingResponseId = null;
          let orderId = null;

          // Try multiple possible paths for ShoppingResponseID based on terminal logs
          if (rawFlightPriceResponse?.ShoppingResponseID?.ResponseID?.value) {
            shoppingResponseId = rawFlightPriceResponse.ShoppingResponseID.ResponseID.value;
          } else if (rawFlightPriceResponse?.data?.ShoppingResponseID?.ResponseID?.value) {
            shoppingResponseId = rawFlightPriceResponse.data.ShoppingResponseID.ResponseID.value;
          } else if (rawFlightPriceResponse?.data?.raw_response?.ShoppingResponseID?.ResponseID?.value) {
            shoppingResponseId = rawFlightPriceResponse.data.raw_response.ShoppingResponseID.ResponseID.value;
          }

          // Try multiple possible paths for OfferID
          if (rawFlightPriceResponse?.PricedFlightOffers?.PricedFlightOffer?.[0]?.OfferID?.value) {
            orderId = rawFlightPriceResponse.PricedFlightOffers.PricedFlightOffer[0].OfferID.value;
          } else if (rawFlightPriceResponse?.data?.PricedFlightOffers?.PricedFlightOffer?.[0]?.OfferID?.value) {
            orderId = rawFlightPriceResponse.data.PricedFlightOffers.PricedFlightOffer[0].OfferID.value;
          } else if (rawFlightPriceResponse?.data?.raw_response?.PricedFlightOffers?.PricedFlightOffer?.[0]?.OfferID?.value) {
            orderId = rawFlightPriceResponse.data.raw_response.PricedFlightOffers.PricedFlightOffer[0].OfferID.value;
          }

          // Try to get optimized metadata first
          const storedMetadata = sessionStorage.getItem('flightPriceMetadata');
          const flightPriceMetadata = storedMetadata ? JSON.parse(storedMetadata) : null;

          flightOfferWithOptimizedData = {
            ...pricedOffer,
            metadata: flightPriceMetadata,  // Include metadata with cache key for optimized retrieval
            raw_flight_price_response: rawFlightPriceResponse,  // Fallback for backward compatibility
            shopping_response_id: shoppingResponseId,
            order_id: orderId
          }

          if (flightPriceMetadata?.flight_price_cache_key) {
          } else {
          }
        }
        

        const bookingData = {
          ...pendingBooking,
          flightOffer: flightOfferWithOptimizedData, // Pass the optimized flight offer with metadata/cache key
          flightDetails: pricedOffer, // For backward compatibility with UI components
          totalAmount: totalPrice,
          currency: currency,
          pricing: {
            baseFare: 0, // Will be extracted from priced offer in OrderSummary
            taxes: 0, // Will be extracted from priced offer in OrderSummary
            total: totalPrice,
            currency: currency
          },
          status: "pending"
        }
        
        setBooking(bookingData)
      } catch (error) {
        router.push(`/flights/${flightId}`)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookingData()
  }, [flightId, router])

  const createBookingWithBackend = async (paymentData: any) => {
    try {
      if (!booking) {
        throw new Error("No booking data available")
      }

      // Import the API client
      const { api } = await import('@/utils/api-client')
      
      // Prepare payment information based on payment method
      // Map frontend payment method values to backend expected values
      const mapPaymentMethod = (frontendMethod: string) => {
        switch (frontendMethod) {
          case 'CASH':
            return 'CASH';
          case 'PAYMENTCARD':
            return 'CREDIT_CARD';
          case 'EASYPAY':
            return 'EASYPAY';
          case 'OTHER':
            return 'OTHER';
          default:
            return 'CREDIT_CARD';
        }
      };

      const paymentInfo: { payment_method: string; paymentMethodId?: string; paymentInfo?: any } = {
        payment_method: mapPaymentMethod(booking.paymentMethod),
      };

      // Include payment data based on payment method
      if (paymentInfo.payment_method === 'CREDIT_CARD' && paymentData && typeof paymentData === 'object') {
        // Include payment method ID if available
        if (paymentData.id) {
          paymentInfo.paymentMethodId = paymentData.id;
        }
        
        // Include the structured payment info for backend processing
        if (paymentData.paymentInfo) {
          paymentInfo.paymentInfo = paymentData.paymentInfo;
        }
      }
      // For other payment methods like 'cash', no additional data from paymentData is added by default.
      // If other methods require specific fields from paymentData, they should be explicitly and safely added here.



      const response = await api.createBooking(
        booking.flightOffer,
        booking.passengers,
        paymentInfo, 
        booking.contactInfo
      )



      if (response.data.status === 'success') {
        // Store the successful booking data using robust storage
        const bookingResult = response.data.data
        const storeSuccess = await storeBookingData(bookingResult)

        if (!storeSuccess) {
        }

        // Store raw OrderCreate response using robust storage for itinerary generation
        if (response.data.raw_order_create_response) {
          const orderCreateData = {
            orderCreateResponse: response.data.raw_order_create_response,
            timestamp: Date.now(),
            expiresAt: Date.now() + (30 * 60 * 1000) // 30 minutes
          }

          // Store in robust storage
          const orderStoreResult = await flightStorageManager.storeSelectedFlight(orderCreateData)
          if (orderStoreResult.success) {
          } else {
            // Fallback to session storage
            sessionStorage.setItem('orderCreateResponse', JSON.stringify(response.data.raw_order_create_response))
          }
        } else {
        }

        // Clear pending booking data
        sessionStorage.removeItem("pendingBookingData")
        sessionStorage.removeItem("selectedFlightOffer")

        return bookingResult
      } else {
        throw new Error(response.data.error || response.data.message || 'Booking creation failed')
      }
    } catch (error) {
      throw error
    }
  }

  const handlePaymentSuccess = async (paymentData: any = {}) => {
    try {
      setIsLoading(true)
      setIsProcessingPayment(true)
      setPaymentStatus("processing") // Show processing state
      
      toast({
        title: "Processing Payment...",
        description: "Please wait while we process your booking.",
      })
      
      // Create the booking with the backend and wait for response
      const bookingResult = await createBookingWithBackend(paymentData)
      
      // Validate that we received a proper booking reference
      // Backend response structure: { data: { bookingReference: "..." } }
      const bookingReference = bookingResult.bookingReference ||
                              bookingResult.booking_reference ||
                              bookingResult.order_id ||
                              bookingResult.data?.bookingReference ||
                              bookingResult.data?.booking_reference ||
                              bookingResult.data?.order_id

      if (!bookingReference) {
        throw new Error("Booking was processed but no booking reference was returned")
      }

      // Store only the backend response for the confirmation page using hybrid storage
      // Backend now provides complete data structure, no frontend enrichment needed
      console.log('🔍 Storing booking data for confirmation page:', {
        bookingReference: bookingResult.bookingReference,
        hasData: !!bookingResult,
        dataKeys: Object.keys(bookingResult || {}),
        fullData: bookingResult
      });

      storeBookingData(bookingResult);
      
      // Update component's booking state (optional, as we redirect soon)
      setBooking((prev: any) => ({
        ...prev,
        ...bookingResult, // Use backend data directly
        id: bookingReference, // Ensure booking ID/reference is updated
        status: 'confirmed'
      }))
      
      setPaymentStatus("success")
       
       toast({
         title: "Booking Confirmed!",
         description: `Your booking has been confirmed. Reference: ${bookingReference}`,
       })
       
       // Redirect to confirmation page after successful booking
       setTimeout(() => {
         router.push(`/flights/${encodeURIComponent(flightId)}/payment/confirmation?reference=${bookingReference}`)
       }, 2000)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      setError(`Payment failed: ${errorMessage}`)
      setPaymentStatus("error")
      
      toast({
        title: "Booking Failed",
        description: errorMessage || "There was an error processing your booking. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
      setIsProcessingPayment(false)
    }
  }

  const handlePaymentError = (errorMessage: string) => {
    setPaymentStatus("error")
    setError(errorMessage)
  }

  // Show loading spinner while checking authentication or loading data
  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center space-y-4">
        <LoadingSpinner className="h-8 w-8" />
        <div className="text-center">
          <p className="text-lg font-medium">Loading Payment Details</p>
          <p className="text-sm text-muted-foreground">Please wait while we prepare your payment information...</p>
        </div>
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
              href={`/flights/${flightId}`}
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Go to Flight Details
            </Link>
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
        <ErrorBoundary>
          <div className="container py-6">
            {paymentStatus !== "success" && (
              <div className="mb-6">
                <Link
                  href={`/flights/${encodeURIComponent(flightId)}`}
                  className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
                >
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Back to Flight Details
                </Link>

                <h1 className="mt-4 text-2xl font-bold md:text-3xl">Payment</h1>
                <div className="mt-2 flex items-center text-sm text-muted-foreground">
                  <Lock className="mr-1 h-4 w-4" />
                  <span>Secure payment processing</span>
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
                      {booking.paymentMethod === 'PAYMENTCARD' && (
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
                      )}
                    </div>
                    <Separator />
                    
                    {/* Conditional Payment Method Rendering */}
                    {booking.paymentMethod === 'PAYMENTCARD' ? (
                      <CardPaymentForm 
                        bookingReference={booking.bookingReference || ""} 
                        amount={booking.totalAmount || 0} 
                        currency={booking.currency || "USD"} 
                        flightDetails={{
                          id: booking.flightOffer?.flight_segments?.[0]?.flight_number || "",
                          from: booking.flightOffer?.flight_segments?.[0]?.departure_airport || "",
                          to: booking.flightOffer?.flight_segments?.[booking.flightOffer?.flight_segments?.length - 1]?.arrival_airport || "",
                          departureDate: booking.flightOffer?.flight_segments?.[0]?.departure_datetime || "",
                          returnDate: booking.flightOffer?.direction === 'roundtrip' ? booking.flightOffer?.flight_segments?.return?.[0]?.departure_datetime : undefined
                        }}
                        onPaymentSuccess={async (paymentData?: any) => {
                          try {
                            // Call the backend to actually book the flight with the captured payment data
                            await handlePaymentSuccess(paymentData)
                          } catch (error) {
                            setError(`Card payment captured but booking failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
                            setPaymentStatus("error")
                          }
                        }}
                        onPaymentError={(error: string) => {
                          // Update booking status to failed
                          setBooking((prev: any) => ({
                            ...prev,
                            status: 'FAILED',
                            paymentStatus: 'FAILED'
                          }))
                          
                          // Show error message
                          alert(`Payment failed: ${error}`)
                        }}/>
                    ) : booking.paymentMethod === 'CASH' ? (
                      <div className="p-6">
                        <div className="text-center space-y-4">
                          <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                          </div>
                          <h3 className="text-lg font-semibold">Cash Payment Selected</h3>
                          <p className="text-muted-foreground">
                            You have selected to pay with cash at the airport counter.
                          </p>
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 className="font-medium text-blue-900 mb-2">Payment Instructions:</h4>
                            <ul className="text-sm text-blue-800 space-y-1">
                              <li>• Arrive at the airport at least 2 hours before departure</li>
                              <li>• Visit the Rea Travel counter with your booking reference</li>
                              <li>• Bring exact cash amount: {booking.totalAmount} {booking.currency}</li>
                              <li>• Present valid ID and booking confirmation</li>
                            </ul>
                          </div>
                          <LoadingButton
                            onClick={handlePaymentSuccess}
                            loading={isProcessingPayment}
                            loadingText="Processing..."
                            className="w-full"
                          >
                            Confirm Cash Payment
                          </LoadingButton>
                        </div>
                      </div>
                    ) : booking.paymentMethod === 'EASYPAY' ? (
                      <div className="p-6">
                        <div className="text-center space-y-4">
                          <div className="w-16 h-16 mx-auto bg-purple-100 rounded-full flex items-center justify-center">
                            <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                            </svg>
                          </div>
                          <h3 className="text-lg font-semibold">EasyPay Payment</h3>
                          <p className="text-muted-foreground">
                            Complete your payment using your EasyPay account.
                          </p>
                          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <p className="text-sm text-purple-800">
                              You will be redirected to EasyPay to complete your payment of ${booking.totalAmount}.
                            </p>
                          </div>
                          <LoadingButton
                            onClick={() => {
                              // In a real implementation, this would redirect to EasyPay
                              alert('Redirecting to EasyPay...');
                              handlePaymentSuccess();
                            }}
                            loading={isProcessingPayment}
                            loadingText="Redirecting..."
                            className="w-full bg-purple-600 text-white hover:bg-purple-700"
                          >
                            Pay with EasyPay
                          </LoadingButton>
                        </div>
                      </div>
                    ) : booking.paymentMethod === 'OTHER' ? (
                      <div className="p-6">
                        <div className="text-center space-y-4">
                          <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                            <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <h3 className="text-lg font-semibold">Alternative Payment Method</h3>
                          <p className="text-muted-foreground">
                            You have selected an alternative payment method.
                          </p>
                          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                            <p className="text-sm text-gray-800">
                              Our customer service team will contact you within 24 hours to arrange payment for ${booking.totalAmount}.
                            </p>
                          </div>
                          <LoadingButton
                            onClick={handlePaymentSuccess}
                            loading={isProcessingPayment}
                            loadingText="Processing..."
                            className="w-full bg-gray-600 text-white hover:bg-gray-700"
                          >
                            Confirm Alternative Payment
                          </LoadingButton>
                        </div>
                      </div>
                    ) : (
                      <div className="p-6 text-center">
                        <p className="text-muted-foreground">Unknown payment method selected.</p>
                      </div>
                    )}
                  </div>

                  {booking.paymentMethod === 'PAYMENTCARD' && (
                    <div className="rounded-lg border bg-muted/50 p-4">
                      <div className="flex items-start space-x-4">
                        <Shield className="mt-0.5 h-6 w-6 text-muted-foreground" />
                        <div>
                          <h3 className="font-medium">Secure Payment</h3>
                          <p className="text-sm text-muted-foreground">
                            Your payment information is securely processed by the airline. Your card details are handled according to the highest security standards.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
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
