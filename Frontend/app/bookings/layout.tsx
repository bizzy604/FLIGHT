import { ReactNode } from 'react';
import { MainNav } from '@/components/navigation/MainNav';
import { MobileNav } from '@/components/navigation/MainNav';

export default function BookingsLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b bg-background">
        <div className="container flex h-16 items-center justify-between py-4">
          <MainNav />
        </div>
      </header>
      <main className="flex-1">
        <div className="container py-6">
          {children}
        </div>
      </main>
      <MobileNav />
    </div>
  );
}
