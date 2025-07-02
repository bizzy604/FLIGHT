import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/utils/prisma';
import { auth } from '@clerk/nextjs/server';

export async function POST(request: NextRequest) {
  console.log('[[ DEBUG ]] Next.js /api/verteil/order-create route HIT'); // Added for debugging
  try {
    const body = await request.json();
    
    // DEBUG: Log request summary (without verbose content)
    console.log('[[ DEBUG ]] Frontend data received by Next.js API route');
    console.log('[[ DEBUG ]] Flight offer present:', !!body.flight_offer);
    console.log('[[ DEBUG ]] Passengers count:', body.passengers ? body.passengers.length : 0);
    console.log('[[ DEBUG ]] Payment method:', body.payment ? body.payment.method : 'None');
    console.log('[[ DEBUG ]] Contact info present:', !!body.contact_info);
    
    // Extract data from the request body (no transformation needed - backend handles it)
    const passengers = body.passengers;
    const payment = body.payment;
    const contact_info = body.contact_info;
    
    // Prepare backend request body with raw frontend data
    const backendRequestBody: {
      passengers: any;
      payment: any;
      contact_info: any;
      flight_price_response?: any;
      ShoppingResponseID?: string;
      OfferID?: string;
    } = {
      passengers: passengers,
      payment: payment,
      contact_info: contact_info
    };
    
    // Check if flight_offer contains raw_flight_price_response
    if (body.flight_offer && body.flight_offer.raw_flight_price_response) {
      console.log('[[ DEBUG ]] Using raw flight_price_response:', !!body.flight_offer.raw_flight_price_response);
      console.log('[[ DEBUG ]] Raw response keys:', Object.keys(body.flight_offer.raw_flight_price_response));
      backendRequestBody.flight_price_response = body.flight_offer.raw_flight_price_response;
    } else {
      console.log('[[ DEBUG ]] No raw flight price response found in flight_offer');
    }
    
    // Add ShoppingResponseID if available
    if (body.flight_offer && body.flight_offer.shopping_response_id) {
      console.log('[[ DEBUG ]] Using ShoppingResponseID:', body.flight_offer.shopping_response_id);
      backendRequestBody.ShoppingResponseID = body.flight_offer.shopping_response_id;
    } else {
      console.log('[[ DEBUG ]] No shopping_response_id found in flight_offer');
    }
    
    // Add OfferID if available - try both offer_id and order_id
    if (body.flight_offer && (body.flight_offer.offer_id || body.flight_offer.order_id)) {
      const offerId = body.flight_offer.offer_id || body.flight_offer.order_id;
      console.log('[[ DEBUG ]] Using OfferID:', offerId);
      backendRequestBody.OfferID = offerId;
    } else {
      console.log('[[ DEBUG ]] No offer_id or order_id found in flight_offer');
    }
    
    console.log('[[ DEBUG ]] Backend request body:', JSON.stringify(backendRequestBody, null, 2));
    
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';
    console.log('[[ DEBUG ]] Forwarding to backend URL:', `${backendUrl}/api/verteil/order-create`);
    
    const response = await fetch(`${backendUrl}/api/verteil/order-create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendRequestBody),
    });
    
    const data = await response.json();
    
    // DEBUG: Log the response from backend
    console.log('[[ DEBUG ]] Backend response status:', response.status);
    console.log('[[ DEBUG ]] Backend response data:', JSON.stringify(data, null, 2));
    
    // Store booking data in database if successful
    let dbBookingId = null;
    if (response.status === 200 && data.status === 'success' && data.data) {
      try {
        const { userId } = await auth();
        const bookingData = data.data;
        
        // Extract flight details from the original flight offer
         const flightOffer = body.flight_offer;
         const passengers = body.passengers || [];
         const contactInfo = body.contact_info || {};
         const paymentInfo = body.payment || {};
         
         // Extract the priced offer from nested structure
         const pricedOffer = flightOffer?.data?.data?.priced_offers?.[0] || flightOffer;
         const flightSegments = flightOffer?.data?.data?.flight_segments || flightOffer?.flight_segments || [];
         const segments = flightOffer?.segments || pricedOffer?.segments || [];
         const pricing = flightOffer?.data?.data?.pricing || flightOffer?.pricing || {};
         
         // Extract airline code from various possible paths
         const airlineCode = segments?.[0]?.airline?.code || 
                            flightSegments?.[0]?.airline?.code ||
                            pricedOffer?.airline?.code || 
                            flightOffer?.airline?.code || 'Unknown';
         
         // Extract flight numbers
         const outboundFlightNumber = segments?.[0]?.flightNumber || 
                                    flightSegments?.[0]?.flightNumber ||
                                    pricedOffer?.flightNumber || 
                                    flightOffer?.flightNumber || 'Unknown';
         
         const returnFlightNumber = segments?.[1]?.flightNumber || 
                                  flightSegments?.[1]?.flightNumber || null;
         
         // Extract route information
         const origin = segments?.[0]?.departure?.airport || 
                       flightSegments?.[0]?.departure?.airport ||
                       flightOffer?.departure?.airport || 
                       segments?.[0]?.origin || 'Unknown';
         
         const destination = segments?.[0]?.arrival?.airport || 
                            flightSegments?.[0]?.arrival?.airport ||
                            flightOffer?.arrival?.airport || 
                            segments?.[0]?.destination || 'Unknown';
         
         // Extract departure and arrival times
         const departureTime = segments?.[0]?.departure?.datetime || 
                              flightSegments?.[0]?.departure?.datetime ||
                              flightOffer?.departure?.datetime || 
                              segments?.[0]?.departureTime || new Date().toISOString();
         
         const arrivalTime = segments?.[0]?.arrival?.datetime || 
                            flightSegments?.[0]?.arrival?.datetime ||
                            flightOffer?.arrival?.datetime || 
                            segments?.[0]?.arrivalTime || new Date().toISOString();
         
         // Extract passenger information
         const passengerNames = passengers.map((p: any) => `${p.firstName || ''} ${p.lastName || ''}`).join(', ');
         const passengerTypes = passengers.map((p: any) => p.type || 'ADT');
         const documentNumbers = passengers.map((p: any) => p.documentNumber || '').filter((d: string) => d);
         
         // Extract class and cabin information
         const classOfService = segments?.[0]?.class || 
                               pricedOffer?.class || 
                               flightOffer?.class || 'Economy';
         
         const cabinClass = segments?.[0]?.cabin || 
                           pricedOffer?.cabin || 
                           flightOffer?.cabin || 'Economy';
         
         // Extract total amount from pricing structure
         const totalAmount = parseFloat(
           pricing?.total_price_per_traveler || 
           pricing?.total_price || 
           flightOffer?.totalPrice || 
           flightOffer?.price || 
           '0'
         );
         
         // Extract currency
         const currency = pricing?.currency || flightOffer?.currency || 'USD';
        
        // Create booking record in database
        const dbBooking = await prisma.booking.create({
          data: {
            bookingReference: bookingData.bookingReference || bookingData.booking_reference,
            userId: userId || 'guest-user',
            airlineCode,
            flightNumbers: [outboundFlightNumber, returnFlightNumber].filter(Boolean),
            routeSegments: {
              origin,
              destination,
              departureTime,
              arrivalTime,
              segments: flightOffer?.segments || []
            },
            passengerTypes,
            documentNumbers,
            classOfService,
            cabinClass,
            flightDetails: {
              airlineCode,
              outboundFlightNumber,
              returnFlightNumber,
              origin,
              destination,
              departureTime,
              arrivalTime,
              classOfService,
              cabinClass,
              segments: flightOffer?.segments || []
            },
            passengerDetails: {
              names: passengerNames,
              types: passengerTypes,
              documents: documentNumbers
            },
            contactInfo: {
              email: contactInfo.email || '',
              phone: contactInfo.phone || ''
            },
            totalAmount,
            status: 'confirmed'
          }
        });
        
        dbBookingId = dbBooking.id;
        console.log('[[ DEBUG ]] Booking stored in database with ID:', dbBookingId);
        
        // Create payment record if payment info exists
        if (paymentInfo.method && paymentInfo.method !== 'CASH') {
          await prisma.payment.create({
            data: {
              bookingId: dbBooking.id,
              amount: totalAmount,
              currency,
              status: 'completed',
              paymentMethod: paymentInfo.method,
              paymentIntentId: `pi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            }
          });
          console.log('[[ DEBUG ]] Payment record created for booking:', dbBooking.id);
        }
        
      } catch (dbError) {
        console.error('[[ DEBUG ]] Error storing booking in database:', dbError);
        // Don't fail the entire request if database storage fails
      }
    }
    
    // Add debug info to response for frontend visibility
    const responseWithDebug = {
      ...data,
      debug_info: {
        nextjs_route_hit: true,
        flight_offer_received: !!body.flight_offer,
        raw_flight_price_response_found: !!(body.flight_offer && body.flight_offer.raw_flight_price_response),
        flight_offer_keys: body.flight_offer ? Object.keys(body.flight_offer) : [],
        backend_request_had_flight_price_response: !!backendRequestBody.flight_price_response,
        backend_url: `${backendUrl}/api/verteil/order-create`,
        backend_status: response.status,
        db_booking_stored: !!dbBookingId,
        db_booking_id: dbBookingId
      }
    };
    
    console.log('[[ DEBUG ]] Response with debug info:', JSON.stringify(responseWithDebug, null, 2));
    
    return NextResponse.json(responseWithDebug, { status: response.status });
  } catch (error) {
    console.error('Error forwarding order-create request:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        debug_info: {
          nextjs_route_hit: true,
          error_occurred: true,
          error_message: error instanceof Error ? error.message : 'Unknown error'
        }
      },
      { status: 500 }
    );
  }
}

// Force recompilation - timestamp: 2025-06-18 00:25:33