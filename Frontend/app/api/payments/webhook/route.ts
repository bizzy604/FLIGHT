import { type NextRequest, NextResponse } from "next/server"
import { prisma } from "@/utils/db"
import { handleApiError } from "@/utils/error-handler"
import { logger } from "@/utils/logger"

/**
 * Next.js API route handler for processing payment gateway webhooks.
 *
 * Validates an HMAC-SHA256 webhook signature (expects `x-webhook-signature` and
 * `x-webhook-timestamp` headers and a `WEBHOOK_SECRET` environment variable),
 * parses the verified JSON payload, and routes events to the appropriate
 * handlers (e.g., `payment.succeeded`, `payment.failed`, `payment.canceled`).
 *
 * On successful processing returns a JSON response `{ received: true }`.
 * If the webhook secret is not configured, responds with 500; if the signature
 * is invalid, responds with 400. Any internal error is handled and returned via
 * the project's `handleApiError`.
 *
 * Note: this function reads the raw request body for signature verification
 * before parsing JSON and does not rethrow errors from individual event
 * handlers to avoid unnecessary webhook retries.
 *
 * @returns A NextResponse indicating processing result (JSON).
 */
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

/**
 * Verifies a hex-encoded HMAC-SHA256 signature for the given data using the provided secret.
 *
 * Computes an HMAC-SHA256 over `data` with `secret`, converts the result to hex, and performs
 * a constant-time comparison against `signatureHex`. Returns `true` if the signature matches;
 * returns `false` if it does not match or if verification fails (errors are caught and logged).
 *
 * @param secret - The HMAC secret key used to compute the MAC.
 * @param data - The exact string that was signed (must match what the sender used).
 * @param signatureHex - Expected signature encoded as a lowercase hex string.
 * @returns `true` when the signature is valid, otherwise `false`.
 */
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

/**
 * Convert an ArrayBuffer into a lowercase hexadecimal string.
 *
 * @param buffer - Binary data to encode.
 * @returns Hex-encoded string using two lowercase hex characters per byte (no `0x` prefix).
 */
function bufferToHex(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let hex = ''
  for (let i = 0; i < bytes.length; i++) {
    const h = bytes[i].toString(16).padStart(2, '0')
    hex += h
  }
  return hex
}

/**
 * Performs a constant-time comparison of two strings to prevent timing attacks.
 *
 * Returns `true` if both strings have the same length and identical contents; otherwise returns `false`.
 *
 * @param a - First string to compare.
 * @param b - Second string to compare.
 * @returns Whether `a` and `b` are equal.
 */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }
  return result === 0
}

/**
 * Process a successful payment webhook by marking the associated booking as paid and confirmed.
 *
 * Expects `paymentData` to include an `id` (payment identifier) and `metadata.bookingId`. If `bookingId`
 * is missing the function logs a warning and returns. On success it updates the booking record (status,
 * paymentStatus, paymentId, paymentDate) and logs the result. Errors are caught and logged and not rethrown
 * to avoid triggering webhook retries.
 *
 * @param paymentData - Webhook payment object containing at minimum `id` and `metadata.bookingId`
 */
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
