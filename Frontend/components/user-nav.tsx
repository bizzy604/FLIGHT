"use client"
import { useUser, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { usePathname } from "next/navigation"

export function UserNav() {
  const { isSignedIn, user } = useUser()
  const pathname = usePathname()

  return (
    <div className="flex items-center gap-2">
      <div className="hidden sm:block">
        <ThemeToggle />
      </div>

      {isSignedIn ? (
        <div className="flex items-center gap-2 sm:gap-4">
          <span className="hidden text-xs sm:inline-block sm:text-sm">
            Welcome, {user?.firstName || user?.username || "User"}
          </span>
          <UserButton 
            afterSignOutUrl="/"
            appearance={{
              elements: {
                userButtonBox: "flex items-center gap-2"
              }
            }}
          />
        </div>
      ) : (
        <div className="flex items-center gap-1 sm:gap-2">
          <SignInButton>
            <Button variant="ghost" size="sm" className="text-xs sm:text-sm">
              Log in
            </Button>
          </SignInButton>
          <SignUpButton>
            <Button size="sm" className="text-xs sm:text-sm">
              Register
            </Button>
          </SignUpButton>
        </div>
      )}
    </div>
  )
}

