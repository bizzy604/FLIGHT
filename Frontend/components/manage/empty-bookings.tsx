import Link from "next/link"
import { CalendarRange } from "lucide-react"
import { Button } from "@/components/ui/button"

interface EmptyBookingsProps {
  message: string
  description: string
  showBookButton?: boolean
}

export function EmptyBookings({ message, description, showBookButton = false }: EmptyBookingsProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        <CalendarRange className="h-6 w-6 text-muted-foreground" />
      </div>
      <h3 className="mt-4 text-lg font-medium">{message}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      {showBookButton && (
        <Link href="/" className="mt-4">
          <Button>Book a Flight</Button>
        </Link>
      )}
    </div>
  )
}

