// src/lib/validators/schemas.ts
import { z } from 'zod'
import { UPLOAD_CONFIG, UI_CONFIG } from '@/config/env'

// ─────────────────────────────────────────────────────────────
// File upload validation
// ─────────────────────────────────────────────────────────────

export const resumeFileSchema = z
  .instanceof(File, { message: 'Please select a file.' })
  .refine(
    (file) => file.size <= UPLOAD_CONFIG.MAX_FILE_SIZE_BYTES,
    `File must be smaller than ${UPLOAD_CONFIG.MAX_FILE_SIZE_MB}MB.`
  )
  .refine(
    (file) => Object.keys(UPLOAD_CONFIG.ACCEPTED_TYPES).includes(file.type),
    'Only PDF, DOC, and DOCX files are accepted.'
  )

// ─────────────────────────────────────────────────────────────
// Job description form validation
// ─────────────────────────────────────────────────────────────

export const jobDescriptionSchema = z.object({
  jobDescription: z
    .string()
    .min(UI_CONFIG.MIN_JD_LENGTH, `Please enter at least ${UI_CONFIG.MIN_JD_LENGTH} characters.`)
    .max(UI_CONFIG.MAX_JD_LENGTH, `Job description is too long (max ${UI_CONFIG.MAX_JD_LENGTH} chars).`),
})

export type JobDescriptionFormValues = z.infer<typeof jobDescriptionSchema>

// ─────────────────────────────────────────────────────────────
// Analyze page combined schema
// ─────────────────────────────────────────────────────────────

export const analyzeFormSchema = z.object({
  resume: resumeFileSchema,
  jobDescription: jobDescriptionSchema.shape.jobDescription,
})

export type AnalyzeFormValues = z.infer<typeof analyzeFormSchema>
