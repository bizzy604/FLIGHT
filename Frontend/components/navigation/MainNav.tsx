'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from "@/utils/cn";
import { Button } from '@/components/ui/button';
import { Home, Plane, Ticket, User } from 'lucide-react';

export function MainNav() {
  const pathname = usePathname();
  const isActive = (path: string) => pathname === path;

  return (
    <nav className="flex items-center space-x-4 lg:space-x-6">
      <Link href="/" className="flex items-center space-x-2">
        <Plane className="h-6 w-6" />
        <span className="font-bold">AeroLux</span>
      </Link>
      <div className="hidden md:flex items-center space-x-1">
        <Link href="/" passHref>
          <Button
            variant={isActive('/') ? 'secondary' : 'ghost'}
            className="flex items-center gap-1"
          >
            <Home className="h-4 w-4" />
            <span>Home</span>
          </Button>
        </Link>
        <Link href="/bookings" passHref>
          <Button
            variant={isActive('/bookings') ? 'secondary' : 'ghost'}
            className="flex items-center gap-1"
          >
            <Ticket className="h-4 w-4" />
            <span>My Bookings</span>
          </Button>
        </Link>
      </div>
    </nav>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  const isActive = (path: string) => pathname === path;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-background border-t border-border flex justify-around items-center p-2 md:hidden z-50">
      <Link href="/" className={cn(
        'flex flex-col items-center p-2 rounded-lg',
        isActive('/') ? 'text-blue-600' : 'text-muted-foreground hover:text-foreground'
      )}>
        <Home className="h-5 w-5" />
        <span className="text-xs mt-1">Home</span>
      </Link>
      <Link href="/bookings" className={cn(
        'flex flex-col items-center p-2 rounded-lg',
        isActive('/bookings') ? 'text-blue-600' : 'text-muted-foreground hover:text-foreground'
      )}>
        <Ticket className="h-5 w-5" />
        <span className="text-xs mt-1">Bookings</span>
      </Link>
      <Link href="/profile" className={cn(
        'flex flex-col items-center p-2 rounded-lg',
        isActive('/profile') ? 'text-blue-600' : 'text-muted-foreground hover:text-foreground'
      )}>
        <User className="h-5 w-5" />
        <span className="text-xs mt-1">Profile</span>
      </Link>
    </nav>
  );
}
