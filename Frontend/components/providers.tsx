'use client';

import { ClerkProvider } from '@clerk/nextjs';
import { ThemeProvider } from 'next-themes';
import { LoadingProvider } from '@/utils/loading-state';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        <LoadingProvider>
          {children}
        </LoadingProvider>
      </ThemeProvider>
    </ClerkProvider>
  );
}
