// You can add other global type definitions here if needed

// --- Clerk Module Augmentation --- 
import type { UserPublicMetadata } from "@clerk/nextjs/server";

declare module "@clerk/nextjs/server" {
  interface UserPublicMetadata {
    role?: string;
  }
}
// --- End Clerk Module Augmentation --- 

export {}; // Ensures this file is treated as a module