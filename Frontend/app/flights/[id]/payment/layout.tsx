"use client"

import type React from "react"
import { useAuth } from "@clerk/nextjs"
import { useRouter, usePathname } from "next/navigation"
import { LoadingSpinner } from "@/components/loading-spinner"

export default function PaymentLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isLoaded, userId } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  if (!isLoaded) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <LoadingSpinner className="h-8 w-8" />
        <p className="text-gray-600">Processing your request...</p>
      </div>
    )
  }

  if (!userId) {
    router.push(`/sign-in?redirect_url=${encodeURIComponent(pathname)}`)
    return null
  }

  return <>{children}</>
}

