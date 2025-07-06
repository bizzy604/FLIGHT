import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/utils/prisma';
import { auth } from '@clerk/nextjs/server';

// Enhanced extraction function using OrderCreate response as primary source
function extractDatabaseFieldsFromOrderCreate(orderCreateResponse: any, flightOffer: any = {}, passengers: any[] = [], contactInfo: any = {}) {
  console.log('🔍 Starting OrderCreate response extraction...');

  try {
    // Validate input data
    if (!orderCreateResponse) {
      console.warn('⚠️ No OrderCreate response provided, falling back to flight offer data');
      return extractFallbackData(flightOffer, passengers);
    }

    const response = orderCreateResponse.Response || orderCreateResponse;

    // Validate response structure
    if (!response || typeof response !== 'object') {
      console.warn('⚠️ Invalid OrderCreate response structure, falling back to flight offer data');
      return extractFallbackData(flightOffer, passengers);
    }

    // Handle Order array structure with error handling
    let orders: any[] = [];
    try {
      orders = Array.isArray(response.Order) ? response.Order : [response.Order].filter(Boolean);
      if (orders.length === 0) {
        console.warn('⚠️ No valid orders found in OrderCreate response');
        return extractFallbackData(flightOffer, passengers);
      }
    } catch (error) {
      console.error('❌ Error processing Order structure:', error);
      return extractFallbackData(flightOffer, passengers);
    }

    const firstOrder = orders[0] || {};

    // Extract from OrderCreate response (primary source) with error handling
    let orderItems: any[] = [];
    let flightSegments: any[] = [];
    let firstSegment: any = null;

    try {
      orderItems = firstOrder.OrderItems?.OrderItem || [];
      const flightItem = orderItems.find((item: any) => item.FlightItem);
      const flightSegmentRefs = flightItem?.FlightItem?.FlightSegmentReference || [];

      // Get flight segments from DataLists
      flightSegments = response.DataLists?.FlightSegmentList?.FlightSegment || [];
      firstSegment = flightSegments[0];

      if (!firstSegment) {
        console.warn('⚠️ No flight segments found in OrderCreate response');
        return extractFallbackData(flightOffer, passengers);
      }
    } catch (error) {
      console.error('❌ Error extracting flight segments:', error);
      return extractFallbackData(flightOffer, passengers);
    }

    // Extract airline code with multiple fallback options
    let airlineCode = 'Unknown';
    try {
      airlineCode = firstSegment?.MarketingCarrier?.AirlineID?.value ||
                   firstSegment?.OperatingCarrier?.AirlineID?.value ||
                   flightSegments[0]?.MarketingCarrier?.AirlineID?.value ||
                   'Unknown';

      if (airlineCode === 'Unknown') {
        console.warn('⚠️ Could not extract airline code from OrderCreate response');
      } else {
        console.log('✅ Extracted airline code:', airlineCode);
      }
    } catch (error) {
      console.error('❌ Error extracting airline code:', error);
      airlineCode = 'Unknown';
    }

    // Extract flight numbers with error handling
    let flightNumbers: string[] = [];
    try {
      flightNumbers = flightSegments.map((segment: any) =>
        segment.MarketingCarrier?.FlightNumber?.value ||
        segment.OperatingCarrier?.FlightNumber?.value ||
        'Unknown'
      ).filter((fn: string) => fn !== 'Unknown');

      if (flightNumbers.length === 0) {
        console.warn('⚠️ No flight numbers found in OrderCreate response');
      } else {
        console.log('✅ Extracted flight numbers:', flightNumbers);
      }
    } catch (error) {
      console.error('❌ Error extracting flight numbers:', error);
      flightNumbers = [];
    }

    // Extract route information with error handling
    let origin = 'Unknown';
    let destination = 'Unknown';
    try {
      origin = firstSegment?.Departure?.AirportCode?.value || 'Unknown';
      destination = flightSegments[flightSegments.length - 1]?.Arrival?.AirportCode?.value || 'Unknown';

      if (origin === 'Unknown' || destination === 'Unknown') {
        console.warn('⚠️ Could not extract complete route information');
      } else {
        console.log('✅ Extracted route:', `${origin} → ${destination}`);
      }
    } catch (error) {
      console.error('❌ Error extracting route information:', error);
    }

    // Extract departure and arrival times with error handling
    let departureTime = new Date().toISOString();
    let arrivalTime = new Date().toISOString();
    try {
      departureTime = firstSegment?.Departure?.Date || firstSegment?.Departure?.Time || new Date().toISOString();
      arrivalTime = flightSegments[flightSegments.length - 1]?.Arrival?.Date ||
                   flightSegments[flightSegments.length - 1]?.Arrival?.Time ||
                   new Date().toISOString();

      console.log('✅ Extracted times:', { departureTime, arrivalTime });
    } catch (error) {
      console.error('❌ Error extracting flight times:', error);
    }

    // Extract passenger information from OrderCreate response with error handling
    let passengerTypes: string[] = [];
    let documentNumbers: string[] = [];
    try {
      const orderPassengers = response.Passengers?.Passenger || [];
      passengerTypes = orderPassengers.map((p: any) => p.PTC?.value || 'ADT');

      // Extract document numbers from PassengerDocument
      orderPassengers.forEach((passenger: any) => {
        try {
          const passengerDocs = passenger.PassengerIDInfo?.PassengerDocument || [];
          passengerDocs.forEach((doc: any) => {
            if (doc.ID) {
              documentNumbers.push(doc.ID);
            }
          });
        } catch (docError) {
          console.warn('⚠️ Error extracting document for passenger:', docError);
        }
      });

      console.log('✅ Extracted passenger data:', {
        passengerCount: passengerTypes.length,
        documentCount: documentNumbers.length
      });
    } catch (error) {
      console.error('❌ Error extracting passenger information:', error);
      passengerTypes = ['ADT']; // Default fallback
    }

    // Extract class of service from multiple sources (enhanced)
    let classOfService = 'Economy';
    let cabinClass = 'Economy';

    // Method 1: Extract from FlightSegment ClassOfService
    if (firstSegment?.ClassOfService) {
      const classInfo = firstSegment.ClassOfService;
      classOfService = classInfo.Code?.value || classInfo.MarketingName?.value || 'Economy';
      cabinClass = classInfo.MarketingName?.value || 'Economy';

      // Map cabin designator to readable names
      const cabinDesignator = classInfo.MarketingName?.CabinDesignator;
      if (cabinDesignator === 'C') {
        cabinClass = 'Business';
      } else if (cabinDesignator === 'F') {
        cabinClass = 'First';
      } else if (cabinDesignator === 'Y') {
        cabinClass = 'Economy';
      }
    }

    // Method 2: Fallback to fare basis codes if ClassOfService not available
    if (classOfService === 'Economy') {
      const fareComponents = response.DataLists?.FareList?.FareGroup?.[0]?.Fare?.[0]?.FareDetail?.[0]?.FareComponent || [];
      const fareBasisCode = fareComponents[0]?.FareBasisCode?.Code;
      if (fareBasisCode) {
        classOfService = fareBasisCode;
        // Determine cabin class from fare basis patterns
        if (fareBasisCode.includes('C') || fareBasisCode.includes('J') || fareBasisCode.includes('D')) {
          cabinClass = 'Business';
        } else if (fareBasisCode.includes('F') || fareBasisCode.includes('A')) {
          cabinClass = 'First';
        }
      }
    }

    // Method 3: Extract from PriceClassList if available
    const priceClassList = response.DataLists?.PriceClassList?.PriceClass || [];
    if (priceClassList.length > 0 && classOfService === 'Economy') {
      const priceClass = priceClassList[0];
      classOfService = priceClass.Name || 'Economy';
    }

    // Extract total amount from pricing with error handling
    let totalAmount = 0;
    let currency = 'USD';
    try {
      const totalPriceBreakdown = firstOrder.TotalOrderPrice?.SimpleCurrencyPrice ||
                                 response.TotalPrice?.DetailCurrencyPrice?.Total ||
                                 response.TotalPrice?.SimpleCurrencyPrice || {};
      totalAmount = parseFloat(totalPriceBreakdown.value || '0');
      currency = totalPriceBreakdown.Code || 'USD';

      if (totalAmount === 0) {
        console.warn('⚠️ Could not extract valid total amount from OrderCreate response');
      } else {
        console.log('✅ Extracted pricing:', { totalAmount, currency });
      }
    } catch (error) {
      console.error('❌ Error extracting pricing information:', error);
    }

    // Extract booking reference with error handling
    let bookingReference = 'Unknown';
    try {
      bookingReference = firstOrder.BookingReferences?.BookingReference?.[0]?.ID ||
                        firstOrder.OrderID?.value ||
                        'Unknown';

      if (bookingReference === 'Unknown') {
        console.warn('⚠️ Could not extract booking reference from OrderCreate response');
      } else {
        console.log('✅ Extracted booking reference:', bookingReference);
      }
    } catch (error) {
      console.error('❌ Error extracting booking reference:', error);
    }

    // Extract order item ID with error handling
    let orderItemId = null;
    try {
      orderItemId = orderItems[0]?.OrderItemID?.value || null;
      if (orderItemId) {
        console.log('✅ Extracted order item ID:', orderItemId);
      }
    } catch (error) {
      console.error('❌ Error extracting order item ID:', error);
    }

    return {
      bookingReference,
      airlineCode,
      flightNumbers,
      routeSegments: {
        origin,
        destination,
        departureTime,
        arrivalTime,
        segments: flightSegments.map((seg: any) => ({
          departure: seg.Departure,
          arrival: seg.Arrival,
          marketingCarrier: seg.MarketingCarrier,
          operatingCarrier: seg.OperatingCarrier
        }))
      },
      passengerTypes,
      documentNumbers,
      classOfService,
      cabinClass,
      orderItemId,
      totalAmount,
      currency
    };
  } catch (error) {
    console.error('❌ Critical error in OrderCreate response extraction:', error);
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

    // Debug: Log what we received
    console.log('🔍 Order creation request received:');
    console.log('- Has flight_offer:', !!body.flight_offer);
    console.log('- Has raw_flight_price_response:', !!(body.flight_offer?.raw_flight_price_response));
    console.log('- Has metadata:', !!(body.flight_offer?.metadata));
    console.log('- Flight offer keys:', body.flight_offer ? Object.keys(body.flight_offer) : 'none');
    
    // Get session ID from localStorage (sent by frontend)
    const sessionId = body.session_id || body.flight_offer?.session_id;
    console.log('🔍 Session ID for order creation:', sessionId);
    console.log('🔍 Full request body keys:', Object.keys(body));
    console.log('🔍 Flight offer keys:', body.flight_offer ? Object.keys(body.flight_offer) : 'none');

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
         
         // Extract data for database storage using OrderCreate response as primary source
         const extractedData = extractDatabaseFieldsFromOrderCreate(data.data, flightOffer, passengers, contactInfo);

         // Destructure extracted data
         const {
           bookingReference: extractedBookingRef,
           airlineCode,
           flightNumbers,
           routeSegments,
           passengerTypes,
           documentNumbers,
           classOfService,
           cabinClass,
           orderItemId,
           totalAmount,
           currency
         } = extractedData;

         // Extract flight numbers for backward compatibility
         const outboundFlightNumber = flightNumbers[0] || 'Unknown';
         const returnFlightNumber = flightNumbers[1] || null;

         // Extract route components for backward compatibility
         const origin = routeSegments.origin;
         const destination = routeSegments.destination;
         const departureTime = routeSegments.departureTime;
         const arrivalTime = routeSegments.arrivalTime;

         // Extract passenger names from frontend data
         const passengerNames = passengers.map((p: any) => `${p.firstName || ''} ${p.lastName || ''}`).join(', ');

        // Ensure we have a valid booking reference
        const finalBookingReference = extractedBookingRef && extractedBookingRef !== 'Unknown'
          ? extractedBookingRef
          : (bookingData.bookingReference || bookingData.booking_reference || `BK${Date.now()}`);

        console.log('🔍 Booking reference values:', {
          extractedBookingRef,
          'bookingData.bookingReference': bookingData.bookingReference,
          'bookingData.booking_reference': bookingData.booking_reference,
          finalBookingReference
        });

        // Create booking record in database
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
            status: 'confirmed',
            // Store the raw NDC OrderCreate response for itinerary generation
            orderCreateResponse: data.raw_order_create_response || data.data,
            // Store original flight offer for reference
            originalFlightOffer: flightOffer
          }
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
              paymentIntentId: `pi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            }
          });
        }

      } catch (dbError) {
        // Don't fail the entire request if database storage fails
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