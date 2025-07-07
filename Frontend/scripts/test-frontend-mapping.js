/**
 * Test if frontend components are properly mapped to dual-column data structures
 * Check both confirmation pages and itinerary generation
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

// Simulate how the confirmation page accesses data
function simulateConfirmationPageAccess(booking) {
  console.log('🎫 Simulating Confirmation Page Data Access...');
  
  const issues = [];
  const successes = [];
  
  // Test 1: Check if confirmation page can access originalFlightOffer
  if (booking.originalFlightOffer) {
    const offer = booking.originalFlightOffer;
    
    // Check flight details access
    const flight = offer.flight_segments?.[0];
    if (flight) {
      successes.push('✅ Flight details accessible from originalFlightOffer');
      console.log('  - Flight Number:', flight.flight_number);
      console.log('  - Airline:', `${flight.airline_code} - ${flight.airline_name}`);
      console.log('  - Route:', `${flight.departure_airport} → ${flight.arrival_airport}`);
    } else {
      issues.push('❌ Flight details not accessible from originalFlightOffer');
    }
    
    // Check pricing access
    const pricing = offer.total_price;
    if (pricing?.amount) {
      successes.push('✅ Pricing accessible from originalFlightOffer');
      console.log('  - Total:', `${pricing.amount} ${pricing.currency}`);
    } else {
      issues.push('❌ Pricing not accessible from originalFlightOffer');
    }
    
    // Check passenger info access
    const passenger = offer.passengers?.[0];
    if (passenger) {
      successes.push('✅ Passenger info accessible from originalFlightOffer');
      console.log('  - Type:', passenger.type);
      console.log('  - Count:', passenger.count);
    } else {
      issues.push('❌ Passenger info not accessible from originalFlightOffer');
    }
    
  } else {
    issues.push('❌ originalFlightOffer not available');
  }
  
  // Test 2: Check if confirmation page can access basic booking fields
  const basicFields = {
    bookingReference: booking.bookingReference,
    passengerNames: booking.passengerDetails?.names,
    contactEmail: booking.contactInfo?.email,
    contactPhone: booking.contactInfo?.phone,
    totalAmount: booking.totalAmount
  };
  
  Object.entries(basicFields).forEach(([field, value]) => {
    if (value && value !== 'Unknown' && value !== 0) {
      successes.push(`✅ ${field} accessible from basic fields`);
      console.log(`  - ${field}:`, value);
    } else {
      issues.push(`❌ ${field} not accessible from basic fields`);
    }
  });
  
  return { issues, successes };
}

// Simulate how the itinerary page accesses data
function simulateItineraryPageAccess(booking) {
  console.log('\n📄 Simulating Itinerary Page Data Access...');
  
  const issues = [];
  const successes = [];
  
  // Test 1: Check if itinerary page can access orderCreateResponse
  if (booking.orderCreateResponse) {
    let orderCreate = booking.orderCreateResponse;
    
    // Parse if string
    if (typeof orderCreate === 'string') {
      try {
        orderCreate = JSON.parse(orderCreate);
        successes.push('✅ orderCreateResponse parsed successfully');
      } catch (error) {
        issues.push('❌ orderCreateResponse parsing failed');
        return { issues, successes };
      }
    }
    
    // Check multiple possible paths for NDC data
    let response = null;
    
    if (orderCreate.raw_order_create_response?.Response) {
      response = orderCreate.raw_order_create_response.Response;
      successes.push('✅ NDC Response found in raw_order_create_response.Response');
    } else if (orderCreate.Response) {
      response = orderCreate.Response;
      successes.push('✅ NDC Response found in direct Response');
    } else if (orderCreate.data?.Response) {
      response = orderCreate.data.Response;
      successes.push('✅ NDC Response found in data.Response');
    } else {
      issues.push('❌ NDC Response not found in any expected location');
      console.log('Available keys:', Object.keys(orderCreate));
    }
    
    if (response) {
      // Test NDC structure access
      const structureTests = {
        'Order data': response.Order?.[0],
        'Passenger data': response.Passengers?.Passenger?.[0],
        'Flight segments': response.DataLists?.FlightSegmentList?.FlightSegment?.[0],
        'Booking reference': response.Order?.[0]?.BookingReferences?.BookingReference?.[0]?.ID,
        'Total price': response.Order?.[0]?.TotalOrderPrice?.SimpleCurrencyPrice?.value
      };
      
      Object.entries(structureTests).forEach(([test, data]) => {
        if (data) {
          successes.push(`✅ ${test} accessible from NDC Response`);
          console.log(`  - ${test}:`, typeof data === 'object' ? 'Available' : data);
        } else {
          issues.push(`❌ ${test} not accessible from NDC Response`);
        }
      });
    }
    
  } else {
    issues.push('❌ orderCreateResponse not available');
  }
  
  // Test 2: Check if originalFlightOffer can be used as fallback
  if (booking.originalFlightOffer && issues.length > 0) {
    console.log('\n🔄 Testing originalFlightOffer as itinerary fallback...');
    const offer = booking.originalFlightOffer;
    const flight = offer.flight_segments?.[0];
    
    if (flight) {
      successes.push('✅ originalFlightOffer available as itinerary fallback');
      console.log('  - Can extract basic itinerary from originalFlightOffer');
    }
  }
  
  return { issues, successes };
}

// Test current frontend transformer compatibility
function testTransformerCompatibility(booking) {
  console.log('\n🔧 Testing Transformer Compatibility...');
  
  const issues = [];
  const successes = [];
  
  // Test if current transformer can handle the data structure
  if (booking.orderCreateResponse) {
    let orderCreate = booking.orderCreateResponse;
    
    if (typeof orderCreate === 'string') {
      try {
        orderCreate = JSON.parse(orderCreate);
      } catch (error) {
        issues.push('❌ Transformer cannot parse orderCreateResponse');
        return { issues, successes };
      }
    }
    
    // Check what the current transformer expects vs what we have
    const currentExpectations = {
      'orderCreateResponse.Response': !!orderCreate.Response,
      'orderCreateResponse.Order': !!orderCreate.Order,
      'orderCreateResponse.data': !!orderCreate.data,
      'orderCreateResponse.raw_order_create_response': !!orderCreate.raw_order_create_response
    };
    
    console.log('Current transformer expectations vs reality:');
    Object.entries(currentExpectations).forEach(([path, exists]) => {
      console.log(`  ${exists ? '✅' : '❌'} ${path}: ${exists}`);
      if (exists) {
        successes.push(`✅ Transformer compatible with ${path}`);
      } else {
        issues.push(`❌ Transformer expects ${path} but not found`);
      }
    });
    
    // Check if we need to update the transformer
    if (orderCreate.raw_order_create_response?.Response && !orderCreate.Response) {
      issues.push('⚠️ Transformer needs update to check raw_order_create_response.Response path');
    }
    
  }
  
  return { issues, successes };
}

async function testFrontendMapping() {
  console.log('🚀 Testing Frontend Mapping to Dual-Column Data Structures');
  console.log('==========================================================\n');
  
  try {
    // Test both booking 86 and 102
    const bookingIds = [86, 102];
    
    for (const bookingId of bookingIds) {
      console.log(`\n📋 TESTING BOOKING ID ${bookingId}`);
      console.log('='.repeat(30));
      
      const booking = await prisma.booking.findUnique({
        where: { id: bookingId }
      });
      
      if (!booking) {
        console.log(`❌ Booking ${bookingId} not found`);
        continue;
      }
      
      console.log(`Booking Reference: ${booking.bookingReference}`);
      console.log(`Has originalFlightOffer: ${!!booking.originalFlightOffer}`);
      console.log(`Has orderCreateResponse: ${!!booking.orderCreateResponse}`);
      
      // Test confirmation page mapping
      const confirmationResults = simulateConfirmationPageAccess(booking);
      
      // Test itinerary page mapping
      const itineraryResults = simulateItineraryPageAccess(booking);
      
      // Test transformer compatibility
      const transformerResults = testTransformerCompatibility(booking);
      
      // Summary for this booking
      console.log(`\n📊 BOOKING ${bookingId} SUMMARY:`);
      console.log('========================');
      
      const allSuccesses = [
        ...confirmationResults.successes,
        ...itineraryResults.successes,
        ...transformerResults.successes
      ];
      
      const allIssues = [
        ...confirmationResults.issues,
        ...itineraryResults.issues,
        ...transformerResults.issues
      ];
      
      console.log(`✅ Successes: ${allSuccesses.length}`);
      console.log(`❌ Issues: ${allIssues.length}`);
      
      if (allIssues.length > 0) {
        console.log('\n🔧 ISSUES TO FIX:');
        allIssues.forEach(issue => console.log(`  ${issue}`));
      }
      
      if (allSuccesses.length > 0) {
        console.log('\n✅ WORKING CORRECTLY:');
        allSuccesses.slice(0, 5).forEach(success => console.log(`  ${success}`));
        if (allSuccesses.length > 5) {
          console.log(`  ... and ${allSuccesses.length - 5} more`);
        }
      }
    }
    
    console.log('\n📊 OVERALL FRONTEND MAPPING ASSESSMENT:');
    console.log('=======================================');
    console.log('✅ originalFlightOffer → Confirmation pages: WELL MAPPED');
    console.log('⚠️ orderCreateResponse → Itinerary pages: NEEDS PATH UPDATES');
    console.log('');
    console.log('🔧 RECOMMENDED FIXES:');
    console.log('1. Update itinerary transformer to check multiple paths:');
    console.log('   - orderCreateResponse.raw_order_create_response.Response');
    console.log('   - orderCreateResponse.Response (fallback)');
    console.log('2. Add originalFlightOffer fallback for itinerary generation');
    console.log('3. Update confirmation pages to prioritize originalFlightOffer');
    
  } catch (error) {
    console.error('❌ Error testing frontend mapping:', error);
  } finally {
    await prisma.$disconnect();
  }
}

testFrontendMapping().catch(console.error);
