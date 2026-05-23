const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: unknown,
  ) {
    super(`API error ${status}`);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({
      title: response.statusText,
    }));
    throw new ApiError(response.status, errorBody);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, token?: string) =>
    request<T>(path, { token }),

  post: <T>(path: string, body: unknown, token?: string) =>
    request<T>(path, { method: "POST", body, token }),

  patch: <T>(path: string, body: unknown, token?: string) =>
    request<T>(path, { method: "PATCH", body, token }),

  delete: <T>(path: string, token?: string) =>
    request<T>(path, { method: "DELETE", token }),
};
