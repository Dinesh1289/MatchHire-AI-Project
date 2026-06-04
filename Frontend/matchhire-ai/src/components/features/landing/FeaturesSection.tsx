// src/components/features/landing/FeaturesSection.tsx
'use client'

import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'
import {
  Target, Brain, Shield, Zap, BarChart3, Lightbulb,
  CheckCircle2, FileSearch, TrendingUp
} from 'lucide-react'

const features = [
  {
    icon: Target,
    color: 'text-brand-500',
    bg: 'bg-brand-500/10',
    title: 'AI match scoring',
    description: 'Get a weighted compatibility percentage that considers skills, experience level, education, and role-specific requirements.',
  },
  {
    icon: Brain,
    color: 'text-score-excellent',
    bg: 'bg-score-excellent/10',
    title: 'Skill gap detection',
    description: 'Instantly see which skills you have vs. what the employer requires — with actionable suggestions to close each gap.',
  },
  {
    icon: Shield,
    color: 'text-score-good',
    bg: 'bg-score-good/10',
    title: 'ATS optimization',
    description: 'Identify missing ATS keywords before submission. Know which resume bots would reject your application and why.',
  },
  {
    icon: Lightbulb,
    color: 'text-score-fair',
    bg: 'bg-score-fair/10',
    title: 'Smart recommendations',
    description: 'Prioritized action items with specific impact estimates. Know exactly what to fix first for maximum improvement.',
  },
  {
    icon: BarChart3,
    color: 'text-brand-400',
    bg: 'bg-brand-400/10',
    title: 'Multi-dimensional scoring',
    description: 'Separate scores for skills, experience, education, and ATS compatibility — understand where you stand in each dimension.',
  },
  {
    icon: TrendingUp,
    color: 'text-score-excellent',
    bg: 'bg-score-excellent/10',
    title: 'Strengths & weaknesses',
    description: 'Clear breakdown of what makes you a strong candidate and what might give hiring managers pause.',
  },
]

export function FeaturesSection() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section id="features" className="py-24 relative" ref={ref}>
      <div className="absolute inset-0 dot-grid opacity-30 dark:opacity-20" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <p className="text-sm font-semibold text-brand-500 uppercase tracking-widest mb-3">Features</p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-foreground tracking-tight mb-4">
            Everything you need to
            <br />
            <span className="gradient-text">land the interview</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            MatchHire AI goes beyond a simple score. You get a full intelligence report
            that tells you exactly how to improve your application.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feat, i) => {
            const Icon = feat.icon
            return (
              <motion.div
                key={feat.title}
                initial={{ opacity: 0, y: 20 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="group rounded-2xl border border-border bg-card p-6 hover:border-brand-200/40 dark:hover:border-brand-200/20 hover:shadow-md transition-all duration-200"
              >
                <div className={`h-11 w-11 rounded-xl ${feat.bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200`}>
                  <Icon className={`h-5 w-5 ${feat.color}`} />
                </div>
                <h3 className="font-display font-semibold text-foreground mb-2">{feat.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feat.description}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

// ─────────────────────────────────────────────────────────────
// How it works section
// ─────────────────────────────────────────────────────────────

export function HowItWorksSection() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  const steps = [
    {
      number: '01',
      icon: FileSearch,
      title: 'Upload your resume',
      description: 'Drop in your PDF, DOC, or DOCX. Our parser extracts skills, experience, and education automatically.',
    },
    {
      number: '02',
      icon: Brain,
      title: 'Paste the job description',
      description: 'Copy the full job posting — the more detail, the more accurate your analysis will be.',
    },
    {
      number: '03',
      icon: Zap,
      title: 'Get your AI report',
      description: 'In under 60 seconds, receive a full compatibility analysis with actionable improvement steps.',
    },
  ]

  return (
    <section id="how-it-works" className="py-24 border-y border-border bg-muted/20" ref={ref}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <p className="text-sm font-semibold text-brand-500 uppercase tracking-widest mb-3">How it works</p>
          <h2 className="font-display text-4xl font-bold text-foreground tracking-tight mb-4">
            Three steps to clarity
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Connector line */}
          <div className="hidden md:block absolute top-10 left-1/3 right-1/3 h-px bg-gradient-to-r from-border via-brand-400/40 to-border" />

          {steps.map((step, i) => {
            const Icon = step.icon
            return (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 20 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.4, delay: i * 0.12 }}
                className="text-center relative"
              >
                <div className="relative inline-flex mb-5">
                  <div className="h-20 w-20 rounded-2xl bg-card border border-border shadow-sm flex items-center justify-center">
                    <Icon className="h-8 w-8 text-brand-500" />
                  </div>
                  <span className="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center font-display">
                    {i + 1}
                  </span>
                </div>
                <h3 className="font-display font-semibold text-lg text-foreground mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed max-w-xs mx-auto">{step.description}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

// ─────────────────────────────────────────────────────────────
// Footer
// ─────────────────────────────────────────────────────────────

export function Footer() {
  return (
    <footer className="border-t border-border py-10">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center">
              <Zap className="h-3.5 w-3.5 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display font-bold text-sm text-foreground">
              MatchHire<span className="gradient-text">AI</span>
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            © 2024 MatchHire AI. Built for job seekers who refuse to settle.
          </p>
          <div className="flex items-center gap-4">
            {['Privacy', 'Terms', 'Contact'].map((link) => (
              <a key={link} href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                {link}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}
