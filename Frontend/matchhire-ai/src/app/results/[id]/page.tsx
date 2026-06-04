// src/app/results/[id]/page.tsx
'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, Download, RefreshCw, Zap, Share2 } from 'lucide-react'
import Link from 'next/link'
import { useAnalyzeStore } from '@/store/analyzeStore'
import { ScoreRing, ScoreBar } from '@/components/ui/ScoreRing'
import { SkillAnalysisSection } from '@/components/features/results/SkillAnalysis'
import { ATSSection } from '@/components/features/results/ATSSection'
import { StrengthsPanel, WeaknessesPanel, RecommendationsSection } from '@/components/features/results/InsightPanels'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { DashboardSkeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { cn, getScoreLabel, getScoreCategory, formatDate } from '@/lib/utils'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
}

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.25, 0.4, 0.25, 1] } },
}

export default function ResultsPage() {
  const params = useParams()
  const router = useRouter()
  const { matchResult, step, error, reset } = useAnalyzeStore()

  // Guard: if no result in store, redirect to analyze
  useEffect(() => {
    if (step !== 'complete' && step !== 'error' && !matchResult) {
      const timer = setTimeout(() => router.push('/analyze'), 300)
      return () => clearTimeout(timer)
    }
  }, [step, matchResult, router])

  if (step === 'error' || error) {
    return (
      <ResultsLayout>
        <ErrorState error={error ?? undefined} onRetry={reset} />
      </ResultsLayout>
    )
  }

  if (!matchResult) {
    return (
      <ResultsLayout>
        <DashboardSkeleton />
      </ResultsLayout>
    )
  }

  const result = (matchResult as any).result

const overall_score = result?.match_score_pct ?? 0

const skill_match_score =
  Math.round((result?.breakdown?.skills_match?.raw_score ?? 0) * 100)

const experience_score =
  Math.round((result?.breakdown?.experience_match?.raw_score ?? 0) * 100)

const education_score =
  Math.round((result?.breakdown?.education_match?.raw_score ?? 0) * 100)

const ats_score =
  Math.round((result?.breakdown?.keyword_match?.raw_score ?? 0) * 100)

const matching_skills = result?.matched_skills ?? []
const missing_skills = result?.missing_skills ?? []

const strengths =
  result?.strengths?.map((s: any) => s.title) ?? []

const weaknesses =
  result?.weaknesses?.map((w: any) => w.title) ?? []

const recommendations = []

const ats_keywords = []

const ats_coverage_percentage = 0

const skill_breakdown = []

const job_insights = {
  title: result?.parsed_jd?.title,
  company: result?.parsed_jd?.company,
}

const resume_insights = null

const created_at = new Date().toISOString()
  const scoreCategory = getScoreCategory(overall_score)
  const scoreLabel = getScoreLabel(overall_score)

  return (
    <ResultsLayout>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* ── Hero score card ──────────────────────────────── */}
        <motion.div variants={cardVariants}>
          <div className={cn(
            'rounded-2xl border p-6 sm:p-8 relative overflow-hidden',
            scoreCategory === 'excellent' ? 'border-score-excellent/25 bg-score-excellent/5' :
            scoreCategory === 'good' ? 'border-score-good/25 bg-score-good/5' :
            scoreCategory === 'fair' ? 'border-score-fair/25 bg-score-fair/5' :
            'border-destructive/25 bg-destructive/5'
          )}>
            {/* Background glow */}
            <div className={cn(
              'absolute -top-16 -right-16 w-64 h-64 rounded-full blur-3xl opacity-20',
              scoreCategory === 'excellent' ? 'bg-score-excellent' :
              scoreCategory === 'good' ? 'bg-score-good' :
              scoreCategory === 'fair' ? 'bg-score-fair' : 'bg-destructive'
            )} />

            <div className="relative flex flex-col sm:flex-row items-start sm:items-center gap-6">
              {/* Score ring */}
              <ScoreRing
                score={overall_score}
                size="xl"
                showLabel
                animated
              />

              {/* Info column */}
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <Badge variant={
                    scoreCategory === 'excellent' ? 'success' :
                    scoreCategory === 'good' ? 'default' :
                    scoreCategory === 'fair' ? 'warning' : 'destructive'
                  } className="text-sm px-3 py-1">
                    {scoreLabel}
                  </Badge>
                  {job_insights?.title && (
                    <Badge variant="muted">{job_insights.title}</Badge>
                  )}
                  {job_insights?.company && (
                    <Badge variant="outline">{job_insights.company}</Badge>
                  )}
                </div>

                <h1 className="font-display text-2xl sm:text-3xl font-bold text-foreground mb-2">
                  {overall_score >= 70
                    ? 'Strong candidate — apply with confidence.'
                    : overall_score >= 50
                    ? 'Good foundation — with some improvements.'
                    : 'Significant gaps — focus on these areas first.'}
                </h1>

                <p className="text-muted-foreground text-sm leading-relaxed max-w-lg">
                  {overall_score >= 70
                    ? `You match ${overall_score}% of this role's requirements. Your background aligns well — make sure to highlight your matching skills prominently.`
                    : overall_score >= 50
                    ? `You have ${matching_skills.length} of the required skills but ${missing_skills.length} gaps. Review our recommendations to strengthen your application.`
                    : `You're missing ${missing_skills.length} key skills. Focus on adding relevant experience and keywords before applying.`}
                </p>

                {created_at && (
                  <p className="text-xs text-muted-foreground/60 mt-3">
                    Analyzed {formatDate(created_at)}
                  </p>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex flex-row sm:flex-col gap-2 sm:shrink-0">
                <Link href="/analyze">
                  <Button variant="outline" size="sm" leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
                    New analysis
                  </Button>
                </Link>
                <Button variant="ghost" size="sm" leftIcon={<Share2 className="h-3.5 w-3.5" />}>
                  Share
                </Button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── Sub-score cards ───────────────────────────────── */}
        <motion.div variants={cardVariants} className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Skill match', score: skill_match_score },
            { label: 'Experience', score: experience_score },
            { label: 'Education', score: education_score },
            { label: 'ATS score', score: ats_score },
          ].map((item) => (
            <SubScoreCard key={item.label} label={item.label} score={item.score} />
          ))}
        </motion.div>

        {/* ── Resume insight pills ──────────────────────────── */}
        {resume_insights && (
          <motion.div variants={cardVariants}>
            <ResumeInsightBar insights={resume_insights} />
          </motion.div>
        )}

        {/* ── Main grid: Skills + ATS ───────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Skills: wider column */}
          <motion.div variants={cardVariants} className="lg:col-span-3">
            <div className="rounded-2xl border border-border bg-card p-6">
              {/* <SkillAnalysisSection
                matchingSkills={matching_skills}
                missingSkills={missing_skills}
                skillBreakdown={skill_breakdown}
              /> */}
              <SkillAnalysisSection
                matchingSkills={matching_skills.map((s:any) => s.name)}
                missingSkills={missing_skills.map((s:any) => s.name)}
                skillBreakdown={result?.matched_skills ?? []}
              />
            </div>
          </motion.div>

          {/* ATS: narrower column */}
          <motion.div variants={cardVariants} className="lg:col-span-2">
            <div className="rounded-2xl border border-border bg-card p-6 h-full">
              {/* <ATSSection
                keywords={ats_keywords}
                coveragePercentage={ats_coverage_percentage}
              /> */}
              <div>ATS Section Placeholder</div>
            </div>
          </motion.div>
        </div>

        {/* ── Strengths + Weaknesses row ────────────────────── */}
        <motion.div variants={cardVariants} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <StrengthsPanel strengths={strengths} />
          <WeaknessesPanel weaknesses={weaknesses} />
        </motion.div>

        {/* ── Recommendations ───────────────────────────────── */}
        <motion.div variants={cardVariants}>
          <div className="rounded-2xl border border-border bg-card p-6">
            {/* <RecommendationsSection recommendations={recommendations} /> */}
            <div>Recommendations Placeholder</div>
          </div>
        </motion.div>

        {/* ── Sub-scores detail ─────────────────────────────── */}
        <motion.div variants={cardVariants}>
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="font-display font-semibold text-foreground mb-5">Score breakdown</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <ScoreBar label="Skill match" score={skill_match_score} />
              <ScoreBar label="Experience alignment" score={experience_score} />
              <ScoreBar label="Education fit" score={education_score} />
              <ScoreBar label="ATS compatibility" score={ats_score} />
            </div>
          </div>
        </motion.div>

        {/* ── Footer CTA ────────────────────────────────────── */}
        <motion.div variants={cardVariants} className="text-center py-6 space-y-3">
          <p className="text-sm text-muted-foreground">
            Not happy with your score? Follow the recommendations above and re-analyze.
          </p>
          <Link href="/analyze">
            <Button variant="brand" leftIcon={<RefreshCw className="h-4 w-4" />}>
              Analyze another job
            </Button>
          </Link>
        </motion.div>
      </motion.div>
    </ResultsLayout>
  )
}

// ─────────────────────────────────────────────────────────────
// Sub-score card
// ─────────────────────────────────────────────────────────────

function SubScoreCard({ label, score }: { label: string; score: number }) {
  const category = getScoreCategory(score)
  return (
    <div className="rounded-xl border border-border bg-card p-4 text-center hover:border-brand-200/30 transition-colors">
      <ScoreRing score={score} size="sm" showLabel={false} animated />
      <p className="text-xs font-medium text-muted-foreground mt-2">{label}</p>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Resume insight bar
// ─────────────────────────────────────────────────────────────

function ResumeInsightBar({ insights }: { insights: NonNullable<any> }) {
  const items = [
    insights.word_count && { label: 'Words', value: insights.word_count },
    insights.quantified_achievements && { label: 'Achievements', value: insights.quantified_achievements },
    insights.action_verbs_count && { label: 'Action verbs', value: insights.action_verbs_count },
    insights.sections_found?.length && { label: 'Sections', value: insights.sections_found.length },
  ].filter(Boolean) as { label: string; value: number }[]

  if (items.length === 0) return null

  return (
    <div className="rounded-xl border border-border bg-card/60 px-5 py-3 flex items-center gap-6 overflow-x-auto scrollbar-thin">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide shrink-0">
        Resume stats
      </p>
      {items.map((item) => (
        <div key={item.label} className="text-center shrink-0">
          <p className="font-display font-bold text-lg text-foreground tabular-nums">{item.value}</p>
          <p className="text-xs text-muted-foreground">{item.label}</p>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Results layout wrapper
// ─────────────────────────────────────────────────────────────

function ResultsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-xl sticky top-0 z-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/analyze"
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            <div className="h-4 w-px bg-border" />
            <Link href="/" className="flex items-center gap-2 group">
              <div className="h-6 w-6 rounded-md bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center">
                <Zap className="h-3 w-3 text-white" strokeWidth={2.5} />
              </div>
              <span className="font-display font-bold text-sm text-foreground">
                MatchHire<span className="gradient-text">AI</span>
              </span>
            </Link>
          </div>
          <Badge variant="brand" className="text-xs">
            Analysis complete
          </Badge>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
        {children}
      </main>
    </div>
  )
}
