// src/components/features/jd-input/JobDescriptionInput.tsx
'use client'

import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clipboard, X, CheckCircle2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { UI_CONFIG } from '@/config/env'
import { Button } from '@/components/ui/Button'

interface JobDescriptionInputProps {
  value: string
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
  className?: string
}

export function JobDescriptionInput({
  value,
  onChange,
  error,
  disabled,
  className,
}: JobDescriptionInputProps) {
  const [isFocused, setIsFocused] = useState(false)
  const [pasteSuccess, setPasteSuccess] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const charCount = value.length
  const isOverLimit = charCount > UI_CONFIG.MAX_JD_LENGTH
  const isValidLength = charCount >= UI_CONFIG.MIN_JD_LENGTH

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText()
      onChange(text)
      setPasteSuccess(true)
      setTimeout(() => setPasteSuccess(false), 2000)
      textareaRef.current?.focus()
    } catch {
      // Clipboard access denied — user can paste manually
    }
  }

  const handleClear = () => {
    onChange('')
    textareaRef.current?.focus()
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">Job description</label>
        <div className="flex items-center gap-2">
          {value && (
            <button
              type="button"
              onClick={handleClear}
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          )}
          <button
            type="button"
            onClick={handlePaste}
            disabled={disabled}
            className={cn(
              'flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md transition-all duration-200',
              pasteSuccess
                ? 'bg-score-excellent/10 text-score-excellent'
                : 'bg-secondary text-muted-foreground hover:bg-accent hover:text-foreground'
            )}
          >
            {pasteSuccess ? (
              <>
                <CheckCircle2 className="h-3 w-3" />
                Pasted!
              </>
            ) : (
              <>
                <Clipboard className="h-3 w-3" />
                Paste from clipboard
              </>
            )}
          </button>
        </div>
      </div>

      {/* Textarea container */}
      <div className={cn(
        'relative rounded-xl border transition-all duration-200 overflow-hidden',
        isFocused && !error ? 'border-brand-400/60 ring-2 ring-brand-400/20' : '',
        error ? 'border-destructive/60 ring-2 ring-destructive/20' : '',
        !isFocused && !error ? 'border-border hover:border-border/80' : '',
      )}>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          disabled={disabled}
          placeholder="Paste the full job description here — include required skills, responsibilities, qualifications, and any other details for the most accurate analysis..."
          className={cn(
            'w-full bg-card text-foreground text-sm placeholder:text-muted-foreground/50',
            'px-4 py-3.5 resize-none outline-none',
            'scrollbar-thin',
            isExpanded ? 'min-h-[400px]' : 'min-h-[200px]',
            'transition-[min-height] duration-300',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Job description"
          aria-invalid={!!error}
        />

        {/* Expand toggle at bottom */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-border bg-muted/30">
          <div className="flex items-center gap-2">
            {isValidLength ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-score-excellent" />
            ) : (
              <AlertCircle className="h-3.5 w-3.5 text-muted-foreground" />
            )}
            <span className={cn(
              'text-xs',
              isOverLimit ? 'text-destructive' : 'text-muted-foreground'
            )}>
              {charCount.toLocaleString()} / {UI_CONFIG.MAX_JD_LENGTH.toLocaleString()} chars
              {!isValidLength && ` (min ${UI_CONFIG.MIN_JD_LENGTH})`}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {isExpanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>

      {/* Error message */}
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-xs text-destructive flex items-center gap-1.5"
          >
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Helper text */}
      {!error && (
        <p className="text-xs text-muted-foreground">
          For best results, paste the complete job posting including requirements and responsibilities.
        </p>
      )}
    </div>
  )
}
