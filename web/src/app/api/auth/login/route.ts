import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAMES } from "../../../../lib/auth";

const DJANGO_LOGIN_URL = "http://localhost:8000/api/auth/login";

type TokenPair = {
  access: string;
  refresh: string;
};

export async function POST(request: Request) {
  const credentials = await request.json();

  const djangoResponse = await fetch(DJANGO_LOGIN_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });

  const body = await djangoResponse.json().catch(() => null);

  if (!djangoResponse.ok) {
    return NextResponse.json(
      { detail: body?.detail ?? "Invalid credentials" },
      { status: djangoResponse.status },
    );
  }

  const tokens = body as TokenPair;
  if (!tokens.access || !tokens.refresh) {
    return NextResponse.json(
      { detail: "Invalid auth response" },
      { status: 502 },
    );
  }

  const cookieStore = await cookies();
  cookieStore.set(AUTH_COOKIE_NAMES.access, tokens.access, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
  });
  cookieStore.set(AUTH_COOKIE_NAMES.refresh, tokens.refresh, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
  });

  return NextResponse.json({ ok: true });
}
