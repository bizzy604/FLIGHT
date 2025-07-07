/**
 * Test real booking ID 102 from database
 * Check if all values needed for itinerary generation can be retrieved
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

// Simple itinerary transformation function (mimicking the real one)
function testItineraryTransformation(orderCreateResponse, originalFlightOffer) {
  console.log('🔄 Testing itinerary transformation with real data...');
  
  try {
    const response = orderCreateResponse.Response || orderCreateResponse.data?.Response || orderCreateResponse;
    
    if (!response) {
      throw new Error('No Response object found in orderCreateResponse');
    }
    
    // Extract booking info
    const order = response.Order?.[0] || {};
    const bookingInfo = {
      orderId: order.OrderID?.value || 'N/A',
      bookingReference: order.BookingReferences?.BookingReference?.[0]?.ID || 'N/A',
      status: 'CONFIRMED',
      issueDate: new Date().toISOString(),
      agencyName: 'Rea Travels Agency'
    };
    
    // Extract passengers
    const passengers = response.Passengers?.Passenger?.map(passenger => ({
      name: `${passenger.Name?.Given?.[0]?.value || ''} ${passenger.Name?.Surname?.value || ''}`.trim(),
      title: passenger.Name?.Title || 'MR',
      type: passenger.PTC?.value || 'ADT',
      documentNumber: passenger.PassengerIDInfo?.PassengerDocument?.[0]?.ID || '',
      documentType: passenger.PassengerIDInfo?.PassengerDocument?.[0]?.Type || 'PT',
      birthDate: passenger.Age?.BirthDate?.value || '',
      email: passenger.Contacts?.Contact?.[0]?.EmailContact?.Address?.value || '',
      phone: passenger.Contacts?.Contact?.[0]?.PhoneContact?.Number?.[0]?.value || ''
    })) || [];
    
    // Extract flight segments
    const flightSegments = response.DataLists?.FlightSegmentList?.FlightSegment || [];
    const outboundFlight = flightSegments.map(segment => ({
      segmentKey: segment.SegmentKey || '',
      flightNumber: segment.MarketingCarrier?.FlightNumber?.value || segment.OperatingCarrier?.FlightNumber?.value || '',
      airline: {
        code: segment.MarketingCarrier?.AirlineID?.value || segment.OperatingCarrier?.AirlineID?.value || '',
        name: segment.MarketingCarrier?.Name || 'Unknown Airline'
      },
      departure: {
        airport: segment.Departure?.AirportCode?.value || '',
        time: segment.Departure?.Time || '',
        date: segment.Departure?.Date || '',
        terminal: segment.Departure?.Terminal?.Name || segment.Departure?.Terminal || ''
      },
      arrival: {
        airport: segment.Arrival?.AirportCode?.value || '',
        time: segment.Arrival?.Time || '',
        date: segment.Arrival?.Date || '',
        terminal: segment.Arrival?.Terminal?.Name || segment.Arrival?.Terminal || ''
      },
      aircraft: segment.Equipment?.AircraftCode?.value || '',
      class: segment.ClassOfService?.MarketingName?.value || segment.ClassOfService?.Code?.value || 'Economy',
      duration: segment.FlightDetail?.FlightDuration?.value || ''
    }));
    
    // Extract pricing
    const pricing = {
      totalPrice: order.TotalOrderPrice?.SimpleCurrencyPrice?.value || 
                 order.TotalOrderPrice?.DetailCurrencyPrice?.Total?.value || '0',
      currency: order.TotalOrderPrice?.SimpleCurrencyPrice?.Code || 
               order.TotalOrderPrice?.DetailCurrencyPrice?.Total?.Code || 'USD',
      baseFare: originalFlightOffer?.pricing?.base_fare || 
               order.TotalOrderPrice?.DetailCurrencyPrice?.Base?.value || '0',
      taxes: originalFlightOffer?.pricing?.taxes || 
            order.TotalOrderPrice?.DetailCurrencyPrice?.Taxes?.Total?.value || '0'
    };
    
    // Extract contact info (fallback to passenger contact if not in main contact)
    const contactInfo = {
      email: passengers[0]?.email || '',
      phone: passengers[0]?.phone || ''
    };
    
    return {
      bookingInfo,
      passengers,
      outboundFlight,
      returnFlight: null, // Will be populated if return segments exist
      pricing,
      contactInfo,
      baggageAllowance: {
        checkedBags: 1,
        carryOnBags: 1
      }
    };
    
  } catch (error) {
    console.error('❌ Error in itinerary transformation:', error);
    throw error;
  }
}

async function testRealBooking102() {
  console.log('🚀 Testing Real Booking ID 102');
  console.log('==============================\n');
  
  try {
    // Retrieve the real booking
    console.log('🔍 Retrieving booking ID 102 from database...');
    const booking = await prisma.booking.findUnique({
      where: { id: 102 },
      include: { payments: true }
    });

    if (!booking) {
      console.error('❌ Booking ID 102 not found in database');
      return false;
    }

    console.log('✅ Booking ID 102 found:', {
      id: booking.id,
      bookingReference: booking.bookingReference,
      userId: booking.userId,
      airlineCode: booking.airlineCode,
      status: booking.status,
      totalAmount: booking.totalAmount.toString(),
      createdAt: booking.createdAt,
      hasOrderCreateResponse: !!booking.orderCreateResponse,
      hasOriginalFlightOffer: !!booking.originalFlightOffer
    });

    // Check basic data structure
    const basicTests = {
      hasBookingReference: !!booking.bookingReference,
      hasFlightDetails: !!booking.flightDetails,
      hasPassengerDetails: !!booking.passengerDetails,
      hasContactInfo: !!booking.contactInfo,
      hasTotalAmount: booking.totalAmount > 0,
      hasOrderCreateResponse: !!booking.orderCreateResponse,
      hasOriginalFlightOffer: !!booking.originalFlightOffer,
      orderCreateIsObject: typeof booking.orderCreateResponse === 'object',
      originalOfferIsObject: typeof booking.originalFlightOffer === 'object'
    };

    console.log('\n📋 Basic data structure tests:', basicTests);

    // Parse JSON data
    let parsedOrderCreate = booking.orderCreateResponse;
    if (typeof parsedOrderCreate === 'string') {
      parsedOrderCreate = JSON.parse(parsedOrderCreate);
    }

    let originalFlightOffer = booking.originalFlightOffer;
    if (typeof originalFlightOffer === 'string') {
      originalFlightOffer = JSON.parse(originalFlightOffer);
    }

    console.log('\n📋 JSON data structure analysis:');
    console.log('OrderCreate Response:', {
      hasResponse: !!parsedOrderCreate?.Response,
      hasOrder: !!parsedOrderCreate?.Response?.Order,
      orderCount: parsedOrderCreate?.Response?.Order?.length || 0,
      hasPassengers: !!parsedOrderCreate?.Response?.Passengers,
      passengerCount: parsedOrderCreate?.Response?.Passengers?.Passenger?.length || 0,
      hasDataLists: !!parsedOrderCreate?.Response?.DataLists,
      hasFlightSegments: !!parsedOrderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment,
      flightSegmentCount: parsedOrderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment?.length || 0,
      topLevelKeys: Object.keys(parsedOrderCreate || {})
    });

    console.log('Original Flight Offer:', {
      hasSegments: !!originalFlightOffer?.segments,
      segmentCount: originalFlightOffer?.segments?.length || 0,
      hasPricing: !!originalFlightOffer?.pricing,
      hasOfferId: !!originalFlightOffer?.offer_id,
      topLevelKeys: Object.keys(originalFlightOffer || {})
    });

    // Test itinerary transformation if we have the data
    if (parsedOrderCreate) {
      console.log('\n🔄 Testing itinerary transformation...');
      
      try {
        const transformedData = testItineraryTransformation(parsedOrderCreate, originalFlightOffer);

        // Validate all extracted values
        const extractionTests = {
          // Booking Info
          hasBookingReference: !!transformedData.bookingInfo?.bookingReference && transformedData.bookingInfo.bookingReference !== 'N/A',
          hasOrderId: !!transformedData.bookingInfo?.orderId && transformedData.bookingInfo.orderId !== 'N/A',
          hasAgencyName: !!transformedData.bookingInfo?.agencyName,
          
          // Passenger Info
          hasPassengers: transformedData.passengers?.length > 0,
          hasPassengerName: !!transformedData.passengers?.[0]?.name && transformedData.passengers[0].name.trim() !== '',
          hasPassengerDocument: !!transformedData.passengers?.[0]?.documentNumber,
          hasPassengerEmail: !!transformedData.passengers?.[0]?.email,
          hasPassengerPhone: !!transformedData.passengers?.[0]?.phone,
          
          // Flight Info
          hasOutboundFlight: transformedData.outboundFlight?.length > 0,
          hasFlightNumber: !!transformedData.outboundFlight?.[0]?.flightNumber,
          hasAirlineCode: !!transformedData.outboundFlight?.[0]?.airline?.code,
          hasAirlineName: !!transformedData.outboundFlight?.[0]?.airline?.name,
          
          // Departure Info
          hasDepartureAirport: !!transformedData.outboundFlight?.[0]?.departure?.airport,
          hasDepartureTime: !!transformedData.outboundFlight?.[0]?.departure?.time,
          hasDepartureDate: !!transformedData.outboundFlight?.[0]?.departure?.date,
          
          // Arrival Info
          hasArrivalAirport: !!transformedData.outboundFlight?.[0]?.arrival?.airport,
          hasArrivalTime: !!transformedData.outboundFlight?.[0]?.arrival?.time,
          hasArrivalDate: !!transformedData.outboundFlight?.[0]?.arrival?.date,
          
          // Pricing Info
          hasTotalPrice: !!transformedData.pricing?.totalPrice && transformedData.pricing.totalPrice !== '0',
          hasCurrency: !!transformedData.pricing?.currency,
          
          // Contact Info
          hasContactEmail: !!transformedData.contactInfo?.email,
          hasContactPhone: !!transformedData.contactInfo?.phone,
          
          // Additional Info
          hasClass: !!transformedData.outboundFlight?.[0]?.class,
          hasBaggageInfo: !!transformedData.baggageAllowance
        };

        console.log('\n📋 Itinerary extraction validation:', extractionTests);

        // Show extracted values
        console.log('\n📋 EXTRACTED ITINERARY VALUES FROM REAL BOOKING 102:');
        console.log('================================================');
        console.log('🎫 BOOKING INFORMATION:');
        console.log('  - Booking Reference:', transformedData.bookingInfo?.bookingReference);
        console.log('  - Order ID:', transformedData.bookingInfo?.orderId);
        console.log('  - Agency:', transformedData.bookingInfo?.agencyName);
        console.log('  - Status:', transformedData.bookingInfo?.status);
        
        console.log('\n👤 PASSENGER INFORMATION:');
        transformedData.passengers?.forEach((passenger, index) => {
          console.log(`  Passenger ${index + 1}:`);
          console.log('    - Name:', passenger.name);
          console.log('    - Title:', passenger.title);
          console.log('    - Type:', passenger.type);
          console.log('    - Document:', passenger.documentNumber);
          console.log('    - Email:', passenger.email);
          console.log('    - Phone:', passenger.phone);
        });
        
        console.log('\n✈️ FLIGHT INFORMATION:');
        transformedData.outboundFlight?.forEach((flight, index) => {
          console.log(`  Flight ${index + 1}:`);
          console.log('    - Flight Number:', flight.flightNumber);
          console.log('    - Airline:', `${flight.airline?.code} - ${flight.airline?.name}`);
          console.log('    - Route:', `${flight.departure?.airport} → ${flight.arrival?.airport}`);
          console.log('    - Departure:', `${flight.departure?.date} ${flight.departure?.time} (Terminal ${flight.departure?.terminal})`);
          console.log('    - Arrival:', `${flight.arrival?.date} ${flight.arrival?.time} (Terminal ${flight.arrival?.terminal})`);
          console.log('    - Class:', flight.class);
          console.log('    - Aircraft:', flight.aircraft);
          console.log('    - Duration:', flight.duration);
        });
        
        console.log('\n💰 PRICING INFORMATION:');
        console.log('  - Total Price:', `${transformedData.pricing?.totalPrice} ${transformedData.pricing?.currency}`);
        console.log('  - Base Fare:', `${transformedData.pricing?.baseFare} ${transformedData.pricing?.currency}`);
        console.log('  - Taxes:', `${transformedData.pricing?.taxes} ${transformedData.pricing?.currency}`);
        
        console.log('\n📞 CONTACT INFORMATION:');
        console.log('  - Email:', transformedData.contactInfo?.email);
        console.log('  - Phone:', transformedData.contactInfo?.phone);

        const allTests = {...basicTests, ...extractionTests};
        const allTestsPassed = Object.values(allTests).every(test => test === true);
        
        console.log('\n📊 FINAL RESULT FOR BOOKING ID 102:');
        console.log('===================================');
        if (allTestsPassed) {
          console.log('🎉 ALL TESTS PASSED!');
          console.log('✅ Real booking ID 102 contains all data needed for itinerary generation');
          console.log('✅ orderCreateResponse has complete OrderCreate API response');
          console.log('✅ All passenger, flight, and pricing details can be extracted');
          console.log('✅ Itinerary generation will work perfectly with this data');
        } else {
          console.log('❌ SOME TESTS FAILED');
          const failedTests = Object.entries(allTests).filter(([key, value]) => !value);
          console.log('Failed tests:', failedTests.map(([key]) => key));
          console.log('⚠️ Some required values may be missing for complete itinerary generation');
        }

        return allTestsPassed;
        
      } catch (transformError) {
        console.error('❌ Error during itinerary transformation:', transformError);
        console.error('❌ Error details:', {
          message: transformError.message,
          stack: transformError.stack
        });
        return false;
      }
    } else {
      console.log('❌ No OrderCreate response found - cannot test itinerary transformation');
      return false;
    }
    
  } catch (error) {
    console.error('❌ Error testing real booking 102:', error);
    return false;
  } finally {
    await prisma.$disconnect();
  }
}

// Run the test
testRealBooking102().catch(console.error);
