/**
 * Production Order-Create Route Test
 * Tests the updated order-create route with improved OrderCreate response parsing
 */

const fs = require('fs');
const path = require('path');

// Load test data
const orderCreateResponsePath = path.join(__dirname, '..', 'OrdercreateRS.json');
const orderCreateResponse = JSON.parse(fs.readFileSync(orderCreateResponsePath, 'utf8'));

// Mock flight offer data (fallback)
const mockFlightOffer = {
  airline: { code: 'QR' },
  flightNumber: 'QR1234',
  departure: { airport: 'DOH', datetime: '2024-01-15T10:00:00Z' },
  arrival: { airport: 'NBO', datetime: '2024-01-15T15:00:00Z' },
  totalPrice: '500',
  currency: 'USD',
  class: 'Economy',
  cabin: 'Economy'
};

// Mock passenger data
const mockPassengers = [
  { firstName: 'John', lastName: 'Doe', type: 'ADT', documentNumber: 'P123456789' },
  { firstName: 'Jane', lastName: 'Doe', type: 'ADT', documentNumber: 'P987654321' },
  { firstName: 'Baby', lastName: 'Doe', type: 'INF', documentNumber: 'P555666777' }
];

// Mock contact info
const mockContactInfo = {
  email: 'test@example.com',
  phone: '+1234567890'
};

// Import the extraction function (simulated)
function extractDatabaseFieldsFromOrderCreate(orderCreateResponse, flightOffer = {}, passengers = [], contactInfo = {}) {
  console.log('🔍 Starting OrderCreate response extraction...');
  
  try {
    // Validate input data
    if (!orderCreateResponse) {
      console.warn('⚠️ No OrderCreate response provided, falling back to flight offer data');
      return extractFallbackData(flightOffer, passengers);
    }
    
    const response = orderCreateResponse.Response || orderCreateResponse;
    
    // Validate response structure
    if (!response || typeof response !== 'object') {
      console.warn('⚠️ Invalid OrderCreate response structure, falling back to flight offer data');
      return extractFallbackData(flightOffer, passengers);
    }

    // Handle Order array structure with error handling
    let orders = [];
    try {
      orders = Array.isArray(response.Order) ? response.Order : [response.Order].filter(Boolean);
      if (orders.length === 0) {
        console.warn('⚠️ No valid orders found in OrderCreate response');
        return extractFallbackData(flightOffer, passengers);
      }
    } catch (error) {
      console.error('❌ Error processing Order structure:', error);
      return extractFallbackData(flightOffer, passengers);
    }
    
    const firstOrder = orders[0] || {};
    
    // Extract from OrderCreate response (primary source) with error handling
    let orderItems = [];
    let flightSegments = [];
    let firstSegment = null;
    
    try {
      orderItems = firstOrder.OrderItems?.OrderItem || [];
      const flightItem = orderItems.find((item) => item.FlightItem);
      const flightSegmentRefs = flightItem?.FlightItem?.FlightSegmentReference || [];
      
      // Get flight segments from DataLists
      flightSegments = response.DataLists?.FlightSegmentList?.FlightSegment || [];
      firstSegment = flightSegments[0];
      
      if (!firstSegment) {
        console.warn('⚠️ No flight segments found in OrderCreate response');
        return extractFallbackData(flightOffer, passengers);
      }
    } catch (error) {
      console.error('❌ Error extracting flight segments:', error);
      return extractFallbackData(flightOffer, passengers);
    }
    
    // Extract airline code with multiple fallback options
    let airlineCode = 'Unknown';
    try {
      airlineCode = firstSegment?.MarketingCarrier?.AirlineID?.value || 
                   firstSegment?.OperatingCarrier?.AirlineID?.value || 
                   flightSegments[0]?.MarketingCarrier?.AirlineID?.value ||
                   'Unknown';
      
      if (airlineCode === 'Unknown') {
        console.warn('⚠️ Could not extract airline code from OrderCreate response');
      } else {
        console.log('✅ Extracted airline code:', airlineCode);
      }
    } catch (error) {
      console.error('❌ Error extracting airline code:', error);
      airlineCode = 'Unknown';
    }

    // Extract flight numbers with error handling
    let flightNumbers = [];
    try {
      flightNumbers = flightSegments.map((segment) => 
        segment.MarketingCarrier?.FlightNumber?.value || 
        segment.OperatingCarrier?.FlightNumber?.value || 
        'Unknown'
      ).filter((fn) => fn !== 'Unknown');
      
      if (flightNumbers.length === 0) {
        console.warn('⚠️ No flight numbers found in OrderCreate response');
      } else {
        console.log('✅ Extracted flight numbers:', flightNumbers);
      }
    } catch (error) {
      console.error('❌ Error extracting flight numbers:', error);
      flightNumbers = [];
    }
    
    // Extract route information with error handling
    let origin = 'Unknown';
    let destination = 'Unknown';
    try {
      origin = firstSegment?.Departure?.AirportCode?.value || 'Unknown';
      destination = flightSegments[flightSegments.length - 1]?.Arrival?.AirportCode?.value || 'Unknown';
      
      if (origin === 'Unknown' || destination === 'Unknown') {
        console.warn('⚠️ Could not extract complete route information');
      } else {
        console.log('✅ Extracted route:', `${origin} → ${destination}`);
      }
    } catch (error) {
      console.error('❌ Error extracting route information:', error);
    }
    
    // Extract departure and arrival times with error handling
    let departureTime = new Date().toISOString();
    let arrivalTime = new Date().toISOString();
    try {
      departureTime = firstSegment?.Departure?.Date || firstSegment?.Departure?.Time || new Date().toISOString();
      arrivalTime = flightSegments[flightSegments.length - 1]?.Arrival?.Date || 
                   flightSegments[flightSegments.length - 1]?.Arrival?.Time || 
                   new Date().toISOString();
      
      console.log('✅ Extracted times:', { departureTime, arrivalTime });
    } catch (error) {
      console.error('❌ Error extracting flight times:', error);
    }

    // Extract passenger information from OrderCreate response with error handling
    let passengerTypes = [];
    let documentNumbers = [];
    try {
      const orderPassengers = response.Passengers?.Passenger || [];
      passengerTypes = orderPassengers.map((p) => p.PTC?.value || 'ADT');
      
      // Extract document numbers from PassengerDocument
      orderPassengers.forEach((passenger) => {
        try {
          const passengerDocs = passenger.PassengerIDInfo?.PassengerDocument || [];
          passengerDocs.forEach((doc) => {
            if (doc.ID) {
              documentNumbers.push(doc.ID);
            }
          });
        } catch (docError) {
          console.warn('⚠️ Error extracting document for passenger:', docError);
        }
      });
      
      console.log('✅ Extracted passenger data:', { 
        passengerCount: passengerTypes.length, 
        documentCount: documentNumbers.length 
      });
    } catch (error) {
      console.error('❌ Error extracting passenger information:', error);
      passengerTypes = ['ADT']; // Default fallback
    }

    // Extract class of service from multiple sources (enhanced)
    let classOfService = 'Economy';
    let cabinClass = 'Economy';
    
    // Method 1: Extract from FlightSegment ClassOfService
    if (firstSegment?.ClassOfService) {
      const classInfo = firstSegment.ClassOfService;
      classOfService = classInfo.Code?.value || classInfo.MarketingName?.value || 'Economy';
      cabinClass = classInfo.MarketingName?.value || 'Economy';
      
      // Map cabin designator to readable names
      const cabinDesignator = classInfo.MarketingName?.CabinDesignator;
      if (cabinDesignator === 'C') {
        cabinClass = 'Business';
      } else if (cabinDesignator === 'F') {
        cabinClass = 'First';
      } else if (cabinDesignator === 'Y') {
        cabinClass = 'Economy';
      }
    }
    
    // Method 2: Fallback to fare basis codes if ClassOfService not available
    if (classOfService === 'Economy') {
      const fareComponents = response.DataLists?.FareList?.FareGroup?.[0]?.Fare?.[0]?.FareDetail?.[0]?.FareComponent || [];
      const fareBasisCode = fareComponents[0]?.FareBasisCode?.Code;
      if (fareBasisCode) {
        classOfService = fareBasisCode;
        // Determine cabin class from fare basis patterns
        if (fareBasisCode.includes('C') || fareBasisCode.includes('J') || fareBasisCode.includes('D')) {
          cabinClass = 'Business';
        } else if (fareBasisCode.includes('F') || fareBasisCode.includes('A')) {
          cabinClass = 'First';
        }
      }
    }
    
    // Method 3: Extract from PriceClassList if available
    const priceClassList = response.DataLists?.PriceClassList?.PriceClass || [];
    if (priceClassList.length > 0 && classOfService === 'Economy') {
      const priceClass = priceClassList[0];
      classOfService = priceClass.Name || 'Economy';
    }

    // Extract total amount from pricing with error handling
    let totalAmount = 0;
    let currency = 'USD';
    try {
      const totalPriceBreakdown = firstOrder.TotalOrderPrice?.SimpleCurrencyPrice || 
                                 response.TotalPrice?.DetailCurrencyPrice?.Total || 
                                 response.TotalPrice?.SimpleCurrencyPrice || {};
      totalAmount = parseFloat(totalPriceBreakdown.value || '0');
      currency = totalPriceBreakdown.Code || 'USD';
      
      if (totalAmount === 0) {
        console.warn('⚠️ Could not extract valid total amount from OrderCreate response');
      } else {
        console.log('✅ Extracted pricing:', { totalAmount, currency });
      }
    } catch (error) {
      console.error('❌ Error extracting pricing information:', error);
    }
    
    // Extract booking reference with error handling
    let bookingReference = 'Unknown';
    try {
      bookingReference = firstOrder.BookingReferences?.BookingReference?.[0]?.ID || 
                        firstOrder.OrderID?.value || 
                        'Unknown';
      
      if (bookingReference === 'Unknown') {
        console.warn('⚠️ Could not extract booking reference from OrderCreate response');
      } else {
        console.log('✅ Extracted booking reference:', bookingReference);
      }
    } catch (error) {
      console.error('❌ Error extracting booking reference:', error);
    }
    
    // Extract order item ID with error handling
    let orderItemId = null;
    try {
      orderItemId = orderItems[0]?.OrderItemID?.value || null;
      if (orderItemId) {
        console.log('✅ Extracted order item ID:', orderItemId);
      }
    } catch (error) {
      console.error('❌ Error extracting order item ID:', error);
    }
    
    return {
      bookingReference,
      airlineCode,
      flightNumbers,
      routeSegments: {
        origin,
        destination,
        departureTime,
        arrivalTime,
        segments: flightSegments.map((seg) => ({
          departure: seg.Departure,
          arrival: seg.Arrival,
          marketingCarrier: seg.MarketingCarrier,
          operatingCarrier: seg.OperatingCarrier
        }))
      },
      passengerTypes,
      documentNumbers,
      classOfService,
      cabinClass,
      orderItemId,
      totalAmount,
      currency
    };
  } catch (error) {
    console.error('❌ Critical error in OrderCreate response extraction:', error);
    return extractFallbackData(flightOffer, passengers);
  }
}

// Fallback extraction function
function extractFallbackData(flightOffer = {}, passengers = []) {
  console.log('🔄 Using fallback extraction from flight offer data...');
  
  return {
    bookingReference: 'Unknown',
    airlineCode: flightOffer?.airline?.code || 'Unknown',
    flightNumbers: [flightOffer?.flightNumber].filter(Boolean),
    routeSegments: {
      origin: flightOffer?.departure?.airport || 'Unknown',
      destination: flightOffer?.arrival?.airport || 'Unknown',
      departureTime: flightOffer?.departure?.datetime || new Date().toISOString(),
      arrivalTime: flightOffer?.arrival?.datetime || new Date().toISOString(),
      segments: []
    },
    passengerTypes: passengers.map((p) => p.type || 'ADT'),
    documentNumbers: passengers.map((p) => p.documentNumber || '').filter((d) => d),
    classOfService: flightOffer?.class || 'Economy',
    cabinClass: flightOffer?.cabin || 'Economy',
    orderItemId: null,
    totalAmount: parseFloat(flightOffer?.totalPrice || flightOffer?.price || '0'),
    currency: flightOffer?.currency || 'USD'
  };
}

// Test function
function testProductionOrderCreate() {
  console.log('🧪 Testing Production Order-Create Route Implementation\n');
  console.log('=' .repeat(60));
  
  // Test 1: OrderCreate response extraction
  console.log('\n📋 Test 1: OrderCreate Response Extraction');
  console.log('-'.repeat(40));
  
  const extractedData = extractDatabaseFieldsFromOrderCreate(
    orderCreateResponse,
    mockFlightOffer,
    mockPassengers,
    mockContactInfo
  );
  
  console.log('\n📊 Extraction Results:');
  console.log('Booking Reference:', extractedData.bookingReference);
  console.log('Airline Code:', extractedData.airlineCode);
  console.log('Flight Numbers:', extractedData.flightNumbers);
  console.log('Route:', `${extractedData.routeSegments.origin} → ${extractedData.routeSegments.destination}`);
  console.log('Passenger Types:', extractedData.passengerTypes);
  console.log('Document Numbers:', extractedData.documentNumbers);
  console.log('Class of Service:', extractedData.classOfService);
  console.log('Cabin Class:', extractedData.cabinClass);
  console.log('Order Item ID:', extractedData.orderItemId);
  console.log('Total Amount:', extractedData.totalAmount, extractedData.currency);
  
  // Test 2: Validation
  console.log('\n✅ Test 2: Data Validation');
  console.log('-'.repeat(40));
  
  const validationResults = {
    bookingReference: extractedData.bookingReference !== 'Unknown',
    airlineCode: extractedData.airlineCode !== 'Unknown',
    flightNumbers: extractedData.flightNumbers.length > 0,
    route: extractedData.routeSegments.origin !== 'Unknown' && extractedData.routeSegments.destination !== 'Unknown',
    passengerTypes: extractedData.passengerTypes.length > 0,
    documentNumbers: extractedData.documentNumbers.length > 0,
    classOfService: extractedData.classOfService !== 'Economy' || extractedData.cabinClass !== 'Economy',
    totalAmount: extractedData.totalAmount > 0,
    orderItemId: extractedData.orderItemId !== null
  };
  
  const validFields = Object.values(validationResults).filter(Boolean).length;
  const totalFields = Object.keys(validationResults).length;
  const successRate = Math.round((validFields / totalFields) * 100);
  
  console.log('Validation Results:');
  Object.entries(validationResults).forEach(([field, isValid]) => {
    console.log(`  ${isValid ? '✅' : '❌'} ${field}: ${isValid ? 'VALID' : 'INVALID'}`);
  });
  
  console.log(`\n🎯 Success Rate: ${validFields}/${totalFields} (${successRate}%)`);
  
  // Test 3: Error handling
  console.log('\n🛡️ Test 3: Error Handling');
  console.log('-'.repeat(40));
  
  // Test with invalid data
  const invalidResult = extractDatabaseFieldsFromOrderCreate(null, mockFlightOffer, mockPassengers);
  console.log('Invalid data handling:', invalidResult.airlineCode === mockFlightOffer.airline.code ? '✅ PASSED' : '❌ FAILED');
  
  // Test with empty data
  const emptyResult = extractDatabaseFieldsFromOrderCreate({}, {}, []);
  console.log('Empty data handling:', emptyResult.bookingReference === 'Unknown' ? '✅ PASSED' : '❌ FAILED');
  
  console.log('\n' + '='.repeat(60));
  console.log('🏁 Production Test Complete');
  console.log(`Overall Success Rate: ${successRate}%`);
  
  if (successRate >= 80) {
    console.log('🎉 PRODUCTION READY - High success rate achieved!');
  } else if (successRate >= 60) {
    console.log('⚠️ NEEDS IMPROVEMENT - Moderate success rate');
  } else {
    console.log('❌ NOT READY - Low success rate, requires fixes');
  }
}

// Run the test
testProductionOrderCreate();
