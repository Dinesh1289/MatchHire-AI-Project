// src/components/features/results/SkillAnalysis.tsx
'use client'

import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SkillMatch } from '@/types'

// ─────────────────────────────────────────────────────────────
// Individual skill badge
// ─────────────────────────────────────────────────────────────

interface SkillBadgeProps {
  skill: string
  present?: boolean
  score?: number
  index?: number
  className?: string
}

export function SkillBadge({ skill, present = true, score, index = 0, className }: SkillBadgeProps) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.035, duration: 0.2, ease: 'backOut' }}
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors',
        present
          ? 'bg-score-excellent/8 text-score-excellent border-score-excellent/20 hover:bg-score-excellent/15'
          : 'bg-destructive/8 text-destructive border-destructive/20 hover:bg-destructive/15',
        className
      )}
    >
      {present ? (
        <CheckCircle2 className="h-3 w-3 shrink-0" />
      ) : (
        <XCircle className="h-3 w-3 shrink-0" />
      )}
      {skill}
    </motion.span>
  )
}

// ─────────────────────────────────────────────────────────────
// Full skill gap analysis section
// ─────────────────────────────────────────────────────────────

interface SkillAnalysisSectionProps {
  matchingSkills: string[]
  missingSkills: string[]
  skillBreakdown?: SkillMatch[]
  className?: string
}

export function SkillAnalysisSection({
  matchingSkills,
  missingSkills,
  skillBreakdown,
  className,
}: SkillAnalysisSectionProps) {
  const total = matchingSkills.length + missingSkills.length
  const matchRate = total > 0 ? Math.round((matchingSkills.length / total) * 100) : 0

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header with ratio */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-display font-semibold text-foreground">Skill Analysis</h3>
          <p className="text-sm text-muted-foreground mt-0.5">
            {matchingSkills.length} of {total} required skills detected
          </p>
        </div>
        <div className="text-right">
          <p className="font-display text-2xl font-bold text-foreground">{matchRate}%</p>
          <p className="text-xs text-muted-foreground">skill coverage</p>
        </div>
      </div>

      {/* Progress bar */}
      <SkillProgressBar matched={matchingSkills.length} total={total} />

      {/* Skills present */}
      {matchingSkills.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-score-excellent" />
            <h4 className="text-sm font-semibold text-foreground">
              Present ({matchingSkills.length})
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {matchingSkills.map((skill, i) => (
              <SkillBadge key={skill} skill={skill} present index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Skills missing */}
      {missingSkills.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-destructive" />
            <h4 className="text-sm font-semibold text-foreground">
              Missing ({missingSkills.length})
            </h4>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-destructive/10 text-destructive text-xs">
              Add these to your resume
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {missingSkills.map((skill, i) => (
              <SkillBadge key={skill} skill={skill} present={false} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Breakdown table (if available) */}
      {skillBreakdown && skillBreakdown.length > 0 && (
        <SkillBreakdownTable breakdown={skillBreakdown} />
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Skill progress bar
// ─────────────────────────────────────────────────────────────

function SkillProgressBar({ matched, total }: { matched: number; total: number }) {
  const percent = total > 0 ? (matched / total) * 100 : 0

  return (
    <div className="space-y-1">
      <div className="h-2 rounded-full bg-border overflow-hidden flex">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
          className="h-full bg-score-excellent rounded-full"
        />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span className="text-score-excellent">{matched} matched</span>
        <span className="text-destructive">{total - matched} missing</span>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Skill breakdown detail table
// ─────────────────────────────────────────────────────────────

function SkillBreakdownTable({ breakdown }: { breakdown: SkillMatch[] }) {
  const categories = ['technical', 'soft', 'domain', 'tool'] as const
  const grouped = categories.reduce((acc, cat) => {
    const skills = breakdown.filter((s) => s.category === cat)
    if (skills.length > 0) acc[cat] = skills
    return acc
  }, {} as Record<string, SkillMatch[]>)

  const categoryLabels: Record<string, string> = {
    technical: 'Technical',
    soft: 'Soft skills',
    domain: 'Domain',
    tool: 'Tools & platforms',
  }

  const hasCategories = Object.keys(grouped).length > 0
  if (!hasCategories) return null

  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-muted/30 flex items-center gap-2">
        <Info className="h-3.5 w-3.5 text-muted-foreground" />
        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Skill breakdown by category
        </h4>
      </div>
      <div className="divide-y divide-border">
        {Object.entries(grouped).map(([cat, skills]) => (
          <div key={cat} className="px-4 py-3">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              {categoryLabels[cat] ?? cat}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {skills.map((s) => (
                <span
                  key={s.skill}
                  className={cn(
                    'px-2 py-0.5 rounded-md text-xs font-medium',
                    s.present
                      ? 'bg-score-excellent/10 text-score-excellent'
                      : 'bg-muted text-muted-foreground line-through'
                  )}
                >
                  {s.skill}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
