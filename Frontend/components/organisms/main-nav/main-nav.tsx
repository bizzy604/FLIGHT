"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { cn } from "@/utils/cn"

const items = [
  {
    title: "Home",
    href: "/",
  },
  {
    title: "Flights",
    href: "/flights",
  },
  {
    title: "Manage Booking",
    href: "/manage",
  },
  {
    title: "About",
    href: "/about",
  },
  {
    title: "Contact",
    href: "/contact",
  },
]

interface MainNavProps {
  className?: string
}

export function MainNav({ className }: MainNavProps = {}) {
  const [showMobileMenu, setShowMobileMenu] = React.useState<boolean>(false)
  const pathname = usePathname()

  return (
    <>
      {/* Desktop Navigation */}
      <div className={cn("hidden md:flex items-center", className)}>
        <NavigationMenu>
          <NavigationMenuList>
            {items.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href))

              return (
                <NavigationMenuItem key={item.title}>
                  <Link href={item.href} legacyBehavior passHref>
                    <NavigationMenuLink
                      className={cn(navigationMenuTriggerStyle(), isActive && "bg-accent text-accent-foreground")}
                      aria-current={isActive ? "page" : undefined}
                    >
                      {item.title}
                    </NavigationMenuLink>
                  </Link>
                </NavigationMenuItem>
              )
            })}
          </NavigationMenuList>
        </NavigationMenu>
      </div>

      {/* Mobile Navigation Button */}
      <div className="md:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setShowMobileMenu(!showMobileMenu)}
          aria-label="Toggle Menu"
          aria-expanded={showMobileMenu}
          aria-controls="mobile-menu"
        >
          {showMobileMenu ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {/* Mobile Menu Overlay */}
      {showMobileMenu && (
        <div
          id="mobile-menu"
          className="fixed inset-x-0 top-16 z-50 bg-background border-b shadow-lg md:hidden"
        >
          <div className="container px-4 py-6">
            <nav className="grid gap-4">
              {items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href))

                return (
                  <Link
                    key={item.title}
                    href={item.href}
                    className={cn(
                      "block px-3 py-2 text-base font-medium rounded-md transition-colors",
                      isActive
                        ? "bg-accent text-accent-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                    )}
                    aria-current={isActive ? "page" : undefined}
                    onClick={() => setShowMobileMenu(false)}
                  >
                    {item.title}
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      )}
    </>
  )
}

