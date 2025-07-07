import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/utils/prisma';
import { auth } from '@clerk/nextjs/server';

// Simplified extraction function that focuses on essential database fields
// The complete data is stored in orderCreateResponse and originalFlightOffer JSON columns
function extractEssentialFieldsForDatabase(backendResponse: any, rawOrderCreateResponse: any, flightOffer: any = {}, passengers: any[] = []) {
  console.log('🔍 Extracting essential fields for database indexing...');

  try {
    // Priority 1: Use backend-processed data (already transformed and clean)
    if (backendResponse?.bookingReference && backendResponse?.flightDetails) {
      console.log('✅ Using backend-processed data structure');

      const outboundFlight = backendResponse.flightDetails?.outbound;
      const returnFlight = backendResponse.flightDetails?.return;

      return {
        bookingReference: backendResponse.bookingReference,
        airlineCode: outboundFlight?.airline?.code || 'Unknown',
        flightNumbers: [
          outboundFlight?.airline?.flightNumber,
          returnFlight?.airline?.flightNumber
        ].filter(Boolean),
        routeSegments: {
          origin: outboundFlight?.departure?.code || 'Unknown',
          destination: outboundFlight?.arrival?.code || 'Unknown',
          departureTime: outboundFlight?.departure?.fullDate || new Date().toISOString(),
          arrivalTime: outboundFlight?.arrival?.fullDate || new Date().toISOString(),
          segments: [outboundFlight, returnFlight].filter(Boolean)
        },
        passengerTypes: backendResponse.passengers?.map((p: any) =>
          p.type === 'adult' ? 'ADT' : p.type === 'child' ? 'CHD' : 'INF'
        ) || ['ADT'],
        documentNumbers: backendResponse.passengers?.map((p: any) => p.documentNumber).filter(Boolean) || [],
        classOfService: outboundFlight?.classOfService || 'Economy',
        cabinClass: outboundFlight?.cabinClass || 'Economy',
        orderItemId: backendResponse.order_id || null,
        totalAmount: backendResponse.pricing?.total?.amount || 0,
        currency: backendResponse.pricing?.total?.currency || 'USD'
      };
    }

    // Priority 2: Try to extract from raw OrderCreate response if available
    if (rawOrderCreateResponse) {
      console.log('✅ Attempting extraction from raw OrderCreate response');
      return extractFromRawOrderCreate(rawOrderCreateResponse, flightOffer, passengers);
    }

    // Priority 3: Fallback to flight offer data
    console.log('⚠️ Using fallback extraction from flight offer data');
    return extractFallbackData(flightOffer, passengers);

  } catch (error) {
    console.error('❌ Error in essential fields extraction:', error);
    return extractFallbackData(flightOffer, passengers);
  }
}

// Extract essential fields from raw OrderCreate response
function extractFromRawOrderCreate(rawOrderCreateResponse: any, flightOffer: any, passengers: any[]) {
  try {
    const response = rawOrderCreateResponse.Response || rawOrderCreateResponse.data?.Response || rawOrderCreateResponse;

    if (!response?.Order?.[0]) {
      console.warn('⚠️ Invalid raw OrderCreate response structure');
      return extractFallbackData(flightOffer, passengers);
    }

    const firstOrder = response.Order[0];
    const flightSegments = response.DataLists?.FlightSegmentList?.FlightSegment || [];
    const firstSegment = flightSegments[0];

    // Extract booking reference
    let bookingReference = 'Unknown';
    if (firstOrder.BookingReferences?.BookingReference?.[0]?.ID) {
      bookingReference = firstOrder.BookingReferences.BookingReference[0].ID;
    } else if (firstOrder.OrderID?.value) {
      bookingReference = firstOrder.OrderID.value;
    }

    // Extract basic flight info
    const airlineCode = firstSegment?.MarketingCarrier?.AirlineID?.value || 'Unknown';
    const flightNumbers = flightSegments.map((seg: any) =>
      seg.MarketingCarrier?.FlightNumber?.value || seg.OperatingCarrier?.FlightNumber?.value
    ).filter(Boolean);

    // Extract route info
    const origin = firstSegment?.Departure?.AirportCode?.value || 'Unknown';
    const destination = flightSegments[flightSegments.length - 1]?.Arrival?.AirportCode?.value || 'Unknown';

    // Extract passenger info
    const orderPassengers = response.Passengers?.Passenger || [];
    const passengerTypes = orderPassengers.map((p: any) => p.PTC?.value || 'ADT');
    const documentNumbers: string[] = [];
    orderPassengers.forEach((passenger: any) => {
      const docs = passenger.PassengerIDInfo?.PassengerDocument || [];
      docs.forEach((doc: any) => {
        if (doc.ID) documentNumbers.push(doc.ID);
      });
    });

    // Extract pricing
    const totalPriceBreakdown = firstOrder.TotalOrderPrice?.SimpleCurrencyPrice || {};
    const totalAmount = parseFloat(totalPriceBreakdown.value || '0');
    const currency = totalPriceBreakdown.Code || 'USD';

    return {
      bookingReference,
      airlineCode,
      flightNumbers,
      routeSegments: {
        origin,
        destination,
        departureTime: firstSegment?.Departure?.Date || new Date().toISOString(),
        arrivalTime: flightSegments[flightSegments.length - 1]?.Arrival?.Date || new Date().toISOString(),
        segments: flightSegments
      },
      passengerTypes,
      documentNumbers,
      classOfService: firstSegment?.ClassOfService?.Code?.value || 'Economy',
      cabinClass: 'Economy',
      orderItemId: firstOrder.OrderItems?.OrderItem?.[0]?.OrderItemID?.value || null,
      totalAmount,
      currency
    };
  } catch (error) {
    console.error('❌ Error extracting from raw OrderCreate response:', error);
    return extractFallbackData(flightOffer, passengers);
  }
}

// Fallback extraction function for when OrderCreate response is unavailable or invalid
function extractFallbackData(flightOffer: any = {}, passengers: any[] = []) {
  console.log('🔄 Using fallback extraction from flight offer data...');

  try {
    const segments = flightOffer?.segments || [];
    const pricedOffer = flightOffer?.data?.data?.priced_offers?.[0] || flightOffer;
    const flightSegments = flightOffer?.data?.data?.flight_segments || flightOffer?.flight_segments || [];
    const pricing = flightOffer?.data?.data?.pricing || flightOffer?.pricing || {};

    return {
      bookingReference: 'Unknown',
      airlineCode: segments?.[0]?.airline?.code ||
                  flightSegments?.[0]?.airline?.code ||
                  pricedOffer?.airline?.code ||
                  flightOffer?.airline?.code || 'Unknown',
      flightNumbers: [
        segments?.[0]?.flightNumber || flightSegments?.[0]?.flightNumber,
        segments?.[1]?.flightNumber || flightSegments?.[1]?.flightNumber
      ].filter(Boolean),
      routeSegments: {
        origin: segments?.[0]?.departure?.airport ||
               flightSegments?.[0]?.departure?.airport ||
               flightOffer?.departure?.airport || 'Unknown',
        destination: segments?.[0]?.arrival?.airport ||
                    flightSegments?.[0]?.arrival?.airport ||
                    flightOffer?.arrival?.airport || 'Unknown',
        departureTime: segments?.[0]?.departure?.datetime ||
                      flightSegments?.[0]?.departure?.datetime ||
                      flightOffer?.departure?.datetime || new Date().toISOString(),
        arrivalTime: segments?.[0]?.arrival?.datetime ||
                    flightSegments?.[0]?.arrival?.datetime ||
                    flightOffer?.arrival?.datetime || new Date().toISOString(),
        segments: segments.length > 0 ? segments : flightSegments || []
      },
      passengerTypes: passengers.map((p: any) => p.type || 'ADT'),
      documentNumbers: passengers.map((p: any) => p.documentNumber || '').filter((d: string) => d),
      classOfService: segments?.[0]?.class ||
                     pricedOffer?.class ||
                     flightOffer?.class || 'Economy',
      cabinClass: segments?.[0]?.cabin ||
                 pricedOffer?.cabin ||
                 flightOffer?.cabin || 'Economy',
      orderItemId: null,
      totalAmount: parseFloat(
        pricing?.total_price_per_traveler ||
        pricing?.total_price ||
        flightOffer?.totalPrice ||
        flightOffer?.price || '0'
      ),
      currency: pricing?.currency || flightOffer?.currency || 'USD'
    };
  } catch (error) {
    console.error('❌ Error in fallback extraction:', error);

    // Ultimate fallback with minimal data
    return {
      bookingReference: 'Unknown',
      airlineCode: 'Unknown',
      flightNumbers: [],
      routeSegments: {
        origin: 'Unknown',
        destination: 'Unknown',
        departureTime: new Date().toISOString(),
        arrivalTime: new Date().toISOString(),
        segments: []
      },
      passengerTypes: passengers.map((p: any) => p.type || 'ADT'),
      documentNumbers: passengers.map((p: any) => p.documentNumber || '').filter((d: string) => d),
      classOfService: 'Economy',
      cabinClass: 'Economy',
      orderItemId: null,
      totalAmount: 0,
      currency: 'USD'
    };
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Extract data from the request body (no transformation needed - backend handles it)
    const passengers = body.passengers;
    const payment = body.payment;
    const contact_info = body.contact_info;
    const sessionId = body.session_id;

    // Prepare backend request body with raw frontend data
    const backendRequestBody: {
      passengers: any;
      payment: any;
      contact_info: any;
      flight_price_response?: any;
      ShoppingResponseID?: string;
      OfferID?: string;
      session_id?: string;
    } = {
      passengers: passengers,
      payment: payment,
      contact_info: contact_info,
      session_id: sessionId
    };
    
    // Simple approach: Send what we have to the backend, let it handle cache retrieval
    if (body.flight_offer && body.flight_offer.raw_flight_price_response) {
      // If we have the raw response, use it directly
      backendRequestBody.flight_price_response = body.flight_offer.raw_flight_price_response;
      console.log('✅ Using raw flight price response for order creation');
    } else if (body.flight_offer && body.flight_offer.metadata) {
      // If we have metadata with cache key, send it to backend for cache retrieval
      backendRequestBody.flight_price_response = { metadata: body.flight_offer.metadata };
      console.log('✅ Using metadata for backend cache retrieval');
    } else {
      console.warn('⚠️ No flight price response or metadata found in flight offer');
    }

    // Add ShoppingResponseID if available
    if (body.flight_offer && body.flight_offer.shopping_response_id) {
      backendRequestBody.ShoppingResponseID = body.flight_offer.shopping_response_id;
    }

    // Add OfferID if available - try both offer_id and order_id
    if (body.flight_offer && (body.flight_offer.offer_id || body.flight_offer.order_id)) {
      const offerId = body.flight_offer.offer_id || body.flight_offer.order_id;
      backendRequestBody.OfferID = offerId;
    }
    
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';
    
    const response = await fetch(`${backendUrl}/api/verteil/order-create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendRequestBody),
    });
    
    const data = await response.json();

    // Debug: Log basic structure (keep minimal logging for monitoring)
    console.log('🔍 Data received from backend:', {
      status: data.status,
      hasData: !!data.data,
      hasNestedData: !!data.data?.data,
      bookingReferenceFound: !!data.data?.data?.bookingReference,
      hasRawOrderCreateResponse: !!data.raw_order_create_response,
      rawOrderCreateResponseType: typeof data.raw_order_create_response,
      topLevelKeys: Object.keys(data)
    });

    // Additional debug for raw_order_create_response
    console.log('🔍 Raw OrderCreate Response Debug:', {
      available: !!data.raw_order_create_response,
      type: typeof data.raw_order_create_response,
      keys: data.raw_order_create_response ? Object.keys(data.raw_order_create_response) : null,
      sample: data.raw_order_create_response ? JSON.stringify(data.raw_order_create_response).substring(0, 200) : null
    });

    // Store booking data in database if successful
    let dbBookingId = null;
    let userId: string | null = null;
    let airlineCode: string = 'Unknown';
    let totalAmount: number = 0;
    let extractedBookingRef: string | null = null;

    if (response.status === 200 && data.status === 'success' && data.data) {
      try {
        const authResult = await auth();
        userId = authResult.userId;
        const bookingData = data.data;


        
        // Extract flight details from the original flight offer
         const flightOffer = body.flight_offer;
         const passengers = body.passengers || [];
         const contactInfo = body.contact_info || {};
         const paymentInfo = body.payment || {};
         
         // Extract essential fields for database indexing
         // Complete data is stored in orderCreateResponse and originalFlightOffer JSON columns
         const extractedData = extractEssentialFieldsForDatabase(bookingData, data.raw_order_create_response, flightOffer, passengers);

         console.log('🔍 Extracted data for database storage:', {
           bookingReference: extractedData.bookingReference,
           airlineCode: extractedData.airlineCode,
           totalAmount: extractedData.totalAmount,
           currency: extractedData.currency,
           flightNumbers: extractedData.flightNumbers
         });

         // Destructure extracted data
         const {
           bookingReference,
           flightNumbers,
           routeSegments,
           passengerTypes,
           documentNumbers,
           classOfService,
           cabinClass,
           orderItemId,
           currency
         } = extractedData;

         // Assign to outer scope variables for error logging
         airlineCode = extractedData.airlineCode;
         totalAmount = extractedData.totalAmount;

         // Extract passenger names from frontend data
         const passengerNames = passengers.map((p: any) => `${p.firstName || ''} ${p.lastName || ''}`).join(', ');

        // Extract booking reference from the actual API response
        // The backend already extracts and transforms the booking reference, so use that first



        // Priority 1: Use the already-transformed booking reference from backend
        // Handle the double-nested structure: data.data.data.bookingReference
        if (data.data?.data?.bookingReference && data.data.data.bookingReference !== 'Unknown') {
          extractedBookingRef = data.data.data.bookingReference;
          console.log('✅ Using backend-extracted booking reference from data.data.data:', extractedBookingRef);
        }
        // Priority 1b: Try single-nested structure data.data.bookingReference
        else if (data.data?.bookingReference && data.data.bookingReference !== 'Unknown') {
          extractedBookingRef = data.data.bookingReference;
          console.log('✅ Using backend-extracted booking reference from data.data:', extractedBookingRef);
        }
        // Priority 1c: Try bookingData (which is data.data)
        else if (bookingData?.bookingReference && bookingData.bookingReference !== 'Unknown') {
          extractedBookingRef = bookingData.bookingReference;
          console.log('✅ Using backend-extracted booking reference from bookingData:', extractedBookingRef);
        }
        // Priority 1d: Try bookingData.data.bookingReference (if bookingData has nested data)
        else if (bookingData?.data?.bookingReference && bookingData.data.bookingReference !== 'Unknown') {
          extractedBookingRef = bookingData.data.bookingReference;
          console.log('✅ Using backend-extracted booking reference from bookingData.data:', extractedBookingRef);
        }
        // Priority 2: Try to extract from raw OrderCreate response if backend didn't extract it
        else if (data.raw_order_create_response?.data?.Response?.Order?.[0]?.BookingReferences?.BookingReference?.[0]?.ID) {
          extractedBookingRef = data.raw_order_create_response.data.Response.Order[0].BookingReferences.BookingReference[0].ID;
          console.log('✅ Extracted booking reference from raw OrderCreate response (nested data):', extractedBookingRef);
        }
        // Priority 3: Try alternative raw response structure
        else if (data.raw_order_create_response?.Response?.Order?.[0]?.BookingReferences?.BookingReference?.[0]?.ID) {
          extractedBookingRef = data.raw_order_create_response.Response.Order[0].BookingReferences.BookingReference[0].ID;
          console.log('✅ Extracted booking reference from raw OrderCreate response (direct):', extractedBookingRef);
        }
        // Priority 4: Check if it's in the extractedData from the function
        else if (bookingReference && bookingReference !== 'Unknown') {
          extractedBookingRef = bookingReference;
          console.log('✅ Using booking reference from extraction function:', extractedBookingRef);
        }

        // Ensure we have a valid booking reference
        const finalBookingReference = extractedBookingRef && extractedBookingRef !== 'Unknown'
          ? extractedBookingRef
          : `BK${Date.now()}`; // Last resort fallback

        console.log('🔍 Booking reference values:', {
          extractedBookingRef,
          'bookingData.bookingReference': bookingData.bookingReference,
          'bookingData.booking_reference': bookingData.booking_reference,
          finalBookingReference
        });

        // Debug: Log what we're about to save to database
        console.log('💾 About to save to database:', {
          bookingReference: finalBookingReference,
          hasOrderCreateResponse: !!data.raw_order_create_response,
          orderCreateResponseType: typeof data.raw_order_create_response,
          orderCreateResponseSize: data.raw_order_create_response ? JSON.stringify(data.raw_order_create_response).length : 0
        });

        // Create booking record in database using the properly extracted data
        const dbBooking = await prisma.booking.create({
          data: {
            bookingReference: finalBookingReference,
            userId: userId || 'guest-user',
            airlineCode,
            flightNumbers,
            routeSegments,
            orderItemId,
            passengerTypes,
            documentNumbers,
            classOfService,
            cabinClass,
            // Store the complete backend-processed flight details structure
            flightDetails: bookingData.flightDetails || {
              outbound: null,
              return: null
            },
            // Store the complete backend-processed passenger details
            passengerDetails: {
              names: passengerNames,
              types: passengerTypes,
              documents: documentNumbers,
              // Include the complete passenger data from backend
              passengers: bookingData.passengers || []
            },
            // Store the complete backend-processed contact info
            contactInfo: bookingData.contactInfo || {
              email: contactInfo.email || '',
              phone: contactInfo.phone || ''
            },
            totalAmount,
            status: 'confirmed',
            // Store the raw NDC OrderCreate response for itinerary generation
            // Try multiple possible paths for the raw response
            orderCreateResponse: data.raw_order_create_response ||
                                data.data?.raw_order_create_response ||
                                data.rawOrderCreateResponse ||
                                null,
            // Store original flight offer for reference
            originalFlightOffer: flightOffer
          }
        });

        console.log('✅ Database booking created successfully:', {
          id: dbBooking.id,
          bookingReference: dbBooking.bookingReference,
          hasOrderCreateResponse: !!dbBooking.orderCreateResponse,
          hasFlightDetails: !!dbBooking.flightDetails,
          orderCreateResponseType: typeof dbBooking.orderCreateResponse
        });

        console.log('🔍 Raw OrderCreate response availability:', {
          hasRawResponse: !!data.raw_order_create_response,
          rawResponseType: typeof data.raw_order_create_response,
          rawResponseStructure: data.raw_order_create_response ? {
            hasResponse: !!(data.raw_order_create_response as any).Response,
            hasOrder: !!(data.raw_order_create_response as any).Response?.Order,
            topLevelKeys: Object.keys(data.raw_order_create_response as any)
          } : null
        });
        
        dbBookingId = dbBooking.id;

        // Create payment record if payment info exists
        if (paymentInfo.method && paymentInfo.method !== 'CASH') {
          await prisma.payment.create({
            data: {
              bookingId: dbBooking.id,
              amount: totalAmount,
              currency,
              status: 'completed',
              paymentMethod: paymentInfo.method,
              paymentIntentId: `pi_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`
            }
          });
        }

      } catch (dbError) {
        // Log the database error for debugging but don't fail the entire request
        console.error('❌ Database storage failed:', dbError);
        console.error('❌ Database error details:', {
          message: dbError instanceof Error ? dbError.message : 'Unknown error',
          stack: dbError instanceof Error ? dbError.stack : 'No stack trace',
          extractedData: {
            bookingReference: extractedBookingRef,
            airlineCode,
            totalAmount,
            userId: userId || 'guest-user'
          }
        });
      }
    }
    
    // Add debug info to response for frontend visibility
    const responseWithDebug = {
      ...data,
      // Include raw OrderCreate response for frontend session storage
      raw_order_create_response: data.raw_order_create_response,
      debug_info: {
        nextjs_route_hit: true,
        flight_offer_received: !!body.flight_offer,
        raw_flight_price_response_found: !!(body.flight_offer && body.flight_offer.raw_flight_price_response),
        flight_offer_keys: body.flight_offer ? Object.keys(body.flight_offer) : [],
        backend_request_had_flight_price_response: !!backendRequestBody.flight_price_response,
        backend_url: `${backendUrl}/api/verteil/order-create`,
        backend_status: response.status,
        db_booking_stored: !!dbBookingId,
        db_booking_id: dbBookingId,
        raw_order_create_response_available: !!data.raw_order_create_response
      }
    };
    
    return NextResponse.json(responseWithDebug, { status: response.status });
  } catch (error) {
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