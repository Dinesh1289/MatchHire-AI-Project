// src/components/ui/ScoreRing.tsx
'use client'

import { useEffect, useRef, useState } from 'react'
import { cn, getScoreColor, getScoreLabel, getScoreCategory } from '@/lib/utils'

interface ScoreRingProps {
  score: number
  size?: 'sm' | 'md' | 'lg' | 'xl'
  label?: string
  sublabel?: string
  showLabel?: boolean
  animated?: boolean
  className?: string
}

const sizeMap = {
  sm:  { dim: 80,  stroke: 6,  r: 32, textSize: 'text-xl',   subSize: 'text-xs' },
  md:  { dim: 120, stroke: 8,  r: 48, textSize: 'text-3xl',  subSize: 'text-xs' },
  lg:  { dim: 160, stroke: 10, r: 64, textSize: 'text-4xl',  subSize: 'text-sm' },
  xl:  { dim: 200, stroke: 12, r: 80, textSize: 'text-5xl',  subSize: 'text-sm' },
}

export function ScoreRing({
  score,
  size = 'lg',
  label,
  sublabel,
  showLabel = true,
  animated = true,
  className,
}: ScoreRingProps) {
  const { dim, stroke, r, textSize, subSize } = sizeMap[size]
  const circumference = 2 * Math.PI * r
  const targetOffset = circumference - (score / 100) * circumference
  const color = getScoreColor(score)
  const category = getScoreCategory(score)

  const [displayScore, setDisplayScore] = useState(animated ? 0 : score)
  const [offset, setOffset] = useState(animated ? circumference : targetOffset)
  const animRef = useRef<number>()
  const startRef = useRef<number>()

  useEffect(() => {
    if (!animated) return

    const duration = 1200
    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3)

    const animate = (timestamp: number) => {
      if (!startRef.current) startRef.current = timestamp
      const elapsed = timestamp - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = easeOutCubic(progress)

      setDisplayScore(Math.round(eased * score))
      setOffset(circumference - eased * (score / 100) * circumference)

      if (progress < 1) {
        animRef.current = requestAnimationFrame(animate)
      }
    }

    // Small delay before starting animation
    const timeout = setTimeout(() => {
      animRef.current = requestAnimationFrame(animate)
    }, 200)

    return () => {
      clearTimeout(timeout)
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [score])

  const cx = dim / 2
  const cy = dim / 2

  return (
    <div className={cn('relative inline-flex flex-col items-center gap-2', className)}>
      <div className="relative" style={{ width: dim, height: dim }}>
        <svg
          width={dim}
          height={dim}
          viewBox={`0 0 ${dim} ${dim}`}
          className="-rotate-90"
          aria-label={`Match score: ${score}%`}
        >
          {/* Track ring */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="hsl(var(--border))"
            strokeWidth={stroke}
            strokeLinecap="round"
          />
          {/* Score ring */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              filter: `drop-shadow(0 0 ${stroke}px ${color}40)`,
              transition: animated ? 'none' : 'stroke-dashoffset 0.6s ease',
            }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={cn('font-display font-bold tabular-nums leading-none', textSize)}
            style={{ color }}
          >
            {displayScore}
          </span>
          {showLabel && (
            <span className={cn('text-muted-foreground font-sans mt-0.5', subSize)}>
              out of 100
            </span>
          )}
        </div>
      </div>

      {/* Label below ring */}
      {label && (
        <div className="text-center">
          <p className="text-sm font-medium text-foreground">{label}</p>
          {sublabel && (
            <p className="text-xs text-muted-foreground mt-0.5">{sublabel}</p>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Compact linear score bar for sub-scores
// ─────────────────────────────────────────────────────────────

interface ScoreBarProps {
  label: string
  score: number
  className?: string
}

export function ScoreBar({ label, score, className }: ScoreBarProps) {
  const [width, setWidth] = useState(0)
  const color = getScoreColor(score)

  useEffect(() => {
    const t = setTimeout(() => setWidth(score), 300)
    return () => clearTimeout(t)
  }, [score])

  return (
    <div className={cn('space-y-1.5', className)}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-foreground/80 font-medium">{label}</span>
        <span className="font-mono font-medium tabular-nums" style={{ color }}>
          {score}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-border overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${width}%`,
            backgroundColor: color,
            boxShadow: `0 0 6px ${color}60`,
          }}
        />
      </div>
    </div>
  )
}
