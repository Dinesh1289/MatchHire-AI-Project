// src/store/analyzeStore.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { AnalysisState, MatchAnalyzeResponse, AnalysisStep } from '@/types'

interface AnalyzeStore extends AnalysisState {
  // Actions
  setStep: (step: AnalysisStep) => void
  setResumeId: (id: string) => void
  setJdId: (id: string) => void
  setMatchResult: (result: MatchAnalyzeResponse) => void
  setUploadedFile: (file: File | null) => void
  setJobDescription: (text: string) => void
  setError: (error: string | null) => void
  setProgress: (progress: number) => void
  reset: () => void
}

const initialState: AnalysisState = {
  step: 'idle',
  resumeId: null,
  jdId: null,
  matchResult: null,
  uploadedFile: null,
  jobDescriptionText: '',
  error: null,
  progress: 0,
}

export const useAnalyzeStore = create<AnalyzeStore>()(
  devtools(
    (set) => ({
      ...initialState,

      setStep: (step) => set({ step }, false, 'setStep'),
      setResumeId: (resumeId) => set({ resumeId }, false, 'setResumeId'),
      setJdId: (jdId) => set({ jdId }, false, 'setJdId'),
      setMatchResult: (matchResult) =>
        set({ matchResult, step: 'complete' }, false, 'setMatchResult'),
      setUploadedFile: (uploadedFile) => set({ uploadedFile }, false, 'setUploadedFile'),
      setJobDescription: (jobDescriptionText) =>
        set({ jobDescriptionText }, false, 'setJobDescription'),
      setError: (error) => set({ error, step: error ? 'error' : 'idle' }, false, 'setError'),
      setProgress: (progress) => set({ progress }, false, 'setProgress'),
      reset: () => set(initialState, false, 'reset'),
    }),
    { name: 'AnalyzeStore' }
  )
)
