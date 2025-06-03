"use client"

import type React from "react"
import { useAuth } from "@clerk/nextjs"
import { useRouter, usePathname } from "next/navigation"
import { LoadingSpinner } from "@/components/loading-spinner"

export default function BookingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isLoaded, userId } = useAuth()
    const router = useRouter()
    const pathname = usePathname()

  // If user is not authenticated, redirect to sign-in
  if (!isLoaded) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      )
    }
  
    if (!userId) {
      router.push(`/sign-in?redirect_url=${encodeURIComponent(pathname)}`)
      return null
    }
  
    return <>{children}</>
}

