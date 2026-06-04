// src/components/features/upload/ResumeDropzone.tsx
'use client'

import { useCallback, useState } from 'react'
import { useDropzone, type FileRejection } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, CheckCircle2, X, AlertCircle, File } from 'lucide-react'
import { cn, formatFileSize } from '@/lib/utils'
import { UPLOAD_CONFIG } from '@/config/env'
import { Button } from '@/components/ui/Button'

interface ResumeDropzoneProps {
  onFileAccepted: (file: File) => void
  onFileRemoved?: () => void
  currentFile?: File | null
  disabled?: boolean
  className?: string
}

export function ResumeDropzone({
  onFileAccepted,
  onFileRemoved,
  currentFile,
  disabled,
  className,
}: ResumeDropzoneProps) {
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      setError(null)

      if (rejectedFiles.length > 0) {
        const firstError = rejectedFiles[0]?.errors[0]
        if (firstError?.code === 'file-too-large') {
          setError(`File is too large. Max size is ${UPLOAD_CONFIG.MAX_FILE_SIZE_MB}MB.`)
        } else if (firstError?.code === 'file-invalid-type') {
          setError('Invalid file type. Please upload a PDF, DOC, or DOCX.')
        } else {
          setError('Could not process this file. Please try another.')
        }
        return
      }

      if (acceptedFiles.length > 0) {
        onFileAccepted(acceptedFiles[0])
      }
    },
    [onFileAccepted]
  )

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: UPLOAD_CONFIG.ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: UPLOAD_CONFIG.MAX_FILE_SIZE_BYTES,
    disabled: disabled || !!currentFile,
    multiple: false,
  })

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation()
    setError(null)
    onFileRemoved?.()
  }

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    return <FileText className={cn(
      'h-10 w-10',
      ext === 'pdf' ? 'text-destructive' : 'text-brand-500'
    )} />
  }

  return (
    <div className={cn('space-y-2', className)}>
      <label className="text-sm font-medium text-foreground">Resume</label>

      <AnimatePresence mode="wait">
        {currentFile ? (
          // File uploaded state
          <motion.div
            key="file-uploaded"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.2 }}
            className="rounded-xl border border-score-excellent/30 bg-score-excellent/5 p-4"
          >
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-lg bg-score-excellent/10 flex items-center justify-center shrink-0">
                {getFileIcon(currentFile.name)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  {currentFile.name}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-score-excellent shrink-0" />
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(currentFile.size)} · Ready to analyze
                  </p>
                </div>
              </div>
              {!disabled && (
                <button
                  onClick={handleRemove}
                  className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Remove file"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </motion.div>
        ) : (
          // Dropzone state
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.2 }}
          >
            <div
              {...getRootProps()}
              className={cn(
                'relative rounded-xl border-2 border-dashed p-8 transition-all duration-200 cursor-pointer outline-none',
                'flex flex-col items-center justify-center text-center gap-3',
                isDragActive && !isDragReject && 'border-brand-400 bg-brand-50/50 dark:bg-brand-50/5 scale-[1.01]',
                isDragReject && 'border-destructive bg-destructive/5',
                !isDragActive && 'border-border hover:border-brand-300 dark:hover:border-brand-300/40 hover:bg-accent/30',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              <input {...getInputProps()} />

              {/* Upload icon */}
              <div className={cn(
                'h-14 w-14 rounded-2xl flex items-center justify-center transition-colors duration-200',
                isDragActive && !isDragReject ? 'bg-brand-100 dark:bg-brand-50/10' : 'bg-secondary',
                isDragReject && 'bg-destructive/10'
              )}>
                {isDragReject ? (
                  <AlertCircle className="h-7 w-7 text-destructive" />
                ) : (
                  <Upload className={cn(
                    'h-7 w-7 transition-colors',
                    isDragActive ? 'text-brand-500' : 'text-muted-foreground'
                  )} />
                )}
              </div>

              {/* Text */}
              <div>
                <p className={cn(
                  'text-sm font-medium transition-colors',
                  isDragActive && !isDragReject ? 'text-brand-600 dark:text-brand-400' : 'text-foreground',
                  isDragReject && 'text-destructive'
                )}>
                  {isDragReject
                    ? 'This file type is not supported'
                    : isDragActive
                    ? 'Release to upload'
                    : 'Drop your resume here'}
                </p>
                {!isDragActive && (
                  <p className="text-xs text-muted-foreground mt-1">
                    or{' '}
                    <span className="text-brand-500 hover:text-brand-600 underline underline-offset-2 cursor-pointer">
                      click to browse
                    </span>
                    {' '}— PDF, DOC, DOCX up to {UPLOAD_CONFIG.MAX_FILE_SIZE_MB}MB
                  </p>
                )}
              </div>

              {/* Accepted formats */}
              {!isDragActive && (
                <div className="flex items-center gap-1.5 mt-1">
                  {UPLOAD_CONFIG.ACCEPTED_EXTENSIONS.map((ext) => (
                    <span
                      key={ext}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-muted text-xs text-muted-foreground font-mono"
                    >
                      <File className="h-2.5 w-2.5" />
                      {ext}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error state */}
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
    </div>
  )
}
