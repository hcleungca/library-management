/**
 * Centralized API client for the Intelligent Library System.
 * Injects active Bearer authentication tokens, standardizes JSON serialization,
 * and normalizes backend FastAPI error responses.
 */

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

/**
 * Fetch wrapper for API calls with automatic Bearer token injection and error parsing.
 *
 * @param endpoint Relative API endpoint (e.g. '/books' or '/circulation/checkout')
 * @param options Standard fetch RequestInit options
 * @returns Parsed JSON response of type T
 */
export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options?.headers || {});

  // Default to application/json if body is not FormData
  if (!headers.has('Content-Type') && !(options?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Attach active Bearer auth token if present in localStorage
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
    try {
      const errorBody = await response.json();
      if (errorBody && typeof errorBody.detail === 'string') {
        errorMessage = errorBody.detail;
      } else if (errorBody && Array.isArray(errorBody.detail)) {
        // FastAPI Pydantic validation error array
        errorMessage = errorBody.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(', ');
      }
    } catch {
      // Non-JSON error payload, fallback to HTTP status
    }
    throw new ApiError(response.status, errorMessage);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}
