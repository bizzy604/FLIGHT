"use client"

import type React from "react"
import { useState } from "react"
import { CreditCard, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { LoadingSpinner } from "@/components/loading-spinner"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertCircle, CheckCircle2 } from "lucide-react"
import { cn } from "@/utils/cn"

interface CardPaymentFormProps {
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
  onPaymentSuccess: (paymentData?: any) => void
  onPaymentError: (error: string) => void
}

export function CardPaymentForm({
  amount,
  currency,
  flightDetails,
  onPaymentSuccess,
  onPaymentError,
}: CardPaymentFormProps) {
  const [cardNumber, setCardNumber] = useState("")
  const [cardName, setCardName] = useState("")
  const [expiryMonth, setExpiryMonth] = useState("")
  const [expiryYear, setExpiryYear] = useState("")
  const [cvv, setCvv] = useState("")
  const [processing, setProcessing] = useState(false)
  const [succeeded, setSucceeded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

  // Format currency for display
  const formattedAmount = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
  }).format(amount)

  // Format card number with spaces
  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "")
    const matches = v.match(/\d{4,16}/g)
    const match = (matches && matches[0]) || ""
    const parts = []

    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4))
    }

    if (parts.length) {
      return parts.join(" ")
    } else {
      return value
    }
  }

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formattedValue = formatCardNumber(e.target.value)
    setCardNumber(formattedValue)

    // Clear error when user types
    if (formErrors.cardNumber) {
      setFormErrors({
        ...formErrors,
        cardNumber: "",
      })
    }
  }

  const validateForm = () => {
    const errors: Record<string, string> = {}

    if (!cardNumber.trim()) {
      errors.cardNumber = "Card number is required"
    } else if (cardNumber.replace(/\s/g, "").length < 16) {
      errors.cardNumber = "Please enter a valid card number"
    }

    if (!cardName.trim()) {
      errors.cardName = "Cardholder name is required"
    }

    if (!expiryMonth) {
      errors.expiryMonth = "Expiry month is required"
    }

    if (!expiryYear) {
      errors.expiryYear = "Expiry year is required"
    }

    if (!cvv.trim()) {
      errors.cvv = "CVV is required"
    } else if (cvv.length < 3) {
      errors.cvv = "CVV must be 3 or 4 digits"
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    if (!validateForm()) {
      return
    }

    setProcessing(true)
    setError(null)

    try {
      
      const response = await fetch("/api/payments", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          cardDetails: {
            cardNumber: cardNumber.replace(/\s/g, ""), // Remove spaces for processing
            cardName,
            expiryMonth,
            expiryYear,
            cvv,
          },
          bookingData: {
            amount,
            currency,
            flightDetails
          }
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error?.message || "Failed to process payment")
      }

      const data = await response.json()
      
      if (data.success) {
        setSucceeded(true)
        
        // Pass payment data to the success callback
        // This includes the payment info structure needed for the backend booking API
        const paymentData = {
          id: data.paymentId, // Payment method ID for backend
          paymentId: data.paymentId,
          status: data.status,
          message: data.message,
          paymentInfo: data.paymentInfo, // Include backend-ready payment info
          bookingReference: data.bookingReference
        }
        
        // Call the parent's payment success handler which will create the actual booking
        onPaymentSuccess(paymentData)
      } else {
        throw new Error(data.message || "Card details capture failed")
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
      setError(errorMessage)
      onPaymentError(errorMessage)
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Card className="w-full border-0 shadow-none">
      <CardContent className="p-6">

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
              Payment details captured successfully! Processing with airline...
            </AlertDescription>
          </Alert>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="card-number">Card Number</Label>
              <div className="relative">
                <Input
                  id="card-number"
                  placeholder="1234 5678 9012 3456"
                  value={cardNumber}
                  onChange={handleCardNumberChange}
                  maxLength={19}
                  className={cn("pl-10", formErrors.cardNumber && "border-destructive")}
                  aria-invalid={!!formErrors.cardNumber}
                  aria-describedby={formErrors.cardNumber ? "card-number-error" : undefined}
                  required
                />
                <CreditCard className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              </div>
              {formErrors.cardNumber && (
                <p id="card-number-error" className="text-xs text-destructive">
                  {formErrors.cardNumber}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="card-name">Cardholder Name</Label>
              <Input
                id="card-name"
                placeholder="John Doe"
                value={cardName}
                onChange={(e) => {
                  setCardName(e.target.value)
                  if (formErrors.cardName) {
                    setFormErrors({
                      ...formErrors,
                      cardName: "",
                    })
                  }
                }}
                className={cn(formErrors.cardName && "border-destructive")}
                aria-invalid={!!formErrors.cardName}
                aria-describedby={formErrors.cardName ? "card-name-error" : undefined}
                required
              />
              {formErrors.cardName && (
                <p id="card-name-error" className="text-xs text-destructive">
                  {formErrors.cardName}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="expiry">Expiry Date</Label>
                <div className="flex space-x-2">
                  <Select
                    value={expiryMonth}
                    onValueChange={(value) => {
                      setExpiryMonth(value)
                      if (formErrors.expiryMonth) {
                        setFormErrors({
                          ...formErrors,
                          expiryMonth: "",
                        })
                      }
                    }}
                    required
                  >
                    <SelectTrigger
                      id="expiry-month"
                      className={cn("w-full", formErrors.expiryMonth && "border-destructive")}
                      aria-invalid={!!formErrors.expiryMonth}
                      aria-describedby={formErrors.expiryMonth ? "expiry-month-error" : undefined}
                    >
                      <SelectValue placeholder="MM" />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 12 }, (_, i) => {
                        const month = i + 1
                        return (
                          <SelectItem key={month} value={month.toString().padStart(2, "0")}>
                            {month.toString().padStart(2, "0")}
                          </SelectItem>
                        )
                      })}
                    </SelectContent>
                  </Select>
                  <Select
                    value={expiryYear}
                    onValueChange={(value) => {
                      setExpiryYear(value)
                      if (formErrors.expiryYear) {
                        setFormErrors({
                          ...formErrors,
                          expiryYear: "",
                        })
                      }
                    }}
                    required
                  >
                    <SelectTrigger
                      id="expiry-year"
                      className={cn("w-full", formErrors.expiryYear && "border-destructive")}
                      aria-invalid={!!formErrors.expiryYear}
                      aria-describedby={formErrors.expiryYear ? "expiry-year-error" : undefined}
                    >
                      <SelectValue placeholder="YY" />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 10 }, (_, i) => {
                        const year = new Date().getFullYear() + i
                        return (
                          <SelectItem key={year} value={year.toString().slice(-2)}>
                            {year}
                          </SelectItem>
                        )
                      })}
                    </SelectContent>
                  </Select>
                </div>
                {(formErrors.expiryMonth || formErrors.expiryYear) && (
                  <p
                    id={formErrors.expiryMonth ? "expiry-month-error" : "expiry-year-error"}
                    className="text-xs text-destructive"
                  >
                    {formErrors.expiryMonth || formErrors.expiryYear}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="cvv">CVV</Label>
                <div className="relative">
                  <Input
                    id="cvv"
                    placeholder="123"
                    value={cvv}
                    onChange={(e) => {
                      setCvv(e.target.value.replace(/\D/g, ""))
                      if (formErrors.cvv) {
                        setFormErrors({
                          ...formErrors,
                          cvv: "",
                        })
                      }
                    }}
                    maxLength={4}
                    className={cn("pl-10", formErrors.cvv && "border-destructive")}
                    aria-invalid={!!formErrors.cvv}
                    aria-describedby={formErrors.cvv ? "cvv-error" : undefined}
                    required
                  />
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                </div>
                {formErrors.cvv && (
                  <p id="cvv-error" className="text-xs text-destructive">
                    {formErrors.cvv}
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  3 or 4 digit security code, usually on the back of your card
                </p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Your card details will be securely processed by the airline. 
                Your payment will be processed directly with the airline's payment system.
              </p>
            </div>

            <Button type="submit" className="w-full" disabled={processing}>
              {processing ? (
                <>
                  <LoadingSpinner className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                `Book Now`
              )}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  )
}