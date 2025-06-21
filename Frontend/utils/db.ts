import { PrismaClient as PrismaClientType, Prisma } from '@prisma/client/edge';
import { logger } from './logger';

// PrismaClient is attached to the `global` object in development to prevent
// exhausting your database connection limit.
// Learn more: https://pris.ly/d/help/next-js-best-practices

// Import types from @prisma/client
import type { PrismaClientOptions } from '@prisma/client/runtime/library';

// Define the Prisma client type
type PrismaClient = ReturnType<typeof getPrismaClient>;

// Define transaction client type
type TransactionClient = Omit<PrismaClient, '$connect' | '$disconnect' | '$on' | '$transaction' | '$use' | '$extends'>;

// Extend the global type to include our prisma client
declare global {
  // eslint-disable-next-line no-var
  var prisma: PrismaClient | undefined;
}

// Helper function to create a new Prisma client
function getPrismaClient() {
  return new PrismaClientType({
    log: process.env.NODE_ENV === 'development' ? ['query'] : [],
  });
}

// Initialize Prisma client
export const prisma: PrismaClient = global.prisma || getPrismaClient();

// Store in global object in development to prevent multiple instances
if (process.env.NODE_ENV !== 'production') {
  global.prisma = prisma;
}

/**
 * Initializes the database connection
 * @returns PrismaClient instance
 */
export const initializeDb = async (): Promise<PrismaClient> => {
  try {
    await prisma.$connect();
    logger.info('Successfully connected to the database');
    return prisma;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    logger.error('Failed to connect to the database:', { error: errorMessage });
    throw new Error('Failed to connect to the database');
  }
};

/**
 * Executes a raw SQL query with type safety
 * @param sql SQL query string
 * @param values Optional parameter values
 * @returns Query result with proper typing
 */
export const query = async <T = unknown>(
  sql: string,
  values: unknown[] = []
): Promise<T> => {
  try {
    // Use type assertion since we trust the query result will match T
    const result = await prisma.$queryRawUnsafe(sql, ...values) as T;
    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    logger.error('Database query error:', { 
      error: errorMessage, 
      sql, 
      values: values.map(v => (typeof v === 'string' ? v : JSON.stringify(v)))
    });
    throw error;
  }
};

/**
 * Helper to handle database transactions with proper typing
 * @param callback Async callback function that contains the transaction logic
 * @returns Result of the transaction with proper typing
 */
export const transaction = async <T>(
  callback: (tx: TransactionClient) => Promise<T>,
  options?: { maxWait?: number; timeout?: number; isolationLevel?: string }
): Promise<T> => {
  return await prisma.$transaction(async (tx: any) => {
    return await callback(tx as TransactionClient);
  }, options as any);
};

// Export Prisma types for type safety
export type { PrismaClient } from '@prisma/client/edge';

// Export common Prisma enums and types
export * from '@prisma/client/edge';

// Export Prisma client as default
export default prisma;
