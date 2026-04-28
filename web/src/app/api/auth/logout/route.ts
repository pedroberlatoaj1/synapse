import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAMES } from "../../../../lib/auth";

export async function POST() {
  const cookieStore = await cookies();

  cookieStore.set(AUTH_COOKIE_NAMES.access, "", {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  cookieStore.set(AUTH_COOKIE_NAMES.refresh, "", {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });

  return NextResponse.json({ ok: true });
}
