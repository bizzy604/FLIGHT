import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { query } from "@/lib/db"
import { handleApiError, createUnauthorizedError, createForbiddenError } from "@/lib/error-handler"

export async function GET(request: NextRequest) {
  try {
    // Check authentication
    const { userId, orgRoles } = auth()
    if (!userId) {
      throw createUnauthorizedError()
    }

    // Check if user has admin role
    if (!orgRoles?.includes("admin")) {
      throw createForbiddenError("Admin access required")
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
async function generateRevenueReport(startDate: string, endDate: string, groupBy: string) {
  let dateFormat
  switch (groupBy) {
    case "day":
      dateFormat = "YYYY-MM-DD"
      break
    case "week":
      dateFormat = 'YYYY-"W"IW'
      break
    case "month":
      dateFormat = "YYYY-MM"
      break
  }

  const result = await query(
    `
    SELECT
      TO_CHAR(DATE_TRUNC('${groupBy}', p.created_at), '${dateFormat}') as period,
      SUM(p.amount) as total_revenue,
      COUNT(*) as payment_count,
      COUNT(CASE WHEN p.status = 'succeeded' THEN 1 END) as successful_payments,
      COUNT(CASE WHEN p.status = 'failed' THEN 1 END) as failed_payments,
      AVG(p.amount) as average_amount
    FROM payments p
    WHERE p.created_at BETWEEN $1 AND $2
    GROUP BY DATE_TRUNC('${groupBy}', p.created_at)
    ORDER BY DATE_TRUNC('${groupBy}', p.created_at)
  `,
    [`${startDate}T00:00:00Z`, `${endDate}T23:59:59Z`],
  )

  return result.rows
}

// Generate bookings report
async function generateBookingsReport(startDate: string, endDate: string, groupBy: string) {
  let dateFormat
  switch (groupBy) {
    case "day":
      dateFormat = "YYYY-MM-DD"
      break
    case "week":
      dateFormat = 'YYYY-"W"IW'
      break
    case "month":
      dateFormat = "YYYY-MM"
      break
  }

  const result = await query(
    `
    SELECT
      TO_CHAR(DATE_TRUNC('${groupBy}', b.created_at), '${dateFormat}') as period,
      COUNT(*) as total_bookings,
      COUNT(CASE WHEN b.status = 'confirmed' THEN 1 END) as confirmed_bookings,
      COUNT(CASE WHEN b.status = 'pending' THEN 1 END) as pending_bookings,
      COUNT(CASE WHEN b.status = 'cancelled' THEN 1 END) as cancelled_bookings,
      AVG(b.total_amount) as average_booking_value,
      COUNT(DISTINCT b.user_id) as unique_users
    FROM bookings b
    WHERE b.created_at BETWEEN $1 AND $2
    GROUP BY DATE_TRUNC('${groupBy}', b.created_at)
    ORDER BY DATE_TRUNC('${groupBy}', b.created_at)
  `,
    [`${startDate}T00:00:00Z`, `${endDate}T23:59:59Z`],
  )

  return result.rows
}

// Generate users report
async function generateUsersReport(startDate: string, endDate: string, groupBy: string) {
  let dateFormat
  switch (groupBy) {
    case "day":
      dateFormat = "YYYY-MM-DD"
      break
    case "week":
      dateFormat = 'YYYY-"W"IW'
      break
    case "month":
      dateFormat = "YYYY-MM"
      break
  }

  const result = await query(
    `
    SELECT
      TO_CHAR(DATE_TRUNC('${groupBy}', b.created_at), '${dateFormat}') as period,
      COUNT(DISTINCT b.user_id) as active_users,
      COUNT(*) as total_bookings,
      SUM(b.total_amount) as total_spent,
      AVG(b.total_amount) as average_spent_per_booking
    FROM bookings b
    WHERE b.created_at BETWEEN $1 AND $2
    GROUP BY DATE_TRUNC('${groupBy}', b.created_at)
    ORDER BY DATE_TRUNC('${groupBy}', b.created_at)
  `,
    [`${startDate}T00:00:00Z`, `${endDate}T23:59:59Z`],
  )

  return result.rows
}

