// src/hooks/useMatchAnalysis.ts
'use client'

import { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { resumeApi, jobDescriptionApi, matchApi } from '@/lib/api/services'
import { useAnalyzeStore } from '@/store/analyzeStore'

export function useMatchAnalysis() {
  const router = useRouter()
  const {
    step,
    progress,
    error,
    matchResult,
    uploadedFile,
    jobDescriptionText,
    setStep,
    setResumeId,
    setJdId,
    setMatchResult,
    setError,
    setProgress,
    reset,
  } = useAnalyzeStore()

  const runAnalysis = useCallback(
    async (file: File, jdText: string) => {
      try {
        // ── Step 1: Upload resume ──────────────────────────────
        setStep('uploading_resume')
        setProgress(5)

        const resumeResult = await resumeApi.upload(file, (uploadPercent) => {
          // Map upload progress to 5-35% of total
          setProgress(5 + Math.floor(uploadPercent * 0.30))
        })

        if (resumeResult.status === 'error') {
          throw new Error(resumeResult.message ?? 'Resume upload failed.')
        }

        setResumeId(resumeResult.resume_id)
        setProgress(38)

        // ── Step 2: Parse job description ─────────────────────
        setStep('parsing_jd')
        setProgress(42)

        const jdResult = await jobDescriptionApi.parse({ text: jdText })

        if (jdResult.status === 'error') {
          throw new Error(jdResult.message ?? 'Job description parsing failed.')
        }

        setJdId(jdResult.jd_id)
        setProgress(65)

        // ── Step 3: Run match analysis ─────────────────────────
        setStep('analyzing')
        setProgress(70)

        // Simulate smooth progress while waiting for AI
        let currentProgress = 70
        const progressInterval = setInterval(() => {
          currentProgress = Math.min(currentProgress + 2, 92)
          setProgress(currentProgress)
          if (currentProgress >= 92) clearInterval(progressInterval)
        }, 400)

        const matchResult = await matchApi.analyze({
          parsed_resume: resumeResult.parsed,
          jd_text: jdText,
        })

        console.log(
          "MATCH RESULT",
          JSON.stringify(matchResult, null, 2)
        )

        clearInterval(progressInterval)

        if (matchResult.status === 'error') {
          throw new Error(matchResult.message ?? 'Match analysis failed.')
        }

        setProgress(100)
        setMatchResult(matchResult)

        // Navigate to results
        router.push('/results/demo')
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Something went wrong. Please try again.'
        setError(message)
        setProgress(0)
      }
    },
    [router, setError, setJdId, setMatchResult, setProgress, setResumeId, setStep]
  )

  const isLoading = ['uploading_resume', 'parsing_jd', 'analyzing'].includes(step)

  return {
    runAnalysis,
    isLoading,
    step,
    progress,
    error,
    matchResult,
    uploadedFile,
    jobDescriptionText,
    reset,
  }
}
