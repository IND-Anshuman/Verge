const API_BASE = '';
const MAX_RETRIES = 3;
const RETRY_BASE_MS = 500;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  retries?: number;
  signal?: AbortSignal;
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, retries = MAX_RETRIES, signal, ...init } = options;
  const url = `${API_BASE}${path}`;

  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...(init.headers as Record<string, string>),
  };

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...init,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
      });

      if (!response.ok) {
        const errorBody = await response.text().catch(() => null);
        throw new ApiError(
          `API request failed: ${response.status} ${response.statusText}`,
          response.status,
          errorBody
        );
      }

      if (response.status === 204) return undefined as T;
      return (await response.json()) as T;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));

      // Don't retry on client errors (4xx) or abort
      if (err instanceof ApiError && err.status >= 400 && err.status < 500) throw err;
      if (signal?.aborted) throw err;

      // Exponential backoff
      if (attempt < retries) {
        await sleep(RETRY_BASE_MS * Math.pow(2, attempt));
      }
    }
  }

  throw lastError ?? new Error('Request failed');
}
