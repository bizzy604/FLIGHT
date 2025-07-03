/**
 * Test script to validate database column mappings with OrderCreate response values
 * This test ensures that data extraction logic correctly maps OrderCreate response to database fields
 */

const fs = require('fs');
const path = require('path');

// Load test data
function loadOrderCreateResponse() {
  try {
    const testDataPath = path.join(__dirname, '..', 'OrdercreateRS.json');
    const rawData = fs.readFileSync(testDataPath, 'utf8');
    return JSON.parse(rawData);
  } catch (error) {
    console.error('Error loading OrderCreate response:', error);
    return null;
  }
}

// Simulate the extraction logic from order-create route
function extractDatabaseFields(orderCreateResponse, mockFlightOffer = {}, mockPassengers = [], mockContactInfo = {}) {
  const response = orderCreateResponse.Response || orderCreateResponse;
  
  // Extract airline code from OrderCreate response
  const orders = Array.isArray(response.Order) ? response.Order : [response.Order].filter(Boolean);
  const firstOrder = orders[0] || {};
  const orderItems = firstOrder.OrderItems?.OrderItem || [];
  const flightItem = orderItems.find(item => item.FlightItem);
  const flightSegmentRefs = flightItem?.FlightItem?.FlightSegmentReference || [];
  
  // Get flight segments from DataLists
  const flightSegments = response.DataLists?.FlightSegmentList?.FlightSegment || [];
  const firstSegment = flightSegments[0];
  
  // Extract airline code
  const airlineCode = firstSegment?.MarketingCarrier?.AirlineID?.value || 
                     firstSegment?.OperatingCarrier?.AirlineID?.value || 
                     'Unknown';
  
  // Extract flight numbers
  const flightNumbers = flightSegments.map(segment => 
    segment.MarketingCarrier?.FlightNumber?.value || 
    segment.OperatingCarrier?.FlightNumber?.value || 
    'Unknown'
  ).filter(fn => fn !== 'Unknown');
  
  // Extract route information
  const origin = firstSegment?.Departure?.AirportCode?.value || 'Unknown';
  const destination = flightSegments[flightSegments.length - 1]?.Arrival?.AirportCode?.value || 'Unknown';
  
  // Extract departure and arrival times
  const departureTime = firstSegment?.Departure?.Date || firstSegment?.Departure?.Time || new Date().toISOString();
  const arrivalTime = flightSegments[flightSegments.length - 1]?.Arrival?.Date || 
                     flightSegments[flightSegments.length - 1]?.Arrival?.Time || 
                     new Date().toISOString();
  
  // Extract passenger information from OrderCreate response
  const passengers = response.Passengers?.Passenger || [];
  const passengerTypes = passengers.map(p => p.PTC?.value || 'ADT');
  
  // Extract document numbers from PassengerDocument
  const documentNumbers = [];
  passengers.forEach(passenger => {
    const passengerDocs = passenger.PassengerIDInfo?.PassengerDocument || [];
    passengerDocs.forEach(doc => {
      if (doc.ID) {
        documentNumbers.push(doc.ID);
      }
    });
  });
  
  // Extract class of service from fare basis
  const fareComponents = response.DataLists?.FareList?.FareGroup?.[0]?.Fare?.[0]?.FareDetail?.[0]?.FareComponent || [];
  const classOfService = fareComponents[0]?.FareBasisCode?.Code || 'Economy';
  
  // Extract cabin class from service definitions
  const serviceDefinitions = response.DataLists?.ServiceDefinitionList?.ServiceDefinition || [];
  const cabinService = serviceDefinitions.find(service => service.Name?.includes('Cabin') || service.Name?.includes('Class'));
  const cabinClass = cabinService?.Name || 'Economy';
  
  // Extract total amount from pricing
  const totalPriceBreakdown = firstOrder.TotalOrderPrice?.SimpleCurrencyPrice ||
                             response.TotalPrice?.DetailCurrencyPrice?.Total ||
                             response.TotalPrice?.SimpleCurrencyPrice || {};
  const totalAmount = parseFloat(totalPriceBreakdown.value || '0');
  const currency = totalPriceBreakdown.Code || 'USD';

  // Extract booking reference
  const bookingReference = firstOrder.BookingReferences?.BookingReference?.[0]?.ID ||
                          firstOrder.OrderID?.value ||
                          'Unknown';
  
  // Extract order item ID
  const orderItemId = orderItems[0]?.OrderItemID?.value || null;
  
  return {
    // Database field mappings
    bookingReference,
    airlineCode,
    flightNumbers,
    routeSegments: {
      origin,
      destination,
      departureTime,
      arrivalTime,
      segments: flightSegments.map(seg => ({
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
    currency,
    
    // Additional extracted data for validation
    extractedData: {
      totalPassengers: passengers.length,
      totalSegments: flightSegments.length,
      hasIdentityDocuments: documentNumbers.length > 0,
      hasFareComponents: fareComponents.length > 0,
      hasServiceDefinitions: serviceDefinitions.length > 0,
      hasPricing: !!totalPriceBreakdown.value,
      totalPriceValue: totalPriceBreakdown.value
    }
  };
}

// Validation tests
function validateDatabaseMapping(extractedFields) {
  console.log('\n=== DATABASE MAPPING VALIDATION ===');
  
  const validationChecks = [
    {
      name: 'Booking Reference extracted',
      pass: extractedFields.bookingReference && extractedFields.bookingReference !== 'Unknown',
      value: extractedFields.bookingReference
    },
    {
      name: 'Airline Code extracted',
      pass: extractedFields.airlineCode && extractedFields.airlineCode !== 'Unknown',
      value: extractedFields.airlineCode
    },
    {
      name: 'Flight Numbers extracted',
      pass: extractedFields.flightNumbers && extractedFields.flightNumbers.length > 0,
      value: extractedFields.flightNumbers
    },
    {
      name: 'Route Segments extracted',
      pass: extractedFields.routeSegments.origin !== 'Unknown' && extractedFields.routeSegments.destination !== 'Unknown',
      value: `${extractedFields.routeSegments.origin} → ${extractedFields.routeSegments.destination}`
    },
    {
      name: 'Passenger Types extracted',
      pass: extractedFields.passengerTypes && extractedFields.passengerTypes.length > 0,
      value: extractedFields.passengerTypes
    },
    {
      name: 'Document Numbers extracted',
      pass: extractedFields.documentNumbers && extractedFields.documentNumbers.length > 0,
      value: extractedFields.documentNumbers.length + ' documents'
    },
    {
      name: 'Class of Service extracted',
      pass: extractedFields.classOfService && extractedFields.classOfService !== 'Economy',
      value: extractedFields.classOfService
    },
    {
      name: 'Total Amount extracted',
      pass: extractedFields.totalAmount > 0,
      value: `${extractedFields.totalAmount} ${extractedFields.currency}`
    },
    {
      name: 'Order Item ID extracted',
      pass: !!extractedFields.orderItemId,
      value: extractedFields.orderItemId
    }
  ];
  
  console.log('Database Field Extraction Results:');
  validationChecks.forEach(check => {
    const status = check.pass ? '✅' : '❌';
    console.log(`  ${status} ${check.name}: ${check.value || 'Not found'}`);
  });
  
  // Additional data structure validation
  console.log('\nAdditional Data Structure Validation:');
  const additionalChecks = [
    { name: 'Total Passengers', value: extractedFields.extractedData.totalPassengers },
    { name: 'Total Flight Segments', value: extractedFields.extractedData.totalSegments },
    { name: 'Has Identity Documents', value: extractedFields.extractedData.hasIdentityDocuments },
    { name: 'Has Fare Components', value: extractedFields.extractedData.hasFareComponents },
    { name: 'Has Service Definitions', value: extractedFields.extractedData.hasServiceDefinitions },
    { name: 'Has Pricing Data', value: extractedFields.extractedData.hasPricing }
  ];
  
  additionalChecks.forEach(check => {
    console.log(`  📊 ${check.name}: ${check.value}`);
  });
  
  const passedChecks = validationChecks.filter(check => check.pass).length;
  const totalChecks = validationChecks.length;
  
  console.log(`\n📈 Validation Score: ${passedChecks}/${totalChecks} (${Math.round(passedChecks/totalChecks*100)}%)`);
  
  return passedChecks === totalChecks;
}

// Compare with current extraction logic
function compareExtractionMethods(orderCreateResponse) {
  console.log('\n=== EXTRACTION METHOD COMPARISON ===');
  
  // Method 1: Direct OrderCreate response extraction (new approach)
  const directExtraction = extractDatabaseFields(orderCreateResponse);
  
  // Method 2: Flight offer based extraction (current approach in route.ts)
  // This would typically use the flight offer data passed from frontend
  const mockFlightOffer = {
    airline: { code: 'MOCK' },
    flightNumber: 'MOCK123',
    departure: { airport: 'MOCK_DEP' },
    arrival: { airport: 'MOCK_ARR' }
  };
  
  console.log('Direct OrderCreate Extraction:');
  console.log(`  Airline: ${directExtraction.airlineCode}`);
  console.log(`  Flight Numbers: ${directExtraction.flightNumbers.join(', ')}`);
  console.log(`  Route: ${directExtraction.routeSegments.origin} → ${directExtraction.routeSegments.destination}`);
  console.log(`  Passengers: ${directExtraction.passengerTypes.join(', ')}`);
  console.log(`  Total Amount: ${directExtraction.totalAmount} ${directExtraction.currency}`);
  
  console.log('\nRecommendation:');
  console.log('✅ Use OrderCreate response as primary data source for database fields');
  console.log('✅ Flight offer data should be used as fallback only');
  console.log('✅ OrderCreate response contains authoritative booking information');
  
  return directExtraction;
}

// Main test execution
function runDatabaseMappingTests() {
  console.log('🗄️  DATABASE MAPPING VALIDATION TEST');
  console.log('=====================================');
  
  const orderCreateResponse = loadOrderCreateResponse();
  if (!orderCreateResponse) {
    console.error('❌ Failed to load OrderCreate response');
    return false;
  }
  
  console.log('✅ OrderCreate response loaded successfully');
  
  // Extract database fields using improved logic
  const extractedFields = extractDatabaseFields(orderCreateResponse);
  
  // Validate the extraction
  const validationPassed = validateDatabaseMapping(extractedFields);
  
  // Compare extraction methods
  compareExtractionMethods(orderCreateResponse);
  
  console.log(`\n🎯 Overall Result: ${validationPassed ? 'VALIDATION PASSED' : 'VALIDATION NEEDS IMPROVEMENT'}`);
  
  return validationPassed;
}

// Run the tests
if (require.main === module) {
  runDatabaseMappingTests();
}

module.exports = {
  runDatabaseMappingTests,
  extractDatabaseFields,
  validateDatabaseMapping,
  loadOrderCreateResponse
};
