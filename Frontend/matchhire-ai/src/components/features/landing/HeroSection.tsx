// src/components/features/landing/HeroSection.tsx
'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, Target, TrendingUp, Shield } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.10, delayChildren: 0.1 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.25, 0.4, 0.25, 1] } },
}

const statItems = [
  { value: '94%', label: 'ATS pass rate improvement' },
  { value: '3.2x', label: 'More interview callbacks' },
  { value: '<60s', label: 'Full analysis time' },
]

const socialProof = [
  'Senior Engineers', 'Product Managers', 'Data Scientists', 'Designers'
]

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden pt-16">
      {/* Background elements */}
      <div className="absolute inset-0 dot-grid opacity-40 dark:opacity-20" />

      {/* Gradient orbs */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 rounded-full bg-brand-500/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 rounded-full bg-brand-400/8 blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] rounded-full bg-brand-600/5 blur-3xl pointer-events-none" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-24 w-full">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="max-w-4xl mx-auto text-center"
        >
          {/* Announcement badge */}
          <motion.div variants={itemVariants} className="flex justify-center mb-8">
            <Badge variant="brand" className="px-4 py-1.5 text-sm gap-2">
              <Sparkles className="h-3.5 w-3.5" />
              AI-powered resume intelligence — now live
            </Badge>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={itemVariants}
            className="font-display text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight text-foreground leading-[1.05] mb-6"
          >
            Know exactly why
            <br />
            <span className="gradient-text">you&apos;re getting rejected</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            variants={itemVariants}
            className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed mb-10"
          >
            Upload your resume and paste any job description. Our AI analyzes your match
            score, skill gaps, ATS compatibility, and gives you a precise action plan to
            land the interview.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-16"
          >
            <Link href="/analyze">
              <Button
                variant="brand"
                size="xl"
                rightIcon={<ArrowRight className="h-4 w-4" />}
                className="min-w-52"
              >
                Analyze my resume
              </Button>
            </Link>
            <Link href="/#how-it-works">
              <Button variant="outline" size="xl" className="min-w-44">
                See how it works
              </Button>
            </Link>
          </motion.div>

          {/* Social proof */}
          <motion.p variants={itemVariants} className="text-xs text-muted-foreground mb-12">
            Used by {socialProof.join(' · ')} · No account required
          </motion.p>

          {/* Stats row */}
          <motion.div
            variants={itemVariants}
            className="grid grid-cols-3 gap-6 max-w-xl mx-auto"
          >
            {statItems.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="font-display text-3xl font-bold text-foreground mb-1">
                  {stat.value}
                </p>
                <p className="text-xs text-muted-foreground leading-tight">{stat.label}</p>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Feature cards row */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7, ease: [0.25, 0.4, 0.25, 1] }}
          className="mt-24 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto"
        >
          {[
            {
              icon: <Target className="h-5 w-5 text-brand-500" />,
              title: 'Precision match score',
              desc: 'AI-weighted compatibility percentage across skills, experience, and culture fit.',
            },
            {
              icon: <TrendingUp className="h-5 w-5 text-score-excellent" />,
              title: 'Skill gap analysis',
              desc: 'See exactly which skills you have, which you\'re missing, and how to close the gap fast.',
            },
            {
              icon: <Shield className="h-5 w-5 text-score-good" />,
              title: 'ATS optimization',
              desc: 'Know which keywords are missing before your resume hits the robot screener.',
            },
          ].map((feat, i) => (
            <div
              key={i}
              className="rounded-2xl border border-border bg-card/60 backdrop-blur-sm p-5 hover:border-brand-200/50 dark:hover:border-brand-200/20 hover:bg-card transition-all duration-200 group"
            >
              <div className="mb-3 h-9 w-9 rounded-lg bg-secondary flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                {feat.icon}
              </div>
              <h3 className="font-display font-semibold text-sm text-foreground mb-1">
                {feat.title}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{feat.desc}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
