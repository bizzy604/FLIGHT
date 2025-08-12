import type { Metadata } from "next"
import { BookingsTable, BookingsFilter } from "@/components/organisms"

export const metadata: Metadata = {
  title: "Rea Travel Admin - Bookings",
  description: "Admin dashboard for Rea Travel flight booking portal",
}

export default function AdminBookingsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Bookings</h1>
        <p className="text-muted-foreground">View and manage all flight bookings</p>
      </div>

      <BookingsFilter />
      <BookingsTable />
    </div>
  )
}

