# Database Retrieval Tests

This directory contains comprehensive tests to verify that the `orderCreateResponse` and `originalFlightOffer` JSON columns in the booking model are correctly storing and retrieving data for both confirmation pages and itinerary generation.

## Test Files

### 1. `database-retrieval-test.ts`
- **Purpose**: Comprehensive TypeScript test suite
- **Features**: 
  - Creates test booking with complete JSON data
  - Tests confirmation page data retrieval
  - Tests itinerary generation and transformation
  - Validates data integrity and structure
  - Automatic cleanup

### 2. `test-database-simple.js` (in scripts folder)
- **Purpose**: Simple Node.js test that can be run directly
- **Features**:
  - Basic database operations test
  - JSON data integrity validation
  - Data extraction simulation
  - Easy to run and understand

## How to Run Tests

### Option 1: Simple Node.js Test (Recommended)
```bash
cd Frontend
node scripts/test-database-simple.js
```

### Option 2: TypeScript Test Suite
```bash
cd Frontend
npx tsx scripts/run-database-tests.ts
```

### Option 3: Add to package.json (if not already added)
Add this to your `package.json` scripts section:
```json
{
  "scripts": {
    "test:database": "node scripts/test-database-simple.js",
    "test:database:full": "npx tsx scripts/run-database-tests.ts"
  }
}
```

Then run:
```bash
npm run test:database
```

## What These Tests Verify

### ✅ Database Storage
- `orderCreateResponse` JSON column stores complete OrderCreate API response
- `originalFlightOffer` JSON column stores original flight offer data
- Data is stored as proper JSON objects (not strings)
- All essential indexing fields are populated correctly

### ✅ Confirmation Page Data Retrieval
- Booking can be retrieved by booking reference
- Essential fields are accessible: `bookingReference`, `flightDetails`, `passengerDetails`, `contactInfo`, `totalAmount`
- JSON columns contain complete data structures
- Data format matches what confirmation page expects

### ✅ Itinerary Generation
- OrderCreate response can be parsed and transformed
- All required data points are extractable:
  - Booking reference from `Order[0].BookingReferences.BookingReference[0].ID`
  - Passenger names from `Passengers.Passenger[0].Name`
  - Flight details from `DataLists.FlightSegmentList.FlightSegment`
  - Pricing from `Order[0].TotalOrderPrice`
- Transformation function works with stored data
- Generated itinerary contains all necessary information

### ✅ Data Integrity
- JSON data maintains proper structure after database round-trip
- No data loss during storage/retrieval
- Type consistency (objects remain objects, not converted to strings)
- All nested properties are accessible

## Expected Test Output

When tests pass, you should see:
```
🚀 Starting Database Retrieval Tests
====================================

🧪 Creating test booking...
✅ Test booking created: { id: 123, bookingReference: 'TEST_1234567890', hasOrderCreateResponse: true, hasOriginalFlightOffer: true }

🧪 Testing data retrieval...
📋 Data retrieval tests: { hasBookingReference: true, hasFlightDetails: true, ... }
📋 JSON data integrity tests: { orderCreateHasResponse: true, orderCreateHasOrder: true, ... }
📋 Data extraction tests: { canExtractBookingRef: true, canExtractPassengerName: true, ... }

✅ ALL TESTS PASSED - Database retrieval working correctly!

📋 Sample extracted data:
- Booking Reference: 1802459
- Passenger Name: AMONI EROT
- Flight Number: 423
- Route: BOM → SIN
- Total Price: 35541 INR

🧪 Cleaning up test data...
✅ Test data cleaned up successfully

📊 FINAL RESULT:
🎉 ALL TESTS PASSED - orderCreateResponse and originalFlightOffer columns are working correctly!
✅ Confirmation pages can retrieve all necessary data
✅ Itinerary generation can access complete OrderCreate response
✅ Data integrity is maintained in JSON columns
```

## Troubleshooting

### Database Connection Issues
- Ensure your `.env` file has correct `DATABASE_URL`
- Make sure PostgreSQL is running
- Verify Prisma client is generated: `npx prisma generate`

### Test Failures
- Check that the booking model schema matches the test expectations
- Verify that `orderCreateResponse` and `originalFlightOffer` columns exist
- Ensure JSON data types are properly configured in PostgreSQL

### Missing Dependencies
If you get import errors:
```bash
npm install @prisma/client
npx prisma generate
```

## Integration with Existing Code

These tests validate that your current implementation correctly:

1. **Stores comprehensive data** in the JSON columns during order creation
2. **Retrieves complete data** for confirmation page display
3. **Transforms data properly** for itinerary generation
4. **Maintains data integrity** throughout the process

The tests simulate exactly what your confirmation pages and itinerary generation code do, ensuring the database layer works correctly with your existing frontend components.
