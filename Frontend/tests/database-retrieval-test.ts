/**
 * Comprehensive test file to verify database data retrieval for:
 * 1. Confirmation page data display
 * 2. Itinerary generation
 * 
 * This test validates that the orderCreateResponse and originalFlightOffer 
 * JSON columns are properly storing and retrieving all necessary data.
 */

import { prisma } from '@/utils/prisma';
import { transformOrderCreateToItinerary } from '@/utils/itinerary-data-transformer';

// Mock booking data structure for testing
const mockBookingReference = `TEST_${Date.now()}`;

// Sample OrderCreate response structure (based on actual API response)
const sampleOrderCreateResponse = {
  "Response": {
    "Passengers": {
      "Passenger": [
        {
          "ObjectKey": "PAX1",
          "PTC": { "value": "ADT" },
          "Age": { "BirthDate": { "value": "2000-09-07T00:00:00.000" } },
          "Name": {
            "Surname": { "value": "EROT" },
            "Given": [{ "value": "AMONI" }],
            "Title": "MR"
          },
          "Contacts": {
            "Contact": [{
              "EmailContact": { "Address": { "value": "test@gmail.com" } },
              "PhoneContact": {
                "Application": "MOBILE",
                "Number": [{ "value": "123456778", "CountryCode": "358" }]
              },
              "ContactType": "STANDARD"
            }]
          },
          "PassengerIDInfo": {
            "PassengerDocument": [{
              "Type": "PT",
              "ID": "A20394854",
              "DateOfExpiration": "2038-03-10T00:00:00.000",
              "CountryOfIssuance": "DE"
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
      },
      "OrderItems": {
        "OrderItem": [{
          "OrderItemID": { "value": "ITEM_001" }
        }]
      }
    }],
    "DataLists": {
      "FlightSegmentList": {
        "FlightSegment": [{
          "SegmentKey": "SEG1",
          "Departure": {
            "AirportCode": { "value": "BOM" },
            "Date": "2025-07-16T23:40:00.000",
            "Time": "23:40",
            "Terminal": { "Name": "2" }
          },
          "Arrival": {
            "AirportCode": { "value": "SIN" },
            "Date": "2025-07-17T07:40:00.000",
            "Time": "07:40",
            "Terminal": { "Name": "0" }
          },
          "MarketingCarrier": {
            "AirlineID": { "value": "SQ" },
            "FlightNumber": { "value": "423" }
          },
          "OperatingCarrier": {
            "AirlineID": { "value": "SQ" },
            "FlightNumber": { "value": "423" }
          },
          "ClassOfService": {
            "Code": { "value": "Y" },
            "MarketingName": { "value": "Economy" }
          }
        }]
      }
    }
  }
};

// Sample original flight offer structure
const sampleOriginalFlightOffer = {
  "offer_id": "1H0SQZ_U9YY1WYKKSPCZ14FY9X8JEFPUJWQ",
  "segments": [{
    "departure": {
      "airport": "BOM",
      "datetime": "2025-07-16T23:40:00.000",
      "terminal": "2"
    },
    "arrival": {
      "airport": "SIN", 
      "datetime": "2025-07-17T07:40:00.000",
      "terminal": "0"
    },
    "airline": {
      "code": "SQ",
      "flightNumber": "423"
    },
    "class": "Economy",
    "cabin": "Economy"
  }],
  "pricing": {
    "total_price": "35541",
    "currency": "INR"
  }
};

// Test functions
export class DatabaseRetrievalTest {
  
  /**
   * Test 1: Create a test booking with complete JSON data
   */
  static async createTestBooking(): Promise<string> {
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
            arrivalTime: '2025-07-17T07:40:00.000',
            segments: sampleOriginalFlightOffer.segments
          },
          passengerTypes: ['ADT'],
          documentNumbers: ['A20394854'],
          classOfService: 'Y',
          cabinClass: 'Economy',
          flightDetails: {
            outbound: {
              departure: {
                city: "BOM",
                airport: "BOM - Chhatrapati Shivaji Maharaj International Airport",
                code: "BOM",
                time: "23:40",
                fullDate: "2025-07-16T23:40:00.000",
                terminal: "2"
              },
              arrival: {
                city: "Singapore",
                airport: "SIN - Singapore Changi Airport", 
                code: "SIN",
                time: "07:40",
                fullDate: "2025-07-17T07:40:00.000",
                terminal: "0"
              },
              airline: {
                code: "SQ",
                flightNumber: "423"
              },
              classOfService: "Economy",
              cabinClass: "Economy"
            }
          },
          passengerDetails: {
            names: "AMONI EROT",
            types: ["ADT"],
            documents: ["A20394854"],
            passengers: [{
              firstName: "AMONI",
              lastName: "EROT",
              type: "adult",
              documentNumber: "A20394854"
            }]
          },
          contactInfo: {
            email: "test@gmail.com",
            phone: "123456778"
          },
          totalAmount: 35541,
          status: 'confirmed',
          // Store the complete OrderCreate response
          orderCreateResponse: sampleOrderCreateResponse,
          // Store the original flight offer
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

  /**
   * Test 2: Retrieve booking data as confirmation page would
   */
  static async testConfirmationPageRetrieval(bookingReference: string): Promise<boolean> {
    console.log('🧪 Testing confirmation page data retrieval...');
    
    try {
      // Simulate the API call that confirmation page makes
      const booking = await prisma.booking.findUnique({
        where: { bookingReference },
        include: { payments: true }
      });

      if (!booking) {
        console.error('❌ Booking not found');
        return false;
      }

      // Test essential fields for confirmation display
      const confirmationTests = {
        hasBookingReference: !!booking.bookingReference,
        hasFlightDetails: !!booking.flightDetails,
        hasPassengerDetails: !!booking.passengerDetails,
        hasContactInfo: !!booking.contactInfo,
        hasTotalAmount: booking.totalAmount > 0,
        hasOrderCreateResponse: !!booking.orderCreateResponse,
        hasOriginalFlightOffer: !!booking.originalFlightOffer
      };

      console.log('📋 Confirmation page data validation:', confirmationTests);

      // Test data structure integrity
      const flightDetails = booking.flightDetails as any;
      const passengerDetails = booking.passengerDetails as any;
      const contactInfo = booking.contactInfo as any;

      const structureTests = {
        flightDetailsHasOutbound: !!flightDetails?.outbound,
        passengerDetailsHasNames: !!passengerDetails?.names,
        contactInfoHasEmail: !!contactInfo?.email,
        orderCreateResponseIsObject: typeof booking.orderCreateResponse === 'object',
        originalFlightOfferIsObject: typeof booking.originalFlightOffer === 'object'
      };

      console.log('📋 Data structure validation:', structureTests);

      const allTestsPassed = Object.values({...confirmationTests, ...structureTests}).every(test => test === true);
      
      if (allTestsPassed) {
        console.log('✅ Confirmation page retrieval test PASSED');
      } else {
        console.log('❌ Confirmation page retrieval test FAILED');
      }

      return allTestsPassed;
    } catch (error) {
      console.error('❌ Error in confirmation page test:', error);
      return false;
    }
  }

  /**
   * Test 3: Test itinerary generation from stored data
   */
  static async testItineraryGeneration(bookingReference: string): Promise<boolean> {
    console.log('🧪 Testing itinerary generation...');
    
    try {
      // Retrieve booking as itinerary page would
      const booking = await prisma.booking.findUnique({
        where: { bookingReference }
      });

      if (!booking) {
        console.error('❌ Booking not found for itinerary test');
        return false;
      }

      // Parse the JSON data as the itinerary page does
      let parsedOrderCreate = booking.orderCreateResponse;
      if (typeof parsedOrderCreate === 'string') {
        parsedOrderCreate = JSON.parse(parsedOrderCreate);
      }

      let originalFlightOffer = booking.originalFlightOffer;
      if (typeof originalFlightOffer === 'string') {
        originalFlightOffer = JSON.parse(originalFlightOffer);
      }

      console.log('📋 Parsed data for itinerary:', {
        hasOrderCreate: !!parsedOrderCreate,
        hasOriginalOffer: !!originalFlightOffer,
        orderCreateKeys: parsedOrderCreate ? Object.keys(parsedOrderCreate) : [],
        originalOfferKeys: originalFlightOffer ? Object.keys(originalFlightOffer) : []
      });

      // Test the transformation function
      const transformedData = transformOrderCreateToItinerary(parsedOrderCreate, originalFlightOffer);

      // Validate transformed data structure
      const itineraryTests = {
        hasBookingInfo: !!transformedData.bookingInfo,
        hasPassengers: !!transformedData.passengers && transformedData.passengers.length > 0,
        hasOutboundFlight: !!transformedData.outboundFlight && transformedData.outboundFlight.length > 0,
        hasPricing: !!transformedData.pricing,
        hasContactInfo: !!transformedData.contactInfo,
        bookingReferenceMatches: transformedData.bookingInfo?.bookingReference === bookingReference
      };

      console.log('📋 Itinerary transformation validation:', itineraryTests);

      // Test specific data points
      const dataPointTests = {
        passengerNameExists: !!transformedData.passengers?.[0]?.name,
        flightNumberExists: !!transformedData.outboundFlight?.[0]?.flightNumber,
        departureAirportExists: !!transformedData.outboundFlight?.[0]?.departure?.airport,
        arrivalAirportExists: !!transformedData.outboundFlight?.[0]?.arrival?.airport,
        totalPriceExists: !!transformedData.pricing?.totalPrice
      };

      console.log('📋 Specific data points validation:', dataPointTests);

      const allTestsPassed = Object.values({...itineraryTests, ...dataPointTests}).every(test => test === true);
      
      if (allTestsPassed) {
        console.log('✅ Itinerary generation test PASSED');
        console.log('📋 Sample transformed data:', {
          bookingReference: transformedData.bookingInfo?.bookingReference,
          passengerName: transformedData.passengers?.[0]?.name,
          flightNumber: transformedData.outboundFlight?.[0]?.flightNumber,
          route: `${transformedData.outboundFlight?.[0]?.departure?.airport} → ${transformedData.outboundFlight?.[0]?.arrival?.airport}`,
          totalPrice: transformedData.pricing?.totalPrice
        });
      } else {
        console.log('❌ Itinerary generation test FAILED');
      }

      return allTestsPassed;
    } catch (error) {
      console.error('❌ Error in itinerary generation test:', error);
      console.error('❌ Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      return false;
    }
  }

  /**
   * Test 4: Clean up test data
   */
  static async cleanupTestData(bookingReference: string): Promise<void> {
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

  /**
   * Run all tests
   */
  static async runAllTests(): Promise<void> {
    console.log('🚀 Starting comprehensive database retrieval tests...');
    
    let bookingReference: string | null = null;
    
    try {
      // Test 1: Create test booking
      bookingReference = await this.createTestBooking();
      
      // Test 2: Confirmation page retrieval
      const confirmationPassed = await this.testConfirmationPageRetrieval(bookingReference);
      
      // Test 3: Itinerary generation
      const itineraryPassed = await this.testItineraryGeneration(bookingReference);
      
      // Summary
      console.log('\n📊 TEST SUMMARY:');
      console.log(`✅ Confirmation Page Test: ${confirmationPassed ? 'PASSED' : 'FAILED'}`);
      console.log(`✅ Itinerary Generation Test: ${itineraryPassed ? 'PASSED' : 'FAILED'}`);
      
      if (confirmationPassed && itineraryPassed) {
        console.log('🎉 ALL TESTS PASSED - Database retrieval is working correctly!');
      } else {
        console.log('❌ SOME TESTS FAILED - Database retrieval needs attention');
      }
      
    } catch (error) {
      console.error('❌ Test suite failed:', error);
    } finally {
      // Clean up
      if (bookingReference) {
        await this.cleanupTestData(bookingReference);
      }
    }
  }
}

// Export for use in other test files or manual execution
export default DatabaseRetrievalTest;
