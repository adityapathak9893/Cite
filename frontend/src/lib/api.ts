import { supabase } from "./supabase"

const API_URL = import.meta.env.VITE_API_URL as string

if (!API_URL) {
  throw new Error("Missing VITE_API_URL environment variable in .env")
}

interface ApiRequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE"
  body?: unknown
  headers?: Record<string, string>
  timeout?: number
}

interface ApiError {
  error: {
    code: string
    message: string
    status: number
  }
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const { data } = await supabase.auth.getSession()
    const token = data.session?.access_token

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    return headers
  }

  async request<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
    const { method = "GET", body, headers: customHeaders, timeout = 30000 } = options

    const authHeaders = await this.getAuthHeaders()
    const headers = { ...authHeaders, ...customHeaders }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = (await response.json().catch(() => null)) as ApiError | null

        if (response.status === 401) {
          await supabase.auth.signOut()
          window.location.href = "/login"
        }

        throw new ApiClientError(
          errorData?.error?.message ?? `Request failed with status ${response.status}`,
          response.status,
          errorData?.error?.code ?? "UNKNOWN_ERROR"
        )
      }

      if (response.status === 204) {
        return undefined as T
      }

      return (await response.json()) as T
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof ApiClientError) {
        throw error
      }

      if (error instanceof DOMException && error.name === "AbortError") {
        throw new ApiClientError(
          "Unable to connect. Please check your internet and try again.",
          0,
          "TIMEOUT"
        )
      }

      throw new ApiClientError(
        "Unable to connect. Please check your internet and try again.",
        0,
        "NETWORK_ERROR"
      )
    }
  }

  async get<T>(endpoint: string, options?: Omit<ApiRequestOptions, "method" | "body">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" })
  }

  async post<T>(endpoint: string, body?: unknown, options?: Omit<ApiRequestOptions, "method" | "body">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "POST", body })
  }

  async put<T>(endpoint: string, body?: unknown, options?: Omit<ApiRequestOptions, "method" | "body">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "PUT", body })
  }

  async delete<T>(endpoint: string, options?: Omit<ApiRequestOptions, "method" | "body">): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" })
  }
}

export class ApiClientError extends Error {
  status: number
  code: string

  constructor(message: string, status: number, code: string) {
    super(message)
    this.name = "ApiClientError"
    this.status = status
    this.code = code
  }
}

export const api = new ApiClient(API_URL)
