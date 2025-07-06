/**
 * Storage Integration Example
 * Shows how to replace old storage patterns with the new robust storage manager
 */

import { flightStorageManager, FlightSearchData, FlightPriceData } from './flight-storage-manager';
import { migrateStorageNow } from './storage-migration';

/**
 * Example: How to replace old flight search storage
 */
export class FlightSearchStorageExample {
  
  // OLD WAY (PRONE TO CORRUPTION):
  /*
  storeFlightSearchOld(data: any) {
    try {
      const flightDataForStorage = {
        airShoppingResponse: data,
        searchParams: {...},
        timestamp: Date.now(),
        expiresAt: Date.now() + (30 * 60 * 1000)
      };
      
      // Multiple storage calls - race condition risk
      sessionStorage.setItem('currentFlightSearch', JSON.stringify(flightDataForStorage));
      localStorage.setItem('flightData_' + Date.now(), JSON.stringify(flightDataForStorage));
      localStorage.setItem('currentFlightDataKey', 'flightData_' + Date.now());
    } catch (error) {
      // Silent failure - data corruption risk
      console.error('Storage failed:', error);
    }
  }
  */

  // NEW WAY (ROBUST AND SAFE):
  async storeFlightSearch(airShoppingResponse: any, searchParams: any): Promise<boolean> {
    const flightSearchData: FlightSearchData = {
      airShoppingResponse,
      searchParams,
      timestamp: Date.now(),
      expiresAt: Date.now() + (30 * 60 * 1000) // 30 minutes
    };

    const result = await flightStorageManager.storeFlightSearch(flightSearchData);
    
    if (!result.success) {
      console.error('Failed to store flight search data:', result.error);
      return false;
    }

    console.log('✅ Flight search data stored successfully');
    return true;
  }

  // NEW WAY (ROBUST RETRIEVAL):
  async getFlightSearch(): Promise<FlightSearchData | null> {
    const result = await flightStorageManager.getFlightSearch();
    
    if (!result.success) {
      console.log('No valid flight search data found:', result.error);
      return null;
    }

    if (result.recovered) {
      console.log('🔄 Flight search data was recovered from backup storage');
    }

    return result.data || null;
  }
}

/**
 * Example: How to replace old flight price storage
 */
export class FlightPriceStorageExample {
  
  // NEW WAY (ROBUST STORAGE):
  async storeFlightPrice(
    flightId: string, 
    pricedOffer: any, 
    rawResponse: any, 
    searchParams: any
  ): Promise<boolean> {
    const flightPriceData: FlightPriceData = {
      flightId,
      pricedOffer,
      rawResponse,
      searchParams,
      timestamp: Date.now(),
      expiresAt: Date.now() + (30 * 60 * 1000) // 30 minutes
    };

    const result = await flightStorageManager.storeFlightPrice(flightPriceData);
    
    if (!result.success) {
      console.error('Failed to store flight price data:', result.error);
      return false;
    }

    console.log('✅ Flight price data stored successfully');
    return true;
  }

  // NEW WAY (ROBUST RETRIEVAL):
  async getFlightPrice(): Promise<FlightPriceData | null> {
    const result = await flightStorageManager.getFlightPrice();
    
    if (!result.success) {
      console.log('No valid flight price data found:', result.error);
      return null;
    }

    if (result.recovered) {
      console.log('🔄 Flight price data was recovered from backup storage');
    }

    return result.data || null;
  }
}

/**
 * Migration helper for existing applications
 */
export class StorageMigrationHelper {
  
  /**
   * Run migration on app startup
   */
  async runStartupMigration(): Promise<void> {
    console.log('🔄 Running storage migration on startup...');
    
    try {
      const migrationResult = await migrateStorageNow();
      
      if (migrationResult.success) {
        console.log('✅ Storage migration completed successfully');
        console.log(`📊 Migration summary:
          - Migrated keys: ${migrationResult.migratedKeys.length}
          - Cleaned keys: ${migrationResult.cleanedKeys.length}
          - Errors: ${migrationResult.errors.length}`);
        
        if (migrationResult.errors.length > 0) {
          console.warn('⚠️ Migration errors:', migrationResult.errors);
        }
      } else {
        console.error('❌ Storage migration failed');
      }
    } catch (error) {
      console.error('❌ Migration error:', error);
    }
  }

  /**
   * Health check for storage system
   */
  async performHealthCheck(): Promise<boolean> {
    try {
      const health = await flightStorageManager.healthCheck();
      const stats = flightStorageManager.getStorageStats();
      
      console.log('📊 Storage Health Check:', {
        health,
        stats: {
          sessionStorage: `${Math.round(stats.sessionStorage.used / 1024)}KB used, ${stats.sessionStorage.itemCount} items`,
          localStorage: `${Math.round(stats.localStorage.used / 1024)}KB used, ${stats.localStorage.itemCount} items`
        }
      });
      
      return health.overallHealth;
    } catch (error) {
      console.error('❌ Health check failed:', error);
      return false;
    }
  }
}

/**
 * Utility functions for common storage operations
 */
export class StorageUtils {
  
  /**
   * Safe way to check if flight search data exists
   */
  static async hasValidFlightSearch(): Promise<boolean> {
    const result = await flightStorageManager.getFlightSearch();
    return result.success;
  }

  /**
   * Safe way to check if flight price data exists
   */
  static async hasValidFlightPrice(): Promise<boolean> {
    const result = await flightStorageManager.getFlightPrice();
    return result.success;
  }

  /**
   * Clear all flight data (useful for logout or reset)
   */
  static async clearAllFlightData(): Promise<void> {
    await flightStorageManager.clearAllFlightData();
    console.log('🗑️ All flight data cleared');
  }

  /**
   * Emergency storage cleanup (use when storage is corrupted)
   */
  static async emergencyCleanup(): Promise<void> {
    console.log('🚨 Emergency storage cleanup initiated...');

    // Clear all flight data
    await flightStorageManager.clearAllFlightData();

    // Clear any remaining old storage patterns
    const oldKeys = [
      'currentFlightSearch',
      'currentFlightDataKey',
      'currentFlightPrice',
      'flightPriceResponseForBooking',
      'rawFlightPriceResponse',
      'completedBooking',
      'dev_completedBooking'
    ];

    oldKeys.forEach(key => {
      sessionStorage.removeItem(key);
      localStorage.removeItem(key);
    });

    // Clean up timestamped keys and test data
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('flightData_') ||
          key.includes('flight_') ||
          key.startsWith('test_cleanup_') ||
          key.includes('test')) {
        localStorage.removeItem(key);
      }
    });

    // Also clean sessionStorage test data
    Object.keys(sessionStorage).forEach(key => {
      if (key.startsWith('test_cleanup_') ||
          key.includes('test')) {
        sessionStorage.removeItem(key);
      }
    });

    console.log('✅ Emergency cleanup completed');
  }
}

// Export instances for easy use
export const flightSearchStorage = new FlightSearchStorageExample();
export const flightPriceStorage = new FlightPriceStorageExample();
export const migrationHelper = new StorageMigrationHelper();

/**
 * Quick setup function for new applications
 */
export async function setupRobustStorage(): Promise<void> {
  console.log('🚀 Setting up robust storage system...');
  
  // Run migration to handle any existing data
  await migrationHelper.runStartupMigration();
  
  // Perform health check
  const isHealthy = await migrationHelper.performHealthCheck();
  
  if (isHealthy) {
    console.log('✅ Robust storage system is ready');
  } else {
    console.warn('⚠️ Storage system needs attention');
  }
}

/**
 * Integration guide for replacing old storage calls
 */
export const INTEGRATION_GUIDE = {
  // Replace this:
  OLD_PATTERN: `
    sessionStorage.setItem('currentFlightSearch', JSON.stringify(data));
    localStorage.setItem('flightData_' + Date.now(), JSON.stringify(data));
  `,
  
  // With this:
  NEW_PATTERN: `
    import { flightStorageManager } from './utils/flight-storage-manager';
    
    const result = await flightStorageManager.storeFlightSearch({
      airShoppingResponse: data.airShoppingResponse,
      searchParams: data.searchParams,
      timestamp: Date.now(),
      expiresAt: Date.now() + (30 * 60 * 1000)
    });
    
    if (!result.success) {
      console.error('Storage failed:', result.error);
    }
  `,
  
  // For retrieval, replace this:
  OLD_RETRIEVAL: `
    const data = sessionStorage.getItem('currentFlightSearch');
    if (data) {
      return JSON.parse(data);
    }
  `,
  
  // With this:
  NEW_RETRIEVAL: `
    const result = await flightStorageManager.getFlightSearch();
    if (result.success) {
      return result.data;
    }
    console.log('No data found:', result.error);
    return null;
  `
};
