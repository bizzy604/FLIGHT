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
        <div className="container flex h-16 items-center justify-between px-4 sm:px-8">
          <div className="flex items-center gap-2">
            <MobileNav />
            <Image 
              src="/logo1.png" 
              alt="SkyWay Logo" 
              width={60} 
              height={60}
              className="w-12 h-12 sm:w-16 sm:h-16" 
            />
            <span className="text-lg font-bold sm:text-xl">Rea Travel</span>
          </div>
          <MainNav />
          <UserNav />
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative">
          <div className="absolute inset-0 z-0">
            <Image
              src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600&auto=format&fit=crop&q=80"
              alt="Travel destinations"
              fill
              className="object-cover brightness-[0.7]"
              loading="lazy"
            />
          </div>
          <div className="container relative z-10 py-24 md:py-32">
            <div className="mx-auto max-w-4xl text-center">
              <h1 className="mb-6 text-4xl font-bold tracking-tight text-white sm:text-5xl md:text-6xl">
                Discover the World with Rea Travel
              </h1>
              <p className="mb-10 text-xl text-white/90">
                Find and book the best deals on flights to your dream destinations
              </p>

              {/* Flight Search Form */}
              <div className="mx-auto max-w-3xl rounded-xl bg-white p-4 shadow-lg">
                <FlightSearchForm />
              </div>
            </div>
          </div>
        </section>
      <div>
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

