// src/app/analyze/page.tsx
'use client'

import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Sparkles, ArrowRight, Zap } from 'lucide-react'
import Link from 'next/link'
import { analyzeFormSchema, type AnalyzeFormValues } from '@/lib/validators/schemas'
import { useMatchAnalysis } from '@/hooks/useMatchAnalysis'
import { useAnalyzeStore } from '@/store/analyzeStore'
import { ResumeDropzone } from '@/components/features/upload/ResumeDropzone'
import { JobDescriptionInput } from '@/components/features/jd-input/JobDescriptionInput'
import { LoadingScreen } from '@/components/features/analysis/LoadingScreen'
import { ErrorBanner } from '@/components/ui/States'
import { Button } from '@/components/ui/Button'
import type { Metadata } from 'next'

export default function AnalyzePage() {
  const { runAnalysis, isLoading, step, progress, error, reset } = useMatchAnalysis()
  const { setUploadedFile, setJobDescription, uploadedFile, jobDescriptionText } = useAnalyzeStore()

  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<AnalyzeFormValues>({
    resolver: zodResolver(analyzeFormSchema),
    defaultValues: {
      jobDescription: jobDescriptionText,
    },
  })

  const watchedJD = watch('jobDescription')

  const onSubmit = async (data: AnalyzeFormValues) => {
    if (!uploadedFile) return
    await runAnalysis(uploadedFile, data.jobDescription)
  }

  const handleFileAccepted = (file: File) => {
    setUploadedFile(file)
    setValue('resume', file, { shouldValidate: true })
  }

  const handleFileRemoved = () => {
    setUploadedFile(null)
    // @ts-expect-error reset file field
    setValue('resume', undefined)
  }

  const handleJDChange = (text: string) => {
    setJobDescription(text)
    setValue('jobDescription', text, { shouldValidate: text.length > 0 })
  }

  return (
    <>
      {/* Full-screen loading overlay */}
      <AnimatePresence>
        {isLoading && <LoadingScreen step={step} progress={progress} />}
      </AnimatePresence>

      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b border-border/50 bg-background/80 backdrop-blur-xl sticky top-0 z-10">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="h-7 w-7 rounded-md bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center">
                <Zap className="h-3.5 w-3.5 text-white" strokeWidth={2.5} />
              </div>
              <span className="font-display font-bold text-sm text-foreground">
                MatchHire<span className="gradient-text">AI</span>
              </span>
            </Link>
            <p className="text-sm text-muted-foreground hidden sm:block">
              Analyze resume fit in seconds
            </p>
          </div>
        </header>

        {/* Main content */}
        <main className="mx-auto max-w-4xl px-4 sm:px-6 py-10">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          >
            {/* Page header */}
            <div className="mb-8 text-center">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-100 dark:bg-brand-50/10 border border-brand-200/50 dark:border-brand-200/20 text-brand-600 dark:text-brand-400 text-xs font-medium mb-4">
                <Sparkles className="h-3.5 w-3.5" />
                AI-powered match analysis
              </div>
              <h1 className="font-display text-3xl sm:text-4xl font-bold text-foreground tracking-tight mb-3">
                How well do you match?
              </h1>
              <p className="text-muted-foreground max-w-lg mx-auto">
                Upload your resume and paste the job description. We&apos;ll give you a detailed
                compatibility report in under 60 seconds.
              </p>
            </div>

            {/* Error banner */}
            <AnimatePresence>
              {error && (
                <div className="mb-6">
                  <ErrorBanner message={error} onDismiss={reset} />
                </div>
              )}
            </AnimatePresence>

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} noValidate>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Left: Resume upload */}
                <div className="space-y-1">
                  <ResumeDropzone
                    onFileAccepted={handleFileAccepted}
                    onFileRemoved={handleFileRemoved}
                    currentFile={uploadedFile}
                    disabled={isLoading}
                  />
                  {errors.resume && (
                    <p className="text-xs text-destructive">{errors.resume.message}</p>
                  )}
                </div>

                {/* Right: Job description */}
                <JobDescriptionInput
                  value={watchedJD || ''}
                  onChange={handleJDChange}
                  error={errors.jobDescription?.message}
                  disabled={isLoading}
                />
              </div>

              {/* What you&apos;ll get section */}
              <div className="mb-8 rounded-2xl border border-border bg-card/60 p-5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-4">
                  What you&apos;ll get
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { emoji: '🎯', label: 'Match score' },
                    { emoji: '🧠', label: 'Skill gap report' },
                    { emoji: '🛡️', label: 'ATS keywords' },
                    { emoji: '💡', label: 'Recommendations' },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                      <span className="text-base">{item.emoji}</span>
                      <span className="text-sm text-foreground/80">{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Submit button */}
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <Button
                  type="submit"
                  variant="brand"
                  size="xl"
                  loading={isLoading}
                  disabled={!uploadedFile}
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                  className="w-full sm:w-auto sm:min-w-56"
                >
                  {isLoading ? 'Analyzing...' : 'Analyze match'}
                </Button>
                <p className="text-xs text-muted-foreground text-center sm:text-left">
                  No account required · Your data is not stored
                </p>
              </div>
            </form>
          </motion.div>
        </main>
      </div>
    </>
  )
}
