"use client"

import { useState, useEffect } from "react"
import { ArrowUpDown, ChevronDown, MoreHorizontal, Search } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { LoadingSpinner } from "@/components/loading-spinner"

// Mock data for recent bookings
const mockBookings = [
  {
    id: "BK-12345678",
    passengerName: "John Doe",
    flightDetails: "SW1234 - JFK to LAX",
    date: "2025-04-15",
    amount: 445.57,
    status: "confirmed",
  },
  {
    id: "BK-12345679",
    passengerName: "Jane Smith",
    flightDetails: "SW4321 - LAX to JFK",
    date: "2025-04-16",
    amount: 389.99,
    status: "confirmed",
  },
  {
    id: "BK-12345680",
    passengerName: "Michael Johnson",
    flightDetails: "SW2468 - ORD to SFO",
    date: "2025-04-17",
    amount: 512.25,
    status: "pending",
  },
  {
    id: "BK-12345681",
    passengerName: "Emily Williams",
    flightDetails: "SW1357 - DFW to SEA",
    date: "2025-04-18",
    amount: 478.3,
    status: "confirmed",
  },
  {
    id: "BK-12345682",
    passengerName: "David Brown",
    flightDetails: "SW9876 - ATL to MIA",
    date: "2025-04-19",
    amount: 356.75,
    status: "cancelled",
  },
  {
    id: "BK-12345683",
    passengerName: "Sarah Miller",
    flightDetails: "SW5432 - LAS to DEN",
    date: "2025-04-20",
    amount: 299.99,
    status: "confirmed",
  },
  {
    id: "BK-12345684",
    passengerName: "Robert Wilson",
    flightDetails: "SW8765 - PHX to HOU",
    date: "2025-04-21",
    amount: 425.5,
    status: "pending",
  },
]

export function RecentBookings() {
  const [isLoading, setIsLoading] = useState(true)
  const [bookings, setBookings] = useState<typeof mockBookings>([])
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    // Simulate API call to fetch bookings
    const fetchBookings = async () => {
      try {
        // In a real app, this would be an API call
        await new Promise((resolve) => setTimeout(resolve, 1500))
        setBookings(mockBookings)
      } catch (error) {
        console.error("Failed to fetch bookings:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookings()
  }, [])

  const filteredBookings = bookings.filter(
    (booking) =>
      booking.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      booking.passengerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      booking.flightDetails.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
      case "pending":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400"
      case "cancelled":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400"
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Bookings</CardTitle>
            <CardDescription>Overview of the latest flight bookings</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search bookings..."
                className="w-[200px] pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <span>Filter</span>
                  <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>All Bookings</DropdownMenuItem>
                <DropdownMenuItem>Confirmed</DropdownMenuItem>
                <DropdownMenuItem>Pending</DropdownMenuItem>
                <DropdownMenuItem>Cancelled</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <Button variant="ghost" className="p-0 font-medium">
                      Booking ID
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>Passenger</TableHead>
                  <TableHead>Flight Details</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredBookings.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-24 text-center">
                      No bookings found.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredBookings.map((booking) => (
                    <TableRow key={booking.id}>
                      <TableCell className="font-medium">{booking.id}</TableCell>
                      <TableCell>{booking.passengerName}</TableCell>
                      <TableCell>{booking.flightDetails}</TableCell>
                      <TableCell>{new Date(booking.date).toLocaleDateString()}</TableCell>
                      <TableCell>${booking.amount.toFixed(2)}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(booking.status)} variant="outline">
                          {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">Open menu</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem>View details</DropdownMenuItem>
                            <DropdownMenuItem>Edit booking</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>Send email</DropdownMenuItem>
                            <DropdownMenuItem className="text-destructive">Cancel booking</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        )}
        <div className="mt-4 flex items-center justify-end space-x-2">
          <Button variant="outline" size="sm">
            Previous
          </Button>
          <Button variant="outline" size="sm">
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

