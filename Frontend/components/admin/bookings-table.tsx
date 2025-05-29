"use client"

import { useState, useEffect } from "react"
import { ArrowUpDown, ChevronLeft, ChevronRight, Download, MoreHorizontal, Printer, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
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

// Extended mock data for bookings
const mockBookings = Array.from({ length: 50 }, (_, i) => {
  const statuses = ["confirmed", "pending", "cancelled", "refunded"]
  const flightRoutes = [
    "SW1234 - JFK to LAX",
    "SW4321 - LAX to JFK",
    "SW2468 - ORD to SFO",
    "SW1357 - DFW to SEA",
    "SW9876 - ATL to MIA",
    "SW5432 - LAS to DEN",
    "SW8765 - PHX to HOU",
  ]
  const names = [
    "John Doe",
    "Jane Smith",
    "Michael Johnson",
    "Emily Williams",
    "David Brown",
    "Sarah Miller",
    "Robert Wilson",
    "Jennifer Taylor",
    "William Anderson",
    "Elizabeth Thomas",
  ]

  const randomDate = new Date()
  randomDate.setDate(randomDate.getDate() + Math.floor(Math.random() * 30))

  return {
    id: `BK-${(12345678 + i).toString()}`,
    passengerName: names[Math.floor(Math.random() * names.length)],
    flightDetails: flightRoutes[Math.floor(Math.random() * flightRoutes.length)],
    date: randomDate.toISOString().split("T")[0],
    amount: Math.floor(Math.random() * 500) + 200 + Math.random(),
    status: statuses[Math.floor(Math.random() * statuses.length)],
    passengers: Math.floor(Math.random() * 4) + 1,
    paymentMethod: Math.random() > 0.5 ? "Credit Card" : "PayPal",
  }
})

export function BookingsTable() {
  const [isLoading, setIsLoading] = useState(true)
  const [bookings, setBookings] = useState<typeof mockBookings>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(10)
  const [sortField, setSortField] = useState("date")
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc")

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

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  const sortedBookings = [...bookings].sort((a, b) => {
    let comparison = 0

    switch (sortField) {
      case "id":
        comparison = a.id.localeCompare(b.id)
        break
      case "passengerName":
        comparison = a.passengerName.localeCompare(b.passengerName)
        break
      case "date":
        comparison = new Date(a.date).getTime() - new Date(b.date).getTime()
        break
      case "amount":
        comparison = a.amount - b.amount
        break
      case "status":
        comparison = a.status.localeCompare(b.status)
        break
      default:
        comparison = 0
    }

    return sortDirection === "asc" ? comparison : -comparison
  })

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = sortedBookings.slice(indexOfFirstItem, indexOfLastItem)
  const totalPages = Math.ceil(sortedBookings.length / itemsPerPage)

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
      case "pending":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400"
      case "cancelled":
        return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400"
      case "refunded":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400"
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setIsLoading(true)}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        </div>
        <div className="text-sm text-muted-foreground">
          Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, sortedBookings.length)} of {sortedBookings.length}{" "}
          bookings
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-[400px] items-center justify-center rounded-md border">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <Button variant="ghost" className="p-0 font-medium" onClick={() => handleSort("id")}>
                    Booking ID
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button variant="ghost" className="p-0 font-medium" onClick={() => handleSort("passengerName")}>
                    Passenger
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>Flight Details</TableHead>
                <TableHead>
                  <Button variant="ghost" className="p-0 font-medium" onClick={() => handleSort("date")}>
                    Date
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>Passengers</TableHead>
                <TableHead>
                  <Button variant="ghost" className="p-0 font-medium" onClick={() => handleSort("amount")}>
                    Amount
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>Payment Method</TableHead>
                <TableHead>
                  <Button variant="ghost" className="p-0 font-medium" onClick={() => handleSort("status")}>
                    Status
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="h-24 text-center">
                    No bookings found.
                  </TableCell>
                </TableRow>
              ) : (
                currentItems.map((booking) => (
                  <TableRow key={booking.id}>
                    <TableCell className="font-medium">{booking.id}</TableCell>
                    <TableCell>{booking.passengerName}</TableCell>
                    <TableCell>{booking.flightDetails}</TableCell>
                    <TableCell>{new Date(booking.date).toLocaleDateString()}</TableCell>
                    <TableCell>{booking.passengers}</TableCell>
                    <TableCell>${booking.amount.toFixed(2)}</TableCell>
                    <TableCell>{booking.paymentMethod}</TableCell>
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
                          <DropdownMenuItem>Resend confirmation</DropdownMenuItem>
                          <DropdownMenuSeparator />
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

      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Page {currentPage} of {totalPages}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

