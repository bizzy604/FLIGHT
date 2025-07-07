/**
 * Detailed analysis of booking ID 102
 * Check what data is actually available and if we can extract itinerary info
 */

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function analyzeBooking102() {
  console.log('🔍 Detailed Analysis of Booking ID 102');
  console.log('=====================================\n');
  
  try {
    // Retrieve the real booking
    const booking = await prisma.booking.findUnique({
      where: { id: 102 },
      include: { payments: true }
    });

    if (!booking) {
      console.error('❌ Booking ID 102 not found');
      return;
    }

    console.log('📋 BOOKING OVERVIEW:');
    console.log('===================');
    console.log('ID:', booking.id);
    console.log('Booking Reference:', booking.bookingReference);
    console.log('User ID:', booking.userId);
    console.log('Status:', booking.status);
    console.log('Total Amount:', booking.totalAmount.toString());
    console.log('Created At:', booking.createdAt);
    console.log('Airline Code:', booking.airlineCode);
    console.log('Flight Numbers:', booking.flightNumbers);
    console.log('Passenger Types:', booking.passengerTypes);
    console.log('Document Numbers:', booking.documentNumbers);
    console.log('Class of Service:', booking.classOfService);
    console.log('Cabin Class:', booking.cabinClass);

    console.log('\n📋 JSON COLUMNS ANALYSIS:');
    console.log('=========================');
    
    // Analyze flightDetails
    console.log('\n🛫 FLIGHT DETAILS:');
    if (booking.flightDetails) {
      console.log('Type:', typeof booking.flightDetails);
      console.log('Keys:', Object.keys(booking.flightDetails));
      console.log('Content:', JSON.stringify(booking.flightDetails, null, 2));
    } else {
      console.log('❌ No flight details');
    }

    // Analyze passengerDetails  
    console.log('\n👤 PASSENGER DETAILS:');
    if (booking.passengerDetails) {
      console.log('Type:', typeof booking.passengerDetails);
      console.log('Keys:', Object.keys(booking.passengerDetails));
      console.log('Content:', JSON.stringify(booking.passengerDetails, null, 2));
    } else {
      console.log('❌ No passenger details');
    }

    // Analyze contactInfo
    console.log('\n📞 CONTACT INFO:');
    if (booking.contactInfo) {
      console.log('Type:', typeof booking.contactInfo);
      console.log('Keys:', Object.keys(booking.contactInfo));
      console.log('Content:', JSON.stringify(booking.contactInfo, null, 2));
    } else {
      console.log('❌ No contact info');
    }

    // Analyze orderCreateResponse
    console.log('\n📄 ORDER CREATE RESPONSE:');
    if (booking.orderCreateResponse) {
      console.log('Type:', typeof booking.orderCreateResponse);
      console.log('Keys:', Object.keys(booking.orderCreateResponse));
      console.log('Content preview:', JSON.stringify(booking.orderCreateResponse, null, 2).substring(0, 500) + '...');
    } else {
      console.log('❌ No OrderCreate response - THIS IS THE MAIN ISSUE!');
    }

    // Analyze originalFlightOffer in detail
    console.log('\n✈️ ORIGINAL FLIGHT OFFER (DETAILED):');
    if (booking.originalFlightOffer) {
      console.log('Type:', typeof booking.originalFlightOffer);
      console.log('Top-level keys:', Object.keys(booking.originalFlightOffer));
      
      const offer = booking.originalFlightOffer;
      
      console.log('\n📋 Flight Offer Structure:');
      console.log('- offer_id:', offer.offer_id);
      console.log('- order_id:', offer.order_id);
      console.log('- direction:', offer.direction);
      console.log('- total_price:', offer.total_price);
      console.log('- shopping_response_id:', offer.shopping_response_id);
      console.log('- original_offer_id:', offer.original_offer_id);
      
      if (offer.passengers) {
        console.log('- passengers count:', offer.passengers.length);
        console.log('- passengers:', JSON.stringify(offer.passengers, null, 2));
      }
      
      if (offer.flight_segments) {
        console.log('- flight_segments count:', offer.flight_segments.length);
        console.log('- flight_segments:', JSON.stringify(offer.flight_segments, null, 2));
      }
      
      if (offer.fare_family) {
        console.log('- fare_family:', JSON.stringify(offer.fare_family, null, 2));
      }
      
      if (offer.time_limits) {
        console.log('- time_limits:', JSON.stringify(offer.time_limits, null, 2));
      }

      // Check if raw_flight_price_response exists and analyze it
      if (offer.raw_flight_price_response) {
        console.log('\n🎯 RAW FLIGHT PRICE RESPONSE FOUND!');
        console.log('Type:', typeof offer.raw_flight_price_response);
        
        if (typeof offer.raw_flight_price_response === 'object') {
          console.log('Keys:', Object.keys(offer.raw_flight_price_response));
          
          // Check if this contains OrderCreate-like data
          const rawResponse = offer.raw_flight_price_response;
          
          if (rawResponse.Response) {
            console.log('✅ Found Response object in raw_flight_price_response!');
            console.log('Response keys:', Object.keys(rawResponse.Response));
            
            if (rawResponse.Response.Order) {
              console.log('✅ Found Order in Response!');
              console.log('Order count:', rawResponse.Response.Order.length);
            }
            
            if (rawResponse.Response.Passengers) {
              console.log('✅ Found Passengers in Response!');
              console.log('Passenger count:', rawResponse.Response.Passengers.Passenger?.length || 0);
            }
            
            if (rawResponse.Response.DataLists) {
              console.log('✅ Found DataLists in Response!');
              console.log('DataLists keys:', Object.keys(rawResponse.Response.DataLists));
              
              if (rawResponse.Response.DataLists.FlightSegmentList) {
                console.log('✅ Found FlightSegmentList!');
                console.log('Flight segments count:', rawResponse.Response.DataLists.FlightSegmentList.FlightSegment?.length || 0);
              }
            }
            
            // Try to extract some key data points
            console.log('\n🔍 EXTRACTABLE DATA FROM RAW RESPONSE:');
            try {
              const order = rawResponse.Response.Order?.[0];
              if (order) {
                console.log('- Booking Reference:', order.BookingReferences?.BookingReference?.[0]?.ID);
                console.log('- Order ID:', order.OrderID?.value);
                console.log('- Total Price:', order.TotalOrderPrice?.SimpleCurrencyPrice?.value, order.TotalOrderPrice?.SimpleCurrencyPrice?.Code);
              }
              
              const passenger = rawResponse.Response.Passengers?.Passenger?.[0];
              if (passenger) {
                console.log('- Passenger Name:', `${passenger.Name?.Given?.[0]?.value} ${passenger.Name?.Surname?.value}`);
                console.log('- Document Number:', passenger.PassengerIDInfo?.PassengerDocument?.[0]?.ID);
                console.log('- Email:', passenger.Contacts?.Contact?.[0]?.EmailContact?.Address?.value);
              }
              
              const segment = rawResponse.Response.DataLists?.FlightSegmentList?.FlightSegment?.[0];
              if (segment) {
                console.log('- Flight Number:', segment.MarketingCarrier?.FlightNumber?.value);
                console.log('- Airline:', segment.MarketingCarrier?.AirlineID?.value);
                console.log('- Route:', `${segment.Departure?.AirportCode?.value} → ${segment.Arrival?.AirportCode?.value}`);
                console.log('- Departure:', segment.Departure?.Date, segment.Departure?.Time);
                console.log('- Arrival:', segment.Arrival?.Date, segment.Arrival?.Time);
              }
              
            } catch (extractError) {
              console.error('❌ Error extracting data:', extractError.message);
            }
          } else {
            console.log('❌ No Response object in raw_flight_price_response');
            console.log('Raw response structure:', JSON.stringify(rawResponse, null, 2).substring(0, 1000) + '...');
          }
        } else {
          console.log('Raw flight price response content:', offer.raw_flight_price_response);
        }
      } else {
        console.log('❌ No raw_flight_price_response found');
      }
      
    } else {
      console.log('❌ No original flight offer');
    }

    // Check payments
    console.log('\n💳 PAYMENTS:');
    if (booking.payments && booking.payments.length > 0) {
      booking.payments.forEach((payment, index) => {
        console.log(`Payment ${index + 1}:`, {
          id: payment.id,
          amount: payment.amount.toString(),
          currency: payment.currency,
          status: payment.status,
          method: payment.paymentMethod
        });
      });
    } else {
      console.log('❌ No payments found');
    }

    console.log('\n📊 SUMMARY FOR BOOKING ID 102:');
    console.log('==============================');
    console.log('✅ Booking exists and has basic information');
    console.log('✅ originalFlightOffer contains structured data');
    console.log('❌ orderCreateResponse is missing (main issue)');
    console.log('❌ totalAmount is 0 (pricing not stored properly)');
    console.log('❌ airlineCode is "Unknown" (extraction failed)');
    
    if (booking.originalFlightOffer?.raw_flight_price_response?.Response) {
      console.log('🎯 POTENTIAL SOLUTION: raw_flight_price_response contains OrderCreate-like data!');
      console.log('💡 We could potentially use this as a fallback for itinerary generation');
    } else {
      console.log('⚠️ No usable OrderCreate data found in any field');
    }
    
  } catch (error) {
    console.error('❌ Error analyzing booking 102:', error);
  } finally {
    await prisma.$disconnect();
  }
}

// Run the analysis
analyzeBooking102().catch(console.error);
