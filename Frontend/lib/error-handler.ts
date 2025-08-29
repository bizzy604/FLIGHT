import { NextResponse } from "next/server"
import { logger } from "./logger"

// Error types
export enum ErrorType {
  VALIDATION = "VALIDATION_ERROR",
  NOT_FOUND = "NOT_FOUND",
  UNAUTHORIZED = "UNAUTHORIZED",
  FORBIDDEN = "FORBIDDEN",
  CONFLICT = "CONFLICT",
  INTERNAL = "INTERNAL_SERVER_ERROR",
  EXTERNAL_API = "EXTERNAL_API_ERROR",
  PAYMENT = "PAYMENT_ERROR",
}

// Custom error class
export class AppError extends Error {
  type: ErrorType
  statusCode: number
  details?: any

  constructor(message: string, type: ErrorType, statusCode: number, details?: any) {
    super(message)
    this.name = "AppError"
    this.type = type
    this.statusCode = statusCode
    this.details = details
  }
}

// Error handler for API routes
export function handleApiError(error: any) {
  // If it's already an AppError, use its properties
  if (error instanceof AppError) {
    logger.error(error.message, {
      type: error.type,
      statusCode: error.statusCode,
      details: error.details,
      stack: error.stack,
    })

    return NextResponse.json(
      {
        error: {
          type: error.type,
          message: error.message,
          ...(error.details && { details: error.details }),
        },
      },
      { status: error.statusCode },
    )
  }

  // Handle Stripe errors
  if (error.type?.startsWith("Stripe")) {
    logger.error("Stripe error", {
      type: error.type,
      message: error.message,
      code: error.code,
      stack: error.stack,
    })

    return NextResponse.json(
      {
        error: {
          type: ErrorType.PAYMENT,
          message: error.message,
          code: error.code,
        },
      },
      { status: 400 },
    )
  }

  // Handle Axios errors (for external API calls)
  if (error.isAxiosError) {
    logger.error("External API error", {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
      stack: error.stack,
    })

    return NextResponse.json(
      {
        error: {
          type: ErrorType.EXTERNAL_API,
          message: "Error communicating with external service",
          details: error.response?.data || error.message,
        },
      },
      { status: error.response?.status || 500 },
    )
  }

  // Default to internal server error
  logger.error("Unhandled error", {
    message: error.message,
    stack: error.stack,
  })

  return NextResponse.json(
    {
      error: {
        type: ErrorType.INTERNAL,
        message: "An unexpected error occurred",
      },
    },
    { status: 500 },
  )
}

// Validation error helper
export function createValidationError(message: string, details: any) {
  return new AppError(message, ErrorType.VALIDATION, 400, details)
}

// Not found error helper
export function createNotFoundError(message: string) {
  return new AppError(message, ErrorType.NOT_FOUND, 404)
}

// Unauthorized error helper
export function createUnauthorizedError(message = "Authentication required") {
  return new AppError(message, ErrorType.UNAUTHORIZED, 401)
}

// Forbidden error helper
export function createForbiddenError(message = "Access denied") {
  return new AppError(message, ErrorType.FORBIDDEN, 403)
}

// Conflict error helper
export function createConflictError(message: string, details?: any) {
  return new AppError(message, ErrorType.CONFLICT, 409, details)
}

// External API error helper
export function createExternalApiError(message: string, details?: any) {
  return new AppError(message, ErrorType.EXTERNAL_API, 502, details)
}

// Payment error helper
export function createPaymentError(message: string, details?: any) {
  return new AppError(message, ErrorType.PAYMENT, 400, details)
}

