"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export function BookingsTable() {
  // This is a placeholder component for admin bookings table
  const mockBookings = [
    {
      id: "1",
      reference: "BK001",
      passenger: "John Doe",
      route: "NYC → LAX",
      status: "confirmed",
      amount: "$450"
    },
    {
      id: "2", 
      reference: "BK002",
      passenger: "Jane Smith",
      route: "LAX → NYC",
      status: "pending",
      amount: "$520"
    }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Bookings</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Reference</TableHead>
              <TableHead>Passenger</TableHead>
              <TableHead>Route</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockBookings.map((booking) => (
              <TableRow key={booking.id}>
                <TableCell className="font-medium">{booking.reference}</TableCell>
                <TableCell>{booking.passenger}</TableCell>
                <TableCell>{booking.route}</TableCell>
                <TableCell>
                  <Badge 
                    className={booking.status === 'confirmed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}
                  >
                    {booking.status}
                  </Badge>
                </TableCell>
                <TableCell>{booking.amount}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}