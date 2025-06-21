import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { prisma } from "@/utils/prisma"
import { handleApiError } from "@/utils/error-handler"

// Helper functions for error responses
const createErrorResponse = (message: string, status: number) => 
  new Response(JSON.stringify({ error: message }), { status });

const createUnauthorizedError = (message: string = 'Unauthorized') => 
  createErrorResponse(message, 401);
  
const createForbiddenError = (message: string = 'Forbidden') => 
  createErrorResponse(message, 403);

// Force dynamic rendering to prevent static generation during build
export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    // Get the current user session
    const { userId, orgRole } = await auth();
    
    if (!userId) {
      throw createUnauthorizedError();
    }

    // Check if user has admin role in the current organization
    const isAdmin = orgRole === 'org:admin' || orgRole === 'admin';
    
    if (!isAdmin) {
      throw createForbiddenError("Admin access required");
    }

    // Get time range from query parameters
    const searchParams = request.nextUrl.searchParams
    const timeRange = searchParams.get("timeRange") || "day"

    // Determine time filter based on range
    const date = new Date()
    switch (timeRange) {
      case "day":
        date.setDate(date.getDate() - 1)
        break
      case "week":
        date.setDate(date.getDate() - 7)
        break
      case "month":
        date.setDate(date.getDate() - 30)
        break
      case "year":
        date.setDate(date.getDate() - 365)
        break
      default:
        date.setDate(date.getDate() - 1)
    }

    // Get booking metrics using Prisma
    const bookingMetrics = await prisma.booking.aggregate({
      _count: {
        id: true,
        userId: true,
      },
      where: {
        createdAt: {
          gte: date,
        },
      },
    })

    const uniqueUsersCount = await prisma.booking.findMany({
      where: {
        createdAt: {
          gte: date,
        },
      },
      select: {
        userId: true,
      },
      distinct: ['userId'],
    })

    // Get booking status counts
    const bookingStatusCounts = await prisma.booking.groupBy({
      by: ["status"],
      _count: {
        id: true,
      },
      where: {
        createdAt: {
          gte: date,
        },
      },
    })

    // Get revenue metrics using Prisma
    const revenueMetrics = await prisma.payment.aggregate({
      _sum: {
        amount: true,
      },
      _avg: {
        amount: true,
      },
      _count: {
        id: true,
      },
      where: {
        createdAt: {
          gte: date,
        },
      },
    })

    // Get payment status counts
    const paymentStatusCounts = await prisma.payment.groupBy({
      by: ["status"],
      _count: {
        id: true,
      },
      where: {
        createdAt: {
          gte: date,
        },
      },
    })

    // Get recent bookings
    const recentBookings = await prisma.booking.findMany({
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
      take: 10,
    })

    // Format the metrics
    const formattedMetrics = {
      bookings: {
        total_bookings: bookingMetrics._count?.id || 0,
        confirmed_bookings: bookingStatusCounts.find((b) => b.status === "confirmed")?._count?.id || 0,
        pending_bookings: bookingStatusCounts.find((b) => b.status === "pending")?._count?.id || 0,
        cancelled_bookings: bookingStatusCounts.find((b) => b.status === "cancelled")?._count?.id || 0,
        unique_users: uniqueUsersCount.length,
      },
      revenue: {
        total_revenue: revenueMetrics._sum?.amount || 0,
        average_order_value: revenueMetrics._avg?.amount || 0,
        total_payments: revenueMetrics._count || 0,
        successful_payments: paymentStatusCounts.find((p) => p.status === "succeeded")?._count?.id || 0,
        failed_payments: paymentStatusCounts.find((p) => p.status === "failed")?._count?.id || 0,
      },
    }

    // Return dashboard data
    return NextResponse.json({
      metrics: formattedMetrics,
      recentBookings,
      timeRange,
    })
  } catch (error) {
    return handleApiError(error)
  }
}