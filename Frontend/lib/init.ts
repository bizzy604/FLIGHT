import { initializeDb } from "./prisma"
import { logger } from "./logger"

// Initialize application
export async function initializeApp() {
  logger.info("Initializing application...")

  // Initialize database connection
  const dbConnected = await initializeDb()
  if (!dbConnected) {
    logger.error("Failed to connect to database")
    return false
  }

  // With Prisma, we don't need to manually initialize the schema
  // as it's handled by migrations

  logger.info("Application initialized successfully")
  return true
}

// Call initialization on app startup
export async function startApp() {
  try {
    const initialized = await initializeApp()
    if (!initialized) {
      logger.error("Application failed to initialize properly")
      process.exit(1)
    }
  } catch (error) {
    logger.error("Unexpected error during application initialization", { error })
    process.exit(1)
  }
}
