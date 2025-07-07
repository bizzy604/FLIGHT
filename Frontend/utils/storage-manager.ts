/**
 * Robust Storage Manager - Production-ready solution for data persistence
 * Addresses corruption, race conditions, and data integrity issues
 */

// Simple UUID generator to avoid external dependencies
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Data structure interfaces
interface StorageMetadata {
  id: string;
  version: string;
  timestamp: number;
  expiresAt: number;
  checksum: string;
  dataType: string;
}

interface StorageWrapper<T = any> {
  metadata: StorageMetadata;
  data: T;
}

interface StorageOptions {
  expiryMinutes?: number;
  useCompression?: boolean;
  validateOnRead?: boolean;
  retryAttempts?: number;
}

// Storage operation result types
interface StorageResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  recovered?: boolean;
  source?: 'session' | 'local' | 'backup';
}

// Storage manager class
export class StorageManager {
  private static instance: StorageManager;
  private readonly VERSION = '1.0.0';
  private readonly MAX_RETRY_ATTEMPTS = 3;
  private readonly CLEANUP_THRESHOLD = 50; // Max items before cleanup
  private operationLocks = new Map<string, Promise<any>>();

  private constructor() {}

  static getInstance(): StorageManager {
    if (!StorageManager.instance) {
      StorageManager.instance = new StorageManager();
    }
    return StorageManager.instance;
  }

  /**
   * Generate a simple checksum for data integrity validation
   */
  private generateChecksum(data: string): string {
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  }

  /**
   * Validate data integrity using checksum
   */
  private validateChecksum(data: string, expectedChecksum: string): boolean {
    return this.generateChecksum(data) === expectedChecksum;
  }

  /**
   * Create storage wrapper with metadata
   */
  private createWrapper<T>(data: T, dataType: string, options: StorageOptions = {}): StorageWrapper<T> {
    const timestamp = Date.now();
    const expiryMinutes = options.expiryMinutes || 30;
    const dataString = JSON.stringify(data);
    
    return {
      metadata: {
        id: generateUUID(),
        version: this.VERSION,
        timestamp,
        expiresAt: timestamp + (expiryMinutes * 60 * 1000),
        checksum: this.generateChecksum(dataString),
        dataType
      },
      data
    };
  }

  /**
   * Atomic storage operation with locking
   */
  private async atomicOperation<T>(key: string, operation: () => Promise<T>): Promise<T> {
    // Check if operation is already in progress for this key
    if (this.operationLocks.has(key)) {
      await this.operationLocks.get(key);
    }

    // Create new operation lock
    const operationPromise = operation();
    this.operationLocks.set(key, operationPromise);

    try {
      const result = await operationPromise;
      return result;
    } finally {
      this.operationLocks.delete(key);
    }
  }

  /**
   * Store data with comprehensive error handling and validation
   */
  async store<T>(
    key: string, 
    data: T, 
    dataType: string, 
    options: StorageOptions = {}
  ): Promise<StorageResult<T>> {
    return this.atomicOperation(key, async () => {
      try {
        const wrapper = this.createWrapper(data, dataType, options);
        const serializedData = JSON.stringify(wrapper);
        
        // Attempt to store in both storages with retry logic
        const sessionResult = await this.storeWithRetry('session', key, serializedData, options.retryAttempts);
        const localResult = await this.storeWithRetry('local', key, serializedData, options.retryAttempts);

        if (sessionResult || localResult) {
          // Trigger cleanup if needed
          await this.cleanupIfNeeded();
          
          return {
            success: true,
            data,
            source: sessionResult ? 'session' : 'local'
          };
        } else {
          return {
            success: false,
            error: 'Failed to store data in any storage location'
          };
        }
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error(`[StorageManager] Store operation failed for key ${key}:`, error);
        }
        return {
          success: false,
          error: `Storage operation failed: ${(error as Error).message}`
        };
      }
    });
  }

  /**
   * Store with retry logic and quota management
   */
  private async storeWithRetry(
    storageType: 'session' | 'local', 
    key: string, 
    data: string, 
    maxRetries = 3
  ): Promise<boolean> {
    const storage = storageType === 'session' ? sessionStorage : localStorage;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        storage.setItem(key, data);
        return true;
      } catch (error) {
        if (error instanceof DOMException && error.name === 'QuotaExceededError') {
          if (process.env.NODE_ENV === 'development') {
            console.warn(`[StorageManager] Quota exceeded in ${storageType}Storage, attempt ${attempt}/${maxRetries}`);
          }

          // Cleanup old data and retry
          await this.emergencyCleanup(storageType);

          if (attempt === maxRetries) {
            if (process.env.NODE_ENV === 'development') {
              console.error(`[StorageManager] Failed to store after ${maxRetries} attempts in ${storageType}Storage`);
            }
            return false;
          }
        } else {
          if (process.env.NODE_ENV === 'development') {
            console.error(`[StorageManager] Storage error in ${storageType}Storage:`, error);
          }
          return false;
        }
      }
    }
    return false;
  }

  /**
   * Retrieve data with validation and recovery
   */
  async retrieve<T>(key: string, expectedDataType?: string): Promise<StorageResult<T>> {
    return this.atomicOperation(key, async () => {
      try {
        // Try sessionStorage first (faster)
        let result = await this.retrieveFromStorage('session', key, expectedDataType);
        if (result.success) {
          return result;
        }

        // Fallback to localStorage
        result = await this.retrieveFromStorage('local', key, expectedDataType);
        if (result.success) {
          // Restore to sessionStorage for faster future access
          if (result.data) {
            await this.store(key, result.data, expectedDataType || 'unknown', { expiryMinutes: 30 });
          }
          return { ...result, recovered: true };
        }

        return {
          success: false,
          error: 'Data not found in any storage location'
        };
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error(`[StorageManager] Retrieve operation failed for key ${key}:`, error);
        }
        return {
          success: false,
          error: `Retrieve operation failed: ${(error as Error).message}`
        };
      }
    });
  }

  /**
   * Retrieve from specific storage with validation
   */
  private async retrieveFromStorage<T>(
    storageType: 'session' | 'local', 
    key: string, 
    expectedDataType?: string
  ): Promise<StorageResult<T>> {
    const storage = storageType === 'session' ? sessionStorage : localStorage;
    
    try {
      const rawData = storage.getItem(key);
      if (!rawData) {
        return { success: false, error: `No data found in ${storageType}Storage` };
      }

      const wrapper: StorageWrapper<T> = JSON.parse(rawData);
      
      // Validate wrapper structure
      if (!wrapper.metadata || !wrapper.data) {
        if (process.env.NODE_ENV === 'development') {
          console.warn(`[StorageManager] Invalid wrapper structure in ${storageType}Storage for key ${key}`);
        }
        storage.removeItem(key); // Clean up corrupted data
        return { success: false, error: 'Invalid data structure' };
      }

      // Check expiration
      if (Date.now() > wrapper.metadata.expiresAt) {
        if (process.env.NODE_ENV === 'development') {
          console.log(`[StorageManager] Data expired in ${storageType}Storage for key ${key}`);
        }
        storage.removeItem(key);
        return { success: false, error: 'Data expired' };
      }

      // Validate data type if specified
      if (expectedDataType && wrapper.metadata.dataType !== expectedDataType) {
        if (process.env.NODE_ENV === 'development') {
          console.warn(`[StorageManager] Data type mismatch in ${storageType}Storage for key ${key}`);
        }
        return { success: false, error: 'Data type mismatch' };
      }

      // Validate checksum
      const dataString = JSON.stringify(wrapper.data);
      if (!this.validateChecksum(dataString, wrapper.metadata.checksum)) {
        if (process.env.NODE_ENV === 'development') {
          console.error(`[StorageManager] Checksum validation failed in ${storageType}Storage for key ${key}`);
        }
        storage.removeItem(key); // Clean up corrupted data
        return { success: false, error: 'Data corruption detected' };
      }

      return {
        success: true,
        data: wrapper.data,
        source: storageType
      };
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error(`[StorageManager] Parse error in ${storageType}Storage for key ${key}:`, error);
      }
      storage.removeItem(key); // Clean up corrupted data
      return { success: false, error: 'Parse error' };
    }
  }

  /**
   * Emergency cleanup when quota is exceeded
   */
  private async emergencyCleanup(storageType: 'session' | 'local'): Promise<void> {
    const storage = storageType === 'session' ? sessionStorage : localStorage;
    const keys = Object.keys(storage);
    
    // Sort by timestamp (oldest first) and remove expired/oldest items
    const itemsWithTimestamp: Array<{ key: string; timestamp: number; expired: boolean }> = [];
    
    for (const key of keys) {
      try {
        const rawData = storage.getItem(key);
        if (rawData) {
          const wrapper = JSON.parse(rawData);
          if (wrapper.metadata?.timestamp) {
            itemsWithTimestamp.push({
              key,
              timestamp: wrapper.metadata.timestamp,
              expired: Date.now() > wrapper.metadata.expiresAt
            });
          }
        }
      } catch {
        // Remove corrupted items immediately
        storage.removeItem(key);
      }
    }

    // Sort by expired first, then by timestamp (oldest first)
    itemsWithTimestamp.sort((a, b) => {
      if (a.expired !== b.expired) return a.expired ? -1 : 1;
      return a.timestamp - b.timestamp;
    });

    // Remove at least 25% of items or until we have space
    const itemsToRemove = Math.max(Math.floor(itemsWithTimestamp.length * 0.25), 5);
    
    for (let i = 0; i < Math.min(itemsToRemove, itemsWithTimestamp.length); i++) {
      storage.removeItem(itemsWithTimestamp[i].key);
      if (process.env.NODE_ENV === 'development') {
        console.log(`[StorageManager] Emergency cleanup removed: ${itemsWithTimestamp[i].key}`);
      }
    }
  }

  /**
   * Regular cleanup if storage is getting full
   */
  private async cleanupIfNeeded(): Promise<void> {
    const sessionKeys = Object.keys(sessionStorage);
    const localKeys = Object.keys(localStorage);
    
    if (sessionKeys.length > this.CLEANUP_THRESHOLD) {
      await this.emergencyCleanup('session');
    }
    
    if (localKeys.length > this.CLEANUP_THRESHOLD) {
      await this.emergencyCleanup('local');
    }
  }

  /**
   * Remove data from all storage locations
   */
  async remove(key: string): Promise<void> {
    return this.atomicOperation(key, async () => {
      sessionStorage.removeItem(key);
      localStorage.removeItem(key);
      if (process.env.NODE_ENV === 'development') {
        console.log(`[StorageManager] Removed data for key: ${key}`);
      }
    });
  }

  /**
   * Clear all data (use with caution)
   */
  async clearAll(): Promise<void> {
    sessionStorage.clear();
    localStorage.clear();
    this.operationLocks.clear();
    if (process.env.NODE_ENV === 'development') {
      console.log('[StorageManager] All storage cleared');
    }
  }

  /**
   * Get storage statistics for monitoring
   */
  getStorageStats(): {
    sessionStorage: { used: number; available: number; itemCount: number };
    localStorage: { used: number; available: number; itemCount: number };
  } {
    const getStorageInfo = (storage: Storage) => {
      const items = Object.keys(storage);
      let used = 0;
      
      items.forEach(key => {
        const value = storage.getItem(key);
        if (value) {
          used += key.length + value.length;
        }
      });
      
      return {
        used,
        available: 5 * 1024 * 1024 - used, // Approximate 5MB limit
        itemCount: items.length
      };
    };

    return {
      sessionStorage: getStorageInfo(sessionStorage),
      localStorage: getStorageInfo(localStorage)
    };
  }
}

// Export singleton instance
export const storageManager = StorageManager.getInstance();

// Export types for use in other files
export type { StorageResult, StorageOptions };
