import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

export async function GET() {
  const { userId, sessionId, sessionClaims } = auth();
  
  return NextResponse.json({
    userId,
    sessionId,
    sessionClaims,
    role: sessionClaims?.role,
    isAdmin: sessionClaims?.role === "admin"
  });
}