import { type NextRequest, NextResponse } from "next/server"
import { auth, clerkClient } from "@clerk/nextjs/server"
import { handleApiError, createUnauthorizedError, createForbiddenError } from "@/utils/error-handler"

// Force dynamic rendering to prevent static generation during build
export const dynamic = 'force-dynamic'

interface ClerkUser {
  id: string
  firstName: string | null
  lastName: string | null
  emailAddresses: { emailAddress: string }[]
  imageUrl: string
  createdAt: number
  lastSignInAt: number | null
}

interface ClerkUserResponse {
  data: ClerkUser[]
  totalCount: number
}

export async function GET(request: NextRequest) {
  try {
    // Get the current user session
    const { userId, orgRole } = await auth();
    
    if (!userId) {
      throw createUnauthorizedError();
    }

    // Check if user has admin role in the current organization
    const isAdmin = orgRole === 'org:admin' || orgRole === 'admin';
    
    if (!isAdmin) {
      throw createForbiddenError("Admin access required");
    }

    // Get query parameters
    const searchParams = request.nextUrl.searchParams
    const limit = Number.parseInt(searchParams.get("limit") || "20", 10)
    const offset = Number.parseInt(searchParams.get("offset") || "0", 10)
    const query = searchParams.get("query") || ""

    // Initialize Clerk client for user management
    const clerk = await clerkClient();
    
    // Get users from Clerk
    const usersResponse = await clerk.users.getUserList({
      limit,
      offset,
      query,
    }) as unknown as ClerkUserResponse

    // Return users
    return NextResponse.json({
      users: usersResponse.data.map((user: ClerkUser) => ({
        id: user.id,
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.emailAddresses?.[0]?.emailAddress,
        imageUrl: user.imageUrl,
        createdAt: user.createdAt,
        lastSignInAt: user.lastSignInAt,
      })),
      meta: {
        total: usersResponse.totalCount,
        limit,
        offset,
      },
    })
  } catch (error) {
    return handleApiError(error)
  }
}

