/**
 * Deep analysis of booking 86 orderCreateResponse structure
 * Check if raw_order_create_response contains the actual NDC data
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function deepAnalyzeBooking86() {
  console.log('🔍 Deep Analysis of Booking 86 orderCreateResponse');
  console.log('=================================================\n');
  
  try {
    const booking = await prisma.booking.findUnique({
      where: { id: 86 }
    });

    if (!booking?.orderCreateResponse) {
      console.error('❌ No orderCreateResponse found');
      return;
    }

    const orderCreateResponse = booking.orderCreateResponse;
    console.log('📋 orderCreateResponse structure:');
    console.log('Top-level keys:', Object.keys(orderCreateResponse));
    
    // Check each top-level field
    console.log('\n🔍 ANALYZING EACH FIELD:');
    console.log('========================');
    
    if (orderCreateResponse.data) {
      console.log('\n📄 DATA FIELD:');
      console.log('Type:', typeof orderCreateResponse.data);
      if (typeof orderCreateResponse.data === 'object') {
        console.log('Keys:', Object.keys(orderCreateResponse.data));
        console.log('Content preview:', JSON.stringify(orderCreateResponse.data, null, 2).substring(0, 500) + '...');
      }
    }
    
    if (orderCreateResponse.status) {
      console.log('\n📊 STATUS FIELD:');
      console.log('Value:', orderCreateResponse.status);
    }
    
    if (orderCreateResponse.request_id) {
      console.log('\n🆔 REQUEST_ID FIELD:');
      console.log('Value:', orderCreateResponse.request_id);
    }
    
    if (orderCreateResponse.raw_order_create_response) {
      console.log('\n🎯 RAW_ORDER_CREATE_RESPONSE FIELD:');
      console.log('Type:', typeof orderCreateResponse.raw_order_create_response);
      
      if (typeof orderCreateResponse.raw_order_create_response === 'object') {
        const rawResponse = orderCreateResponse.raw_order_create_response;
        console.log('Keys:', Object.keys(rawResponse));
        
        // Check if this has the NDC structure we need
        if (rawResponse.Response) {
          console.log('✅ Found Response object in raw_order_create_response!');
          console.log('Response keys:', Object.keys(rawResponse.Response));
          
          // Test NDC structure
          const response = rawResponse.Response;
          
          console.log('\n📋 NDC STRUCTURE CHECK:');
          console.log('- hasOrder:', !!response.Order);
          console.log('- orderCount:', response.Order?.length || 0);
          console.log('- hasPassengers:', !!response.Passengers);
          console.log('- passengerCount:', response.Passengers?.Passenger?.length || 0);
          console.log('- hasDataLists:', !!response.DataLists);
          console.log('- hasFlightSegments:', !!response.DataLists?.FlightSegmentList?.FlightSegment);
          console.log('- flightSegmentCount:', response.DataLists?.FlightSegmentList?.FlightSegment?.length || 0);
          
          // Try to extract key data
          if (response.Order?.[0]) {
            const order = response.Order[0];
            console.log('\n🎫 EXTRACTABLE BOOKING DATA:');
            console.log('- Booking Reference:', order.BookingReferences?.BookingReference?.[0]?.ID);
            console.log('- Order ID:', order.OrderID?.value);
            console.log('- Total Price:', order.TotalOrderPrice?.SimpleCurrencyPrice?.value, order.TotalOrderPrice?.SimpleCurrencyPrice?.Code);
          }
          
          if (response.Passengers?.Passenger) {
            console.log('\n👥 EXTRACTABLE PASSENGER DATA:');
            response.Passengers.Passenger.forEach((passenger, index) => {
              console.log(`Passenger ${index + 1}:`);
              console.log('  - Name:', `${passenger.Name?.Given?.[0]?.value} ${passenger.Name?.Surname?.value}`);
              console.log('  - Type:', passenger.PTC?.value);
              console.log('  - Document:', passenger.PassengerIDInfo?.PassengerDocument?.[0]?.ID);
              console.log('  - Email:', passenger.Contacts?.Contact?.[0]?.EmailContact?.Address?.value);
            });
          }
          
          if (response.DataLists?.FlightSegmentList?.FlightSegment) {
            console.log('\n✈️ EXTRACTABLE FLIGHT DATA:');
            response.DataLists.FlightSegmentList.FlightSegment.forEach((segment, index) => {
              console.log(`Segment ${index + 1}:`);
              console.log('  - Flight Number:', segment.MarketingCarrier?.FlightNumber?.value);
              console.log('  - Airline:', segment.MarketingCarrier?.AirlineID?.value);
              console.log('  - Route:', `${segment.Departure?.AirportCode?.value} → ${segment.Arrival?.AirportCode?.value}`);
              console.log('  - Departure:', segment.Departure?.Date, segment.Departure?.Time);
              console.log('  - Arrival:', segment.Arrival?.Date, segment.Arrival?.Time);
            });
          }
          
          // Test itinerary extraction with correct path
          console.log('\n🧪 TESTING ITINERARY EXTRACTION WITH CORRECT PATH:');
          const itineraryTests = {
            hasBookingReference: !!response.Order?.[0]?.BookingReferences?.BookingReference?.[0]?.ID,
            hasOrderId: !!response.Order?.[0]?.OrderID?.value,
            hasPassengerName: !!response.Passengers?.Passenger?.[0]?.Name?.Given?.[0]?.value,
            hasPassengerDocument: !!response.Passengers?.Passenger?.[0]?.PassengerIDInfo?.PassengerDocument?.[0]?.ID,
            hasFlightNumber: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.MarketingCarrier?.FlightNumber?.value,
            hasAirlineCode: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.MarketingCarrier?.AirlineID?.value,
            hasDepartureAirport: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Departure?.AirportCode?.value,
            hasArrivalAirport: !!response.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Arrival?.AirportCode?.value,
            hasTotalPrice: !!response.Order?.[0]?.TotalOrderPrice?.SimpleCurrencyPrice?.value,
            hasContactEmail: !!response.Passengers?.Passenger?.[0]?.Contacts?.Contact?.[0]?.EmailContact?.Address?.value
          };
          
          console.log('\n📊 CORRECTED ITINERARY VALIDATION:');
          Object.entries(itineraryTests).forEach(([test, passed]) => {
            console.log(`${passed ? '✅' : '❌'} ${test}: ${passed}`);
          });
          
          const itineraryPassed = Object.values(itineraryTests).every(test => test === true);
          console.log(`\n🎯 Corrected Itinerary Test Result: ${itineraryPassed ? '✅ PASSED' : '❌ FAILED'}`);
          
        } else if (rawResponse.data?.Response) {
          console.log('✅ Found Response object in raw_order_create_response.data!');
          console.log('Nested Response keys:', Object.keys(rawResponse.data.Response));
        } else {
          console.log('❌ No Response object found in raw_order_create_response');
          console.log('Raw response structure:', JSON.stringify(rawResponse, null, 2).substring(0, 1000) + '...');
        }
      }
    }
    
    console.log('\n📊 BOOKING 86 DEEP ANALYSIS SUMMARY:');
    console.log('====================================');
    
    const hasValidOrderCreate = !!(
      orderCreateResponse.raw_order_create_response?.Response ||
      orderCreateResponse.raw_order_create_response?.data?.Response ||
      orderCreateResponse.Response
    );
    
    if (hasValidOrderCreate) {
      console.log('🎉 SUCCESS: Valid NDC OrderCreate data found!');
      console.log('💡 SOLUTION: Update itinerary extraction to check multiple paths:');
      console.log('   1. orderCreateResponse.raw_order_create_response.Response');
      console.log('   2. orderCreateResponse.raw_order_create_response.data.Response');
      console.log('   3. orderCreateResponse.Response (fallback)');
      console.log('');
      console.log('✅ With this fix, booking 86 will support BOTH:');
      console.log('   - Payment confirmation (originalFlightOffer) ✅');
      console.log('   - Itinerary generation (orderCreateResponse.raw_order_create_response) ✅');
    } else {
      console.log('❌ No valid NDC data structure found');
      console.log('⚠️ This booking may need fallback to originalFlightOffer for itinerary');
    }
    
  } catch (error) {
    console.error('❌ Error in deep analysis:', error);
  } finally {
    await prisma.$disconnect();
  }
}

deepAnalyzeBooking86().catch(console.error);
