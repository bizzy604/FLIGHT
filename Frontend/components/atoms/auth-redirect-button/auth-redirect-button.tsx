"use client"

import type React from "react"

import { useRouter } from "next/navigation"
import { useAuth } from "@clerk/nextjs"
import { Button, type ButtonProps } from "@/components/ui/button"

interface AuthRedirectButtonProps extends ButtonProps {
  redirectUrl: string
  children: React.ReactNode
}

export function AuthRedirectButton({ redirectUrl, children, ...props }: AuthRedirectButtonProps) {
  const { isSignedIn } = useAuth()
  const router = useRouter()

  const handleClick = () => {
    if (isSignedIn) {
      router.push(redirectUrl)
    } else {
      // Store the redirect URL in session storage
      sessionStorage.setItem("redirectAfterAuth", redirectUrl)
      router.push(`/sign-in?redirect_url=${encodeURIComponent(redirectUrl)}`)
    }
  }

  return (
    <Button onClick={handleClick} {...props}>
      {children}
    </Button>
  )
}

