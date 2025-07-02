"use client"

import { Button } from "@/components/ui/button"
import Image from "next/image"
import { FlightSearchForm } from "@/components/flight-search-form"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { MobileNav } from "@/components/mobile-nav"
import { ServicesSection } from "@/components/sections/services-section"
import { DestinationsSection } from "@/components/sections/destinations-section"
import { StatsSection } from "@/components/sections/stats-section"
import { TestimonialsSection } from "@/components/sections/testimonials-section"
import { PartnersSection } from "@/components/sections/partners-section"
import { NewsletterSection } from "@/components/sections/newsletter-section"

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 sm:gap-3">
            <MobileNav />
            <Image
              src="/logo1.png"
              alt="SkyWay Logo"
              width={60}
              height={60}
              className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 lg:w-16 lg:h-16"
            />
            <span className="text-base sm:text-lg md:text-xl font-bold">Rea Travel</span>
          </div>
          <MainNav />
          <UserNav />
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative min-h-[85vh] sm:min-h-[90vh] lg:min-h-screen flex items-center">
          <div className="absolute inset-0 z-0">
            <Image
              src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600&auto=format&fit=crop&q=80"
              alt="Travel destinations"
              fill
              className="object-cover brightness-[0.6] sm:brightness-[0.7]"
              loading="lazy"
            />
          </div>
          <div className="container relative z-10 py-12 sm:py-16 md:py-20 lg:py-24 px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-5xl text-center">
              <h1 className="mb-4 sm:mb-6 text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold tracking-tight text-white leading-tight">
                Discover the World with Rea Travel
              </h1>
              <p className="mb-8 sm:mb-10 lg:mb-12 text-lg sm:text-xl lg:text-2xl text-white/90 max-w-3xl mx-auto leading-relaxed">
                Find and book the best deals on flights to your dream destinations
              </p>

              {/* Flight Search Form */}
              <div className="mx-auto max-w-4xl rounded-xl sm:rounded-2xl bg-white/95 backdrop-blur-sm p-3 sm:p-4 lg:p-6 shadow-xl border border-white/20">
                <FlightSearchForm />
              </div>
            </div>
          </div>
        </section>
      <div className="space-y-0">
        <ServicesSection />
        <DestinationsSection />
        <StatsSection />
        <TestimonialsSection />
        <PartnersSection />
        <NewsletterSection />
      </div>
      </main>
    </div>
  )
}

