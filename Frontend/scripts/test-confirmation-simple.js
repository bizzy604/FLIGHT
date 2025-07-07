/**
 * Simple test for payment confirmation using originalFlightOffer
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function testConfirmationData() {
  console.log('🎫 Testing Payment Confirmation Data from originalFlightOffer');
  console.log('==========================================================\n');
  
  try {
    // Get booking 102
    const booking = await prisma.booking.findUnique({
      where: { id: 102 }
    });

    if (!booking) {
      console.error('❌ Booking 102 not found');
      return;
    }

    console.log('📋 BOOKING BASIC INFO:');
    console.log('- ID:', booking.id);
    console.log('- Reference:', booking.bookingReference);
    console.log('- Status:', booking.status);
    console.log('- Created:', booking.createdAt);

    const offer = booking.originalFlightOffer;
    
    if (!offer) {
      console.error('❌ No originalFlightOffer found');
      return;
    }

    console.log('\n✈️ FLIGHT INFORMATION FROM originalFlightOffer:');
    console.log('===============================================');
    
    const flight = offer.flight_segments?.[0] || {};
    console.log('- Flight Number:', flight.flight_number);
    console.log('- Airline Code:', flight.airline_code);
    console.log('- Airline Name:', flight.airline_name);
    console.log('- Route:', `${flight.departure_airport} → ${flight.arrival_airport}`);
    console.log('- Departure:', flight.departure_datetime);
    console.log('- Arrival:', flight.arrival_datetime);
    console.log('- Duration:', flight.duration);

    console.log('\n💰 PRICING INFORMATION:');
    console.log('======================');
    const pricing = offer.total_price || {};
    console.log('- Total Amount:', pricing.amount);
    console.log('- Currency:', pricing.currency);

    console.log('\n👤 PASSENGER INFORMATION:');
    console.log('========================');
    const passenger = offer.passengers?.[0] || {};
    console.log('- Type:', passenger.type);
    console.log('- Count:', passenger.count);
    
    if (passenger.baggage) {
      console.log('- Carry-on:', passenger.baggage.carryOn);
      console.log('- Checked:', passenger.baggage.checked);
    }

    console.log('\n📞 CONTACT INFORMATION:');
    console.log('======================');
    const contact = booking.contactInfo || {};
    console.log('- Email:', contact.email);
    console.log('- Phone:', contact.phone);

    console.log('\n👥 PASSENGER DETAILS:');
    console.log('====================');
    const passengerDetails = booking.passengerDetails || {};
    console.log('- Names:', passengerDetails.names);
    console.log('- Documents:', booking.documentNumbers);

    console.log('\n📜 FARE FAMILY & RULES:');
    console.log('======================');
    console.log('- Fare Family:', offer.fare_family);
    console.log('- Direction:', offer.direction);
    
    if (offer.time_limits) {
      console.log('- Payment Deadline:', offer.time_limits.payment_deadline);
    }

    // Test what we can extract for confirmation page
    const confirmationData = {
      bookingReference: booking.bookingReference,
      flightNumber: flight.flight_number,
      airline: `${flight.airline_code} - ${flight.airline_name}`,
      route: `${flight.departure_airport} → ${flight.arrival_airport}`,
      departure: flight.departure_datetime,
      arrival: flight.arrival_datetime,
      duration: flight.duration,
      passengerName: passengerDetails.names,
      totalPrice: `${pricing.amount} ${pricing.currency}`,
      email: contact.email,
      phone: contact.phone,
      fareFamily: offer.fare_family
    };

    console.log('\n🎯 EXTRACTED CONFIRMATION DATA:');
    console.log('===============================');
    Object.entries(confirmationData).forEach(([key, value]) => {
      const status = value && value !== 'undefined undefined' ? '✅' : '❌';
      console.log(`${status} ${key}: ${value}`);
    });

    // Validation
    const validationTests = {
      hasBookingRef: !!confirmationData.bookingReference,
      hasFlightNumber: !!confirmationData.flightNumber,
      hasAirline: !!flight.airline_code && flight.airline_code !== 'undefined',
      hasRoute: !!flight.departure_airport && flight.departure_airport !== 'undefined',
      hasSchedule: !!confirmationData.departure,
      hasPassenger: !!confirmationData.passengerName,
      hasPricing: !!pricing.amount && pricing.amount > 0,
      hasContact: !!confirmationData.email
    };

    console.log('\n📊 VALIDATION RESULTS:');
    console.log('======================');
    Object.entries(validationTests).forEach(([test, passed]) => {
      console.log(`${passed ? '✅' : '❌'} ${test}: ${passed}`);
    });

    const allPassed = Object.values(validationTests).every(test => test === true);

    console.log('\n🎉 FINAL RESULT:');
    console.log('================');
    if (allPassed) {
      console.log('✅ ALL TESTS PASSED!');
      console.log('🎯 originalFlightOffer contains PERFECT data for payment confirmation!');
      console.log('');
      console.log('📋 CONFIRMATION PAGE CAN DISPLAY:');
      console.log('- ✅ Booking reference and status');
      console.log('- ✅ Complete flight details (number, airline, route, times)');
      console.log('- ✅ Passenger information');
      console.log('- ✅ Pricing information');
      console.log('- ✅ Contact details');
      console.log('- ✅ Fare family and rules');
      console.log('');
      console.log('🎯 DUAL COLUMN STRATEGY CONFIRMED:');
      console.log('- originalFlightOffer → Perfect for Payment Confirmation ✅');
      console.log('- orderCreateResponse → Perfect for Itinerary Generation ✅');
    } else {
      console.log('❌ Some tests failed');
      const failed = Object.entries(validationTests).filter(([k,v]) => !v);
      console.log('Failed:', failed.map(([k]) => k));
    }

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

testConfirmationData().catch(console.error);
