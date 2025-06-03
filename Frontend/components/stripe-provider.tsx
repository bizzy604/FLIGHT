"use client"

import { type ReactNode, useState } from "react"
import { loadStripe } from "@stripe/stripe-js"
import { Elements } from "@stripe/react-stripe-js"

// Initialize Stripe with your publishable key
// This should be your test key in development and your live key in production
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

interface StripeProviderProps {
  children: ReactNode
}

export function StripeProvider({ children }: StripeProviderProps) {
  const [clientSecret, setClientSecret] = useState<string | null>(null)

  // Optional: You can fetch a setup intent here if you want to initialize Stripe
  // with a client secret for future payments or for saving cards

  return (
    <Elements
      stripe={stripePromise}
      options={{
        appearance: {
          theme: "stripe",
          variables: {
            colorPrimary: "#0f172a", // Match your brand color
            borderRadius: "0.5rem",
          },
        },
      }}
    >
      {children}
    </Elements>
  )
}

