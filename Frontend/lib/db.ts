import { Pool, type PoolClient } from "pg"

// Database connection configuration
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === "production" ? { rejectUnauthorized: false } : false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})

// Initialize database connection
export async function initializeDb() {
  try {
    const client = await pool.connect()
    console.log("Database connected successfully")
    client.release()
    return true
  } catch (error) {
    console.error("Database connection error:", error)
    return false
  }
}

// Get a client from the pool
export async function getClient(): Promise<PoolClient> {
  return await pool.connect()
}

// Execute a query with parameters
export async function query(text: string, params: any[] = []) {
  const start = Date.now()
  try {
    const res = await pool.query(text, params)
    const duration = Date.now() - start
    console.log("Executed query", { text, duration, rows: res.rowCount })
    return res
  } catch (error) {
    console.error("Error executing query", { text, error })
    throw error
  }
}

// Transaction helper
export async function withTransaction<T>(callback: (client: PoolClient) => Promise<T>): Promise<T> {
  const client = await pool.connect()
  try {
    await client.query("BEGIN")
    const result = await callback(client)
    await client.query("COMMIT")
    return result
  } catch (error) {
    await client.query("ROLLBACK")
    throw error
  } finally {
    client.release()
  }
}

// Database schema initialization (run on startup)
export async function initializeSchema() {
  try {
    // Create bookings table
    await query(`
      CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        user_id TEXT NOT NULL,
        booking_reference TEXT NOT NULL UNIQUE,
        flight_details JSONB NOT NULL,
        passenger_details JSONB NOT NULL,
        contact_info JSONB NOT NULL,
        extras JSONB,
        total_amount DECIMAL(10, 2) NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `)

    // Create payments table
    await query(`
      CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        booking_id INTEGER REFERENCES bookings(id),
        payment_intent_id TEXT UNIQUE,
        amount DECIMAL(10, 2) NOT NULL,
        currency TEXT NOT NULL DEFAULT 'usd',
        status TEXT NOT NULL,
        payment_method TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `)

    console.log("Database schema initialized")
    return true
  } catch (error) {
    console.error("Error initializing database schema:", error)
    return false
  }
}

