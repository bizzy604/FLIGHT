import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { prisma } from "@/lib/prisma"
import {
  handleApiError,
  createValidationError,
  createNotFoundError,
  createUnauthorizedError,
} from "@/lib/error-handler"
import { logger } from "@/lib/logger"

export async function GET(request: NextRequest, { params }: { params: { reference: string } }) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = auth()
    if (!userId) {
      throw createUnauthorizedError()
    }

    const bookingReference = params.reference
    if (!bookingReference) {
      throw createValidationError("Booking reference is required", {})
    }

    // Check if booking exists and belongs to user using Prisma
    const booking = await prisma.booking.findUnique({
      where: { bookingReference },
      include: {
        payments: true,
      },
    })

    if (!booking) {
      throw createNotFoundError(`Booking with reference ${bookingReference} not found`)
    }

    // Check if booking belongs to the authenticated user
    if (booking.userId !== userId) {
      throw createUnauthorizedError("You do not have permission to view this booking")
    }

    // Return booking details
    return NextResponse.json(booking)
  } catch (error) {
    return handleApiError(error)
  }
}

export async function PATCH(request: NextRequest, { params }: { params: { reference: string } }) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = auth()
    if (!userId) {
      throw createUnauthorizedError()
    }

    const bookingReference = params.reference
    if (!bookingReference) {
      throw createValidationError("Booking reference is required", {})
    }

    // Parse request body
    const body = await request.json()

    // Check if booking exists and belongs to user
    const booking = await prisma.booking.findUnique({
      where: { bookingReference },
    })

    if (!booking) {
      throw createNotFoundError(`Booking with reference ${bookingReference} not found`)
    }

    // Check if booking belongs to the authenticated user
    if (booking.userId !== userId) {
      throw createUnauthorizedError("You do not have permission to modify this booking")
    }

    // Check if booking can be modified (not cancelled or completed)
    if (booking.status === "cancelled" || booking.status === "completed") {
      throw createValidationError(`Booking cannot be modified in status: ${booking.status}`, {
        currentStatus: booking.status,
      })
    }

    // Validate update data
    if (!body.extras) {
      throw createValidationError("No changes provided", {})
    }

    // Update booking in database
    const updatedBooking = await prisma.booking.update({
      where: { id: booking.id },
      data: {
        extras: body.extras,
        // You might want to update other fields based on the changes
        // For example, if seat selection costs extra, you might update totalAmount
        // totalAmount: booking.totalAmount + calculateExtraCost(body.extras),
        status: "confirmed", // Assume changes are confirmed immediately
      },
      include: {
        payments: true,
      },
    })

    logger.info("Booking updated", {
      userId,
      bookingReference,
      changes: body.extras,
    })

    // Return updated booking
    return NextResponse.json(updatedBooking)
  } catch (error) {
    return handleApiError(error)
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { reference: string } }) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = auth()
    if (!userId) {
      throw createUnauthorizedError()
    }

    const bookingReference = params.reference
    if (!bookingReference) {
      throw createValidationError("Booking reference is required", {})
    }

    // Check if booking exists and belongs to user using Prisma
    const booking = await prisma.booking.findUnique({
      where: { bookingReference },
    })

    if (!booking) {
      throw createNotFoundError(`Booking with reference ${bookingReference} not found`)
    }

    // Check if booking belongs to the authenticated user
    if (booking.userId !== userId) {
      throw createUnauthorizedError("You do not have permission to cancel this booking")
    }

    // Check if booking can be cancelled (not already cancelled or completed)
    if (booking.status === "cancelled" || booking.status === "completed") {
      throw createValidationError(`Booking cannot be cancelled in status: ${booking.status}`, {
        currentStatus: booking.status,
      })
    }

    // Update booking status in database using Prisma
    const cancelledBooking = await prisma.booking.update({
      where: { id: booking.id },
      data: { status: "cancelled" },
    })

    logger.info("Booking cancelled", {
      userId,
      bookingReference,
    })

    // Return cancellation result
    return NextResponse.json({
      bookingReference,
      status: "cancelled",
    })
  } catch (error) {
    return handleApiError(error)
  }
}

