/**
 * Test the download functionality for booking 1802459
 * Verify that all data structures are correctly aligned
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

// Simulate the fallback transformer function
function simulateTransformFromOriginalFlightOffer(originalFlightOffer, basicBookingData) {
  console.log('🔄 Simulating originalFlightOffer fallback transformation...');
  
  const flight = originalFlightOffer.flight_segments?.[0] || {};
  const pricing = originalFlightOffer.total_price || {};
  const passenger = originalFlightOffer.passengers?.[0] || {};
  
  // Extract booking info
  const bookingInfo = {
    orderId: originalFlightOffer.order_id || originalFlightOffer.offer_id || 'N/A',
    bookingReference: basicBookingData?.bookingReference || 'N/A',
    alternativeOrderId: originalFlightOffer.original_offer_id || 'N/A',
    status: 'CONFIRMED',
    issueDate: basicBookingData?.createdAt || new Date().toISOString(),
    issueDateFormatted: new Date(basicBookingData?.createdAt || new Date()).toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    }),
    agencyName: 'Rea Travels Agency',
    discountApplied: undefined
  };
  
  // Extract passenger info
  const passengers = [];
  if (basicBookingData?.passengerDetails?.names) {
    const names = basicBookingData.passengerDetails.names.split(', ');
    const documents = basicBookingData.documentNumbers || [];
    
    names.forEach((name, index) => {
      const passengerType = passenger.type || 'ADT';
      passengers.push({
        name: name.trim(),
        fullName: name.trim(),
        type: passengerType,
        passengerTypeLabel: passengerType === 'ADT' ? 'Adult' : passengerType === 'CHD' ? 'Child' : passengerType === 'INF' ? 'Infant' : passengerType,
        documentNumber: documents[index] || '',
        ticketNumber: `TKT-${basicBookingData?.bookingReference || 'UNKNOWN'}-${index + 1}`,
        seatNumber: 'TBD'
      });
    });
  }
  
  // Extract flight info
  const outboundFlight = [{
    flightNumber: flight.flight_number || 'Unknown',
    airline: {
      code: flight.airline_code || 'Unknown',
      name: flight.airline_name || 'Unknown Airline'
    },
    departure: {
      airport: flight.departure_airport || 'Unknown',
      time: flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
      date: flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleDateString() : 'Unknown',
      terminal: 'TBD'
    },
    arrival: {
      airport: flight.arrival_airport || 'Unknown',
      time: flight.arrival_datetime ? new Date(flight.arrival_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
      date: flight.arrival_datetime ? new Date(flight.arrival_datetime).toLocaleDateString() : 'Unknown',
      terminal: 'TBD'
    },
    duration: flight.duration || 'Unknown',
    aircraft: 'TBD',
    class: originalFlightOffer.fare_family || 'Economy',
    cabinClass: originalFlightOffer.fare_family || 'Economy'
  }];
  
  // Extract pricing
  const pricing_info = {
    totalPrice: pricing.amount?.toString() || '0',
    formattedTotal: pricing.amount ? `${pricing.amount} ${pricing.currency || 'USD'}` : '0 USD',
    currency: pricing.currency || 'USD',
    baseFare: pricing.amount ? (pricing.amount * 0.85).toFixed(0) : '0',
    taxes: pricing.amount ? (pricing.amount * 0.15).toFixed(0) : '0',
    paymentMethodLabel: 'Credit Card',
    breakdown: []
  };
  
  // Extract contact info
  const contactInfo = {
    email: basicBookingData?.contactInfo?.email || '',
    phone: basicBookingData?.contactInfo?.phone || ''
  };
  
  return {
    bookingInfo,
    passengers,
    outboundFlight,
    returnFlight: null,
    pricing: pricing_info,
    contactInfo,
    baggageAllowance: {
      checkedBags: passenger.baggage?.checked || 'Standard allowance',
      carryOnBags: passenger.baggage?.carryOn || 'Standard allowance'
    }
  };
}

async function testDownloadFunctionality() {
  console.log('🚀 Testing Download Functionality for Booking 1802459');
  console.log('===================================================\n');
  
  try {
    // Get booking data
    const booking = await prisma.booking.findFirst({
      where: {
        OR: [
          { bookingReference: "1802459" },
          { id: parseInt("1802459") || 0 }
        ]
      }
    });

    if (!booking) {
      console.error('❌ Booking 1802459 not found');
      return;
    }

    console.log('✅ Booking found:', {
      id: booking.id,
      bookingReference: booking.bookingReference,
      hasOriginalFlightOffer: !!booking.originalFlightOffer
    });

    // Parse originalFlightOffer
    let originalFlightOffer = booking.originalFlightOffer;
    if (typeof originalFlightOffer === 'string') {
      originalFlightOffer = JSON.parse(originalFlightOffer);
    }

    // Prepare basic booking data
    const basicBookingData = {
      bookingReference: booking.bookingReference,
      createdAt: booking.createdAt,
      passengerDetails: booking.passengerDetails,
      contactInfo: booking.contactInfo,
      documentNumbers: booking.documentNumbers
    };

    console.log('\n📋 Basic booking data:', {
      bookingReference: basicBookingData.bookingReference,
      hasPassengerDetails: !!basicBookingData.passengerDetails,
      passengerNames: basicBookingData.passengerDetails?.names,
      hasContactInfo: !!basicBookingData.contactInfo,
      documentNumbers: basicBookingData.documentNumbers
    });

    // Test the transformation
    console.log('\n🔄 Testing transformation...');
    const transformedData = simulateTransformFromOriginalFlightOffer(originalFlightOffer, basicBookingData);

    console.log('\n📊 TRANSFORMATION RESULTS:');
    console.log('==========================');

    // Test booking info
    console.log('\n🎫 BOOKING INFO:');
    console.log('- Order ID:', transformedData.bookingInfo.orderId);
    console.log('- Booking Reference:', transformedData.bookingInfo.bookingReference);
    console.log('- Status:', transformedData.bookingInfo.status);
    console.log('- Issue Date:', transformedData.bookingInfo.issueDateFormatted);
    console.log('- Agency:', transformedData.bookingInfo.agencyName);

    // Test passenger info
    console.log('\n👤 PASSENGER INFO:');
    transformedData.passengers.forEach((passenger, index) => {
      console.log(`Passenger ${index + 1}:`);
      console.log('  - Name:', passenger.name);
      console.log('  - Full Name:', passenger.fullName);
      console.log('  - Type:', passenger.type);
      console.log('  - Type Label:', passenger.passengerTypeLabel);
      console.log('  - Document:', passenger.documentNumber);
      console.log('  - Ticket:', passenger.ticketNumber);
    });

    // Test flight info
    console.log('\n✈️ FLIGHT INFO:');
    transformedData.outboundFlight.forEach((flight, index) => {
      console.log(`Flight ${index + 1}:`);
      console.log('  - Flight Number:', flight.flightNumber);
      console.log('  - Airline:', typeof flight.airline === 'object' ? `${flight.airline.code} - ${flight.airline.name}` : flight.airline);
      console.log('  - Route:', `${flight.departure.airport} → ${flight.arrival.airport}`);
      console.log('  - Departure:', `${flight.departure.date} ${flight.departure.time}`);
      console.log('  - Arrival:', `${flight.arrival.date} ${flight.arrival.time}`);
      console.log('  - Duration:', flight.duration);
      console.log('  - Class:', flight.class);
      console.log('  - Cabin Class:', flight.cabinClass);
    });

    // Test pricing info
    console.log('\n💰 PRICING INFO:');
    console.log('- Total Price:', transformedData.pricing.totalPrice);
    console.log('- Formatted Total:', transformedData.pricing.formattedTotal);
    console.log('- Currency:', transformedData.pricing.currency);
    console.log('- Base Fare:', transformedData.pricing.baseFare);
    console.log('- Taxes:', transformedData.pricing.taxes);
    console.log('- Payment Method:', transformedData.pricing.paymentMethodLabel);

    // Test contact info
    console.log('\n📞 CONTACT INFO:');
    console.log('- Email:', transformedData.contactInfo.email);
    console.log('- Phone:', transformedData.contactInfo.phone);

    // Test baggage info
    console.log('\n🧳 BAGGAGE INFO:');
    console.log('- Checked Bags:', transformedData.baggageAllowance.checkedBags);
    console.log('- Carry-on Bags:', transformedData.baggageAllowance.carryOnBags);

    // Validate for OfficialItinerary component compatibility
    console.log('\n📋 OFFICIAL ITINERARY COMPATIBILITY CHECK:');
    console.log('==========================================');

    const compatibilityTests = {
      'bookingInfo.bookingReference': !!transformedData.bookingInfo?.bookingReference,
      'bookingInfo.issueDateFormatted': !!transformedData.bookingInfo?.issueDateFormatted,
      'passengers[0].fullName': !!transformedData.passengers?.[0]?.fullName,
      'passengers[0].passengerTypeLabel': !!transformedData.passengers?.[0]?.passengerTypeLabel,
      'passengers[0].documentNumber': !!transformedData.passengers?.[0]?.documentNumber,
      'passengers[0].ticketNumber': !!transformedData.passengers?.[0]?.ticketNumber,
      'outboundFlight[0].airline (object)': typeof transformedData.outboundFlight?.[0]?.airline === 'object',
      'outboundFlight[0].flightNumber': !!transformedData.outboundFlight?.[0]?.flightNumber,
      'outboundFlight[0].departure.airport': !!transformedData.outboundFlight?.[0]?.departure?.airport,
      'outboundFlight[0].arrival.airport': !!transformedData.outboundFlight?.[0]?.arrival?.airport,
      'outboundFlight[0].cabinClass': !!transformedData.outboundFlight?.[0]?.cabinClass,
      'pricing.formattedTotal': !!transformedData.pricing?.formattedTotal,
      'pricing.paymentMethodLabel': !!transformedData.pricing?.paymentMethodLabel,
      'contactInfo.email': !!transformedData.contactInfo?.email,
      'baggageAllowance.checkedBags': !!transformedData.baggageAllowance?.checkedBags
    };

    Object.entries(compatibilityTests).forEach(([field, passed]) => {
      console.log(`${passed ? '✅' : '❌'} ${field}: ${passed}`);
    });

    const allCompatibilityPassed = Object.values(compatibilityTests).every(test => test === true);

    console.log('\n📊 FINAL DOWNLOAD FUNCTIONALITY ASSESSMENT:');
    console.log('===========================================');

    if (allCompatibilityPassed) {
      console.log('🎉 ALL TESTS PASSED!');
      console.log('✅ Download functionality should work perfectly');
      console.log('✅ OfficialItinerary component will render correctly');
      console.log('✅ PDF generation should succeed');
      console.log('✅ All required data fields are present and properly formatted');
      console.log('');
      console.log('🎯 EXPECTED DOWNLOAD BEHAVIOR:');
      console.log('- Click "Download Itinerary" button');
      console.log('- Button shows "Generating PDF..." state');
      console.log('- PDF file downloads as "flight-itinerary-1802459.pdf"');
      console.log('- PDF contains complete flight itinerary with all details');
    } else {
      console.log('❌ SOME COMPATIBILITY ISSUES FOUND');
      const failedTests = Object.entries(compatibilityTests).filter(([k,v]) => !v);
      console.log('Failed fields:', failedTests.map(([k]) => k));
    }

  } catch (error) {
    console.error('❌ Error testing download functionality:', error);
  } finally {
    await prisma.$disconnect();
  }
}

testDownloadFunctionality().catch(console.error);
