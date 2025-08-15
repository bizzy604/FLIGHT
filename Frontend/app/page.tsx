"use client"

import { MainNav, UserNav, FlightSearchForm } from "@/components/organisms"
import { useRouter } from "next/navigation"
import Image from "next/image"

export default function HomePage() {
  const router = useRouter()

  const handleSearch = (results: any[], meta: any, formData?: any) => {
    console.log('Search completed with results:', results.length, 'offers')
  }

  const handleSearchStart = (formData: any) => {
    if (!formData.origin || !formData.destination || !formData.departDate) {
      return false
    }

    const searchParams = new URLSearchParams({
      origin: formData.origin || '',
      destination: formData.destination || '',
      departDate: formData.departDate ? formData.departDate.toISOString().split('T')[0] : '',
      tripType: formData.tripType === 'round-trip' ? 'round-trip' : 'one-way',
      adults: formData.passengers?.adults?.toString() || '1',
      children: formData.passengers?.children?.toString() || '0',
      infants: formData.passengers?.infants?.toString() || '0',
      cabinClass: formData.cabinType || 'ECONOMY'
    })
    
    if (formData.tripType === 'round-trip' && formData.returnDate) {
      searchParams.set('returnDate', formData.returnDate.toISOString().split('T')[0])
    }
    
    router.push(`/flights?${searchParams.toString()}`)
    return true
  }

  const handleError = (error: string) => {
    console.error('Flight search error:', error)
  }
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/95 shadow-sm">
        <div className="container flex h-16 sm:h-18 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Image
              src="/logo1.png"
              alt="Rea Travel Logo"
              width={40}
              height={40}
              className="w-10 h-10 sm:w-12 sm:h-12"
            />
            <span className="text-lg sm:text-xl font-bold text-foreground">Rea Travel</span>
          </div>
          <div className="flex items-center gap-4">
            <MainNav />
            <UserNav />
          </div>
        </div>
      </header>

      <main className="flex-1 bg-secondary/20">
        {/* Compact Search Section */}
        <section className="py-8">
          <div className="w-full px-4">
            <FlightSearchForm 
              onSearch={handleSearch}
              onError={handleError}
              onSearchStart={handleSearchStart}
            />
          </div>
        </section>
      </main>
    </div>
  )
}

