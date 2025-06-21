import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { auth, currentUser } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

// Define public routes that need no protection
const isPublicRoute = createRouteMatcher([
  '/',
  '/flights',
  '/flights/:id',
  '/flights/:id/payment',
  '/flights/:id/payment/confirmation',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/about',
  '/contact',
  '/api/flights/search',
  '/api/flights/search-advanced',
  '/api/health',
  '/api/payments/webhook',
  "/api/seed",
  "/api/bookings(.*)",
  "/api/payments(.*)",
  "/api/verteil(.*)",
  "/api/test",
]);

// Define admin routes
const isAdminRoute = createRouteMatcher([
  '/admin(.*)',
  '/api/admin(.*)',
]);

export default clerkMiddleware(async (auth, req) => {
  // Allow public routes without any protection.
  if (isPublicRoute(req)) {
    return NextResponse.next();
  }

  // For admin routes, enforce RBAC by checking the user has the 'admin' role.
  if (isAdminRoute(req)) {
    try {
      // First check if user is authenticated
      await auth.protect(); // Use auth.protect directly
  
      // Get user ID and fetch organization memberships
      const { userId } = await auth();
      const user = await currentUser();
      
      if (!userId || !user) {
        return NextResponse.redirect(new URL('/sign-in', req.url));
      }

      // Check if user has admin role in any organization
      try {
        // Using Clerk's organization API to get memberships
        const memberships = await fetch(
          `https://api.clerk.com/v1/users/${userId}/organization_memberships`,
          {
            headers: {
              'Authorization': `Bearer ${process.env.CLERK_SECRET_KEY}`,
              'Content-Type': 'application/json',
            },
          }
        );
        
        if (!memberships.ok) {
          throw new Error('Failed to fetch organization memberships');
        }
        
        const membershipsData = await memberships.json();
        const isAdmin = membershipsData.data?.some(
          (membership: { role: string }) => 
            membership.role === 'org:admin' || membership.role === 'admin'
        ) || false;
        
        console.log("Is admin?", isAdmin);
        
        if (!isAdmin) {
          // Redirect to not-authorized page or home
          return NextResponse.redirect(new URL('/', req.url));
        }
      } catch (error) {
        console.error("Error checking admin status:", error);
        return NextResponse.redirect(new URL('/sign-in', req.url));
      }
    } catch (error) {
      // If authentication fails, redirect to sign-in
      return NextResponse.redirect(new URL('/sign-in', req.url));
    }
  } else {
    // For non-admin protected routes, just check authentication
    await auth.protect(); // Use auth.protect directly
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};
