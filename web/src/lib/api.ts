import { getAccessToken } from "./auth";

const API_BASE_URL = "http://localhost:8000/api";

type ApiFetchOptions = RequestInit;

export async function apiFetch<TResponse>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<TResponse> {
  const { headers, ...requestOptions } = options;
  const token = await getAccessToken();
  const requestHeaders = new Headers(headers);

  if (!requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }
  if (token && !requestHeaders.has("Authorization")) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers: requestHeaders,
  });

  if (!response.ok) {
    throw new Error(`Synapse API error: ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}

export { API_BASE_URL };
