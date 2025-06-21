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
    title: "Support",
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
    <div className={cn("flex items-center", className)}>
      <div className="hidden md:flex">
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

      <div className="md:hidden">
        <Button
          variant="ghost"
          className="mr-2 px-0 text-base hover:bg-transparent focus:ring-0"
          onClick={() => setShowMobileMenu(!showMobileMenu)}
          aria-label="Toggle Menu"
          aria-expanded={showMobileMenu}
          aria-controls="mobile-menu"
        >
          {showMobileMenu ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </Button>

        {showMobileMenu && (
          <div id="mobile-menu" className="absolute left-0 top-16 z-50 w-full bg-background pb-6 pt-2 shadow-lg">
            <div className="container grid gap-3">
              {items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href))

                return (
                  <Link
                    key={item.title}
                    href={item.href}
                    className={cn(
                      "text-muted-foreground hover:text-foreground",
                      isActive && "font-medium text-foreground",
                    )}
                    aria-current={isActive ? "page" : undefined}
                    onClick={() => setShowMobileMenu(false)}
                  >
                    {item.title}
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

