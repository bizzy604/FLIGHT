/**
 * Simple logger utility for the application
 */

/**
 * Log levels
 */
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * Log a message with the specified level
 * @param level The log level
 * @param message The message to log
 * @param data Optional data to include in the log
 */
const log = (level: LogLevel, message: string, data?: any) => {
  if (process.env.NODE_ENV === 'production' && level === 'debug') {
    return; // Skip debug logs in production
  }

  const timestamp = new Date().toISOString();
  // Create a typed log entry with optional data
  const logEntry: {
    timestamp: string;
    level: LogLevel;
    message: string;
    data?: any;
  } = { timestamp, level, message };
  
  if (data) {
    logEntry.data = data;
  }

  switch (level) {
    case 'error':
      console.error(JSON.stringify(logEntry));
      break;
    case 'warn':
      console.warn(JSON.stringify(logEntry));
      break;
    case 'info':
      console.info(JSON.stringify(logEntry));
      break;
    case 'debug':
      console.debug(JSON.stringify(logEntry));
      break;
  }
};

export const logger = {
  debug: (message: string, data?: any) => log('debug', message, data),
  info: (message: string, data?: any) => log('info', message, data),
  warn: (message: string, data?: any) => log('warn', message, data),
  error: (message: string, data?: any) => log('error', message, data),
};

export default logger;
