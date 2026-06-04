// src/components/features/results/ATSSection.tsx
'use client'

import { motion } from 'framer-motion'
import { Shield, ShieldCheck, ShieldX, TrendingUp } from 'lucide-react'
import { cn, getScoreColor, getScoreCategory } from '@/lib/utils'
import { ScoreRing } from '@/components/ui/ScoreRing'
import type { ATSKeyword } from '@/types'

interface ATSSectionProps {
  keywords: ATSKeyword[]
  coveragePercentage: number
  className?: string
}

export function ATSSection({ keywords, coveragePercentage, className }: ATSSectionProps) {
  const found = keywords.filter((k) => k.found)
  const missing = keywords.filter((k) => !k.found)
  const highPriority = missing.filter((k) => k.importance === 'high')
  const category = getScoreCategory(coveragePercentage)

  return (
    <div className={cn('space-y-6', className)}>
      {/* ATS header */}
      <div className="flex items-start gap-4">
        <div className={cn(
          'h-12 w-12 rounded-xl flex items-center justify-center shrink-0',
          category === 'excellent' ? 'bg-score-excellent/10' :
          category === 'good' ? 'bg-score-good/10' :
          category === 'fair' ? 'bg-score-fair/10' : 'bg-destructive/10'
        )}>
          {category === 'excellent' || category === 'good' ? (
            <ShieldCheck className={cn(
              'h-6 w-6',
              category === 'excellent' ? 'text-score-excellent' : 'text-score-good'
            )} />
          ) : (
            <ShieldX className="h-6 w-6 text-destructive" />
          )}
        </div>
        <div>
          <h3 className="font-display font-semibold text-foreground">ATS Compatibility</h3>
          <p className="text-sm text-muted-foreground mt-0.5">
            {coveragePercentage >= 70
              ? 'Your resume is likely to pass ATS filters.'
              : 'Your resume may get filtered out before reaching a human.'}
          </p>
        </div>
        <div className="ml-auto">
          <ScoreRing score={coveragePercentage} size="sm" showLabel={false} />
        </div>
      </div>

      {/* High priority missing keywords callout */}
      {highPriority.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-destructive/20 bg-destructive/5 p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-4 w-4 text-destructive" />
            <p className="text-sm font-semibold text-destructive">
              {highPriority.length} high-priority keywords missing
            </p>
          </div>
          <p className="text-xs text-muted-foreground mb-3">
            These keywords appear most frequently in the job description. Add them to your resume to improve ATS pass rate.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {highPriority.map((kw, i) => (
              <motion.span
                key={kw.keyword}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.04 }}
                className="px-2.5 py-1 rounded-full bg-destructive/10 text-destructive text-xs font-medium border border-destructive/20"
              >
                {kw.keyword}
              </motion.span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Keyword coverage visualization */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground">Keyword coverage</h4>
          <span className="text-xs text-muted-foreground">
            {found.length}/{keywords.length} found
          </span>
        </div>

        {/* Visual keyword grid */}
        <div className="grid grid-cols-2 gap-2">
          {keywords.map((kw, i) => (
            <KeywordItem key={kw.keyword} keyword={kw} index={i} />
          ))}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Individual keyword item
// ─────────────────────────────────────────────────────────────

function KeywordItem({ keyword, index }: { keyword: ATSKeyword; index: number }) {
  const importanceColors = {
    high: { dot: 'bg-destructive', text: 'text-destructive' },
    medium: { dot: 'bg-score-fair', text: 'text-score-fair' },
    low: { dot: 'bg-muted-foreground', text: 'text-muted-foreground' },
  }
  const colors = importanceColors[keyword.importance]

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.025 }}
      className={cn(
        'flex items-center gap-2.5 rounded-lg px-3 py-2 border text-xs transition-colors',
        keyword.found
          ? 'border-score-excellent/20 bg-score-excellent/5'
          : 'border-border bg-muted/30'
      )}
    >
      {/* Importance dot */}
      <span className={cn('h-1.5 w-1.5 rounded-full shrink-0 mt-0.5', colors.dot)} />

      {/* Keyword text */}
      <span className={cn(
        'flex-1 font-medium truncate',
        keyword.found ? 'text-foreground' : 'text-muted-foreground'
      )}>
        {keyword.keyword}
      </span>

      {/* Status icon */}
      {keyword.found ? (
        <Shield className="h-3 w-3 text-score-excellent shrink-0" />
      ) : (
        <ShieldX className="h-3 w-3 text-muted-foreground/50 shrink-0" />
      )}
    </motion.div>
  )
}
