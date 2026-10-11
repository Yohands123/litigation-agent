import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Presence check only. The backend verifies the JWT on every request,
// and a rejected token redirects to /login from src/lib/backend.ts.
export function proxy(request: NextRequest) {
  if (!request.cookies.has("lfa_token")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
