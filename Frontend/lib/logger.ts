export const logger = {
  info: (message: string, data?: any) => console.log(`[INFO] ${message}`, data || ''),
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error || '');
    if (error?.response) {
      console.error('Response data:', error.response.data);
      console.error('Status:', error.response.status);
    }
  },
  debug: (message: string, data?: any) => console.debug(`[DEBUG] ${message}`, data || '')
};