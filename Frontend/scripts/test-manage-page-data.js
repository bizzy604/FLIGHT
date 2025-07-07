/**
 * Test the data structure for the manage page
 * Check if booking 1802459 has the right data for download functionality
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function testManagePageData() {
  console.log('🔍 Testing Manage Page Data for Booking 1802459');
  console.log('===============================================\n');
  
  try {
    // Find booking by reference (same logic as the API)
    const booking = await prisma.booking.findFirst({
      where: {
        OR: [
          { bookingReference: "1802459" },
          { id: parseInt("1802459") || 0 }
        ]
      },
      include: {
        payments: true
      }
    });

    if (!booking) {
      console.error('❌ Booking 1802459 not found');
      return;
    }

    console.log('✅ Booking found:', {
      id: booking.id,
      bookingReference: booking.bookingReference,
      status: booking.status,
      totalAmount: booking.totalAmount.toString(),
      createdAt: booking.createdAt
    });

    console.log('\n📋 DATA STRUCTURE ANALYSIS:');
    console.log('===========================');
    console.log('- hasOrderCreateResponse:', !!booking.orderCreateResponse);
    console.log('- hasOriginalFlightOffer:', !!booking.originalFlightOffer);
    console.log('- orderCreateResponse type:', typeof booking.orderCreateResponse);
    console.log('- originalFlightOffer type:', typeof booking.originalFlightOffer);

    // Test what the manage page will receive
    const apiResponse = {
      ...booking,
      // Convert Decimal to string for JSON serialization (like the API does)
      totalAmount: booking.totalAmount.toString()
    };

    console.log('\n🔧 MANAGE PAGE SIMULATION:');
    console.log('==========================');

    // Simulate the manage page logic
    let parsedOrderCreate = apiResponse.orderCreateResponse;
    if (typeof parsedOrderCreate === 'string') {
      try {
        parsedOrderCreate = JSON.parse(parsedOrderCreate);
        console.log('✅ orderCreateResponse parsed successfully');
      } catch (parseError) {
        console.log('❌ orderCreateResponse parsing failed:', parseError.message);
        parsedOrderCreate = null;
      }
    }

    let originalFlightOffer = apiResponse.originalFlightOffer;
    if (typeof originalFlightOffer === 'string') {
      try {
        originalFlightOffer = JSON.parse(originalFlightOffer);
        console.log('✅ originalFlightOffer parsed successfully');
      } catch (parseError) {
        console.log('❌ originalFlightOffer parsing failed:', parseError.message);
        originalFlightOffer = null;
      }
    }

    console.log('\n📊 PARSED DATA AVAILABILITY:');
    console.log('============================');
    console.log('- parsedOrderCreate available:', !!parsedOrderCreate);
    console.log('- originalFlightOffer available:', !!originalFlightOffer);

    if (originalFlightOffer) {
      console.log('\n✈️ ORIGINAL FLIGHT OFFER STRUCTURE:');
      console.log('===================================');
      console.log('- Top-level keys:', Object.keys(originalFlightOffer));
      
      const flight = originalFlightOffer.flight_segments?.[0];
      if (flight) {
        console.log('- Flight Number:', flight.flight_number);
        console.log('- Airline:', `${flight.airline_code} - ${flight.airline_name}`);
        console.log('- Route:', `${flight.departure_airport} → ${flight.arrival_airport}`);
        console.log('- Departure:', flight.departure_datetime);
        console.log('- Arrival:', flight.arrival_datetime);
      }

      const pricing = originalFlightOffer.total_price;
      if (pricing) {
        console.log('- Total Price:', `${pricing.amount} ${pricing.currency}`);
      }
    }

    if (parsedOrderCreate) {
      console.log('\n📄 ORDER CREATE RESPONSE STRUCTURE:');
      console.log('===================================');
      console.log('- Top-level keys:', Object.keys(parsedOrderCreate));
      
      // Check for different possible paths
      const paths = {
        'direct Response': !!parsedOrderCreate.Response,
        'raw_order_create_response.Response': !!parsedOrderCreate.raw_order_create_response?.Response,
        'data.Response': !!parsedOrderCreate.data?.Response,
        'raw_order_create_response.data.Response': !!parsedOrderCreate.raw_order_create_response?.data?.Response
      };
      
      console.log('- Available NDC paths:');
      Object.entries(paths).forEach(([path, available]) => {
        console.log(`  ${available ? '✅' : '❌'} ${path}`);
      });
    }

    // Test basic booking data for fallback
    const basicBookingData = {
      bookingReference: apiResponse.bookingReference,
      createdAt: apiResponse.createdAt,
      passengerDetails: apiResponse.passengerDetails,
      contactInfo: apiResponse.contactInfo,
      documentNumbers: apiResponse.documentNumbers
    };

    console.log('\n👤 BASIC BOOKING DATA:');
    console.log('=====================');
    console.log('- Booking Reference:', basicBookingData.bookingReference);
    console.log('- Created At:', basicBookingData.createdAt);
    console.log('- Has Passenger Details:', !!basicBookingData.passengerDetails);
    console.log('- Has Contact Info:', !!basicBookingData.contactInfo);
    console.log('- Document Numbers:', basicBookingData.documentNumbers);

    if (basicBookingData.passengerDetails) {
      console.log('- Passenger Names:', basicBookingData.passengerDetails.names);
    }

    if (basicBookingData.contactInfo) {
      console.log('- Email:', basicBookingData.contactInfo.email);
      console.log('- Phone:', basicBookingData.contactInfo.phone);
    }

    console.log('\n📊 DOWNLOAD FUNCTIONALITY ASSESSMENT:');
    console.log('=====================================');

    const canTransformItinerary = !!(parsedOrderCreate || originalFlightOffer);
    const hasBasicData = !!(basicBookingData.bookingReference && basicBookingData.passengerDetails);

    console.log('✅ Can Transform Itinerary:', canTransformItinerary ? 'YES' : 'NO');
    console.log('✅ Has Basic Data:', hasBasicData ? 'YES' : 'NO');

    if (canTransformItinerary) {
      console.log('🎉 DOWNLOAD SHOULD WORK!');
      console.log('- Itinerary data can be generated');
      console.log('- PDF download functionality should be available');
      
      if (parsedOrderCreate) {
        console.log('- Using OrderCreate response for complete itinerary');
      } else {
        console.log('- Using originalFlightOffer fallback for basic itinerary');
      }
    } else {
      console.log('❌ DOWNLOAD WILL NOT WORK');
      console.log('- No itinerary data available');
      console.log('- Download button should be disabled');
    }

  } catch (error) {
    console.error('❌ Error testing manage page data:', error);
  } finally {
    await prisma.$disconnect();
  }
}

testManagePageData().catch(console.error);
