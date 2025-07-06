/**
 * Storage Migration Utility
 * Helps migrate from old storage patterns to the new robust storage manager
 */

import { flightStorageManager, FlightSearchData, FlightPriceData } from './flight-storage-manager';

interface MigrationResult {
  success: boolean;
  migratedKeys: string[];
  errors: string[];
  cleanedKeys: string[];
}

export class StorageMigration {
  private static instance: StorageMigration;

  private constructor() {}

  static getInstance(): StorageMigration {
    if (!StorageMigration.instance) {
      StorageMigration.instance = new StorageMigration();
    }
    return StorageMigration.instance;
  }

  /**
   * Migrate all existing flight data to the new storage system
   */
  async migrateAllFlightData(): Promise<MigrationResult> {
    console.log('[StorageMigration] Starting migration of all flight data...');
    
    const result: MigrationResult = {
      success: true,
      migratedKeys: [],
      errors: [],
      cleanedKeys: []
    };

    try {
      // Migrate flight search data
      await this.migrateFlightSearchData(result);
      
      // Migrate flight price data
      await this.migrateFlightPriceData(result);
      
      // Clean up old storage patterns
      await this.cleanupOldStoragePatterns(result);
      
      console.log('[StorageMigration] ✅ Migration completed successfully');
      console.log('[StorageMigration] Summary:', {
        migratedKeys: result.migratedKeys.length,
        errors: result.errors.length,
        cleanedKeys: result.cleanedKeys.length
      });
      
    } catch (error) {
      result.success = false;
      result.errors.push(`Migration failed: ${(error as Error).message}`);
      console.error('[StorageMigration] ❌ Migration failed:', error);
    }

    return result;
  }

  /**
   * Migrate flight search data from old storage patterns
   */
  private async migrateFlightSearchData(result: MigrationResult): Promise<void> {
    const oldKeys = [
      'currentFlightSearch',
      'currentFlightDataKey'
    ];

    for (const key of oldKeys) {
      try {
        // Check sessionStorage first
        let rawData = sessionStorage.getItem(key);
        let source = 'sessionStorage';
        
        if (!rawData) {
          // Check localStorage
          rawData = localStorage.getItem(key);
          source = 'localStorage';
        }

        if (rawData) {
          const parsedData = JSON.parse(rawData);
          
          // Check if this looks like flight search data
          if (this.isFlightSearchData(parsedData)) {
            const flightSearchData: FlightSearchData = {
              airShoppingResponse: parsedData.airShoppingResponse || parsedData.data,
              searchParams: parsedData.searchParams || this.extractSearchParams(parsedData),
              timestamp: parsedData.timestamp || Date.now(),
              expiresAt: parsedData.expiresAt || (Date.now() + 30 * 60 * 1000)
            };

            const storeResult = await flightStorageManager.storeFlightSearch(flightSearchData);
            
            if (storeResult.success) {
              result.migratedKeys.push(`${key} (from ${source})`);
              console.log(`[StorageMigration] ✅ Migrated flight search data from ${key}`);
              
              // Clean up old data
              sessionStorage.removeItem(key);
              localStorage.removeItem(key);
              result.cleanedKeys.push(key);
            } else {
              result.errors.push(`Failed to migrate ${key}: ${storeResult.error}`);
            }
          }
        }
      } catch (error) {
        result.errors.push(`Error migrating ${key}: ${(error as Error).message}`);
        console.error(`[StorageMigration] Error migrating ${key}:`, error);
      }
    }

    // Also check for timestamped flight data keys
    await this.migrateTimestampedFlightData(result);
  }

  /**
   * Migrate timestamped flight data keys (flightData_*)
   */
  private async migrateTimestampedFlightData(result: MigrationResult): Promise<void> {
    const allLocalKeys = Object.keys(localStorage);
    const flightDataKeys = allLocalKeys.filter(key => 
      key.startsWith('flightData_') || key.includes('flight_') || key.includes('Flight')
    );

    for (const key of flightDataKeys) {
      try {
        const rawData = localStorage.getItem(key);
        if (rawData) {
          const parsedData = JSON.parse(rawData);
          
          if (this.isFlightSearchData(parsedData)) {
            const flightSearchData: FlightSearchData = {
              airShoppingResponse: parsedData.airShoppingResponse || parsedData.data,
              searchParams: parsedData.searchParams || this.extractSearchParams(parsedData),
              timestamp: parsedData.timestamp || Date.now(),
              expiresAt: parsedData.expiresAt || (Date.now() + 30 * 60 * 1000)
            };

            // Only migrate if not expired
            if (flightSearchData.expiresAt > Date.now()) {
              const storeResult = await flightStorageManager.storeFlightSearch(flightSearchData);
              
              if (storeResult.success) {
                result.migratedKeys.push(`${key} (timestamped)`);
                console.log(`[StorageMigration] ✅ Migrated timestamped flight data from ${key}`);
              }
            }
            
            // Clean up old data regardless of migration success
            localStorage.removeItem(key);
            result.cleanedKeys.push(key);
          }
        }
      } catch (error) {
        result.errors.push(`Error migrating timestamped key ${key}: ${(error as Error).message}`);
        // Clean up corrupted data
        localStorage.removeItem(key);
        result.cleanedKeys.push(key);
      }
    }
  }

  /**
   * Migrate flight price data
   */
  private async migrateFlightPriceData(result: MigrationResult): Promise<void> {
    const priceKeys = [
      'currentFlightPrice',
      'flightPriceResponseForBooking',
      'rawFlightPriceResponse'
    ];

    for (const key of priceKeys) {
      try {
        // Check sessionStorage first
        let rawData = sessionStorage.getItem(key);
        let source = 'sessionStorage';
        
        if (!rawData) {
          // Check localStorage
          rawData = localStorage.getItem(key);
          source = 'localStorage';
        }

        if (rawData) {
          const parsedData = JSON.parse(rawData);
          
          if (this.isFlightPriceData(parsedData)) {
            const flightPriceData: FlightPriceData = {
              flightId: parsedData.flightId || 'unknown',
              pricedOffer: parsedData.pricedOffer || parsedData,
              rawResponse: parsedData.rawResponse || parsedData,
              searchParams: parsedData.searchParams || {},
              timestamp: parsedData.timestamp || Date.now(),
              expiresAt: parsedData.expiresAt || (Date.now() + 30 * 60 * 1000)
            };

            const storeResult = await flightStorageManager.storeFlightPrice(flightPriceData);
            
            if (storeResult.success) {
              result.migratedKeys.push(`${key} (from ${source})`);
              console.log(`[StorageMigration] ✅ Migrated flight price data from ${key}`);
              
              // Clean up old data
              sessionStorage.removeItem(key);
              localStorage.removeItem(key);
              result.cleanedKeys.push(key);
            } else {
              result.errors.push(`Failed to migrate ${key}: ${storeResult.error}`);
            }
          }
        }
      } catch (error) {
        result.errors.push(`Error migrating ${key}: ${(error as Error).message}`);
        console.error(`[StorageMigration] Error migrating ${key}:`, error);
      }
    }
  }

  /**
   * Clean up old storage patterns and corrupted data
   */
  private async cleanupOldStoragePatterns(result: MigrationResult): Promise<void> {
    // Clean up old booking storage patterns
    const oldBookingKeys = [
      'completedBooking',
      'dev_completedBooking',
      'dev_completedBooking_persistent'
    ];

    for (const key of oldBookingKeys) {
      if (sessionStorage.getItem(key) || localStorage.getItem(key)) {
        sessionStorage.removeItem(key);
        localStorage.removeItem(key);
        result.cleanedKeys.push(key);
      }
    }

    // Clean up any remaining corrupted or expired data
    await this.cleanupCorruptedData(result);
  }

  /**
   * Clean up corrupted or invalid data
   */
  private async cleanupCorruptedData(result: MigrationResult): Promise<void> {
    const storages = [
      { storage: sessionStorage, name: 'sessionStorage' },
      { storage: localStorage, name: 'localStorage' }
    ];

    for (const { storage, name } of storages) {
      const keys = Object.keys(storage);
      
      for (const key of keys) {
        try {
          const rawData = storage.getItem(key);
          if (rawData) {
            JSON.parse(rawData); // Test if it's valid JSON
          }
        } catch (error) {
          // Remove corrupted data
          storage.removeItem(key);
          result.cleanedKeys.push(`${key} (corrupted in ${name})`);
          console.log(`[StorageMigration] 🗑️ Cleaned up corrupted data: ${key} from ${name}`);
        }
      }
    }
  }

  /**
   * Check if data looks like flight search data
   */
  private isFlightSearchData(data: any): boolean {
    return (
      data &&
      typeof data === 'object' &&
      (data.airShoppingResponse || data.data) &&
      (data.searchParams || data.origin || data.destination)
    );
  }

  /**
   * Check if data looks like flight price data
   */
  private isFlightPriceData(data: any): boolean {
    return (
      data &&
      typeof data === 'object' &&
      (data.pricedOffer || data.rawResponse || data.flightId)
    );
  }

  /**
   * Extract search parameters from old data structure
   */
  private extractSearchParams(data: any): any {
    if (data.searchParams) {
      return data.searchParams;
    }

    // Try to extract from other fields
    return {
      origin: data.origin || 'unknown',
      destination: data.destination || 'unknown',
      departDate: data.departDate || data.departureDate || '',
      returnDate: data.returnDate || '',
      tripType: data.tripType || 'oneway',
      passengers: data.passengers || { adults: 1, children: 0, infants: 0 },
      cabinClass: data.cabinClass || 'economy'
    };
  }

  /**
   * Force migration - use this when you need to migrate immediately
   */
  async forceMigration(): Promise<MigrationResult> {
    console.log('[StorageMigration] 🚨 Force migration initiated...');
    
    // Clear any existing new storage first
    await flightStorageManager.clearAllFlightData();
    
    // Run migration
    return await this.migrateAllFlightData();
  }
}

// Export singleton instance
export const storageMigration = StorageMigration.getInstance();

// Convenience function for immediate migration
export async function migrateStorageNow(): Promise<MigrationResult> {
  return await storageMigration.migrateAllFlightData();
}

// Convenience function for force migration
export async function forceMigrateStorageNow(): Promise<MigrationResult> {
  return await storageMigration.forceMigration();
}
