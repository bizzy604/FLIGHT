import { type NextRequest, NextResponse } from "next/server"
import { prisma } from "@/utils/db"
import { handleApiError } from "@/utils/error-handler"
import { logger } from "@/utils/logger"

// This endpoint handles payment webhooks from the payment gateway
export async function POST(request: NextRequest) {
  try {
    // Read raw body for signature verification
    const rawBody = await request.text()

    // Validate HMAC signature (shared secret set in env)
    const signature = request.headers.get('x-webhook-signature') || ''
    const timestamp = request.headers.get('x-webhook-timestamp') || ''
    const secret = process.env.WEBHOOK_SECRET || ''

    if (!secret) {
      logger.warn('WEBHOOK_SECRET is not configured; rejecting webhook for safety')
      return NextResponse.json({ error: 'Webhook not configured' }, { status: 500 })
    }

    const isValid = await verifyHmacSignature(secret, `${timestamp}.${rawBody}`, signature)
    if (!isValid) {
      logger.warn('Invalid webhook signature', { signatureProvided: !!signature, timestamp })
      return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
    }

    // Parse the verified JSON payload
    const payload = JSON.parse(rawBody)
    
    // Log the incoming webhook for debugging (sanitized)
    logger.info('Received payment webhook', { eventType: payload?.type })
    
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

async function verifyHmacSignature(secret: string, data: string, signatureHex: string): Promise<boolean> {
  try {
    // Expect hex-encoded HMAC-SHA256 signature
    const encoder = new TextEncoder()
    const keyData = encoder.encode(secret)
    const key = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    )

    const mac = await crypto.subtle.sign('HMAC', key, encoder.encode(data))
    const macHex = bufferToHex(mac)

    // Constant-time comparison
    return timingSafeEqual(macHex, signatureHex)
  } catch (e) {
    logger.error('HMAC verification failed', e)
    return false
  }
}

function bufferToHex(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let hex = ''
  for (let i = 0; i < bytes.length; i++) {
    const h = bytes[i].toString(16).padStart(2, '0')
    hex += h
  }
  return hex
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }
  return result === 0
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
