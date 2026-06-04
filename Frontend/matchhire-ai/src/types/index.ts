// src/types/index.ts
// Complete type system for MatchHire AI

// ─────────────────────────────────────────────────────────────
// API Request / Response Types
// ─────────────────────────────────────────────────────────────

export interface ResumeUploadResponse {
  resume_id: string
  file_name: string
  file_size_bytes: number
  mime_type: string
  parsed: any
  message: string
}

export interface JobDescriptionParseRequest {
  text: string
}

export interface JobDescriptionParseResponse {
  jd_id: string
  title?: string
  company?: string
  required_skills: string[]
  preferred_skills: string[]
  experience_required?: string
  education_required?: string
  keywords: string[]
  status: 'success' | 'error'
  message?: string
}

export interface MatchAnalyzeRequest {
  parsed_resume: any
  jd_text: string
  job_title_hint?: string
  company_name?: string
}

export interface SkillMatch {
  skill: string
  present: boolean
  score: number
  category?: 'technical' | 'soft' | 'domain' | 'tool'
}

export interface ATSKeyword {
  keyword: string
  found: boolean
  frequency: number
  importance: 'high' | 'medium' | 'low'
}

export interface Recommendation {
  id: string
  type: 'skill_gap' | 'formatting' | 'keyword' | 'experience' | 'achievement'
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  action?: string
  impact?: string
}

export interface MatchAnalyzeResponse {
  match_id: string
  overall_score: number  // 0-100
  skill_match_score: number
  experience_score: number
  education_score: number
  ats_score: number

  skill_breakdown: SkillMatch[]
  missing_skills: string[]
  matching_skills: string[]

  strengths: string[]
  weaknesses: string[]

  ats_keywords: ATSKeyword[]
  ats_coverage_percentage: number

  recommendations: Recommendation[]

  resume_insights: {
    word_count?: number
    sections_found?: string[]
    quantified_achievements?: number
    action_verbs_count?: number
    readability_score?: number
  }

  job_insights: {
    title?: string
    company?: string
    seniority_level?: string
    industry?: string
    remote_type?: string
  }

  created_at: string
  status: 'success' | 'error'
  message?: string
}

// ─────────────────────────────────────────────────────────────
// Application State Types
// ─────────────────────────────────────────────────────────────

export type AnalysisStep =
  | 'idle'
  | 'uploading_resume'
  | 'parsing_jd'
  | 'analyzing'
  | 'complete'
  | 'error'

export interface AnalysisState {
  step: AnalysisStep
  resumeId: string | null
  jdId: string | null
  matchResult: MatchAnalyzeResponse | null
  uploadedFile: File | null
  jobDescriptionText: string
  error: string | null
  progress: number // 0-100
}

export type ScoreCategory = 'excellent' | 'good' | 'fair' | 'poor'

export interface UIState {
  theme: 'light' | 'dark' | 'system'
  activeTab: 'overview' | 'skills' | 'ats' | 'recommendations'
  sidebarOpen: boolean
}

// ─────────────────────────────────────────────────────────────
// Component Props Types
// ─────────────────────────────────────────────────────────────

export interface ScoreRingProps {
  score: number
  size?: 'sm' | 'md' | 'lg' | 'xl'
  label?: string
  showLabel?: boolean
  animated?: boolean
  className?: string
}

export interface SkillBadgeProps {
  skill: string
  present?: boolean
  score?: number
  category?: SkillMatch['category']
  size?: 'sm' | 'md'
}

export interface InsightCardProps {
  title: string
  items: string[]
  type: 'strength' | 'weakness' | 'recommendation'
  icon?: React.ReactNode
  className?: string
}

export interface ATSKeywordProps {
  keywords: ATSKeyword[]
  coveragePercentage: number
  className?: string
}

export interface LoadingStep {
  id: string
  label: string
  sublabel?: string
  duration: number // ms
}

// ─────────────────────────────────────────────────────────────
// Form Types
// ─────────────────────────────────────────────────────────────

export interface AnalyzeFormValues {
  jobDescription: string
}

// ─────────────────────────────────────────────────────────────
// Utility Types
// ─────────────────────────────────────────────────────────────

export type ApiError = {
  status: number
  message: string
  details?: unknown
}

export type AsyncState<T> = {
  data: T | null
  loading: boolean
  error: ApiError | null
}
