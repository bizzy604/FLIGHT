import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { createPaymentIntent, retrievePaymentIntent } from "@/lib/stripe"
import { prisma } from "@/lib/prisma"
import { handleApiError, createValidationError, createNotFoundError } from "@/lib/error-handler"
import { logger } from "@/lib/logger"

export async function POST(request: NextRequest) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = await auth()

    // For development purposes, allow unauthenticated requests
    // In production, you would want to remove this and require authentication
    const userIdToUse = userId || "dev-user-id"

    // Parse request body
    const body = await request.json()

    // Validate required fields
    if (!body.bookingReference || !body.amount || !body.currency) {
      throw createValidationError("Missing required payment information", {
        required: ["bookingReference", "amount", "currency"],
        received: Object.keys(body),
      })
    }

    // Validate amount
    const amount = Number.parseFloat(body.amount)
    if (isNaN(amount) || amount <= 0) {
      throw createValidationError("Invalid payment amount", {
        received: body.amount,
        message: "Amount must be a positive number",
      })
    }

    // Check if booking exists using Prisma
    let booking = await prisma.booking.findUnique({
      where: { bookingReference: body.bookingReference },
    })

    // If booking doesn't exist, create it from the session data
    if (!booking) {
      // Check if we have all the required data to create a booking
      if (!body.flightId || !body.bookingData) {
        throw createValidationError("Missing booking data", {
          required: ["flightId", "bookingData"],
          received: Object.keys(body),
        })
      }
      
      try {
        // Parse booking data if it's a string
        const bookingData = typeof body.bookingData === 'string' 
          ? JSON.parse(body.bookingData) 
          : body.bookingData;
        
        // First check if a booking with this reference already exists (to handle race conditions)
        booking = await prisma.booking.findUnique({
          where: { bookingReference: body.bookingReference },
        });
        
        // If still no booking found, create a new one
        if (!booking) {
          // Generate a unique booking reference if needed
          const bookingReference = body.bookingReference;
          
          // Create a new booking record
          booking = await prisma.booking.create({
            data: {
              userId: userIdToUse,
              bookingReference: bookingReference,
              status: "pending",
              totalAmount: amount,
              flightDetails: {
                ...bookingData.flightDetails,
                flightId: body.flightId
              },
              passengerDetails: bookingData.passengers || [],
              contactInfo: bookingData.contactInfo || {},
              extras: bookingData.extras || {}
            },
          });

          logger.info("Created booking record from client data", {
            bookingReference: bookingReference,
            flightId: body.flightId,
            userId: userIdToUse
          });
        } else {
          logger.info("Using existing booking record", {
            bookingReference: body.bookingReference,
            bookingId: booking.id
          });
        }
      } catch (err) {
        logger.error("Failed to create booking record", { error: err })
        throw createValidationError("Failed to create booking record", {
          error: err instanceof Error ? err.message : String(err)
        })
      }
    } else {
      // Check if booking is in a payable state
      // Allow payments for pending, payment_pending, and payment_failed statuses
      const allowedStatuses = ["pending", "payment_pending", "payment_failed"];
      if (!allowedStatuses.includes(booking.status)) {
        throw createValidationError(`Cannot process payment for booking in status: ${booking.status}`, {
          currentStatus: booking.status,
          allowedStatuses: allowedStatuses,
        })
      }
    }

    // Create payment intent with Stripe
    const paymentIntent = await createPaymentIntent(amount, body.currency.toLowerCase(), {
      booking_reference: body.bookingReference,
      user_id: userIdToUse,
    })

    // Store payment intent in database using Prisma transaction
    await prisma.$transaction([
      // Create payment record
      prisma.payment.create({
        data: {
          bookingId: booking.id,
          paymentIntentId: paymentIntent.id,
          amount,
          currency: body.currency.toLowerCase(),
          status: paymentIntent.status,
        },
      }),

      // Update booking status
      prisma.booking.update({
        where: { id: booking.id },
        data: { status: "payment_pending" },
      }),
    ])

    logger.info("Payment intent created", {
      userId: userIdToUse,
      bookingReference: body.bookingReference,
      paymentIntentId: paymentIntent.id,
      amount,
      currency: body.currency,
    })

    // Return client secret for frontend to complete payment
    return NextResponse.json({
      clientSecret: paymentIntent.client_secret,
      paymentIntentId: paymentIntent.id,
    })
  } catch (error) {
    return handleApiError(error)
  }
}

export async function GET(request: NextRequest) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = await auth()

    // For development purposes, allow unauthenticated requests
    // In production, you would want to remove this and require authentication
    const userIdToUse = userId || "dev-user-id"

    // Get query parameters
    const searchParams = request.nextUrl.searchParams
    const paymentIntentId = searchParams.get("paymentIntentId")

    if (!paymentIntentId) {
      throw createValidationError("Payment intent ID is required", {})
    }

    // Retrieve payment from database
    const payment = await prisma.payment.findUnique({
      where: { paymentIntentId },
      include: { booking: true },
    })

    if (!payment) {
      throw createNotFoundError(`Payment with ID ${paymentIntentId} not found`)
    }

    // Retrieve payment intent from Stripe
    const paymentIntent = await retrievePaymentIntent(paymentIntentId)

    // Return payment details
    return NextResponse.json({
      paymentIntentId: paymentIntent.id,
      amount: payment.amount,
      currency: payment.currency,
      status: paymentIntent.status,
      bookingReference: payment.booking.bookingReference,
      createdAt: payment.createdAt,
    })
  } catch (error) {
    return handleApiError(error)
  }
}
