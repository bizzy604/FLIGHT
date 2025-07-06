"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Image from "next/image"
import { Filter, Search, SlidersHorizontal } from "lucide-react"
import { Input } from "@/components/ui/input"
import { MainNav } from "@/components/main-nav"
import { UserNav } from "@/components/user-nav"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BookingsList } from "@/components/manage/bookings-list"
import { LoadingSpinner } from "@/components/loading-spinner"
import { EmptyBookings } from "@/components/manage/empty-bookings"

export default function ManageBookingsPage() {
  const router = useRouter()
  const { isLoaded, isSignedIn, user } = useUser()
  const [isLoading, setIsLoading] = useState(true)
  const [bookings, setBookings] = useState<any[]>([])
  const [filteredBookings, setFilteredBookings] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sortOrder, setSortOrder] = useState("newest")

  // Fetch user's bookings
  useEffect(() => {
    const fetchBookings = async () => {
      if (!isLoaded) return

      // Redirect to sign-in if not authenticated
      if (!isSignedIn) {
        router.push("/sign-in?redirect_url=/manage")
        return
      }

      try {
        setIsLoading(true)

        // Fetch bookings from API
        const response = await fetch("/api/bookings")

        if (!response.ok) {
          throw new Error("Failed to fetch bookings")
        }

        const data = await response.json()

        // If no bookings in database, check session storage for recent bookings
        let allBookings = data.bookings || []

        // Try to get any bookings from session storage
        const sessionBookingData = sessionStorage.getItem("bookingData")
        if (sessionBookingData) {
          try {
            const sessionBooking = JSON.parse(sessionBookingData)
            // Check if this booking is already in the list
            if (!allBookings.some((b: any) => b.bookingReference === sessionBooking.bookingReference)) {
              allBookings = [sessionBooking, ...allBookings]
            }
          } catch (e) {
            console.error("Error parsing session booking data:", e)
          }
        }

        setBookings(allBookings)
        setFilteredBookings(allBookings)
      } catch (error) {
        console.error("Error fetching bookings:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookings()
  }, [isLoaded, isSignedIn, router])

  // Filter and sort bookings
  useEffect(() => {
    let result = [...bookings]

    // Apply status filter
    if (statusFilter !== "all") {
      result = result.filter((booking) => booking.status === statusFilter)
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        (booking) => {
          // Search by booking reference
          if (booking.bookingReference?.toLowerCase().includes(query)) {
            return true;
          }

          // Search by flight details (legacy structure)
          if (booking.flightDetails?.outbound?.departure?.city?.toLowerCase().includes(query) ||
              booking.flightDetails?.outbound?.arrival?.city?.toLowerCase().includes(query)) {
            return true;
          }

          // Search by new data structure - routeSegments.segments
          if (booking.routeSegments?.segments) {
            for (const segment of booking.routeSegments.segments) {
              if (segment.departure_airport?.toLowerCase().includes(query) ||
                  segment.arrival_airport?.toLowerCase().includes(query) ||
                  segment.airline_name?.toLowerCase().includes(query) ||
                  segment.flight_number?.toLowerCase().includes(query)) {
                return true;
              }
            }
          }

          // Search by top-level routeSegments fields
          if (booking.routeSegments?.origin?.toLowerCase().includes(query) ||
              booking.routeSegments?.destination?.toLowerCase().includes(query)) {
            return true;
          }

          return false;
        }
      )
    }

    // Apply sorting
    result.sort((a, b) => {
      const dateA = new Date(a.createdAt || Date.now())
      const dateB = new Date(b.createdAt || Date.now())

      if (sortOrder === "newest") {
        return dateB.getTime() - dateA.getTime()
      } else {
        return dateA.getTime() - dateB.getTime()
      }
    })

    setFilteredBookings(result)
  }, [bookings, statusFilter, searchQuery, sortOrder])

  // Handle booking cancellation
  const handleCancelBooking = async (bookingReference: string) => {
    try {
      const response = await fetch(`/api/bookings/${bookingReference}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        throw new Error("Failed to cancel booking")
      }

      // Update booking status in the list
      setBookings(
        bookings.map((booking) =>
          booking.bookingReference === bookingReference ? { ...booking, status: "cancelled" } : booking,
        ),
      )
    } catch (error) {
      console.error("Error cancelling booking:", error)
    }
  }

  if (!isLoaded || (isLoading && isSignedIn)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <Image src="/logo1.png" alt="Rea Travel Logo" width={32} height={32} />
            <span className="text-sm sm:text-base md:text-lg font-semibold">Rea Travel</span>
          </div>
          <div className="flex items-center gap-4">
            <MainNav />
            <UserNav />
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="container py-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold md:text-3xl">Manage Your Bookings</h1>
            <p className="text-muted-foreground">View, modify, or cancel your flight bookings</p>
          </div>

          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search by booking reference or destination..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="flex items-center gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[160px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Bookings</SelectItem>
                  <SelectItem value="confirmed">Confirmed</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortOrder} onValueChange={setSortOrder}>
                <SelectTrigger className="w-[160px]">
                  <SlidersHorizontal className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Newest First</SelectItem>
                  <SelectItem value="oldest">Oldest First</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Tabs defaultValue="upcoming" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
              <TabsTrigger value="past">Past</TabsTrigger>
              <TabsTrigger value="all">All Bookings</TabsTrigger>
            </TabsList>

            <TabsContent value="upcoming">
              {filteredBookings.length > 0 ? (
                <BookingsList
                  bookings={filteredBookings.filter(
                    (b) => {
                      if (b.status === "cancelled") return false;

                      // Try to get departure date from new structure first
                      if (b.routeSegments?.segments?.[0]?.departure_datetime) {
                        return new Date(b.routeSegments.segments[0].departure_datetime) >= new Date();
                      }

                      // Fallback to legacy structure
                      if (b.flightDetails?.outbound?.departure?.date) {
                        return new Date(b.flightDetails.outbound.departure.date) >= new Date();
                      }

                      // If no date found, assume it's upcoming
                      return true;
                    }
                  )}
                  onCancelBooking={handleCancelBooking}
                />
              ) : (
                <EmptyBookings
                  message="You don't have any upcoming bookings"
                  description="Book a flight to see your upcoming trips here"
                  showBookButton
                />
              )}
            </TabsContent>

            <TabsContent value="past">
              {filteredBookings.filter((b) => {
                // Try to get departure date from new structure first
                if (b.routeSegments?.segments?.[0]?.departure_datetime) {
                  return new Date(b.routeSegments.segments[0].departure_datetime) < new Date();
                }

                // Fallback to legacy structure
                if (b.flightDetails?.outbound?.departure?.date) {
                  return new Date(b.flightDetails.outbound.departure.date) < new Date();
                }

                // If no date found, assume it's not past
                return false;
              }).length > 0 ? (
                <BookingsList
                  bookings={filteredBookings.filter((b) => {
                    // Try to get departure date from new structure first
                    if (b.routeSegments?.segments?.[0]?.departure_datetime) {
                      return new Date(b.routeSegments.segments[0].departure_datetime) < new Date();
                    }

                    // Fallback to legacy structure
                    if (b.flightDetails?.outbound?.departure?.date) {
                      return new Date(b.flightDetails.outbound.departure.date) < new Date();
                    }

                    // If no date found, assume it's not past
                    return false;
                  })}
                  onCancelBooking={handleCancelBooking}
                  isPast
                />
              ) : (
                <EmptyBookings
                  message="You don't have any past bookings"
                  description="Your travel history will appear here"
                />
              )}
            </TabsContent>

            <TabsContent value="all">
              {filteredBookings.length > 0 ? (
                <BookingsList bookings={filteredBookings} onCancelBooking={handleCancelBooking} />
              ) : (
                <EmptyBookings
                  message="You don't have any bookings"
                  description="Book a flight to get started"
                  showBookButton
                />
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>

      <footer className="border-t bg-background">
        <div className="container py-6 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} Rea Travel. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

