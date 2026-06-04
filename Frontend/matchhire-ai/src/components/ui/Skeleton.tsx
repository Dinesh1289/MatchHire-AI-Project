// src/components/ui/Skeleton.tsx
import { cn } from '@/lib/utils'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'circular' | 'text'
}

export function Skeleton({ className, variant = 'default', ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'skeleton-shimmer',
        variant === 'circular' && 'rounded-full',
        variant === 'default' && 'rounded-lg',
        variant === 'text' && 'rounded-md h-4',
        className
      )}
      {...props}
    />
  )
}

// ─────────────────────────────────────────────────────────────
// Composed skeleton patterns
// ─────────────────────────────────────────────────────────────

export function ScoreCardSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <div className="flex items-center justify-center py-4">
        <Skeleton variant="circular" className="h-40 w-40" />
      </div>
      <div className="space-y-2">
        <Skeleton variant="text" className="w-full" />
        <Skeleton variant="text" className="w-3/4" />
      </div>
    </div>
  )
}

export function SkillGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="flex flex-wrap gap-2">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-7 rounded-full"
          style={{ width: `${Math.floor(Math.random() * 60) + 60}px` }}
        />
      ))}
    </div>
  )
}

export function RecommendationSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border p-4 space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton variant="circular" className="h-8 w-8" />
            <Skeleton className="h-4 w-48" />
          </div>
          <Skeleton variant="text" className="w-full" />
          <Skeleton variant="text" className="w-4/5" />
        </div>
      ))}
    </div>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <ScoreCardSkeleton key={i} />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
          <Skeleton className="h-5 w-40" />
          <SkillGridSkeleton count={12} />
        </div>
        <RecommendationSkeleton count={3} />
      </div>
    </div>
  )
}
