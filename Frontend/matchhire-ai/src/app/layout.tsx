// src/app/layout.tsx
import type { Metadata, Viewport } from 'next'
import { ThemeProvider } from '@/components/ui/ThemeProvider'
import { QueryProvider } from '@/components/ui/QueryProvider'
import '@/styles/globals.css'

export const metadata: Metadata = {
  title: {
    default: 'MatchHire AI — Your AI Recruiting Copilot',
    template: '%s | MatchHire AI',
  },
  description:
    'Instantly analyze how well your resume matches any job description. Get AI-powered insights, skill gap analysis, ATS scores, and personalized recommendations.',
  keywords: ['resume', 'job match', 'ATS', 'AI hiring', 'career', 'skill gap', 'recruitment'],
  authors: [{ name: 'MatchHire AI' }],
  creator: 'MatchHire AI',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://matchhire.ai',
    siteName: 'MatchHire AI',
    title: 'MatchHire AI — Your AI Recruiting Copilot',
    description:
      'Instantly analyze how well your resume matches any job description.',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MatchHire AI',
    description: 'AI-powered resume-to-job matching.',
    images: ['/og-image.png'],
  },
  robots: { index: true, follow: true },
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0d1117' },
  ],
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className="min-h-screen bg-background antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            {children}
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
