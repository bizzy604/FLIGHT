import 'next';

declare module 'next' {
  interface Headers {
    [Symbol.iterator](): IterableIterator<[string, string]>;
    entries(): IterableIterator<[string, string]>;
    keys(): IterableIterator<string>;
    values(): IterableIterator<string>;
  }
}

// Fix for Clerk telemetry type
declare module '@clerk/shared/dist/telemetry' {
  export class Telemetry {
    private _enabled: boolean;
    // Add other necessary properties and methods
  }
}
