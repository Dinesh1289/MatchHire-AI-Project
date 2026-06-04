// src/components/ui/States.tsx
'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { FileSearch, AlertCircle, RefreshCw, Sparkles, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────
// Empty state
// ─────────────────────────────────────────────────────────────

interface EmptyStateProps {
  title?: string
  description?: string
  action?: { label: string; href?: string; onClick?: () => void }
  className?: string
}

export function EmptyState({
  title = 'No analysis yet',
  description = 'Upload your resume and paste a job description to get started.',
  action,
  className,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn(
        'flex flex-col items-center justify-center text-center py-20 px-6',
        className
      )}
    >
      <div className="h-16 w-16 rounded-2xl bg-muted flex items-center justify-center mb-5">
        <FileSearch className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="font-display font-semibold text-lg text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-xs leading-relaxed mb-6">{description}</p>
      {action && (
        action.href ? (
          <Link href={action.href}>
            <Button variant="brand" leftIcon={<Sparkles className="h-3.5 w-3.5" />} rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
              {action.label}
            </Button>
          </Link>
        ) : (
          <Button variant="brand" onClick={action.onClick} leftIcon={<Sparkles className="h-3.5 w-3.5" />}>
            {action.label}
          </Button>
        )
      )}
    </motion.div>
  )
}

// ─────────────────────────────────────────────────────────────
// Error state
// ─────────────────────────────────────────────────────────────

interface ErrorStateProps {
  title?: string
  description?: string
  error?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  description = 'We could not complete the analysis. Please try again.',
  error,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn(
        'flex flex-col items-center justify-center text-center py-20 px-6',
        className
      )}
    >
      <div className="h-16 w-16 rounded-2xl bg-destructive/10 flex items-center justify-center mb-5">
        <AlertCircle className="h-8 w-8 text-destructive" />
      </div>
      <h3 className="font-display font-semibold text-lg text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-xs leading-relaxed mb-3">{description}</p>

      {error && (
        <div className="mb-5 px-4 py-2.5 rounded-lg bg-destructive/8 border border-destructive/20 max-w-sm w-full">
          <p className="text-xs font-mono text-destructive break-all">{error}</p>
        </div>
      )}

      <div className="flex items-center gap-3">
        {onRetry && (
          <Button
            variant="outline"
            onClick={onRetry}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Try again
          </Button>
        )}
        <Link href="/analyze">
          <Button variant="brand" leftIcon={<Sparkles className="h-3.5 w-3.5" />}>
            Start over
          </Button>
        </Link>
      </div>
    </motion.div>
  )
}

// ─────────────────────────────────────────────────────────────
// Inline error banner (for form-level errors)
// ─────────────────────────────────────────────────────────────

interface ErrorBannerProps {
  message: string
  onDismiss?: () => void
  className?: string
}

export function ErrorBanner({ message, onDismiss, className }: ErrorBannerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.98 }}
      className={cn(
        'flex items-start gap-3 rounded-xl border border-destructive/25 bg-destructive/8 px-4 py-3',
        className
      )}
    >
      <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
      <p className="text-sm text-destructive flex-1">{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-destructive/60 hover:text-destructive transition-colors text-xs"
        >
          ✕
        </button>
      )}
    </motion.div>
  )
}
