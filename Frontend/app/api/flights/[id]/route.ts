import { type NextRequest, NextResponse } from "next/server"
import { getFlightDetails } from "@/lib/flight-api"
import { handleApiError, createNotFoundError } from "@/lib/error-handler"
import { logger } from "@/lib/logger"

// Cache configuration
const CACHE_MAX_AGE = 600 // 10 minutes in seconds

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const flightId = params.id

    if (!flightId) {
      throw createNotFoundError("Flight ID is required")
    }

    // Log request
    logger.info("Flight details request", { flightId })

    // Get flight details from API
    const flightDetails = await getFlightDetails(flightId)

    // Return flight details with caching headers
    return NextResponse.json(flightDetails, {
      headers: {
        "Cache-Control": `public, max-age=${CACHE_MAX_AGE}`,
      },
    })
  } catch (error) {
    return handleApiError(error)
  }
}

