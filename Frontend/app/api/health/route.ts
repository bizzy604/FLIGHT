import { type NextRequest, NextResponse } from "next/server"
import { initializeDb } from "@/lib/prisma"
import { logger } from "@/lib/logger"

// Health check endpoint to verify system status
export async function GET(request: NextRequest) {
  try {
    // Check database connection
    const dbStatus = await initializeDb()

    // Check environment variables
    const envStatus = checkEnvironmentVariables()

    // Get system info
    const systemInfo = {
      nodeVersion: process.version,
      environment: process.env.NODE_ENV,
      timestamp: new Date().toISOString(),
    }

    // Determine overall status
    const status = dbStatus && envStatus.valid ? "healthy" : "unhealthy"

    // Log health check
    logger.info("Health check", { status })

    // Return health status
    return NextResponse.json({
      status,
      database: {
        connected: dbStatus,
      },
      environment: envStatus,
      system: systemInfo,
    })
  } catch (error) {
    logger.error("Health check failed", { error })

    return NextResponse.json(
      {
        status: "unhealthy",
        error: "Health check failed",
      },
      { status: 500 },
    )
  }
}

// Check required environment variables
function checkEnvironmentVariables() {
  const requiredVars = [
    "DATABASE_URL",
    "FLIGHT_API_BASE_URL",
    "FLIGHT_API_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "CLERK_SECRET_KEY",
  ]

  const missingVars = requiredVars.filter((varName) => !process.env[varName])

  return {
    valid: missingVars.length === 0,
    missingVariables: missingVars.length > 0 ? missingVars : undefined,
  }
}