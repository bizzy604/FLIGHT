"use client"

import type * as React from "react"
import { useState } from "react"
import { CreditCard, Lock } from "lucide-react"
import Image from "next/image"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { ErrorBoundary } from "@/components/error-boundary"

interface PaymentFormProps {
  onSubmit: () => void
  isLoading: boolean
}

export function PaymentForm({ onSubmit, isLoading }: PaymentFormProps) {
  const [paymentMethod, setPaymentMethod] = useState("credit-card")
  const [cardNumber, setCardNumber] = useState("")
  const [cardName, setCardName] = useState("")
  const [expiryMonth, setExpiryMonth] = useState("")
  const [expiryYear, setExpiryYear] = useState("")
  const [cvv, setCvv] = useState("")
  const [saveCard, setSaveCard] = useState(false)
  const [billingAddressSame, setBillingAddressSame] = useState(true)
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

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

    if (paymentMethod === "credit-card") {
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
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (validateForm()) {
      onSubmit()
    }
  }

  return (
    <ErrorBoundary>
      <form onSubmit={handleSubmit} className="p-4 sm:p-6">
        <Tabs defaultValue="credit-card" onValueChange={setPaymentMethod}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="credit-card">Credit Card</TabsTrigger>
            <TabsTrigger value="paypal">PayPal</TabsTrigger>
            <TabsTrigger value="apple-pay">Apple Pay</TabsTrigger>
          </TabsList>

          <TabsContent value="credit-card" className="mt-4 space-y-4">
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

            <div className="flex items-start space-x-2 pt-2">
              <Checkbox
                id="save-card"
                checked={saveCard}
                onCheckedChange={(checked) => setSaveCard(checked as boolean)}
              />
              <div className="grid gap-1.5 leading-none">
                <label
                  htmlFor="save-card"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Save card for future bookings
                </label>
                <p className="text-xs text-muted-foreground">
                  Your card information will be securely stored for faster checkout
                </p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="paypal" className="mt-4">
            <div className="rounded-md border p-6 text-center">
              <div className="mx-auto mb-4 h-12 w-24 bg-muted">
                <Image
                  src="/placeholder.svg?height=48&width=96"
                  alt="PayPal"
                  width={96}
                  height={48}
                  className="h-full w-full object-contain"
                />
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                You will be redirected to PayPal to complete your payment securely.
              </p>
              <Button type="button" className="w-full" onClick={onSubmit} disabled={isLoading}>
                {isLoading ? "Processing..." : "Continue to PayPal"}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="apple-pay" className="mt-4">
            <div className="rounded-md border p-6 text-center">
              <div className="mx-auto mb-4 h-12 w-24 bg-muted">
                <Image
                  src="/placeholder.svg?height=48&width=96"
                  alt="Apple Pay"
                  width={96}
                  height={48}
                  className="h-full w-full object-contain"
                />
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                Complete your purchase with Apple Pay for a faster checkout experience.
              </p>
              <Button type="button" className="w-full" onClick={onSubmit} disabled={isLoading}>
                {isLoading ? "Processing..." : "Pay with Apple Pay"}
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        <Separator className="my-6" />

        <div className="space-y-4">
          <div className="flex items-start space-x-2">
            <Checkbox
              id="billing-same"
              checked={billingAddressSame}
              onCheckedChange={(checked) => setBillingAddressSame(checked as boolean)}
            />
            <div className="grid gap-1.5 leading-none">
              <label
                htmlFor="billing-same"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Billing address is the same as passenger address
              </label>
            </div>
          </div>

          {!billingAddressSame && (
            <div className="rounded-md border p-4">
              <h3 className="mb-4 text-sm font-medium">Billing Address</h3>
              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="billing-first-name">First Name</Label>
                    <Input id="billing-first-name" placeholder="John" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="billing-last-name">Last Name</Label>
                    <Input id="billing-last-name" placeholder="Doe" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="billing-address">Address</Label>
                  <Input id="billing-address" placeholder="123 Main St" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="billing-city">City</Label>
                    <Input id="billing-city" placeholder="New York" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="billing-postal-code">Postal Code</Label>
                    <Input id="billing-postal-code" placeholder="10001" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="billing-state">State/Province</Label>
                    <Input id="billing-state" placeholder="NY" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="billing-country">Country</Label>
                    <Select>
                      <SelectTrigger id="billing-country">
                        <SelectValue placeholder="Select country" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="us">United States</SelectItem>
                        <SelectItem value="ca">Canada</SelectItem>
                        <SelectItem value="uk">United Kingdom</SelectItem>
                        <SelectItem value="au">Australia</SelectItem>
                        <SelectItem value="fr">France</SelectItem>
                        <SelectItem value="de">Germany</SelectItem>
                        <SelectItem value="jp">Japan</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-start space-x-2">
          <Checkbox id="terms" required />
          <div className="grid gap-1.5 leading-none">
            <label
              htmlFor="terms"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              I agree to the Terms and Conditions
            </label>
            <p className="text-xs text-muted-foreground">
              By checking this box, you agree to our{" "}
              <a href="/terms" className="text-primary underline">
                Terms of Service
              </a>{" "}
              and{" "}
              <a href="/privacy" className="text-primary underline">
                Privacy Policy
              </a>
            </p>
          </div>
        </div>

        <div className="mt-6">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <span className="mr-2">Processing...</span>
                <span className="spinner h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              </>
            ) : (
              `Pay $445.57`
            )}
          </Button>
        </div>
      </form>
    </ErrorBoundary>
  )
}

