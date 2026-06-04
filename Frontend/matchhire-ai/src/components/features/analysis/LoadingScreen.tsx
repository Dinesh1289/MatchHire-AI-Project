// src/components/features/analysis/LoadingScreen.tsx
'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Brain, Sparkles, CheckCircle2, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AnalysisStep } from '@/types'

interface LoadingScreenProps {
  step: AnalysisStep
  progress: number
}

const STEPS = [
  {
    id: 'uploading_resume' as AnalysisStep,
    icon: FileText,
    label: 'Processing your resume',
    sublabel: 'Parsing structure, skills, and experience',
    color: 'text-brand-500',
    bgColor: 'bg-brand-500/10',
  },
  {
    id: 'parsing_jd' as AnalysisStep,
    icon: Brain,
    label: 'Understanding the job',
    sublabel: 'Extracting requirements and keywords',
    color: 'text-score-good',
    bgColor: 'bg-score-good/10',
  },
  {
    id: 'analyzing' as AnalysisStep,
    icon: Sparkles,
    label: 'Running AI analysis',
    sublabel: 'Calculating match score and generating insights',
    color: 'text-score-excellent',
    bgColor: 'bg-score-excellent/10',
  },
]

const stepOrder: AnalysisStep[] = ['uploading_resume', 'parsing_jd', 'analyzing']

function getStepStatus(stepId: AnalysisStep, currentStep: AnalysisStep) {
  const currentIndex = stepOrder.indexOf(currentStep)
  const stepIndex = stepOrder.indexOf(stepId)
  if (stepIndex < currentIndex) return 'done'
  if (stepIndex === currentIndex) return 'active'
  return 'pending'
}

// Typing messages for each stage
const stageCopy: Record<string, string[]> = {
  uploading_resume: [
    'Reading your work history...',
    'Identifying your skill set...',
    'Extracting achievements...',
  ],
  parsing_jd: [
    'Mapping required skills...',
    'Detecting ATS keywords...',
    'Assessing seniority level...',
  ],
  analyzing: [
    'Calculating compatibility...',
    'Finding skill gaps...',
    'Generating recommendations...',
    'Finalizing your report...',
  ],
}

export function LoadingScreen({ step, progress }: LoadingScreenProps) {
  const [messageIndex, setMessageIndex] = useState(0)
  const [displayText, setDisplayText] = useState('')
  const messages = useMemo(() => stageCopy[step] ?? [], [step])

  // Rotate sub-messages during each step
  useEffect(() => {
    setMessageIndex(0)
    const interval = setInterval(() => {
      setMessageIndex((i) => (i + 1) % (messages.length || 1))
    }, 2000)
    return () => clearInterval(interval)
  }, [step, messages.length])

  // Typewriter effect
  useEffect(() => {
    const target = messages[messageIndex] ?? ''
    let i = 0
    setDisplayText('')
    const timer = setInterval(() => {
      setDisplayText(target.slice(0, i + 1))
      i++
      if (i >= target.length) clearInterval(timer)
    }, 28)
    return () => clearInterval(timer)
  }, [messageIndex, messages])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed inset-0 z-50 bg-background flex items-center justify-center"
    >
      {/* Background effects */}
      <div className="absolute inset-0 dot-grid opacity-30" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full bg-brand-500/8 blur-3xl" />

      <div className="relative max-w-md w-full mx-auto px-6 text-center space-y-10">
        {/* Animated logo icon */}
        <motion.div
          animate={{ scale: [1, 1.06, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="mx-auto h-20 w-20 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center shadow-2xl shadow-brand-500/30"
        >
          <Sparkles className="h-9 w-9 text-white" />
        </motion.div>

        {/* Heading */}
        <div>
          <h2 className="font-display text-2xl font-bold text-foreground mb-2">
            Analyzing your match
          </h2>
          <div className="h-6 flex items-center justify-center">
            <AnimatePresence mode="wait">
              <motion.p
                key={displayText}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm text-muted-foreground font-mono"
              >
                {displayText}
                <span className="animate-pulse ml-0.5">|</span>
              </motion.p>
            </AnimatePresence>
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="h-1.5 rounded-full bg-border overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400"
              initial={{ width: '0%' }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              style={{ boxShadow: '0 0 8px hsl(var(--brand-500) / 0.6)' }}
            />
          </div>
          <p className="text-xs text-muted-foreground tabular-nums">{progress}% complete</p>
        </div>

        {/* Step list */}
        <div className="space-y-3">
          {STEPS.map((s, i) => {
            const status = getStepStatus(s.id, step)
            const Icon = s.icon

            return (
              <motion.div
                key={s.id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.12 }}
                className={cn(
                  'flex items-center gap-3 rounded-xl px-4 py-3 transition-all duration-300',
                  status === 'active' && 'bg-card border border-border shadow-sm',
                  status === 'done' && 'opacity-60',
                  status === 'pending' && 'opacity-30'
                )}
              >
                {/* Step icon */}
                <div className={cn(
                  'h-9 w-9 rounded-lg flex items-center justify-center shrink-0 transition-all duration-300',
                  status === 'done' ? 'bg-score-excellent/10' : s.bgColor,
                  status === 'active' && 'ring-2 ring-offset-1 ring-offset-background',
                  status === 'active' && `ring-brand-400/30`
                )}>
                  {status === 'done' ? (
                    <CheckCircle2 className="h-4.5 w-4.5 text-score-excellent" />
                  ) : status === 'active' ? (
                    <Loader2 className={cn('h-4.5 w-4.5 animate-spin', s.color)} />
                  ) : (
                    <Icon className="h-4.5 w-4.5 text-muted-foreground" />
                  )}
                </div>

                {/* Step label */}
                <div className="text-left flex-1">
                  <p className={cn(
                    'text-sm font-medium',
                    status === 'active' ? 'text-foreground' : 'text-muted-foreground'
                  )}>
                    {s.label}
                  </p>
                  <p className="text-xs text-muted-foreground/70">{s.sublabel}</p>
                </div>

                {/* Done indicator */}
                {status === 'done' && (
                  <span className="text-xs text-score-excellent font-medium">Done</span>
                )}
              </motion.div>
            )
          })}
        </div>

        <p className="text-xs text-muted-foreground/50">
          This usually takes 15–30 seconds
        </p>
      </div>
    </motion.div>
  )
}
