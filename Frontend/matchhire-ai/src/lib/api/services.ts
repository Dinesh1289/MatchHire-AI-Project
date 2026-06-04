// src/lib/api/services.ts
import { apiClient } from './client'
import { API_ENDPOINTS } from '@/config/env'
import type {
  ResumeUploadResponse,
  JobDescriptionParseRequest,
  JobDescriptionParseResponse,
  MatchAnalyzeRequest,
  MatchAnalyzeResponse,
} from '@/types'

// ─────────────────────────────────────────────────────────────
// Resume API
// ─────────────────────────────────────────────────────────────

export const resumeApi = {
  /**
   * Upload a resume file (PDF, DOC, DOCX)
   * Returns a resume_id for downstream matching
   */
  upload: async (
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<ResumeUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<ResumeUploadResponse>(
      API_ENDPOINTS.RESUME_UPLOAD,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percent)
          }
        },
      }
    )
    return response.data
  },
}

// ─────────────────────────────────────────────────────────────
// Job Description API
// ─────────────────────────────────────────────────────────────

export const jobDescriptionApi = {
  /**
   * Parse a job description text
   * Returns a jd_id + extracted structured data
   */
  parse: async (payload: JobDescriptionParseRequest): Promise<JobDescriptionParseResponse> => {
    const response = await apiClient.post<JobDescriptionParseResponse>(
      API_ENDPOINTS.JOB_DESCRIPTION_PARSE,
      payload
    )
    return response.data
  },
}

// ─────────────────────────────────────────────────────────────
// Match API
// ─────────────────────────────────────────────────────────────

export const matchApi = {
  /**
   * Run full AI match analysis between resume and job description
   * Returns complete MatchAnalyzeResponse with scores, gaps, recommendations
   */
  analyze: async (payload: MatchAnalyzeRequest): Promise<MatchAnalyzeResponse> => {
    const response = await apiClient.post<MatchAnalyzeResponse>(
      API_ENDPOINTS.MATCH_ANALYZE,
      payload
    )
    return response.data
  },
}
