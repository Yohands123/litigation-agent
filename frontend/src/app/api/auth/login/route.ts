import { NextResponse } from "next/server";
import { TOKEN_COOKIE } from "@/lib/backend";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const EIGHT_HOURS = 60 * 60 * 8;

export async function POST(request: Request) {
  let email: unknown;
  let password: unknown;
  try {
    ({ email, password } = await request.json());
  } catch {
    return NextResponse.json({ error: "Send email and password as JSON." }, { status: 400 });
  }
  if (typeof email !== "string" || typeof password !== "string" || !email || !password) {
    return NextResponse.json({ error: "Enter your email and password." }, { status: 400 });
  }

  let res: Response;
  try {
    res = await fetch(`${BACKEND_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { error: "The underwriting service is unreachable. Try again shortly." },
      { status: 502 },
    );
  }

  if (res.status === 401) {
    return NextResponse.json({ error: "Invalid email or password" }, { status: 401 });
  }
  if (!res.ok) {
    return NextResponse.json(
      { error: "Sign-in failed. Try again shortly." },
      { status: 502 },
    );
  }

  const data = (await res.json()) as {
    access_token: string;
    user: { email: string; role: string };
  };

  const response = NextResponse.json({ user: data.user });
  response.cookies.set(TOKEN_COOKIE, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: EIGHT_HOURS,
  });
  return response;
}
