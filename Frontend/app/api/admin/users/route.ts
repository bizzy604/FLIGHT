import { type NextRequest, NextResponse } from "next/server"
import { auth, clerkClient } from "@clerk/nextjs/server"
import { handleApiError, createUnauthorizedError, createForbiddenError } from "@/lib/error-handler"

export async function GET(request: NextRequest) {
  try {
    // Check authentication
    const { userId, orgRoles } = auth()
    if (!userId) {
      throw createUnauthorizedError()
    }

    // Check if user has admin role
    if (!orgRoles?.includes("admin")) {
      throw createForbiddenError("Admin access required")
    }

    // Get query parameters
    const searchParams = request.nextUrl.searchParams
    const limit = Number.parseInt(searchParams.get("limit") || "20", 10)
    const offset = Number.parseInt(searchParams.get("offset") || "0", 10)
    const query = searchParams.get("query") || ""

    // Get users from Clerk
    const users = await clerkClient.users.getUserList({
      limit,
      offset,
      query,
    })

    // Return users
    return NextResponse.json({
      users: users.map((user) => ({
        id: user.id,
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.emailAddresses[0]?.emailAddress,
        imageUrl: user.imageUrl,
        createdAt: user.createdAt,
        lastSignInAt: user.lastSignInAt,
      })),
      meta: {
        total: users.totalCount,
        limit,
        offset,
      },
    })
  } catch (error) {
    return handleApiError(error)
  }
}

