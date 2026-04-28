import { cookies } from "next/headers";

export const AUTH_COOKIE_NAMES = {
  access: "synapse_access_token",
  refresh: "synapse_refresh_token",
} as const;

export async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(AUTH_COOKIE_NAMES.access)?.value ?? null;
}

export async function getRefreshToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(AUTH_COOKIE_NAMES.refresh)?.value ?? null;
}

export async function isAuthenticated(): Promise<boolean> {
  return Boolean(await getAccessToken());
}
