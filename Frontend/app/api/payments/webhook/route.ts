import { type NextRequest, NextResponse } from "next/server"
import { constructEventFromPayload } from "@/lib/stripe"
import { prisma } from "@/lib/prisma"
import { handleApiError } from "@/lib/error-handler"
import { logger } from "@/lib/logger"

// This endpoint is public (no auth) because Stripe needs to access it
export async function POST(request: NextRequest) {
  try {
    // Get the raw request body
    const payload = await request.text()

    // Get the Stripe signature from headers
    const signature = request.headers.get("stripe-signature")

    if (!signature) {
      return NextResponse.json({ error: "Missing Stripe signature" }, { status: 400 })
    }

    // Verify the event
    const event = constructEventFromPayload(payload, signature)

    logger.info("Webhook received", {
      eventType: event.type,
      eventId: event.id,
    })

    // Handle different event types
    switch (event.type) {
      case "payment_intent.succeeded":
        await handlePaymentSucceeded(event.data.object)
        break

      case "payment_intent.payment_failed":
        await handlePaymentFailed(event.data.object)
        break

      case "payment_intent.canceled":
        await handlePaymentCanceled(event.data.object)
        break

      default:
        logger.info(`Unhandled event type: ${event.type}`)
    }

    // Return a 200 response to acknowledge receipt of the event
    return NextResponse.json({ received: true })
  } catch (error) {
    return handleApiError(error)
  }
}

// Handle successful payment
async function handlePaymentSucceeded(paymentIntent: any) {
  const paymentIntentId = paymentIntent.id

  logger.info("Payment succeeded", {
    paymentIntentId,
    amount: paymentIntent.amount / 100, // Convert from cents
    currency: paymentIntent.currency,
  })

  try {
    // Find the payment in the database
    const payment = await prisma.payment.findUnique({
      where: { paymentIntentId },
    })

    if (!payment) {
      logger.error("Payment not found in database", { paymentIntentId })
      return
    }

    // Update payment and booking status in a transaction
    await prisma.$transaction([
      // Update payment status
      prisma.payment.update({
        where: { id: payment.id },
        data: {
          status: "succeeded",
          paymentMethod: paymentIntent.payment_method_types[0],
        },
      }),

      // Update booking status
      prisma.booking.update({
        where: { id: payment.bookingId },
        data: { status: "confirmed" },
      }),
    ])

    logger.info("Booking confirmed after successful payment", { bookingId: payment.bookingId })
  } catch (error) {
    logger.error("Error processing payment success", {
      error,
      paymentIntentId,
    })
  }
}

// Handle failed payment
async function handlePaymentFailed(paymentIntent: any) {
  const paymentIntentId = paymentIntent.id

  logger.info("Payment failed", {
    paymentIntentId,
    error: paymentIntent.last_payment_error,
  })

  try {
    // Find the payment in the database
    const payment = await prisma.payment.findUnique({
      where: { paymentIntentId },
    })

    if (!payment) {
      logger.error("Payment not found in database", { paymentIntentId })
      return
    }

    // Update payment and booking status in a transaction
    await prisma.$transaction([
      // Update payment status
      prisma.payment.update({
        where: { id: payment.id },
        data: { status: "failed" },
      }),

      // Update booking status
      prisma.booking.update({
        where: { id: payment.bookingId },
        data: { status: "payment_failed" },
      }),
    ])

    logger.info("Booking marked as payment failed", { bookingId: payment.bookingId })
  } catch (error) {
    logger.error("Error processing payment failure", {
      error,
      paymentIntentId,
    })
  }
}

// Handle canceled payment
async function handlePaymentCanceled(paymentIntent: any) {
  const paymentIntentId = paymentIntent.id

  logger.info("Payment canceled", {
    paymentIntentId,
  })

  try {
    // Find the payment in the database
    const payment = await prisma.payment.findUnique({
      where: { paymentIntentId },
    })

    if (!payment) {
      logger.error("Payment not found in database", { paymentIntentId })
      return
    }

    // Update payment and booking status in a transaction
    await prisma.$transaction([
      // Update payment status
      prisma.payment.update({
        where: { id: payment.id },
        data: { status: "canceled" },
      }),

      // Update booking status
      prisma.booking.update({
        where: { id: payment.bookingId },
        data: { status: "pending" },
      }),
    ])

    logger.info("Booking returned to pending status after payment cancellation", { bookingId: payment.bookingId })
  } catch (error) {
    logger.error("Error processing payment cancellation", {
      error,
      paymentIntentId,
    })
  }
}

