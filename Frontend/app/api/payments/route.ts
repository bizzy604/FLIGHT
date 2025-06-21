import { type NextRequest, NextResponse } from "next/server"
import { auth } from "@clerk/nextjs/server"
import { prisma } from "@/utils/prisma"
import { handleApiError, createUnauthorizedError, createForbiddenError, createValidationError, createNotFoundError } from "@/utils/error-handler"
import { logger } from "@/utils/logger"

export async function POST(request: NextRequest) {
  try {
    // Get user ID from Clerk authentication
    const { userId } = await auth()

    // For development purposes, allow unauthenticated requests
    // In production, you would want to remove this and require authentication
    const userIdToUse = userId || "dev-user-id"

    // Parse request body
    const body = await request.json()

    if (!userId) {
      return NextResponse.json(
        { error: 'Forbidden', message: 'User ID is required' },
        { status: 403 }
      );
    }

    // Validate required card details for backend processing
    if (!body.cardDetails) {
      throw createValidationError("Missing card details", {
        required: ["cardDetails"],
        received: Object.keys(body),
      })
    }

    // Validate required booking data
    if (!body.bookingData) {
      throw createValidationError("Missing booking data", {
        required: ["bookingData"],
        received: Object.keys(body),
      })
    }

    const { cardNumber, cardName, expiryMonth, expiryYear, cvv } = body.cardDetails
    if (!cardNumber || !cardName || !expiryMonth || !expiryYear || !cvv) {
      throw createValidationError("Missing required card details", {
        required: ["cardNumber", "cardName", "expiryMonth", "expiryYear", "cvv"],
        received: Object.keys(body.cardDetails || {}),
      })
    }

    // Validate card number format (basic validation)
    const cleanCardNumber = cardNumber.replace(/\s/g, '')
    if (!/^\d{13,19}$/.test(cleanCardNumber)) {
      throw createValidationError("Invalid card number format", {
        message: "Card number must be 13-19 digits",
      })
    }

    // Validate expiry date
    const currentYear = new Date().getFullYear() % 100
    const currentMonth = new Date().getMonth() + 1
    const expMonth = parseInt(expiryMonth)
    const expYear = parseInt(expiryYear)
    
    if (expYear < currentYear || (expYear === currentYear && expMonth < currentMonth)) {
      throw createValidationError("Card has expired", {
        message: "Please use a valid card",
      })
    }

    // Generate unique payment ID for tracking
    const paymentId = `payment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // Determine card type based on card number
    const getCardType = (cardNumber: string) => {
      const firstDigit = cardNumber.charAt(0)
      if (firstDigit === '4') return 'VI' // Visa
      if (firstDigit === '5') return 'MC' // Mastercard
      if (firstDigit === '3') return 'AX' // American Express
      return 'VI' // Default to Visa
    }

    // Create payment info structure that matches backend expectations
    const paymentInfo = {
      MethodType: "PaymentCard",
      Details: {
        CardCode: getCardType(cleanCardNumber),
        CardNumberToken: `tok_${cleanCardNumber}`, // In production, this would be a secure token
        CardHolderName: { value: cardName, refs: [] },
        EffectiveExpireDate: { Expiration: `${expiryMonth}${expiryYear}` },
        CardType: "Credit"
      }
    }

    // First create a booking record
    const booking = await prisma.booking.create({
      data: {
        userId: userIdToUse,
        bookingReference: `BK${Date.now()}`, // Generate a unique booking reference
        orderItemId: body.bookingData.flightDetails.id,
        airlineCode: "Unknown", // Will be updated from flight data
        flightNumbers: [body.bookingData.flightDetails.id],
        routeSegments: {
          departure: {
            airport: body.bookingData.flightDetails.from,
            date: body.bookingData.flightDetails.departureDate
          },
          arrival: {
            airport: body.bookingData.flightDetails.to,
            date: body.bookingData.flightDetails.returnDate || body.bookingData.flightDetails.departureDate
          }
        },
        passengerTypes: ["ADT"], // Default to adult
        documentNumbers: [],
        classOfService: "Y", // Default to economy
        cabinClass: "Economy",
        flightDetails: body.bookingData.flightDetails,
        passengerDetails: {
          name: cardName,
          email: ""
        },
        contactInfo: {
          name: cardName,
          email: ""
        },
        extras: {},
        totalAmount: body.bookingData.amount,
        status: "PENDING",
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    })

    // Store minimal payment record for tracking, linked to the booking
    const payment = await prisma.payment.create({
      data: {
        paymentIntentId: paymentId,
        bookingId: booking.id, // Link payment to the booking
        amount: body.bookingData.amount,
        currency: body.bookingData.currency.toLowerCase(),
        status: "captured", // Card details captured for backend processing
        paymentMethod: `${paymentInfo.Details.CardCode} ending in ${cleanCardNumber.slice(-4)}`,
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    })

    logger.info("Card details captured for backend processing", {
      paymentId: payment.paymentIntentId,
      cardLast4: cleanCardNumber.slice(-4),
      cardType: paymentInfo.Details.CardCode,
    })

    // Return success response with payment and booking details
    return NextResponse.json({
      success: true,
      paymentId: payment.paymentIntentId,
      bookingId: booking.id,
      bookingReference: booking.bookingReference,
      status: payment.status,
      message: "Card details captured successfully. Your booking will be processed by the airline.",
      paymentInfo: paymentInfo // Include payment info for backend processing
    })
  } catch (error) {
    const errorResponse = handleApiError(error);
    if (errorResponse instanceof NextResponse) {
      return errorResponse;
    }
    // Convert any non-NextResponse errors to a proper response
    return NextResponse.json(
      { 
        error: 'Internal Server Error',
        message: error instanceof Error ? error.message : 'An unknown error occurred',
        code: 'INTERNAL_SERVER_ERROR'
      },
      { status: 500 }
    )
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
    const paymentId = searchParams.get("paymentId")

    if (!paymentId) {
      return NextResponse.json(
        { error: "Payment ID is required" },
        { status: 400 }
      )
    }

    // Retrieve payment from database
    const payment = await prisma.payment.findUnique({
      where: { paymentIntentId: paymentId },
      include: { booking: true },
    })

    if (!payment) {
      return NextResponse.json(
        { error: `Payment with ID ${paymentId} not found` },
        { status: 404 }
      )
    }

    if (!payment.booking) {
      return NextResponse.json(
        { error: 'Booking not found' },
        { status: 403 }
      )
    }

    // Return payment details
    return NextResponse.json({
      paymentId: payment.paymentIntentId,
      amount: payment.amount,
      currency: payment.currency,
      status: payment.status,
      bookingReference: payment.booking.bookingReference,
      createdAt: payment.createdAt
    })
  } catch (error) {
    console.error('Error in GET /api/payments:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
