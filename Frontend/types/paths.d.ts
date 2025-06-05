// This file helps TypeScript understand our path aliases
declare module '@/lib/flight-api' {
  export * from '../../../lib/flight-api';
}

declare module '@/lib/logger' {
  export * from '../../../lib/logger';
}
