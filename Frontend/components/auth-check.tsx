"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@clerk/nextjs"
import { LoadingSpinner } from "@/components/loading-spinner"

interface AuthCheckProps {
  children: React.ReactNode
}

export function AuthCheck({ children }: AuthCheckProps) {
  const { isLoaded, userId } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    if (!isLoaded) return

    // Check if the current route requires authentication
    const requiresAuth =
      pathname.includes("/flights/") && pathname.includes("/payment")

    if (requiresAuth && !userId) {
      // Store the current URL to redirect back after authentication
      sessionStorage.setItem("redirectAfterAuth", pathname)
      router.push(`/sign-in?redirect_url=${encodeURIComponent(pathname)}`)
    } else {
      setIsChecking(false)
    }
  }, [isLoaded, userId, router, pathname])

  if (!isLoaded || isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner className="h-8 w-8" />
      </div>
    )
  }

  return <>{children}</>
}

