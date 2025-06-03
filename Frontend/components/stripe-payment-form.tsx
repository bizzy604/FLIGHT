"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import { CardElement, useStripe, useElements } from "@stripe/react-stripe-js"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { LoadingSpinner } from "@/components/loading-spinner"
import { AlertCircle, CheckCircle2 } from "lucide-react"

interface StripePaymentFormProps {
  bookingReference: string
  amount: number
  currency: string
  flightDetails: {
    id: string
    from: string
    to: string
    departureDate: string
    returnDate?: string
  }
  onPaymentSuccess: () => void
  onPaymentError: (error: string) => void
}

export function StripePaymentForm({
  bookingReference,
  amount,
  currency,
  flightDetails,
  onPaymentSuccess,
  onPaymentError,
}: StripePaymentFormProps) {
  const router = useRouter()
  const stripe = useStripe()
  const elements = useElements()
  const { isSignedIn } = useUser()

  const [error, setError] = useState<string | null>(null)
  const [cardComplete, setCardComplete] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [succeeded, setSucceeded] = useState(false)
  const [clientSecret, setClientSecret] = useState("")

  // Format currency for display
  const formattedAmount = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
  }).format(amount)

  // Create payment intent when component mounts
  useEffect(() => {
    // Make sure user is signed in before creating payment intent
    if (!isSignedIn) return

    // Create PaymentIntent as soon as the page loads
    async function createPaymentIntent() {
      try {
        // Get booking data from session storage if available
        const bookingData = sessionStorage.getItem("bookingData")
        
        const response = await fetch("/api/payments", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            bookingReference,
            amount,
            currency: currency.toUpperCase(),
            flightId: flightDetails.id,
            bookingData: bookingData // Send the booking data to the API
          }),
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error?.message || "Failed to create payment intent")
        }

        const data = await response.json()
        setClientSecret(data.clientSecret)
      } catch (err) {
        console.error("Error creating payment intent:", err)
        setError(err instanceof Error ? err.message : "An unknown error occurred")
        onPaymentError(err instanceof Error ? err.message : "Failed to initialize payment")
      }
    }

    createPaymentIntent()
  }, [bookingReference, amount, currency, flightDetails.id, isSignedIn])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    if (!stripe || !elements) {
      // Stripe.js has not loaded yet. Make sure to disable form submission until Stripe.js has loaded
      return
    }

    if (!cardComplete) {
      setError("Please complete your card details")
      return
    }

    setProcessing(true)
    setError(null)

    try {
      const cardElement = elements.getElement(CardElement)
      if (!cardElement) {
        throw new Error("Card element not found")
      }

      const { error: paymentError, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: cardElement,
          billing_details: {
            // You can collect billing details here if needed
          },
        },
      })

      if (paymentError) {
        setError(paymentError.message || "Payment failed")
        onPaymentError(paymentError.message || "Payment failed")
      } else if (paymentIntent.status === "succeeded") {
        setSucceeded(true)
        onPaymentSuccess()

        // Redirect to confirmation page after a short delay
        setTimeout(() => {
          router.push(`/flights/${flightDetails.id}/payment/confirmation?reference=${bookingReference}`)
        }, 1500)
      } else {
        setError(`Payment status: ${paymentIntent.status}. Please try again.`)
        onPaymentError(`Payment status: ${paymentIntent.status}. Please try again.`)
      }
    } catch (err) {
      console.error("Error processing payment:", err)
      setError(err instanceof Error ? err.message : "An unknown error occurred")
      onPaymentError(err instanceof Error ? err.message : "An unknown error occurred")
    } finally {
      setProcessing(false)
    }
  }

  const cardElementOptions = {
    style: {
      base: {
        fontSize: "16px",
        color: "#32325d",
        "::placeholder": {
          color: "#aab7c4",
        },
      },
      invalid: {
        color: "#fa755a",
        iconColor: "#fa755a",
      },
    },
    hidePostalCode: true,
  }

  return (
    <Card className="w-full border-0 shadow-none">
      <CardContent className="p-6">
        <div className="mb-6 p-4 bg-muted rounded-md">
          <div className="flex justify-between mb-2">
            <span>Flight</span>
            <span>
              {flightDetails.from} to {flightDetails.to}
            </span>
          </div>
          <div className="flex justify-between mb-2">
            <span>Date</span>
            <span>{flightDetails.departureDate}</span>
          </div>
          <div className="flex justify-between font-medium text-lg">
            <span>Total</span>
            <span>{formattedAmount}</span>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {succeeded ? (
          <Alert className="mb-4 bg-green-50 border-green-200">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Payment successful! Redirecting to confirmation...
            </AlertDescription>
          </Alert>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-3 border rounded-md">
              <CardElement options={cardElementOptions} onChange={(e) => setCardComplete(e.complete)} />
            </div>

            <Button type="submit" className="w-full" disabled={processing || !stripe || !cardComplete || !clientSecret}>
              {processing ? (
                <>
                  <LoadingSpinner className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                `Pay ${formattedAmount}`
              )}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  )
}