import { type NextRequest, NextResponse } from "next/server"
import prisma from "@/utils/prisma"
import { logger } from "@/utils/logger"

// Health check endpoint to verify system status
export async function GET(request: NextRequest) {
  try {
    // Check database connection
    await prisma.$queryRaw`SELECT 1`;
    
    logger.info('Health check successful');
    
    return NextResponse.json({ 
      status: 'ok',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error("Health check failed", { error });
    return NextResponse.json(
      { status: "error", message: "Service unavailable" },
      { status: 503 }
    );
  }
}

// Check required environment variables
function checkEnvironmentVariables() {
  const requiredVars = [
    "DATABASE_URL",
    "FLIGHT_API_BASE_URL",
    "FLIGHT_API_KEY",
    "CLERK_SECRET_KEY"
  ]

  const missingVars = requiredVars.filter((varName) => !process.env[varName])

  return {
    valid: missingVars.length === 0,
    missingVariables: missingVars.length > 0 ? missingVars : undefined,
  }
}