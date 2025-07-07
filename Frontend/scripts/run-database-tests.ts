#!/usr/bin/env tsx

/**
 * Test runner script for database retrieval tests
 * 
 * Usage:
 * npm run test:database
 * or
 * npx tsx scripts/run-database-tests.ts
 */

import { DatabaseRetrievalTest } from '../tests/database-retrieval-test';

async function main() {
  console.log('🔧 Database Retrieval Test Suite');
  console.log('================================\n');
  
  try {
    await DatabaseRetrievalTest.runAllTests();
  } catch (error) {
    console.error('❌ Test runner failed:', error);
    process.exit(1);
  }
}

// Run the tests
main().catch(console.error);
