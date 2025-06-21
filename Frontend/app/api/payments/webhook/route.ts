import { type NextRequest, NextResponse } from "next/server"
import { prisma } from "@/utils/db"
import { handleApiError } from "@/utils/error-handler"
import { logger } from "@/utils/logger"

// This endpoint handles payment webhooks from the payment gateway
export async function POST(request: NextRequest) {
  try {
    // Get the request body
    const payload = await request.json()
    
    // Log the incoming webhook for debugging
    logger.info('Received payment webhook', { event: payload })
    
    // Process the webhook based on the event type
    const eventType = payload.type || 'unknown'
    
    switch (eventType) {
      case 'payment.succeeded':
        await handlePaymentSucceeded(payload.data?.object || {})
        break
      case 'payment.failed':
        await handlePaymentFailed(payload.data?.object || {})
        break
      case 'payment.canceled':
        await handlePaymentCanceled(payload.data?.object || {})
        break
      default:
        logger.info(`Unhandled webhook event type: ${eventType}`)
    }

    return NextResponse.json({ received: true })
  } catch (error: any) {
    logger.error('Webhook error:', error)
    // Create a proper error object with the message
    const apiError = new Error('Failed to process webhook: ' + (error.message || 'Unknown error'))
    return handleApiError(apiError)
  }
}

// Handle successful payment
async function handlePaymentSucceeded(paymentData: any) {
  try {
    const { id: paymentId, metadata } = paymentData || {}
    const { bookingId } = metadata || {}

    if (!bookingId) {
      logger.warn('Payment succeeded but no bookingId in metadata', { paymentId })
      return
    }

    // Update the booking status to 'confirmed' and set the payment status
    // Type assertion to handle the model name mapping
    const updatedBooking = await (prisma as any).booking.update({
      where: { id: bookingId },
      data: {
        status: 'CONFIRMED',
        paymentStatus: 'PAID',
        paymentId,
        paymentDate: new Date(),
      },
      include: {
        passengers: true,
        flights: true,
      },
    })

    logger.info('Booking confirmed after successful payment', { 
      bookingId,
      paymentId,
      status: updatedBooking.status,
      paymentStatus: updatedBooking.paymentStatus 
    })

    // TODO: Send confirmation email to the customer
    // await sendConfirmationEmail(updatedBooking)

  } catch (error) {
    logger.error('Error handling successful payment:', error)
    // Don't throw here to prevent webhook retries for non-critical errors
  }
}

// Handle failed payment
async function handlePaymentFailed(paymentData: any) {
  try {
    const { id: paymentId, error, metadata } = paymentData || {}
    const { bookingId } = metadata || {}

    if (!bookingId) {
      logger.warn('Payment failed but no bookingId in metadata', { paymentId })
      return
    }

    // Update the booking status to reflect the payment failure
    await (prisma as any).booking.update({
      where: { id: bookingId },
      data: {
        status: 'PENDING',
        paymentStatus: 'FAILED',
        paymentId,
        paymentError: error?.message || 'Payment failed',
      },
    })

    logger.warn('Payment failed for booking', { 
      bookingId, 
      paymentId,
      error: error?.message 
    })

    // TODO: Send failure notification to the customer
    // await sendPaymentFailedEmail(bookingId, error?.message)
  } catch (error) {
    logger.error('Error handling failed payment:', error)
    // Don't throw here to prevent webhook retries for non-critical errors
  }
}

// Handle canceled payment
async function handlePaymentCanceled(paymentData: any) {
  try {
    const { id: paymentId, reason, metadata } = paymentData || {}
    const { bookingId } = metadata || {}

    if (!bookingId) {
      logger.error('Payment canceled but no bookingId in metadata', { paymentData })
      return
    }

    // Update the booking status to reflect the cancellation
    await (prisma as any).booking.update({
      where: { id: bookingId },
      data: {
        status: 'CANCELLED',
        paymentStatus: 'REFUNDED',
        paymentId,
        paymentError: reason || 'Payment was canceled',
      },
    })

    logger.info('Payment canceled for booking', { 
      bookingId, 
      paymentId,
      reason 
    })

    // TODO: Send cancellation email to the customer
    // await sendCancellationEmail(bookingId, reason)
  } catch (error) {
    logger.error('Error handling canceled payment:', error)
    // Don't throw here to prevent webhook retries for non-critical errors
  }
}
