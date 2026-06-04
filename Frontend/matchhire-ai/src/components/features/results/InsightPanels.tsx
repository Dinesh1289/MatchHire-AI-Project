// src/components/features/results/InsightPanels.tsx
'use client'

import { motion } from 'framer-motion'
import {
  ThumbsUp, ThumbsDown, Lightbulb, ArrowRight,
  CheckCircle2, XCircle, AlertTriangle, Star
} from 'lucide-react'
import { cn, getPriorityColor } from '@/lib/utils'
import type { Recommendation } from '@/types'

// ─────────────────────────────────────────────────────────────
// Strengths panel
// ─────────────────────────────────────────────────────────────

interface StrengthsPanelProps {
  strengths: string[]
  className?: string
}

export function StrengthsPanel({ strengths, className }: StrengthsPanelProps) {
  if (strengths.length === 0) return null

  return (
    <div className={cn('rounded-2xl border border-score-excellent/20 bg-score-excellent/5 p-5 space-y-4', className)}>
      <div className="flex items-center gap-2.5">
        <div className="h-8 w-8 rounded-lg bg-score-excellent/15 flex items-center justify-center">
          <ThumbsUp className="h-4 w-4 text-score-excellent" />
        </div>
        <div>
          <h3 className="font-display font-semibold text-sm text-foreground">Your strengths</h3>
          <p className="text-xs text-muted-foreground">Where you stand out for this role</p>
        </div>
        <span className="ml-auto h-6 w-6 rounded-full bg-score-excellent/15 flex items-center justify-center text-xs font-bold text-score-excellent">
          {strengths.length}
        </span>
      </div>

      <div className="space-y-2.5">
        {strengths.map((strength, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06, duration: 0.3 }}
            className="flex items-start gap-2.5"
          >
            <CheckCircle2 className="h-4 w-4 text-score-excellent shrink-0 mt-0.5" />
            <p className="text-sm text-foreground/90 leading-relaxed">{strength}</p>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Weaknesses panel
// ─────────────────────────────────────────────────────────────

interface WeaknessesPanelProps {
  weaknesses: string[]
  className?: string
}

export function WeaknessesPanel({ weaknesses, className }: WeaknessesPanelProps) {
  if (weaknesses.length === 0) return null

  return (
    <div className={cn('rounded-2xl border border-destructive/20 bg-destructive/5 p-5 space-y-4', className)}>
      <div className="flex items-center gap-2.5">
        <div className="h-8 w-8 rounded-lg bg-destructive/15 flex items-center justify-center">
          <ThumbsDown className="h-4 w-4 text-destructive" />
        </div>
        <div>
          <h3 className="font-display font-semibold text-sm text-foreground">Areas to address</h3>
          <p className="text-xs text-muted-foreground">Gaps that may hurt your application</p>
        </div>
        <span className="ml-auto h-6 w-6 rounded-full bg-destructive/15 flex items-center justify-center text-xs font-bold text-destructive">
          {weaknesses.length}
        </span>
      </div>

      <div className="space-y-2.5">
        {weaknesses.map((weakness, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06, duration: 0.3 }}
            className="flex items-start gap-2.5"
          >
            <XCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <p className="text-sm text-foreground/90 leading-relaxed">{weakness}</p>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Recommendations section
// ─────────────────────────────────────────────────────────────

interface RecommendationsSectionProps {
  recommendations: Recommendation[]
  className?: string
}

export function RecommendationsSection({ recommendations, className }: RecommendationsSectionProps) {
  if (recommendations.length === 0) return null

  const highPriority = recommendations.filter((r) => r.priority === 'high')
  const rest = recommendations.filter((r) => r.priority !== 'high')
  const ordered = [...highPriority, ...rest]

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2.5">
        <div className="h-8 w-8 rounded-lg bg-brand-500/10 flex items-center justify-center">
          <Lightbulb className="h-4 w-4 text-brand-500" />
        </div>
        <div>
          <h3 className="font-display font-semibold text-foreground">AI Recommendations</h3>
          <p className="text-sm text-muted-foreground">
            {ordered.length} specific actions to improve your match
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {ordered.map((rec, i) => (
          <RecommendationCard key={rec.id} recommendation={rec} index={i} />
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Individual recommendation card
// ─────────────────────────────────────────────────────────────

function RecommendationCard({ recommendation: rec, index }: { recommendation: Recommendation; index: number }) {
  const priority = getPriorityColor(rec.priority)

  const typeIcons = {
    skill_gap: <Star className="h-3.5 w-3.5" />,
    formatting: <AlertTriangle className="h-3.5 w-3.5" />,
    keyword: <CheckCircle2 className="h-3.5 w-3.5" />,
    experience: <ThumbsUp className="h-3.5 w-3.5" />,
    achievement: <Lightbulb className="h-3.5 w-3.5" />,
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.35, ease: 'easeOut' }}
      className="group rounded-xl border border-border bg-card hover:border-brand-200/50 dark:hover:border-brand-200/20 hover:shadow-sm transition-all duration-200 overflow-hidden"
    >
      <div className="p-4">
        {/* Header row */}
        <div className="flex items-start gap-3">
          <div className={cn('h-8 w-8 rounded-lg flex items-center justify-center shrink-0', priority.bg)}>
            <span className={priority.text}>
              {typeIcons[rec.type] ?? <Lightbulb className="h-3.5 w-3.5" />}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-semibold text-foreground truncate">{rec.title}</h4>
              <span className={cn(
                'inline-flex shrink-0 items-center px-1.5 py-0.5 rounded-md text-xs font-medium border',
                priority.bg, priority.text, priority.border
              )}>
                {rec.priority}
              </span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{rec.description}</p>
          </div>
        </div>

        {/* Action and impact */}
        {(rec.action || rec.impact) && (
          <div className="mt-3 pt-3 border-t border-border space-y-1.5">
            {rec.action && (
              <div className="flex items-start gap-2">
                <ArrowRight className="h-3.5 w-3.5 text-brand-500 shrink-0 mt-0.5" />
                <p className="text-xs text-foreground/80">
                  <span className="font-medium text-brand-500">Action: </span>
                  {rec.action}
                </p>
              </div>
            )}
            {rec.impact && (
              <div className="flex items-start gap-2">
                <TrendingUp className="h-3.5 w-3.5 text-score-excellent shrink-0 mt-0.5" />
                <p className="text-xs text-muted-foreground">
                  <span className="font-medium text-score-excellent">Impact: </span>
                  {rec.impact}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}

function TrendingUp({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  )
}
