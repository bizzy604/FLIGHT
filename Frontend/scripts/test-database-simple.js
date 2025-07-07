/**
 * Simple Node.js test script for database retrieval
 * This can be run directly with: node scripts/test-database-simple.js
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

// Mock data for testing
const mockBookingReference = `TEST_${Date.now()}`;

const sampleOrderCreateResponse = {
  "Response": {
    "Passengers": {
      "Passenger": [
        {
          "ObjectKey": "PAX1",
          "PTC": { "value": "ADT" },
          "Name": {
            "Surname": { "value": "EROT" },
            "Given": [{ "value": "AMONI" }],
            "Title": "MR"
          },
          "PassengerIDInfo": {
            "PassengerDocument": [{
              "Type": "PT",
              "ID": "A20394854"
            }]
          }
        }
      ]
    },
    "Order": [{
      "OrderID": { "value": "DEZ9BN" },
      "BookingReferences": {
        "BookingReference": [{ "ID": "1802459" }]
      },
      "TotalOrderPrice": {
        "SimpleCurrencyPrice": { "value": "35541", "Code": "INR" }
      }
    }],
    "DataLists": {
      "FlightSegmentList": {
        "FlightSegment": [{
          "Departure": {
            "AirportCode": { "value": "BOM" },
            "Date": "2025-07-16T23:40:00.000"
          },
          "Arrival": {
            "AirportCode": { "value": "SIN" },
            "Date": "2025-07-17T07:40:00.000"
          },
          "MarketingCarrier": {
            "AirlineID": { "value": "SQ" },
            "FlightNumber": { "value": "423" }
          }
        }]
      }
    }
  }
};

const sampleOriginalFlightOffer = {
  "offer_id": "1H0SQZ_U9YY1WYKKSPCZ14FY9X8JEFPUJWQ",
  "segments": [{
    "departure": { "airport": "BOM", "datetime": "2025-07-16T23:40:00.000" },
    "arrival": { "airport": "SIN", "datetime": "2025-07-17T07:40:00.000" },
    "airline": { "code": "SQ", "flightNumber": "423" }
  }],
  "pricing": { "total_price": "35541", "currency": "INR" }
};

async function createTestBooking() {
  console.log('🧪 Creating test booking...');
  
  try {
    const booking = await prisma.booking.create({
      data: {
        bookingReference: mockBookingReference,
        userId: 'test-user-id',
        airlineCode: 'SQ',
        flightNumbers: ['423'],
        routeSegments: {
          origin: 'BOM',
          destination: 'SIN',
          departureTime: '2025-07-16T23:40:00.000',
          arrivalTime: '2025-07-17T07:40:00.000'
        },
        passengerTypes: ['ADT'],
        documentNumbers: ['A20394854'],
        classOfService: 'Y',
        cabinClass: 'Economy',
        flightDetails: {
          outbound: {
            departure: { code: "BOM", time: "23:40" },
            arrival: { code: "SIN", time: "07:40" },
            airline: { code: "SQ", flightNumber: "423" }
          }
        },
        passengerDetails: {
          names: "AMONI EROT",
          passengers: [{ firstName: "AMONI", lastName: "EROT", type: "adult" }]
        },
        contactInfo: { email: "test@gmail.com", phone: "123456778" },
        totalAmount: 35541,
        status: 'confirmed',
        orderCreateResponse: sampleOrderCreateResponse,
        originalFlightOffer: sampleOriginalFlightOffer
      }
    });

    console.log('✅ Test booking created:', {
      id: booking.id,
      bookingReference: booking.bookingReference,
      hasOrderCreateResponse: !!booking.orderCreateResponse,
      hasOriginalFlightOffer: !!booking.originalFlightOffer
    });

    return booking.bookingReference;
  } catch (error) {
    console.error('❌ Error creating test booking:', error);
    throw error;
  }
}

async function testDataRetrieval(bookingReference) {
  console.log('🧪 Testing data retrieval...');
  
  try {
    const booking = await prisma.booking.findUnique({
      where: { bookingReference },
      include: { payments: true }
    });

    if (!booking) {
      console.error('❌ Booking not found');
      return false;
    }

    // Test basic data structure
    const tests = {
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

    console.log('📋 Data retrieval tests:', tests);

    // Test JSON data integrity
    const orderCreate = booking.orderCreateResponse;
    const originalOffer = booking.originalFlightOffer;

    const jsonTests = {
      orderCreateHasResponse: !!orderCreate?.Response,
      orderCreateHasOrder: !!orderCreate?.Response?.Order,
      orderCreateHasPassengers: !!orderCreate?.Response?.Passengers,
      orderCreateHasDataLists: !!orderCreate?.Response?.DataLists,
      originalOfferHasSegments: !!originalOffer?.segments,
      originalOfferHasPricing: !!originalOffer?.pricing
    };

    console.log('📋 JSON data integrity tests:', jsonTests);

    // Test specific data extraction (simulating what confirmation/itinerary pages do)
    const extractionTests = {
      canExtractBookingRef: !!orderCreate?.Response?.Order?.[0]?.BookingReferences?.BookingReference?.[0]?.ID,
      canExtractPassengerName: !!orderCreate?.Response?.Passengers?.Passenger?.[0]?.Name?.Given?.[0]?.value,
      canExtractFlightNumber: !!orderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.MarketingCarrier?.FlightNumber?.value,
      canExtractDeparture: !!orderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Departure?.AirportCode?.value,
      canExtractArrival: !!orderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Arrival?.AirportCode?.value,
      canExtractPrice: !!orderCreate?.Response?.Order?.[0]?.TotalOrderPrice?.SimpleCurrencyPrice?.value
    };

    console.log('📋 Data extraction tests:', extractionTests);

    const allTests = {...tests, ...jsonTests, ...extractionTests};
    const allPassed = Object.values(allTests).every(test => test === true);

    if (allPassed) {
      console.log('✅ ALL TESTS PASSED - Database retrieval working correctly!');
      
      // Show sample extracted data
      console.log('\n📋 Sample extracted data:');
      console.log('- Booking Reference:', orderCreate?.Response?.Order?.[0]?.BookingReferences?.BookingReference?.[0]?.ID);
      console.log('- Passenger Name:', `${orderCreate?.Response?.Passengers?.Passenger?.[0]?.Name?.Given?.[0]?.value} ${orderCreate?.Response?.Passengers?.Passenger?.[0]?.Name?.Surname?.value}`);
      console.log('- Flight Number:', orderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.MarketingCarrier?.FlightNumber?.value);
      console.log('- Route:', `${orderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Departure?.AirportCode?.value} → ${orderCreate?.Response?.DataLists?.FlightSegmentList?.FlightSegment?.[0]?.Arrival?.AirportCode?.value}`);
      console.log('- Total Price:', `${orderCreate?.Response?.Order?.[0]?.TotalOrderPrice?.SimpleCurrencyPrice?.value} ${orderCreate?.Response?.Order?.[0]?.TotalOrderPrice?.SimpleCurrencyPrice?.Code}`);
      
    } else {
      console.log('❌ SOME TESTS FAILED');
      const failedTests = Object.entries(allTests).filter(([key, value]) => !value);
      console.log('Failed tests:', failedTests.map(([key]) => key));
    }

    return allPassed;
  } catch (error) {
    console.error('❌ Error in data retrieval test:', error);
    return false;
  }
}

async function cleanupTestData(bookingReference) {
  console.log('🧪 Cleaning up test data...');
  
  try {
    await prisma.booking.delete({
      where: { bookingReference }
    });
    console.log('✅ Test data cleaned up successfully');
  } catch (error) {
    console.error('❌ Error cleaning up test data:', error);
  }
}

async function runTests() {
  console.log('🚀 Starting Database Retrieval Tests');
  console.log('====================================\n');
  
  let bookingReference = null;
  
  try {
    // Create test booking
    bookingReference = await createTestBooking();
    
    // Test data retrieval
    const testsPassed = await testDataRetrieval(bookingReference);
    
    console.log('\n📊 FINAL RESULT:');
    if (testsPassed) {
      console.log('🎉 ALL TESTS PASSED - orderCreateResponse and originalFlightOffer columns are working correctly!');
      console.log('✅ Confirmation pages can retrieve all necessary data');
      console.log('✅ Itinerary generation can access complete OrderCreate response');
      console.log('✅ Data integrity is maintained in JSON columns');
    } else {
      console.log('❌ TESTS FAILED - Database retrieval needs attention');
    }
    
  } catch (error) {
    console.error('❌ Test suite failed:', error);
  } finally {
    // Clean up
    if (bookingReference) {
      await cleanupTestData(bookingReference);
    }
    
    await prisma.$disconnect();
  }
}

// Run the tests
runTests().catch(console.error);
