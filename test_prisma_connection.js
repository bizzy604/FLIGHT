/**
 * Direct test of Prisma database connection
 */

// Load environment variables
require('dotenv').config({ path: './Frontend/.env' });

const { PrismaClient } = require('./Frontend/node_modules/@prisma/client');

async function testPrismaConnection() {
  console.log('🔍 Testing Prisma Database Connection');
  console.log('=====================================\n');

  const prisma = new PrismaClient({
    log: ['query', 'info', 'warn', 'error'],
  });

  try {
    console.log('📡 Attempting to connect to database...');
    
    // Test basic connection
    await prisma.$connect();
    console.log('✅ Database connection successful!');

    // Test a simple query
    console.log('\n📊 Testing simple query...');
    const result = await prisma.$queryRaw`SELECT 1 as test`;
    console.log('✅ Query test successful:', result);

    // Test booking table access
    console.log('\n📋 Testing booking table access...');
    const bookingCount = await prisma.booking.count();
    console.log(`✅ Booking table accessible. Found ${bookingCount} bookings.`);

    // Test booking table structure
    console.log('\n🏗️  Testing booking table structure...');
    const firstBooking = await prisma.booking.findFirst({
      select: {
        id: true,
        bookingReference: true,
        userId: true,
        status: true,
        createdAt: true,
        orderCreateResponse: true,
        originalFlightOffer: true
      }
    });

    if (firstBooking) {
      console.log('✅ Booking table structure test successful');
      console.log('📝 Sample booking fields:');
      console.log(`   🆔 ID: ${firstBooking.id}`);
      console.log(`   📋 Reference: ${firstBooking.bookingReference}`);
      console.log(`   👤 User ID: ${firstBooking.userId}`);
      console.log(`   🎯 Status: ${firstBooking.status}`);
      console.log(`   📅 Created: ${firstBooking.createdAt}`);
      console.log(`   📄 OrderCreate Response: ${firstBooking.orderCreateResponse ? 'Available' : 'Not available'}`);
      console.log(`   ✈️  Original Flight Offer: ${firstBooking.originalFlightOffer ? 'Available' : 'Not available'}`);
    } else {
      console.log('ℹ️  No bookings found in database (this is normal for a fresh system)');
    }

    console.log('\n🎉 All Prisma tests passed successfully!');
    return true;

  } catch (error) {
    console.log('❌ Prisma connection failed:');
    console.log(`📄 Error: ${error.message}`);
    console.log(`🔧 Error Code: ${error.code || 'Unknown'}`);
    
    if (error.message.includes('URL must start with the protocol')) {
      console.log('\n💡 Troubleshooting suggestions:');
      console.log('   1. Check DATABASE_URL in .env file');
      console.log('   2. Ensure the URL format is correct');
      console.log('   3. Try running: npx prisma db push');
      console.log('   4. Try running: npx prisma generate');
    }
    
    return false;
  } finally {
    await prisma.$disconnect();
    console.log('\n🔌 Database connection closed.');
  }
}

// Run the test
testPrismaConnection()
  .then(success => {
    if (success) {
      console.log('\n✅ Prisma is working correctly!');
      process.exit(0);
    } else {
      console.log('\n❌ Prisma connection issues detected.');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('❌ Unexpected error:', error);
    process.exit(1);
  });
