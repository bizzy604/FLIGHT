"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import Link from "next/link"
import { ArrowLeft, Save } from "lucide-react"

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
  const bookingReference = params.reference as string
  const { isLoaded, isSignedIn } = useUser()

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [booking, setBooking] = useState<any>(null)
  const [selectedExtras, setSelectedExtras] = useState<any>({
    seats: {
      outbound: "",
      return: "",
    },
    baggage: {
      included: "",
      additional: "",
    },
    meals: {
      outbound: "",
      return: "",
    },
    additionalServices: [],
  })
  const [hasChanges, setHasChanges] = useState(false)

  // Fetch booking details
  useEffect(() => {
    const fetchBookingDetails = async () => {
      if (!isLoaded) return

      // Redirect to sign-in if not authenticated
      if (!isSignedIn) {
        router.push(`/sign-in?redirect_url=/manage/${bookingReference}/edit`)
        return
      }

      try {
        setIsLoading(true)

        // First try to get booking from session storage
        const sessionBookingData = sessionStorage.getItem("bookingData")
        if (sessionBookingData) {
          try {
            const sessionBooking = JSON.parse(sessionBookingData)
            if (sessionBooking.bookingReference === bookingReference) {
              setBooking(sessionBooking)
              setSelectedExtras(
                sessionBooking.extras || {
                  seats: { outbound: "", return: "" },
                  baggage: { included: "", additional: "" },
                  meals: { outbound: "Standard", return: "Standard" },
                  additionalServices: [],
                },
              )
              setIsLoading(false)
              return
            }
          } catch (e) {
            console.error("Error parsing session booking data:", e)
          }
        }

        // If not in session storage, fetch from API
        const response = await fetch(`/api/bookings/${bookingReference}`)

        if (!response.ok) {
          if (response.status === 404) {
            router.push("/manage?error=booking-not-found")
            return
          }
          throw new Error("Failed to fetch booking details")
        }

        const data = await response.json()
        setBooking(data)
        setSelectedExtras(
          data.extras || {
            seats: { outbound: "", return: "" },
            baggage: { included: "", additional: "" },
            meals: { outbound: "Standard", return: "Standard" },
            additionalServices: [],
          },
        )
      } catch (error) {
        console.error("Error fetching booking details:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookingDetails()
  }, [isLoaded, isSignedIn, router, bookingReference])

  // Track changes
  useEffect(() => {
    if (booking && booking.extras) {
      // Compare current extras with original booking extras
      const originalExtras = booking.extras

      // Check if seats changed
      const seatsChanged =
        selectedExtras.seats.outbound !== originalExtras.seats?.outbound ||
        selectedExtras.seats.return !== originalExtras.seats?.return

      // Check if baggage changed
      const baggageChanged =
        selectedExtras.baggage.included !== originalExtras.baggage?.included ||
        selectedExtras.baggage.additional !== originalExtras.baggage?.additional

      // Check if meals changed
      const mealsChanged =
        selectedExtras.meals.outbound !== originalExtras.meals?.outbound ||
        selectedExtras.meals.return !== originalExtras.meals?.return

      // Check if additional services changed
      const servicesChanged =
        JSON.stringify(selectedExtras.additionalServices.sort()) !==
        JSON.stringify((originalExtras.additionalServices || []).sort())

      setHasChanges(seatsChanged || baggageChanged || mealsChanged || servicesChanged)
    }
  }, [booking, selectedExtras])

  // Handle save changes
  const handleSaveChanges = async () => {
    try {
      setIsSaving(true)

      // In a real app, this would be an API call to update the booking
      // For now, we'll just update the booking in state and session storage

      // Update booking with new extras
      const updatedBooking = {
        ...booking,
        extras: selectedExtras,
        status: "confirmed", // Assume changes are confirmed immediately
      }

      // Update state
      setBooking(updatedBooking)

      // Update session storage if present
      const sessionBookingData = sessionStorage.getItem("bookingData")
      if (sessionBookingData) {
        sessionStorage.setItem("bookingData", JSON.stringify(updatedBooking))
      }

      // Show success message
      toast({
        title: "Changes saved successfully",
        description: "Your booking has been updated with the new selections.",
      })

      // Redirect back to booking details
      setTimeout(() => {
        router.push(`/manage/${bookingReference}`)
      }, 1500)
    } catch (error) {
      console.error("Error saving changes:", error)
      toast({
        title: "Failed to save changes",
        description: "An error occurred while saving your changes. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Handle additional services selection
  const toggleAdditionalService = (service: string) => {
    setSelectedExtras((prev) => {
      const services = [...prev.additionalServices]
      const index = services.indexOf(service)

      if (index === -1) {
        services.push(service)
      } else {
        services.splice(index, 1)
      }

      return {
        ...prev,
        additionalServices: services,
      }
    })
  }

  if (!isLoaded || (isLoading && isSignedIn)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (!booking && !isLoading) {
    return (
      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-16 items-center justify-between">
            <div className="flex items-center gap-2">
              <Image src="/placeholder.svg?height=32&width=32" alt="SkyWay Logo" width={32} height={32} />
              <span className="text-xl font-bold">SkyWay</span>
            </div>
            <MainNav />
            <UserNav />
          </div>
        </header>

        <main className="flex-1 container py-12">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Booking Not Found</h1>
            <p className="mb-6 text-muted-foreground">
              The booking you're trying to edit doesn't exist or you don't have permission to modify it.
            </p>
            <Link href="/manage">
              <Button>Return to Bookings</Button>
            </Link>
          </div>
        </main>
      </div>
    )
  }

  // Check if booking is in a modifiable state
  const canModify = booking.status !== "cancelled" && booking.status !== "completed"

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/placeholder.svg?height=32&width=32" alt="SkyWay Logo" width={32} height={32} />
            <span className="text-xl font-bold">SkyWay</span>
          </div>
          <MainNav />
          <UserNav />
        </div>
      </header>

      <main className="flex-1">
        <div className="container py-6">
          <div className="mb-6">
            <Link
              href={`/manage/${bookingReference}`}
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to Booking Details
            </Link>

            <h1 className="mt-4 text-2xl font-bold md:text-3xl">Modify Booking</h1>
            <p className="text-muted-foreground">Reference: {bookingReference}</p>
          </div>

          {!canModify && (
            <Alert className="mb-6">
              <AlertTitle>This booking cannot be modified</AlertTitle>
              <AlertDescription>
                Bookings that are cancelled or completed cannot be modified. Please contact customer support if you need
                assistance.
              </AlertDescription>
            </Alert>
          )}

          <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
            <div className="space-y-6">
              <Tabs defaultValue="seats">
                <TabsList>
                  <TabsTrigger value="seats">Seat Selection</TabsTrigger>
                  <TabsTrigger value="baggage">Baggage</TabsTrigger>
                  <TabsTrigger value="meals">Meals & Services</TabsTrigger>
                </TabsList>

                <TabsContent value="seats" className="space-y-4 pt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Outbound Flight Seats</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <SeatSelection
                        onSeatSelect={(seat) => {
                          setSelectedExtras({
                            ...selectedExtras,
                            seats: {
                              ...selectedExtras.seats,
                              outbound: seat,
                            },
                          })
                        }}
                      />
                    </CardContent>
                  </Card>

                  {booking.flightDetails.return && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Return Flight Seats</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <SeatSelection
                          onSeatSelect={(seat) => {
                            setSelectedExtras({
                              ...selectedExtras,
                              seats: {
                                ...selectedExtras.seats,
                                return: seat,
                              },
                            })
                          }}
                        />
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="baggage" className="space-y-4 pt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Baggage Options</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <BaggageOptions
                        onChange={(baggage) => {
                          setSelectedExtras({
                            ...selectedExtras,
                            baggage,
                          })
                        }}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="meals" className="space-y-4 pt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Meal Preferences</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <MealOptions
                        onChange={(meals) => {
                          setSelectedExtras({
                            ...selectedExtras,
                            meals,
                          })
                        }}
                      />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Additional Services</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-start space-x-3 rounded-md border p-4">
                          <input
                            type="checkbox"
                            id="travel-insurance"
                            checked={selectedExtras.additionalServices.includes("Travel Insurance")}
                            onChange={() => toggleAdditionalService("Travel Insurance")}
                            className="mt-1"
                          />
                          <div className="space-y-1">
                            <label
                              htmlFor="travel-insurance"
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                              Travel Insurance
                            </label>
                            <p className="text-xs text-muted-foreground">
                              Comprehensive coverage for trip cancellation, medical emergencies, and more
                            </p>
                            <p className="text-sm font-medium">$24.99 per passenger</p>
                          </div>
                        </div>

                        <div className="flex items-start space-x-3 rounded-md border p-4">
                          <input
                            type="checkbox"
                            id="priority-boarding"
                            checked={selectedExtras.additionalServices.includes("Priority Boarding")}
                            onChange={() => toggleAdditionalService("Priority Boarding")}
                            className="mt-1"
                          />
                          <div className="space-y-1">
                            <label
                              htmlFor="priority-boarding"
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                              Priority Boarding
                            </label>
                            <p className="text-xs text-muted-foreground">
                              Be among the first to board the aircraft and secure overhead bin space
                            </p>
                            <p className="text-sm font-medium">$15.99 per passenger</p>
                          </div>
                        </div>

                        <div className="flex items-start space-x-3 rounded-md border p-4">
                          <input
                            type="checkbox"
                            id="airport-lounge"
                            checked={selectedExtras.additionalServices.includes("Airport Lounge Access")}
                            onChange={() => toggleAdditionalService("Airport Lounge Access")}
                            className="mt-1"
                          />
                          <div className="space-y-1">
                            <label
                              htmlFor="airport-lounge"
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                              Airport Lounge Access
                            </label>
                            <p className="text-xs text-muted-foreground">
                              Relax before your flight with complimentary food, drinks, and Wi-Fi
                            </p>
                            <p className="text-sm font-medium">$39.99 per passenger</p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Your Changes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm font-medium">Seats</p>
                      <div className="mt-1 space-y-1 text-sm">
                        <p>
                          <span className="text-muted-foreground">Outbound:</span>{" "}
                          {selectedExtras.seats.outbound || "No change"}
                        </p>
                        {booking.flightDetails.return && (
                          <p>
                            <span className="text-muted-foreground">Return:</span>{" "}
                            {selectedExtras.seats.return || "No change"}
                          </p>
                        )}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-medium">Baggage</p>
                      <div className="mt-1 space-y-1 text-sm">
                        <p>
                          <span className="text-muted-foreground">Included:</span>{" "}
                          {selectedExtras.baggage.included || "No change"}
                        </p>
                        <p>
                          <span className="text-muted-foreground">Additional:</span>{" "}
                          {selectedExtras.baggage.additional || "No change"}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-medium">Meals</p>
                      <div className="mt-1 space-y-1 text-sm">
                        <p>
                          <span className="text-muted-foreground">Outbound:</span>{" "}
                          {selectedExtras.meals.outbound || "No change"}
                        </p>
                        {booking.flightDetails.return && (
                          <p>
                            <span className="text-muted-foreground">Return:</span>{" "}
                            {selectedExtras.meals.return || "No change"}
                          </p>
                        )}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-medium">Additional Services</p>
                      {selectedExtras.additionalServices.length > 0 ? (
                        <ul className="mt-1 list-inside list-disc text-sm">
                          {selectedExtras.additionalServices.map((service: string, index: number) => (
                            <li key={index}>{service}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm">None selected</p>
                      )}
                    </div>

                    <Separator />

                    <div>
                      <p className="text-sm font-medium">Price Adjustment</p>
                      <div className="mt-2 space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span>Original total</span>
                          <span>${booking.totalAmount.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Additional charges</span>
                          <span>$25.00</span>
                        </div>
                        <Separator className="my-1" />
                        <div className="flex justify-between font-medium">
                          <span>New total</span>
                          <span>${(booking.totalAmount + 25).toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Button className="w-full" onClick={handleSaveChanges} disabled={!hasChanges || isSaving || !canModify}>
                {isSaving ? (
                  <>
                    <LoadingSpinner className="mr-2" />
                    Saving Changes...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Save Changes
                  </>
                )}
              </Button>

              <Link href={`/manage/${bookingReference}`}>
                <Button variant="outline" className="w-full">
                  Cancel
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t bg-background">
        <div className="container py-6 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} SkyWay. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

