"use client"

import { SignUp } from "@clerk/nextjs"
import Image from "next/image"
import { useSearchParams } from "next/navigation"
import { Suspense } from "react"

// Force dynamic rendering to prevent static generation during build
export const dynamic = 'force-dynamic'

function SignUpContent() {
  const searchParams = useSearchParams()
  const redirectUrl = searchParams.get("redirect_url") || "/flights"

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30">
      <div className="mb-8 flex items-center gap-2">
        <Image src="/logo1.png" alt="SkyWay Logo" width={50} height={50} />
        <span className="text-xl font-bold">Rea Travel Agency</span>
      </div>

      <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        <SignUp redirectUrl={redirectUrl} />
      </div>
    </div>
  )
}

export default function SignUpPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30">
        <div className="mb-8 flex items-center gap-2">
          <Image src="/logo1.png" alt="SkyWay Logo" width={50} height={50} />
          <span className="text-xl font-bold">Rea Travel Agency</span>
        </div>
        <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </div>
      </div>
    }>
      <SignUpContent />
    </Suspense>
  )
}

