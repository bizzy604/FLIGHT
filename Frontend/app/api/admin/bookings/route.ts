import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { prisma } from "@/lib/prisma"
import { handleApiError, createUnauthorizedError, createForbiddenError } from "@/lib/error-handler"

export async function GET(request: NextRequest) {
  try {
    // Check authentication
    const { userId, orgRole } = await auth()
    if (!userId) {
      throw createUnauthorizedError()
    }

    // Check if user has admin role
    if (orgRole !== "admin") {
      throw createForbiddenError("Admin access required")
    }

    // Get query parameters
    const searchParams = request.nextUrl.searchParams
    const status = searchParams.get("status")
    const search = searchParams.get("search")
    const startDate = searchParams.get("startDate")
    const endDate = searchParams.get("endDate")
    const limit = Number.parseInt(searchParams.get("limit") || "20", 10)
    const offset = Number.parseInt(searchParams.get("offset") || "0", 10)

    // Build where clause for Prisma
    const where: any = {}

    if (status) {
      where.status = status
    }

    if (search) {
      where.OR = [
        { bookingReference: { contains: search, mode: "insensitive" } },
        { userId: { contains: search, mode: "insensitive" } },
        { contactInfo: { path: ["email"], string_contains: search } },
        { contactInfo: { path: ["phone"], string_contains: search } },
      ]
    }

    if (startDate) {
      where.createdAt = {
        ...(where.createdAt || {}),
        gte: new Date(startDate),
      }
    }

    if (endDate) {
      where.createdAt = {
        ...(where.createdAt || {}),
        lte: new Date(endDate),
      }
    }

    // Execute queries with Prisma
    const [bookings, total] = await Promise.all([
      prisma.booking.findMany({
        where,
        include: {
          payments: {
            select: {
              paymentIntentId: true,
              status: true,
            },
          },
        },
        orderBy: {
          createdAt: "desc",
        },
        skip: offset,
        take: limit,
      }),
      prisma.booking.count({ where }),
    ])

    // Return bookings with pagination metadata
    return NextResponse.json({
      bookings,
      meta: {
        total,
        limit,
        offset,
      },
    })
  } catch (error) {
    return handleApiError(error)
  }
}