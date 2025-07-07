/**
 * Test booking ID 86 for dual-column strategy validation
 * Test both originalFlightOffer (confirmation) and orderCreateResponse (itinerary)
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function testBooking86() {
  console.log('🚀 Testing Booking ID 86 - Dual Column Strategy Validation');
  console.log('==========================================================\n');
  
  try {
    // Get booking 86
    const booking = await prisma.booking.findUnique({
      where: { id: 86 },
      include: { payments: true }
    });

    if (!booking) {
      console.error('❌ Booking 86 not found');
      return;
    }

    console.log('📋 BOOKING 86 OVERVIEW:');
    console.log('======================');
    console.log('- ID:', booking.id);
    console.log('- Reference:', booking.bookingReference);
    console.log('- User ID:', booking.userId);
    console.log('- Status:', booking.status);
    console.log('- Total Amount:', booking.totalAmount.toString());
    console.log('- Created:', booking.createdAt);
    console.log('- Airline Code:', booking.airlineCode);
    console.log('- Flight Numbers:', booking.flightNumbers);
    console.log('- Passenger Types:', booking.passengerTypes);
    console.log('- Document Numbers:', booking.documentNumbers);

    console.log('\n📊 COLUMN AVAILABILITY CHECK:');
    console.log('=============================');
    console.log('- hasOrderCreateResponse:', !!booking.orderCreateResponse);
    console.log('- hasOriginalFlightOffer:', !!booking.originalFlightOffer);
    console.log('- orderCreateResponse type:', typeof booking.orderCreateResponse);
    console.log('- originalFlightOffer type:', typeof booking.originalFlightOffer);

    // Test 1: Payment Confirmation using originalFlightOffer
    console.log('\n🎫 TEST 1: PAYMENT CONFIRMATION (originalFlightOffer)');
    console.log('====================================================');
    
    if (booking.originalFlightOffer) {
      const offer = booking.originalFlightOffer;
      console.log('✅ originalFlightOffer found');
      console.log('Top-level keys:', Object.keys(offer));
      
      const flight = offer.flight_segments?.[0] || {};
      const pricing = offer.total_price || {};
      const passenger = offer.passengers?.[0] || {};
      const contact = booking.contactInfo || {};
      const passengerDetails = booking.passengerDetails || {};

      console.log('\n✈️ FLIGHT INFORMATION:');
      console.log('- Flight Number:', flight.flight_number);
      console.log('- Airline:', `${flight.airline_code} - ${flight.airline_name}`);
      console.log('- Route:', `${flight.departure_airport} → ${flight.arrival_airport}`);
      console.log('- Departure:', flight.departure_datetime);
      console.log('- Arrival:', flight.arrival_datetime);
      console.log('- Duration:', flight.duration);

      console.log('\n💰 PRICING INFORMATION:');
      console.log('- Total Amount:', pricing.amount);
      console.log('- Currency:', pricing.currency);

      console.log('\n👤 PASSENGER INFORMATION:');
      console.log('- Name:', passengerDetails.names);
      console.log('- Type:', passenger.type);
      console.log('- Count:', passenger.count);
      console.log('- Document:', booking.documentNumbers?.[0]);

      console.log('\n📞 CONTACT INFORMATION:');
      console.log('- Email:', contact.email);
      console.log('- Phone:', contact.phone);

      console.log('\n🧳 BAGGAGE & FARE INFO:');
      console.log('- Fare Family:', offer.fare_family);
      console.log('- Direction:', offer.direction);
      if (passenger.baggage) {
        console.log('- Carry-on:', passenger.baggage.carryOn);
        console.log('- Checked:', passenger.baggage.checked);
      }

      // Validation for confirmation page
      const confirmationTests = {
        hasBookingRef: !!booking.bookingReference,
        hasFlightNumber: !!flight.flight_number,
        hasAirline: !!flight.airline_code,
        hasRoute: !!flight.departure_airport && !!flight.arrival_airport,
        hasSchedule: !!flight.departure_datetime,
        hasPassenger: !!passengerDetails.names,
        hasPricing: !!pricing.amount && pricing.amount > 0,
        hasContact: !!contact.email
      };

      console.log('\n📊 CONFIRMATION PAGE VALIDATION:');
      Object.entries(confirmationTests).forEach(([test, passed]) => {
        console.log(`${passed ? '✅' : '❌'} ${test}: ${passed}`);
      });

      const confirmationPassed = Object.values(confirmationTests).every(test => test === true);
      console.log(`\n🎯 Confirmation Test Result: ${confirmationPassed ? '✅ PASSED' : '❌ FAILED'}`);

    } else {
      console.log('❌ No originalFlightOffer found');
    }

    // Test 2: Itinerary Generation using orderCreateResponse
    console.log('\n📄 TEST 2: ITINERARY GENERATION (orderCreateResponse)');
    console.log('===================================================');
    
    if (booking.orderCreateResponse) {
      console.log('✅ orderCreateResponse found');
      
      let parsedOrderCreate = booking.orderCreateResponse;
      if (typeof parsedOrderCreate === 'string') {
        parsedOrderCreate = JSON.parse(parsedOrderCreate);
      }

      const response = parsedOrderCreate.Response || parsedOrderCreate.data?.Response || parsedOrderCreate;
      
      if (response) {
        console.log('✅ Response object found');
        console.log('Response keys:', Object.keys(response));

        // Check structure
        const structureCheck = {
          hasOrder: !!response.Order,
          orderCount: response.Order?.length || 0,
          hasPassengers: !!response.Passengers,
          passengerCount: response.Passengers?.Passenger?.length || 0,
          hasDataLists: !!response.DataLists,
          hasFlightSegments: !!response.DataLists?.FlightSegmentList?.FlightSegment,
          flightSegmentCount: response.DataLists?.FlightSegmentList?.FlightSegment?.length || 0
        };

        console.log('\n📋 STRUCTURE CHECK:');
        Object.entries(structureCheck).forEach(([key, value]) => {
          console.log(`- ${key}: ${value}`);
        });

        // Extract key itinerary data
        if (response.Order?.[0]) {
          const order = response.Order[0];
          console.log('\n🎫 BOOKING INFORMATION:');
          console.log('- Booking Reference:', order.BookingReferences?.BookingReference?.[0]?.ID);
          console.log('- Order ID:', order.OrderID?.value);
          console.log('- Total Price:', order.TotalOrderPrice?.SimpleCurrencyPrice?.value, order.TotalOrderPrice?.SimpleCurrencyPrice?.Code);
        }

        if (response.Passengers?.Passenger?.[0]) {
          const passenger = response.Passengers.Passenger[0];
          console.log('\n👤 PASSENGER INFORMATION:');
          console.log('- Name:', `${passenger.Name?.Given?.[0]?.value} ${passenger.Name?.Surname?.value}`);
          console.log('- Type:', passenger.PTC?.value);
          console.log('- Document:', passenger.PassengerIDInfo?.PassengerDocument?.[0]?.ID);
          console.log('- Email:', passenger.Contacts?.Contact?.[0]?.EmailContact?.Address?.value);
          console.log('- Phone:', passenger.Contacts?.Contact?.[0]?.PhoneContact?.Number?.[0]?.value);
        }

        if (response.DataLists?.FlightSegmentList?.FlightSegment?.[0]) {
          const segment = response.DataLists.FlightSegmentList.FlightSegment[0];
          console.log('\n✈️ FLIGHT INFORMATION:');
          console.log('- Flight Number:', segment.MarketingCarrier?.FlightNumber?.value);
          console.log('- Airline:', segment.MarketingCarrier?.AirlineID?.value);
          console.log('- Route:', `${segment.Departure?.AirportCode?.value} → ${segment.Arrival?.AirportCode?.value}`);
          console.log('- Departure:', segment.Departure?.Date, segment.Departure?.Time);
          console.log('- Arrival:', segment.Arrival?.Date, segment.Arrival?.Time);
          console.log('- Class:', segment.ClassOfService?.MarketingName?.value);
        }

        // Validation for itinerary generation
        const itineraryTests = {
          hasBookingReference: !!response.Order?.[0]?.BookingReferences?.BookingReference?.[0]?.ID,
          hasOrderId: !!response.Order?.[0]?.OrderID?.value,
          hasPassengerName: !!response.Passengers?.Passenger?.[0]?.Name?.Given?.[0]?.value,
          hasPassengerDocument: !!response.Passengers?.Passenger?.[0]?.PassengerIDInfo?.PassengerDocument?.[0]?.ID,
          hasFlightNumber: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.MarketingCarrier?.FlightNumber?.value,
          hasAirlineCode: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.MarketingCarrier?.AirlineID?.value,
          hasDepartureAirport: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Departure?.AirportCode?.value,
          hasArrivalAirport: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Arrival?.AirportCode?.value,
          hasDepartureTime: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Departure?.Date,
          hasArrivalTime: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Arrival?.Date,
          hasTotalPrice: !!response.Order?.[0]?.TotalOrderPrice?.SimpleCurrencyPrice?.value,
          hasContactEmail: !!response.Passengers?.Passenger?.[0]?.Contacts?.Contact?.[0]?.EmailContact?.Address?.value
        };

        console.log('\n📊 ITINERARY GENERATION VALIDATION:');
        Object.entries(itineraryTests).forEach(([test, passed]) => {
          console.log(`${passed ? '✅' : '❌'} ${test}: ${passed}`);
        });

        const itineraryPassed = Object.values(itineraryTests).every(test => test === true);
        console.log(`\n🎯 Itinerary Test Result: ${itineraryPassed ? '✅ PASSED' : '❌ FAILED'}`);

      } else {
        console.log('❌ No valid Response object found in orderCreateResponse');
      }

    } else {
      console.log('❌ No orderCreateResponse found');
    }

    // Test 3: Compare data consistency between columns
    console.log('\n🔄 TEST 3: DATA CONSISTENCY CHECK');
    console.log('=================================');
    
    if (booking.originalFlightOffer && booking.orderCreateResponse) {
      console.log('✅ Both columns available - checking consistency');
      
      const offer = booking.originalFlightOffer;
      let orderCreate = booking.orderCreateResponse;
      if (typeof orderCreate === 'string') {
        orderCreate = JSON.parse(orderCreate);
      }
      
      const offerFlight = offer.flight_segments?.[0] || {};
      const orderResponse = orderCreate.Response || orderCreate.data?.Response || orderCreate;
      const orderSegment = orderResponse?.DataLists?.FlightSegmentList?.FlightSegment?.[0] || {};
      const orderOrder = orderResponse?.Order?.[0] || {};
      
      console.log('\n📊 CONSISTENCY COMPARISON:');
      console.log('- Flight Number:');
      console.log('  originalFlightOffer:', offerFlight.flight_number);
      console.log('  orderCreateResponse:', orderSegment.MarketingCarrier?.FlightNumber?.value);
      
      console.log('- Airline Code:');
      console.log('  originalFlightOffer:', offerFlight.airline_code);
      console.log('  orderCreateResponse:', orderSegment.MarketingCarrier?.AirlineID?.value);
      
      console.log('- Departure Airport:');
      console.log('  originalFlightOffer:', offerFlight.departure_airport);
      console.log('  orderCreateResponse:', orderSegment.Departure?.AirportCode?.value);
      
      console.log('- Arrival Airport:');
      console.log('  originalFlightOffer:', offerFlight.arrival_airport);
      console.log('  orderCreateResponse:', orderSegment.Arrival?.AirportCode?.value);
      
      console.log('- Booking Reference:');
      console.log('  database field:', booking.bookingReference);
      console.log('  orderCreateResponse:', orderOrder.BookingReferences?.BookingReference?.[0]?.ID);
      
    } else {
      console.log('⚠️ Cannot compare - one or both columns missing');
    }

    // Final summary
    console.log('\n📊 BOOKING 86 FINAL SUMMARY:');
    console.log('============================');
    console.log('✅ Booking exists and is accessible');
    console.log(`${booking.originalFlightOffer ? '✅' : '❌'} originalFlightOffer available for confirmation pages`);
    console.log(`${booking.orderCreateResponse ? '✅' : '❌'} orderCreateResponse available for itinerary generation`);
    
    if (booking.originalFlightOffer && booking.orderCreateResponse) {
      console.log('🎉 PERFECT: Both columns available - full dual-column strategy supported');
    } else if (booking.originalFlightOffer) {
      console.log('⚠️ PARTIAL: Only originalFlightOffer available - confirmation works, itinerary needs fallback');
    } else if (booking.orderCreateResponse) {
      console.log('⚠️ PARTIAL: Only orderCreateResponse available - itinerary works, confirmation needs extraction');
    } else {
      console.log('❌ ISSUE: Neither column available - both features need fallback');
    }

  } catch (error) {
    console.error('❌ Error testing booking 86:', error);
  } finally {
    await prisma.$disconnect();
  }
}

testBooking86().catch(console.error);
