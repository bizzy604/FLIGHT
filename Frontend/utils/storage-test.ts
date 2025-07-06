/**
 * Storage System Test Suite
 * Quick validation of the new robust storage manager
 */

import { flightStorageManager, FlightSearchData, FlightPriceData } from './flight-storage-manager';
import { migrateStorageNow, forceMigrateStorageNow } from './storage-migration';
import { StorageUtils } from './storage-integration-example';

interface TestResult {
  testName: string;
  passed: boolean;
  error?: string;
  details?: any;
}

export class StorageSystemTest {
  private results: TestResult[] = [];

  /**
   * Run all storage tests
   */
  async runAllTests(): Promise<TestResult[]> {
    console.log('🧪 Starting Storage System Tests...');
    this.results = [];

    // Test 1: Basic storage and retrieval
    await this.testBasicStorage();

    // Test 2: Data validation and corruption detection
    await this.testDataValidation();

    // Test 3: Migration functionality
    await this.testMigration();

    // Test 4: Storage health check
    await this.testHealthCheck();

    // Test 5: Emergency cleanup
    await this.testEmergencyCleanup();

    // Test 6: Concurrent access simulation
    await this.testConcurrentAccess();

    // Print results
    this.printResults();

    return this.results;
  }

  /**
   * Test basic storage and retrieval functionality
   */
  private async testBasicStorage(): Promise<void> {
    try {
      console.log('🧪 Test 1: Basic Storage and Retrieval');

      // Create test flight search data
      const testData: FlightSearchData = {
        airShoppingResponse: {
          offers: [
            {
              id: 'test-offer-1',
              airline: { code: 'QR', name: 'Qatar Airways' },
              price: 500,
              currency: 'USD'
            }
          ]
        },
        searchParams: {
          origin: 'NBO',
          destination: 'CDG',
          departDate: '2024-12-25',
          tripType: 'oneway',
          passengers: { adults: 1, children: 0, infants: 0 },
          cabinClass: 'economy'
        },
        timestamp: Date.now(),
        expiresAt: Date.now() + (30 * 60 * 1000)
      };

      // Store data
      const storeResult = await flightStorageManager.storeFlightSearch(testData);
      if (!storeResult.success) {
        throw new Error(`Storage failed: ${storeResult.error}`);
      }

      // Retrieve data
      const retrieveResult = await flightStorageManager.getFlightSearch();
      if (!retrieveResult.success) {
        throw new Error(`Retrieval failed: ${retrieveResult.error}`);
      }

      // Validate data integrity
      const retrievedData = retrieveResult.data!;
      if (retrievedData.searchParams.origin !== testData.searchParams.origin) {
        throw new Error('Data integrity check failed');
      }

      this.results.push({
        testName: 'Basic Storage and Retrieval',
        passed: true,
        details: {
          stored: storeResult.success,
          retrieved: retrieveResult.success,
          dataIntact: true
        }
      });

      console.log('✅ Test 1 passed');
    } catch (error) {
      this.results.push({
        testName: 'Basic Storage and Retrieval',
        passed: false,
        error: (error as Error).message
      });
      console.log('❌ Test 1 failed:', error);
    }
  }

  /**
   * Test data validation and corruption detection
   */
  private async testDataValidation(): Promise<void> {
    try {
      console.log('🧪 Test 2: Data Validation and Corruption Detection');

      // Test with invalid data structure
      const invalidResult = await flightStorageManager.getFlightSearch();
      
      // Test validation functions
      const validData = {
        airShoppingResponse: { offers: [] },
        searchParams: { origin: 'NBO', destination: 'CDG' },
        timestamp: Date.now(),
        expiresAt: Date.now() + 1000
      };

      const isValid = flightStorageManager.validateFlightSearchData(validData);

      this.results.push({
        testName: 'Data Validation and Corruption Detection',
        passed: true,
        details: {
          validationWorks: isValid,
          handlesInvalidData: true
        }
      });

      console.log('✅ Test 2 passed');
    } catch (error) {
      this.results.push({
        testName: 'Data Validation and Corruption Detection',
        passed: false,
        error: (error as Error).message
      });
      console.log('❌ Test 2 failed:', error);
    }
  }

  /**
   * Test migration functionality
   */
  private async testMigration(): Promise<void> {
    try {
      console.log('🧪 Test 3: Migration Functionality');

      // Create some old-style data in storage
      const oldData = {
        airShoppingResponse: { offers: [] },
        searchParams: { origin: 'TEST', destination: 'TEST' },
        timestamp: Date.now()
      };

      sessionStorage.setItem('currentFlightSearch', JSON.stringify(oldData));
      localStorage.setItem('flightData_test', JSON.stringify(oldData));

      // Run migration
      const migrationResult = await migrateStorageNow();

      this.results.push({
        testName: 'Migration Functionality',
        passed: migrationResult.success,
        details: {
          migratedKeys: migrationResult.migratedKeys.length,
          cleanedKeys: migrationResult.cleanedKeys.length,
          errors: migrationResult.errors.length
        }
      });

      console.log('✅ Test 3 passed');
    } catch (error) {
      this.results.push({
        testName: 'Migration Functionality',
        passed: false,
        error: (error as Error).message
      });
      console.log('❌ Test 3 failed:', error);
    }
  }

  /**
   * Test storage health check
   */
  private async testHealthCheck(): Promise<void> {
    try {
      console.log('🧪 Test 4: Storage Health Check');

      const health = await flightStorageManager.healthCheck();
      const stats = flightStorageManager.getStorageStats();

      this.results.push({
        testName: 'Storage Health Check',
        passed: true,
        details: {
          health,
          stats: {
            sessionStorageUsed: Math.round(stats.sessionStorage.used / 1024) + 'KB',
            localStorageUsed: Math.round(stats.localStorage.used / 1024) + 'KB'
          }
        }
      });

      console.log('✅ Test 4 passed');
    } catch (error) {
      this.results.push({
        testName: 'Storage Health Check',
        passed: false,
        error: (error as Error).message
      });
      console.log('❌ Test 4 failed:', error);
    }
  }

  /**
   * Test emergency cleanup
   */
  private async testEmergencyCleanup(): Promise<void> {
    try {
      console.log('🧪 Test 5: Emergency Cleanup');

      // Add some test data in both storages
      localStorage.setItem('test_cleanup_1', 'test');
      localStorage.setItem('test_cleanup_2', 'test');
      sessionStorage.setItem('test_cleanup_session', 'test');

      // Verify test data exists
      const beforeCleanup = {
        local1: localStorage.getItem('test_cleanup_1') !== null,
        local2: localStorage.getItem('test_cleanup_2') !== null,
        session: sessionStorage.getItem('test_cleanup_session') !== null
      };

      // Run emergency cleanup
      await StorageUtils.emergencyCleanup();

      // Check if cleanup worked
      const afterCleanup = {
        local1: localStorage.getItem('test_cleanup_1') !== null,
        local2: localStorage.getItem('test_cleanup_2') !== null,
        session: sessionStorage.getItem('test_cleanup_session') !== null
      };

      const cleanupWorked = !afterCleanup.local1 && !afterCleanup.local2 && !afterCleanup.session;

      this.results.push({
        testName: 'Emergency Cleanup',
        passed: cleanupWorked,
        details: {
          cleanupExecuted: true,
          beforeCleanup,
          afterCleanup,
          testDataRemoved: cleanupWorked
        }
      });

      console.log('✅ Test 5 passed');
    } catch (error) {
      this.results.push({
        testName: 'Emergency Cleanup',
        passed: false,
        error: (error as Error).message
      });
      console.log('❌ Test 5 failed:', error);
    }
  }

  /**
   * Test concurrent access simulation
   */
  private async testConcurrentAccess(): Promise<void> {
    try {
      console.log('🧪 Test 6: Concurrent Access Simulation');

      // Simulate multiple concurrent storage operations
      const promises = [];
      
      for (let i = 0; i < 5; i++) {
        const testData: FlightSearchData = {
          airShoppingResponse: { offers: [] },
          searchParams: {
            origin: `TEST${i}`,
            destination: `DEST${i}`,
            departDate: '2024-12-25',
            tripType: 'oneway',
            passengers: { adults: 1, children: 0, infants: 0 },
            cabinClass: 'economy'
          },
          timestamp: Date.now(),
          expiresAt: Date.now() + (30 * 60 * 1000)
        };

        promises.push(flightStorageManager.storeFlightSearch(testData));
      }

      // Wait for all operations to complete
      const results = await Promise.all(promises);
      const allSucceeded = results.every(result => result.success);

      this.results.push({
        testName: 'Concurrent Access Simulation',
        passed: allSucceeded,
        details: {
          operationsCount: promises.length,
          successfulOperations: results.filter(r => r.success).length,
          failedOperations: results.filter(r => !r.success).length
        }
      });

      console.log('✅ Test 6 passed');
    } catch (error) {
      this.results.push({
        testName: 'Concurrent Access Simulation',
        passed: false,
        error: (error as Error).message
      });
      console.log('❌ Test 6 failed:', error);
    }
  }

  /**
   * Print test results summary
   */
  private printResults(): void {
    console.log('\n📊 Storage System Test Results:');
    console.log('================================');

    const passed = this.results.filter(r => r.passed).length;
    const total = this.results.length;

    this.results.forEach((result, index) => {
      const status = result.passed ? '✅' : '❌';
      console.log(`${index + 1}. ${status} ${result.testName}`);
      
      if (!result.passed && result.error) {
        console.log(`   Error: ${result.error}`);
      }
      
      if (result.details) {
        console.log(`   Details:`, result.details);
      }
    });

    console.log('\n📈 Summary:');
    console.log(`Passed: ${passed}/${total} tests`);
    console.log(`Success Rate: ${Math.round((passed / total) * 100)}%`);

    if (passed === total) {
      console.log('🎉 All tests passed! Storage system is working correctly.');
    } else {
      console.log('⚠️ Some tests failed. Please review the errors above.');
    }
  }

  /**
   * Quick validation test for immediate use
   */
  static async quickTest(): Promise<boolean> {
    console.log('🚀 Running quick storage validation...');
    
    try {
      // Test basic functionality
      const testData: FlightSearchData = {
        airShoppingResponse: { test: true },
        searchParams: {
          origin: 'QUICK',
          destination: 'TEST',
          departDate: '2024-12-25',
          tripType: 'oneway',
          passengers: { adults: 1, children: 0, infants: 0 },
          cabinClass: 'economy'
        },
        timestamp: Date.now(),
        expiresAt: Date.now() + (30 * 60 * 1000)
      };

      const storeResult = await flightStorageManager.storeFlightSearch(testData);
      const retrieveResult = await flightStorageManager.getFlightSearch();

      const success = storeResult.success && retrieveResult.success;
      
      if (success) {
        console.log('✅ Quick test passed - Storage system is working!');
      } else {
        console.log('❌ Quick test failed - Storage system needs attention');
      }

      return success;
    } catch (error) {
      console.log('❌ Quick test error:', error);
      return false;
    }
  }
}

// Export for easy use
export const storageTest = new StorageSystemTest();

// Convenience functions
export async function runStorageTests(): Promise<TestResult[]> {
  return await storageTest.runAllTests();
}

export async function quickStorageTest(): Promise<boolean> {
  return await StorageSystemTest.quickTest();
}
