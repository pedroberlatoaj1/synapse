const API_BASE_URL = "http://localhost:8000/api";

type ApiFetchOptions = RequestInit;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<TResponse>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<TResponse> {
  const { headers, ...requestOptions } = options;
  const { getAccessToken } = await import("./auth");
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
    const body = await parseResponseBody(response);
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? String(body.detail)
        : `Synapse API error: ${response.status}`;
    throw new ApiError(detail, response.status, body);
  }

  return parseResponseBody(response) as Promise<TResponse>;
}

export async function bffFetch<TResponse>(
  path: string,
  options: RequestInit = {},
): Promise<TResponse> {
  const response = await fetch(path, options);

  if (!response.ok) {
    const body = await parseResponseBody(response);
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? String(body.detail)
        : `Synapse BFF error: ${response.status}`;
    throw new ApiError(detail, response.status, body);
  }

  return parseResponseBody(response) as Promise<TResponse>;
}

async function parseResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export { API_BASE_URL };
