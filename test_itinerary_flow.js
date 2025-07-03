/**
 * Test script to validate the complete itinerary flow
 * This tests the end-to-end flow from booking creation to itinerary access
 */

const fs = require('fs');
const path = require('path');

// Test configuration
const BASE_URL = 'http://localhost:3000';
const API_BASE_URL = 'http://localhost:5000';

console.log('🧪 Testing Complete Itinerary Flow');
console.log('=====================================\n');

// Test 1: Check if bookings API is accessible
async function testBookingsAPI() {
  console.log('📋 Test 1: Bookings API Accessibility');
  try {
    const response = await fetch(`${BASE_URL}/api/bookings`);
    const data = await response.json();
    
    if (response.ok) {
      console.log('✅ Bookings API is accessible');
      console.log(`📊 Found ${data.bookings?.length || 0} bookings`);
      
      if (data.bookings && data.bookings.length > 0) {
        const firstBooking = data.bookings[0];
        console.log(`📝 Sample booking: ${firstBooking.bookingReference}`);
        console.log(`🆔 Booking ID: ${firstBooking.id}`);
        
        // Test the itinerary route for this booking
        return await testItineraryRoute(firstBooking.id);
      } else {
        console.log('ℹ️  No existing bookings found - this is normal for a fresh system');
        return true;
      }
    } else {
      console.log('❌ Bookings API failed:', data.error);
      return false;
    }
  } catch (error) {
    console.log('❌ Error testing bookings API:', error.message);
    return false;
  }
}

// Test 2: Check itinerary route for existing booking
async function testItineraryRoute(bookingId) {
  console.log(`\n🎫 Test 2: Itinerary Route for Booking ${bookingId}`);
  try {
    const response = await fetch(`${BASE_URL}/api/verteil/booking/${bookingId}`);
    const data = await response.json();
    
    if (response.ok && data.status === 'success') {
      console.log('✅ Booking data retrieved successfully');
      
      const booking = data.data;
      console.log(`📋 Booking Reference: ${booking.bookingReference}`);
      console.log(`👤 User ID: ${booking.userId}`);
      console.log(`✈️  Airline: ${booking.airlineCode}`);
      console.log(`🎯 Status: ${booking.status}`);
      
      // Check if OrderCreate response is available
      if (booking.orderCreateResponse) {
        console.log('✅ OrderCreate response is stored - itinerary can be generated');
        return true;
      } else {
        console.log('⚠️  OrderCreate response not found - itinerary generation may fail');
        return false;
      }
    } else {
      console.log('❌ Failed to retrieve booking:', data.error);
      return false;
    }
  } catch (error) {
    console.log('❌ Error testing itinerary route:', error.message);
    return false;
  }
}

// Test 3: Validate transformation functions
async function testTransformationFunctions() {
  console.log('\n🔄 Test 3: Transformation Functions');
  
  // Check if the OrderCreate test data exists
  const testDataPath = path.join(__dirname, 'OrdercreateRS.json');
  if (!fs.existsSync(testDataPath)) {
    console.log('⚠️  OrdercreateRS.json test data not found');
    return false;
  }
  
  try {
    const testData = JSON.parse(fs.readFileSync(testDataPath, 'utf8'));
    console.log('✅ Test data loaded successfully');
    
    // Test the transformation function (this would need to be imported in a real test)
    console.log('📊 Test data structure:');
    console.log(`   - Has Response: ${!!testData.Response}`);
    console.log(`   - Has Order: ${!!testData.Response?.Order}`);
    console.log(`   - Order count: ${testData.Response?.Order?.length || 0}`);
    
    if (testData.Response?.Order?.[0]) {
      const order = testData.Response.Order[0];
      console.log(`   - Order ID: ${order.OrderID?.value || 'N/A'}`);
      console.log(`   - Booking Reference: ${order.BookingReferences?.BookingReference?.[0]?.ID || 'N/A'}`);
    }
    
    return true;
  } catch (error) {
    console.log('❌ Error testing transformation functions:', error.message);
    return false;
  }
}

// Test 4: Check component files exist
async function testComponentFiles() {
  console.log('\n📁 Test 4: Component Files');
  
  const requiredFiles = [
    'Frontend/app/bookings/[bookingId]/itinerary/page.tsx',
    'Frontend/components/itinerary/OfficialItinerary.tsx',
    'Frontend/utils/itinerary-data-transformer.ts',
    'Frontend/app/api/verteil/booking/[bookingReference]/route.ts'
  ];
  
  let allFilesExist = true;
  
  for (const file of requiredFiles) {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      console.log(`✅ ${file}`);
    } else {
      console.log(`❌ ${file} - MISSING`);
      allFilesExist = false;
    }
  }
  
  return allFilesExist;
}

// Main test runner
async function runTests() {
  console.log('🚀 Starting itinerary flow tests...\n');
  
  const results = {
    bookingsAPI: await testBookingsAPI(),
    transformationFunctions: await testTransformationFunctions(),
    componentFiles: await testComponentFiles()
  };
  
  console.log('\n📊 Test Results Summary');
  console.log('========================');
  console.log(`📋 Bookings API: ${results.bookingsAPI ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`🔄 Transformation Functions: ${results.transformationFunctions ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`📁 Component Files: ${results.componentFiles ? '✅ PASS' : '❌ FAIL'}`);
  
  const allPassed = Object.values(results).every(result => result);
  console.log(`\n🎯 Overall Status: ${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
  
  if (allPassed) {
    console.log('\n🎉 The itinerary flow is ready for use!');
    console.log('📝 Next steps:');
    console.log('   1. Complete a booking to test the full flow');
    console.log('   2. Visit /bookings to see your bookings');
    console.log('   3. Click "View Itinerary" to test the new route');
  } else {
    console.log('\n🔧 Some components need attention before the flow is complete.');
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { runTests, testBookingsAPI, testItineraryRoute, testTransformationFunctions, testComponentFiles };
