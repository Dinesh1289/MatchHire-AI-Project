// src/lib/utils/index.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { ScoreCategory } from '@/types'

// ─────────────────────────────────────────────────────────────
// Tailwind class merge utility
// ─────────────────────────────────────────────────────────────

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ─────────────────────────────────────────────────────────────
// Score helpers
// ─────────────────────────────────────────────────────────────

export function getScoreCategory(score: number): ScoreCategory {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'fair'
  return 'poor'
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return 'Excellent Match'
  if (score >= 60) return 'Good Match'
  if (score >= 40) return 'Fair Match'
  return 'Low Match'
}

export function getScoreColor(score: number): string {
  if (score >= 80) return 'hsl(var(--score-excellent))'
  if (score >= 60) return 'hsl(var(--score-good))'
  if (score >= 40) return 'hsl(var(--score-fair))'
  return 'hsl(var(--score-poor))'
}

export function getScoreTailwindColor(score: number): string {
  if (score >= 80) return 'text-score-excellent'
  if (score >= 60) return 'text-score-good'
  if (score >= 40) return 'text-score-fair'
  return 'text-score-poor'
}

export function getScoreBgClass(score: number): string {
  if (score >= 80) return 'score-bg-excellent'
  if (score >= 60) return 'score-bg-good'
  if (score >= 40) return 'score-bg-fair'
  return 'score-bg-poor'
}

// SVG circle helpers for score ring
export function getCircumference(radius: number): number {
  return 2 * Math.PI * radius
}

export function getStrokeDashoffset(score: number, circumference: number): number {
  return circumference - (score / 100) * circumference
}

// ─────────────────────────────────────────────────────────────
// File utilities
// ─────────────────────────────────────────────────────────────

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() ?? ''
}

// ─────────────────────────────────────────────────────────────
// Text utilities
// ─────────────────────────────────────────────────────────────

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen - 3) + '...'
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export function pluralize(count: number, singular: string, plural?: string): string {
  return count === 1 ? singular : (plural ?? singular + 's')
}

// ─────────────────────────────────────────────────────────────
// Number formatting
// ─────────────────────────────────────────────────────────────

export function formatPercent(value: number, decimals = 0): string {
  return `${value.toFixed(decimals)}%`
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

// ─────────────────────────────────────────────────────────────
// Date formatting
// ─────────────────────────────────────────────────────────────

export function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(dateString))
}

// ─────────────────────────────────────────────────────────────
// Priority color helpers
// ─────────────────────────────────────────────────────────────

export function getPriorityColor(priority: 'high' | 'medium' | 'low') {
  switch (priority) {
    case 'high':
      return { bg: 'bg-destructive/10', text: 'text-destructive', border: 'border-destructive/20' }
    case 'medium':
      return { bg: 'bg-score-fair/10', text: 'text-score-fair', border: 'border-score-fair/20' }
    case 'low':
      return { bg: 'bg-muted', text: 'text-muted-foreground', border: 'border-border' }
  }
}
