import { NextResponse } from "next/server";
import { TOKEN_COOKIE } from "@/lib/backend";

export async function POST(request: Request) {
  // 303 so the browser follows the redirect with GET after the form POST.
  const response = NextResponse.redirect(new URL("/login", request.url), 303);
  response.cookies.set(TOKEN_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}
