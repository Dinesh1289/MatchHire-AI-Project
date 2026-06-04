// src/config/env.ts
// All environment variables validated at startup
export const env = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000',
  APP_URL: process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000',
  IS_DEV: process.env.NODE_ENV === 'development',
  IS_PROD: process.env.NODE_ENV === 'production',
} as const

// API endpoint registry — single source of truth
export const API_ENDPOINTS = {
  RESUME_UPLOAD: '/resumes/upload',
  JOB_DESCRIPTION_PARSE: '/job-descriptions/parse',
  MATCH_ANALYZE: '/matches/analyze',
} as const

// Upload constraints
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE_MB: 10,
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024,
  ACCEPTED_TYPES: {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  },
  ACCEPTED_EXTENSIONS: ['.pdf', '.doc', '.docx'],
} as const

// UI config
export const UI_CONFIG = {
  TOAST_DURATION_MS: 4000,
  ANIMATION_DURATION_MS: 300,
  SKELETON_COUNT: 4,
  MIN_JD_LENGTH: 100,
  MAX_JD_LENGTH: 10000,
} as const
