'use client'

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import Link from "next/link"
import { ArrowLeft, Save, Plane } from "lucide-react"

import { Button } from "@/components/ui/button"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { LoadingSpinner } from "@/components/loading-spinner"
import { SeatSelection } from "@/components/seat-selection"
import { BaggageOptions } from "@/components/baggage-options"
import { MealOptions } from "@/components/meal-options"
import { toast } from "@/components/ui/use-toast"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function EditBookingPage() {
  const router = useRouter()
  const params = useParams()
  const bookingId = params.bookingId as string
  const { isLoaded, isSignedIn } = useUser()

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [booking, setBooking] = useState<any>(null)
  const [selectedExtras, setSelectedExtras] = useState<any>({
    seat: null,
    baggage: { checked: 0, cabin: 1 },
    meal: null,
    additionalServices: [],
  })
  const [hasChanges, setHasChanges] = useState(false)

  // Fetch booking details
  useEffect(() => {
    const fetchBookingDetails = async () => {
      if (!isLoaded) return

      try {
        // Check if user is signed in
        if (!isSignedIn) {
          router.push("/sign-in?redirect=/manage")
          return
        }

        // Check if we have the booking in session storage
        const sessionBooking = sessionStorage.getItem(`booking-${bookingId}`)
        if (sessionBooking) {
          const data = JSON.parse(sessionBooking)
          setBooking(data)
          setSelectedExtras({
            seat: data.seat || null,
            baggage: data.baggage || { checked: 0, cabin: 1 },
            meal: data.meal || null,
            additionalServices: data.additionalServices || [],
          })
          setIsLoading(false)
          return
        }

        // If not in session storage, fetch from API
        const response = await fetch(`/api/bookings/${bookingId}`)

        if (!response.ok) {
          if (response.status === 404) {
            toast({
              title: "Booking not found",
              description: "The booking you're looking for doesn't exist.",
              variant: "destructive",
            })
            router.push("/manage")
          } else {
            throw new Error("Failed to fetch booking details")
          }
          return
        }

        const data = await response.json()
        
        // Save to session storage for faster navigation
        sessionStorage.setItem(`booking-${bookingId}`, JSON.stringify(data))
        
        setBooking(data)
        setSelectedExtras({
          seat: data.seat || null,
          baggage: data.baggage || { checked: 0, cabin: 1 },
          meal: data.meal || null,
          additionalServices: data.additionalServices || [],
        })
      } catch (error) {
        console.error("Error fetching booking details:", error)
        toast({
          title: "Error",
          description: "Failed to load booking details. Please try again.",
          variant: "destructive",
        })
        router.push("/manage")
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookingDetails()
  }, [isLoaded, isSignedIn, router, bookingId])

  // Track changes
  useEffect(() => {
    if (!booking) return

    const originalExtras = {
      seat: booking.seat || null,
      baggage: booking.baggage || { checked: 0, cabin: 1 },
      meal: booking.meal || null,
      additionalServices: booking.additionalServices || [],
    }

    const hasChanges = 
      JSON.stringify(selectedExtras.seat) !== JSON.stringify(originalExtras.seat) ||
      JSON.stringify(selectedExtras.baggage) !== JSON.stringify(originalExtras.baggage) ||
      JSON.stringify(selectedExtras.meal) !== JSON.stringify(originalExtras.meal) ||
      JSON.stringify((selectedExtras.additionalServices || []).sort()) !==
      JSON.stringify((originalExtras.additionalServices || []).sort())

    setHasChanges(hasChanges)
  }, [booking, selectedExtras])

  const handleSeatSelect = (flightType: 'outbound' | 'return', updatedSeats: string[]) => {
    setSelectedExtras((prev: any) => ({
      ...prev,
      seat: updatedSeats[0] || null, // Take the first selected seat or null if empty
    }))
  }

  const handleBaggageChange = (baggage: any) => {
    setSelectedExtras((prev: any) => ({
      ...prev,
      baggage,
    }))
  }

  const handleMealSelect = (meal: any) => {
    setSelectedExtras((prev: any) => ({
      ...prev,
      meal,
    }))
  }

  const toggleAdditionalService = (serviceId: string) => {
    setSelectedExtras((prev: any) => {
      const services = [...prev.additionalServices]
      const index = services.indexOf(serviceId)
      
      if (index > -1) {
        services.splice(index, 1)
      } else {
        services.push(serviceId)
      }

      return {
        ...prev,
        additionalServices: services,
      }
    })
  }

  const handleSave = async () => {
    if (!booking) return
    
    try {
      setIsSaving(true)
      
      // In a real app, you would send this to your API
      // const response = await fetch(`/api/bookings/${bookingId}`, {
      //   method: 'PATCH',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify(selectedExtras),
      // })
      // 
      // if (!response.ok) {
      //   throw new Error('Failed to save changes')
      // }
      
      // Update local state with the new data
      const updatedBooking = {
        ...booking,
        ...selectedExtras,
      }
      
      setBooking(updatedBooking)

      // Update session storage
      sessionStorage.setItem(`booking-${bookingId}`, JSON.stringify(updatedBooking))

      // Show success message
      toast({
        title: "Changes saved",
        description: "Your booking has been updated successfully.",
      })

      // Redirect back to booking details
      setTimeout(() => {
        router.push(`/manage/${bookingId}`)
      }, 1500)
    } catch (error) {
      console.error("Error saving changes:", error)
      toast({
        title: "Error",
        description: "Failed to save changes. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (!booking) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Alert className="w-full max-w-md">
          <AlertTitle>Booking not found</AlertTitle>
          <AlertDescription>
            The booking you're looking for doesn't exist or you don't have permission to view it.
          </AlertDescription>
          <Button className="mt-4" onClick={() => router.push('/manage')}>
            Back to My Bookings
          </Button>
        </Alert>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <Link href="/" className="mr-6 flex items-center space-x-2">
              <Plane className="h-6 w-6" />
              <span className="font-bold">AeroLux</span>
            </Link>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              <Link
                href="/"
                className="transition-colors hover:text-foreground/80 text-foreground/60"
              >
                Home
              </Link>
              <Link
                href="/manage"
                className="transition-colors hover:text-foreground/80 text-foreground/60"
              >
                My Bookings
              </Link>
            </nav>
          </div>
          <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
            <UserNav />
          </div>
        </div>
      </header>

      <div className="container py-8">
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            className="mb-4"
            onClick={() => router.back()}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to booking
          </Button>
          
          <h1 className="text-3xl font-bold tracking-tight">Edit Booking</h1>
          <p className="text-muted-foreground">
            Make changes to your booking below
          </p>
        </div>

        <Tabs defaultValue="seats" className="space-y-6">
          <TabsList>
            <TabsTrigger value="seats">Seat Selection</TabsTrigger>
            <TabsTrigger value="baggage">Baggage</TabsTrigger>
            <TabsTrigger value="meals">Meals</TabsTrigger>
            <TabsTrigger value="extras">Extras</TabsTrigger>
          </TabsList>

          <TabsContent value="seats" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Select Your Seat</CardTitle>
              </CardHeader>
              <CardContent>
                <SeatSelection
                  flightType="outbound"
                  selectedSeats={selectedExtras.seat ? [selectedExtras.seat] : []}
                  onSeatChange={handleSeatSelect}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="baggage" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Baggage Allowance</CardTitle>
              </CardHeader>
              <CardContent>
                <BaggageOptions
                  selectedBaggage={selectedExtras.baggage}
                  onBaggageChange={handleBaggageChange}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="meals" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>In-Flight Meals</CardTitle>
              </CardHeader>
              <CardContent>
                <MealOptions
                  selectedMeals={{
                    outbound: selectedExtras.meal || 'standard',
                    return: selectedExtras.returnMeal || 'standard'
                  }}
                  onMealChange={(updatedMeals) => {
                    setSelectedExtras((prev: any) => ({
                      ...prev,
                      meal: updatedMeals.outbound,
                      returnMeal: updatedMeals.return
                    }));
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="extras" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Additional Services</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="priority-boarding"
                    checked={selectedExtras.additionalServices.includes('priority-boarding')}
                    onChange={() => toggleAdditionalService('priority-boarding')}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="priority-boarding" className="text-sm font-medium leading-none">
                    Priority Boarding
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="extra-legroom"
                    checked={selectedExtras.additionalServices.includes('extra-legroom')}
                    onChange={() => toggleAdditionalService('extra-legroom')}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="extra-legroom" className="text-sm font-medium leading-none">
                    Extra Legroom Seat
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="travel-insurance"
                    checked={selectedExtras.additionalServices.includes('travel-insurance')}
                    onChange={() => toggleAdditionalService('travel-insurance')}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="travel-insurance" className="text-sm font-medium leading-none">
                    Travel Insurance
                  </label>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="mt-8 flex justify-end">
          <Button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            className="ml-auto"
          >
            {isSaving ? (
              <>
                <LoadingSpinner className="mr-2 h-4 w-4" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
