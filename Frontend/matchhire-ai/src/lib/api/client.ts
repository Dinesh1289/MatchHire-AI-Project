// src/lib/api/client.ts
import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios'
import { env } from '@/config/env'
import type { ApiError } from '@/types'

// ─────────────────────────────────────────────────────────────
// Base Axios Instance
// ─────────────────────────────────────────────────────────────

const apiClient: AxiosInstance = axios.create({
  baseURL: env.API_BASE_URL,
  timeout: 60000, // 60s for AI analysis
  headers: {
    'Accept': 'application/json',
  },
})

// ─────────────────────────────────────────────────────────────
// Request Interceptor — auth token injection (auth-ready)
// ─────────────────────────────────────────────────────────────

apiClient.interceptors.request.use(
  (config) => {
    // When auth is added: inject Bearer token here
    // const token = getAuthToken()
    // if (token) config.headers.Authorization = `Bearer ${token}`

    if (env.IS_DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => Promise.reject(normalizeError(error))
)

// ─────────────────────────────────────────────────────────────
// Response Interceptor — error normalization
// ─────────────────────────────────────────────────────────────

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (env.IS_DEV) {
      console.error('[API Error]', error.response?.data ?? error.message)
    }

    // Auth-ready: handle 401 globally
    if (error.response?.status === 401) {
      // When auth is added: redirect to login
      // window.location.href = '/auth/login'
    }

    return Promise.reject(normalizeError(error))
  }
)

// ─────────────────────────────────────────────────────────────
// Error normalizer — converts raw Axios errors to ApiError
// ─────────────────────────────────────────────────────────────

function normalizeError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string; message?: string } | undefined
    return {
      status: error.response?.status ?? 0,
      message:
        data?.detail ??
        data?.message ??
        error.message ??
        'An unexpected error occurred.',
      details: error.response?.data,
    }
  }
  return {
    status: 0,
    message: error instanceof Error ? error.message : 'Unknown error',
  }
}

export { apiClient, normalizeError }
