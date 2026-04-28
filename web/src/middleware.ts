import { NextRequest, NextResponse } from "next/server";

const AUTH_COOKIE_NAMES = {
  access: "synapse_access_token",
  refresh: "synapse_refresh_token",
} as const;

export function middleware(request: NextRequest) {
  const hasAccessToken = request.cookies.has(AUTH_COOKIE_NAMES.access);
  const hasRefreshToken = request.cookies.has(AUTH_COOKIE_NAMES.refresh);

  if (!hasAccessToken && !hasRefreshToken) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/review/:path*"],
};
