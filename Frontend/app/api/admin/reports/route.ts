import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { query } from "@/utils/db"
import { handleApiError, createUnauthorizedError, createForbiddenError } from "@/utils/error-handler"
import { logger } from "@/utils/logger"

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

    // Get query parameters
    const searchParams = request.nextUrl.searchParams
    const reportType = searchParams.get("type") || "revenue"
    const startDate =
      searchParams.get("startDate") || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0]
    const endDate = searchParams.get("endDate") || new Date().toISOString().split("T")[0]
    const groupBy = searchParams.get("groupBy") || "day"

    // Validate group by parameter
    if (!["day", "week", "month"].includes(groupBy)) {
      return NextResponse.json(
        { error: "Invalid groupBy parameter. Must be one of: day, week, month" },
        { status: 400 },
      )
    }

    let reportData
    switch (reportType) {
      case "revenue":
        reportData = await generateRevenueReport(startDate, endDate, groupBy)
        break
      case "bookings":
        reportData = await generateBookingsReport(startDate, endDate, groupBy)
        break
      case "users":
        reportData = await generateUsersReport(startDate, endDate, groupBy)
        break
      default:
        return NextResponse.json(
          { error: "Invalid report type. Must be one of: revenue, bookings, users" },
          { status: 400 },
        )
    }

    // Return report data
    return NextResponse.json({
      reportType,
      startDate,
      endDate,
      groupBy,
      data: reportData,
    })
  } catch (error) {
    return handleApiError(error)
  }
}

// Generate revenue report
interface RevenueReportRow {
  period: string;
  total_revenue: string;
  payment_count: string;
  successful_payments: string;
  failed_payments: string;
  average_amount: string;
}

async function generateRevenueReport(startDate: string, endDate: string, groupBy: string): Promise<RevenueReportRow[]> {
  let dateFormat: string
  switch (groupBy) {
    case 'day':
      dateFormat = 'YYYY-MM-DD'
      break
    case 'month':
      dateFormat = 'YYYY-MM'
      break
    case 'year':
      dateFormat = 'YYYY'
      break
    default:
      dateFormat = 'YYYY-MM-DD'
      break
  }

  const result = await query<RevenueReportRow[]>(
    `
    SELECT
      TO_CHAR(DATE_TRUNC('${groupBy}', p.created_at), '${dateFormat}') as period,
      COALESCE(SUM(p.amount)::text, '0') as total_revenue,
      COALESCE(COUNT(*)::text, '0') as payment_count,
      COALESCE(COUNT(CASE WHEN p.status = 'succeeded' THEN 1 END)::text, '0') as successful_payments,
      COALESCE(COUNT(CASE WHEN p.status = 'failed' THEN 1 END)::text, '0') as failed_payments,
      COALESCE(AVG(p.amount)::text, '0') as average_amount
    FROM payments p
    WHERE p.created_at BETWEEN $1 AND $2
    GROUP BY DATE_TRUNC('${groupBy}', p.created_at)
    ORDER BY DATE_TRUNC('${groupBy}', p.created_at)
  `,
    [`${startDate}T00:00:00Z`, `${endDate}T23:59:59Z`],
  )

  if (!Array.isArray(result)) {
    logger.error('Unexpected database response format for revenue report', { result })
    throw new Error('Invalid database response format for revenue report')
  }

  return result
}

// Generate bookings report
interface BookingsReportRow {
  period: string;
  total_bookings: string;
  confirmed_bookings: string;
  pending_bookings: string;
  cancelled_bookings: string;
  average_booking_amount: string;
}

async function generateBookingsReport(startDate: string, endDate: string, groupBy: string): Promise<BookingsReportRow[]> {
  let dateFormat: string
  switch (groupBy) {
    case 'day':
      dateFormat = 'YYYY-MM-DD'
      break
    case 'month':
      dateFormat = 'YYYY-MM'
      break
    case 'year':
      dateFormat = 'YYYY'
      break
    default:
      dateFormat = 'YYYY-MM-DD'
      break
  }

  const result = await query<BookingsReportRow[]>(
    `SELECT
      TO_CHAR(DATE_TRUNC('${groupBy}', b.created_at), '${dateFormat}') as period,
      COALESCE(COUNT(*)::text, '0') as total_bookings,
      COALESCE(COUNT(CASE WHEN b.status = 'CONFIRMED' THEN 1 END)::text, '0') as confirmed_bookings,
      COALESCE(COUNT(CASE WHEN b.status = 'PENDING' THEN 1 END)::text, '0') as pending_bookings,
      COALESCE(COUNT(CASE WHEN b.status = 'CANCELLED' THEN 1 END)::text, '0') as cancelled_bookings,
      COALESCE(AVG(b.total_amount)::text, '0') as average_booking_amount
    FROM bookings b
    WHERE b.created_at BETWEEN $1 AND $2
    GROUP BY DATE_TRUNC('${groupBy}', b.created_at)
    ORDER BY DATE_TRUNC('${groupBy}', b.created_at)
  `,
    [`${startDate}T00:00:00Z`, `${endDate}T23:59:59Z`],
  )

  if (!Array.isArray(result)) {
    logger.error('Unexpected database response format for bookings report', { result })
    throw new Error('Invalid database response format for bookings report')
  }

  return result
}

// Generate users report
interface UsersReportRow {
  period: string;
  active_users: string;
  total_bookings: string;
  total_spent: string;
  average_spent_per_booking: string;
}

async function generateUsersReport(startDate: string, endDate: string, groupBy: string): Promise<UsersReportRow[]> {
  let dateFormat: string
  switch (groupBy) {
    case 'day':
      dateFormat = 'YYYY-MM-DD'
      break
    case 'month':
      dateFormat = 'YYYY-MM'
      break
    case 'year':
      dateFormat = 'YYYY'
      break
    default:
      dateFormat = 'YYYY-MM-DD'
      break
  }

  const result = await query<UsersReportRow[]>(
    `SELECT
      TO_CHAR(DATE_TRUNC('${groupBy}', b.created_at), '${dateFormat}') as period,
      COALESCE(COUNT(DISTINCT b.user_id)::text, '0') as active_users,
      COALESCE(COUNT(*)::text, '0') as total_bookings,
      COALESCE(SUM(b.total_amount)::text, '0') as total_spent,
      COALESCE(AVG(b.total_amount)::text, '0') as average_spent_per_booking
    FROM bookings b
    WHERE b.created_at BETWEEN $1 AND $2
    GROUP BY DATE_TRUNC('${groupBy}', b.created_at)
    ORDER BY DATE_TRUNC('${groupBy}', b.created_at)
  `,
    [`${startDate}T00:00:00Z`, `${endDate}T23:59:59Z`],
  )

  if (!Array.isArray(result)) {
    logger.error('Unexpected database response format for users report', { result })
    throw new Error('Invalid database response format for users report')
  }

  return result
}
