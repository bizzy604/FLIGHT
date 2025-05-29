import { SignUp } from "@clerk/nextjs"
import type { Metadata } from "next"
import Image from "next/image"

export const metadata: Metadata = {
  title: "Sign Up - Rea Travel Agency",
  description: "Create your account",
}

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30">
      <div className="mb-8 flex items-center gap-2">
        <Image src="/logo1.png" alt="SkyWay Logo" width={50} height={50} />
        <span className="text-xl font-bold">Rea Travel Agency</span>
      </div>

      <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        <SignUp
          redirectUrl={getRedirectUrl()}
        />
      </div>
    </div>
  )
}

// Helper function to get the redirect URL from the query parameters
function getRedirectUrl(): string {
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search)
    const redirectUrl = params.get("redirect_url")
    return redirectUrl || "/flights"
  }
  return "/flights"
}

