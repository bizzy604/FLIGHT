"use client"

import { usePathname } from "next/navigation"
import { Footer } from "./footer"
import { SimpleFooter } from "./simple-footer"

export function ConditionalFooter() {
  const pathname = usePathname()
  
  // Show detailed footer only on homepage
  const isHomepage = pathname === "/"
  
  return isHomepage ? <Footer /> : <SimpleFooter />
}
