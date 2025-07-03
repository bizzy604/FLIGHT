import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { prisma } from "@/utils/prisma"
import { handleApiError } from "@/utils/error-handler"

export async function GET(request: NextRequest) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = await auth()

    // For development purposes, allow unauthenticated requests
    // In production, you would want to remove this and require authentication
    const userIdToUse = userId || "dev-user-id"

    const searchParams = request.nextUrl.searchParams
    const flightId = searchParams.get("flightId")
    const bookingReference = searchParams.get("reference")
    const status = searchParams.get("status")
    const page = Number.parseInt(searchParams.get("page") || "1")
    const limit = Number.parseInt(searchParams.get("limit") || "10")
    const offset = (page - 1) * limit

    // Build the where clause based on the provided filters
    const where: any = {}

    // Only filter by userId if authenticated
    if (userId) {
      where.userId = userId
    }

    if (bookingReference) {
      where.bookingReference = bookingReference
    }

    if (status) {
      where.status = status
    }

    if (flightId) {
      // This is a bit tricky since flightId is inside the JSON
      // For PostgreSQL, we can use the jsonb containment operator
      where.flightDetails = {
        path: ["outbound", "airline", "flightNumber"],
        equals: flightId,
      }
    }

    // Get total count for pagination
    const totalCount = await prisma.booking.count({ where })

    // Get bookings with pagination
    const bookings = await prisma.booking.findMany({
      where,
      orderBy: {
        createdAt: "desc",
      },
      skip: offset,
      take: limit,
      include: {
        payments: true,
      },
    })

    return NextResponse.json({
      bookings,
      pagination: {
        total: totalCount,
        page,
        limit,
        pages: Math.ceil(totalCount / limit),
      },
    })
  } catch (error) {
    return handleApiError(error)
  }
}

export async function POST(request: NextRequest) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = await auth()

    // For development purposes, allow unauthenticated requests
    // In production, you would want to remove this and require authentication
    const userIdToUse = userId || "dev-user-id"

    const body = await request.json()

    // Validate required fields
    if (!body.flightDetails || !body.passengerDetails || !body.contactInfo || !body.totalAmount) {
      return NextResponse.json({ error: "Missing required booking information" }, { status: 400 })
    }

    // Generate a unique booking reference
    const bookingReference = `BOOK-${Math.floor(100000 + Math.random() * 900000)}`

    // Create the booking
    const booking = await prisma.booking.create({
      data: {
        userId: userIdToUse,
        bookingReference,
        flightDetails: body.flightDetails,
        passengerDetails: body.passengerDetails,
        contactInfo: body.contactInfo,
        totalAmount: body.totalAmount,
        status: "pending",
      },
    })

    return NextResponse.json(booking, { status: 201 })
  } catch (error) {
    return handleApiError(error)
  }
}
