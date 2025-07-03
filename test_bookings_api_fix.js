/**
 * Quick test to verify the bookings API fix
 * Run this after starting the development server
 */

const BASE_URL = 'http://localhost:3000';

async function testBookingsAPI() {
  console.log('🧪 Testing Bookings API Fix');
  console.log('============================\n');

  try {
    console.log('📡 Making request to /api/bookings...');
    
    const response = await fetch(`${BASE_URL}/api/bookings`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`📊 Response Status: ${response.status}`);
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ API Request Successful!');
      console.log(`📋 Found ${data.bookings?.length || 0} bookings`);
      
      if (data.pagination) {
        console.log(`📄 Pagination: Page ${data.pagination.page} of ${data.pagination.pages}`);
        console.log(`📊 Total Records: ${data.pagination.total}`);
      }

      if (data.bookings && data.bookings.length > 0) {
        const firstBooking = data.bookings[0];
        console.log('\n📝 Sample Booking Data:');
        console.log(`   🆔 ID: ${firstBooking.id}`);
        console.log(`   📋 Reference: ${firstBooking.bookingReference}`);
        console.log(`   👤 User ID: ${firstBooking.userId}`);
        console.log(`   ✈️  Airline: ${firstBooking.airlineCode || 'N/A'}`);
        console.log(`   🎯 Status: ${firstBooking.status}`);
        console.log(`   💰 Amount: ${firstBooking.totalAmount}`);
        console.log(`   📅 Created: ${new Date(firstBooking.createdAt).toLocaleDateString()}`);
        
        // Check if new fields exist
        if (firstBooking.orderCreateResponse) {
          console.log('   ✅ OrderCreate Response: Available');
        } else {
          console.log('   ⚠️  OrderCreate Response: Not available (expected for old bookings)');
        }
        
        if (firstBooking.originalFlightOffer) {
          console.log('   ✅ Original Flight Offer: Available');
        } else {
          console.log('   ⚠️  Original Flight Offer: Not available (expected for old bookings)');
        }
      } else {
        console.log('\nℹ️  No bookings found - this is normal for a fresh system');
      }

      console.log('\n🎉 Bookings API is working correctly!');
      console.log('\n📝 Next Steps:');
      console.log('   1. Complete a new booking to test the full flow');
      console.log('   2. Check that new bookings include OrderCreate response');
      console.log('   3. Test the itinerary route with a booking ID');
      
      return true;
    } else {
      const errorData = await response.text();
      console.log('❌ API Request Failed');
      console.log(`📄 Error Response: ${errorData}`);
      return false;
    }
  } catch (error) {
    console.log('❌ Network Error:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   1. Make sure the development server is running: npm run dev');
    console.log('   2. Check that the database is accessible');
    console.log('   3. Verify Prisma client is generated: npx prisma generate');
    return false;
  }
}

// Test database connection info
async function testDatabaseConnection() {
  console.log('\n🗄️  Testing Database Connection');
  console.log('================================');
  
  try {
    const response = await fetch(`${BASE_URL}/api/bookings?limit=1`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      console.log('✅ Database connection is working');
      return true;
    } else {
      console.log('❌ Database connection issue');
      const errorText = await response.text();
      console.log(`📄 Error: ${errorText}`);
      return false;
    }
  } catch (error) {
    console.log('❌ Database connection failed:', error.message);
    return false;
  }
}

// Main test function
async function runTests() {
  console.log('🚀 Starting Bookings API Tests...\n');
  
  const dbTest = await testDatabaseConnection();
  const apiTest = await testBookingsAPI();
  
  console.log('\n📊 Test Results Summary');
  console.log('========================');
  console.log(`🗄️  Database Connection: ${dbTest ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`📡 Bookings API: ${apiTest ? '✅ PASS' : '❌ FAIL'}`);
  
  const allPassed = dbTest && apiTest;
  console.log(`\n🎯 Overall Status: ${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
  
  if (allPassed) {
    console.log('\n🎉 The Prisma fix worked! The bookings API is now functional.');
  } else {
    console.log('\n🔧 Additional troubleshooting may be needed.');
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { runTests, testBookingsAPI, testDatabaseConnection };
