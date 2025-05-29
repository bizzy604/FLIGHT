"use client"

import { SignIn } from "@clerk/nextjs"
import Image from "next/image"
import { useSearchParams } from "next/navigation"

export default function SignInPage() {
  const searchParams = useSearchParams()
  const redirectUrl = searchParams.get("redirect_url")

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30">
      {/* <div className="mb-8 flex items-center gap-2">
        <Image 
          src="/logo1.png" 
          alt="Rea Travel Logo" 
          width={40} 
          height={40} 
          priority
        />
        <span className="text-xl font-bold">Rea Travel</span>
      </div> */}

      <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        <SignIn
          afterSignInUrl={redirectUrl || "/flights"}
          signUpUrl="/sign-up"
        />
      </div>
    </div>
  )
}