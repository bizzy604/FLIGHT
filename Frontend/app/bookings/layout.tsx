import { ReactNode } from 'react';
import { MainNav, UserNav, SimpleFooter } from '@/components/organisms';
import Image from 'next/image';

export default function BookingsLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 sm:h-16 items-center justify-between px-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 sm:gap-3">
            <Image
              src="/logo1.png"
              alt="Rea Travel Logo"
              width={32}
              height={32}
              className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12"
            />
            <span className="text-sm sm:text-base md:text-lg font-semibold">Rea Travel</span>
          </div>
          <div className="flex items-center gap-4">
            <MainNav />
            <UserNav />
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="container py-6">
          {children}
        </div>
      </main>
      <SimpleFooter />
    </div>
  );
}
