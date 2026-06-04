# MatchHire AI — Frontend

**Your AI recruiting copilot for job seekers.** Upload a resume, paste a job description, and get a full AI-powered compatibility report in under 60 seconds.

---

## Quick start

```bash
# 1. Install dependencies
npm install

# 2. Start your FastAPI backend (separate terminal)
#    Should be running at http://127.0.0.1:8000

# 3. Start the frontend dev server
npm run dev
# → http://localhost:3000
```

That's it. No database, no auth setup, no environment config needed for local dev — `.env.local` is pre-configured to point at your backend.

---

## Project structure

```
src/
├── app/                        # Next.js 14 App Router pages
│   ├── layout.tsx              # Root layout (fonts, providers, metadata)
│   ├── page.tsx                # Landing page (/)
│   ├── analyze/
│   │   └── page.tsx            # Main input workflow (/analyze)
│   └── results/[id]/
│       └── page.tsx            # Results dashboard (/results/:id)
│
├── components/
│   ├── ui/                     # Headless design system primitives
│   │   ├── Button.tsx          # CVA button with variants (brand, outline, ghost…)
│   │   ├── Badge.tsx           # CVA badge with semantic variants
│   │   ├── ScoreRing.tsx       # Animated SVG score ring + ScoreBar
│   │   ├── Skeleton.tsx        # Shimmer skeleton + dashboard-level composites
│   │   ├── States.tsx          # EmptyState, ErrorState, ErrorBanner
│   │   ├── ThemeProvider.tsx   # next-themes SSR-safe wrapper
│   │   └── QueryProvider.tsx   # TanStack Query client provider
│   │
│   └── features/               # Domain-specific feature components
│       ├── landing/
│       │   ├── Navbar.tsx          # Sticky nav, scroll blur, mobile menu, theme toggle
│       │   ├── HeroSection.tsx     # Hero with animated entrance, stats, feature cards
│       │   └── FeaturesSection.tsx # Features grid, How it works, Footer (all exported)
│       ├── upload/
│       │   └── ResumeDropzone.tsx  # Drag-and-drop + click upload with file preview
│       ├── jd-input/
│       │   └── JobDescriptionInput.tsx # Textarea with paste button, char counter
│       ├── analysis/
│       │   └── LoadingScreen.tsx   # Full-screen AI loading with step progress
│       └── results/
│           ├── SkillAnalysis.tsx   # Skill badges, gap section, breakdown table
│           ├── ATSSection.tsx      # ATS keyword grid, coverage ring, alerts
│           └── InsightPanels.tsx   # Strengths, Weaknesses, Recommendations
│
├── lib/
│   ├── api/
│   │   ├── client.ts           # Axios instance with interceptors (auth-ready)
│   │   └── services.ts         # Typed API service methods (resumeApi, matchApi…)
│   ├── utils/
│   │   └── index.ts            # cn(), score helpers, formatters, color utilities
│   └── validators/
│       └── schemas.ts          # Zod schemas for all forms
│
├── store/
│   └── analyzeStore.ts         # Zustand store for analysis state
│
├── hooks/
│   └── useMatchAnalysis.ts     # Main orchestration hook — runs the full API flow
│
├── types/
│   └── index.ts                # Complete TypeScript type system for all API shapes
│
├── config/
│   └── env.ts                  # Environment variables + API endpoint registry
│
└── styles/
    └── globals.css             # CSS variables (light/dark), design tokens, utilities
```

---

## Architecture decisions

### Why these choices were made

**Next.js 14 App Router**
Uses React Server Components for the landing page (static, zero JS) and Client Components only where interactivity is needed. This gives fast initial paint on the marketing page while keeping the analyze/results pages fully interactive.

**Zustand over Redux / Context**
No providers, no boilerplate, no selectors. The `analyzeStore` holds the entire analysis lifecycle state and can be read from any component without wrapping. When auth is added, a second `authStore` can be created in the same pattern.

**Single orchestration hook (`useMatchAnalysis`)**
All three API calls live in `useMatchAnalysis.ts`. Components never call APIs directly. The hook manages step sequencing, progress simulation, error recovery, and navigation. This makes the flow easy to test, modify, or extend (e.g. retry logic, caching).

**Type-safe API layer**
`src/lib/api/services.ts` exports three typed service objects (`resumeApi`, `jobDescriptionApi`, `matchApi`). Every request and response is typed against `src/types/index.ts`. If the backend changes a field, TypeScript catches it immediately.

**Zod + React Hook Form**
Schema-first validation. The Zod schemas in `validators/schemas.ts` are the single source of truth for form rules. RHF handles field state and submission. No manual `if (value.length < 100)` checks anywhere.

**Framer Motion philosophy**
Animations follow a strict hierarchy:
1. **Page entrance** — fade + translate-y, staggered children
2. **Data reveals** — score ring count-up, bar animations on mount
3. **Micro-interactions** — hover scale, button press scale
4. **Loading** — step indicators, typewriter effect, progress bar

No animation exceeds 400ms. All entrance animations use `useInView` so they only fire when visible.

**Dark mode**
`next-themes` handles SSR-safe theme switching. CSS variables in `globals.css` define all colors. The `.dark` class swaps the entire color system — no `dark:` prefix explosion in component code.

**Score color system**
Score thresholds map to semantic CSS variables (`--score-excellent`, `--score-good`, `--score-fair`, `--score-poor`). Helper functions in `utils/index.ts` convert a raw number to the right color, Tailwind class, or background class. Components never hardcode hex values.

---

## Pages

### `/` — Landing page
Static marketing page. Server-rendered. No client JS except Navbar (theme toggle, scroll listener) and animated sections. Built for conversion — hero, feature grid, how-it-works, CTA.

### `/analyze` — Analysis workflow
Client page. Two-column layout: resume dropzone on the left, JD textarea on the right. Validates both inputs with Zod. On submit, shows a full-screen loading overlay and runs the 3-step API flow. On completion, navigates to `/results/:id`.

### `/results/[id]` — Results dashboard
Client page. Reads match result from Zustand store. Renders the full intelligence report:
- Hero score card (animated ring, verdict headline)
- 4 sub-score cards (skill, experience, education, ATS)
- Resume stats bar (word count, achievements, action verbs)
- Skill gap section (matched vs missing badges)
- ATS keywords grid
- Strengths + weaknesses panels
- Prioritized recommendations
- Score breakdown bars

---

## API integration

The frontend calls your FastAPI backend in sequence:

```
1. POST /resumes/upload       → { resume_id }
2. POST /job-descriptions/parse → { jd_id }
3. POST /matches/analyze       → full MatchAnalyzeResponse
```

All in `src/hooks/useMatchAnalysis.ts`. Progress is mapped:
- 5–35% → resume upload (tracks actual upload bytes)
- 38–65% → JD parsing
- 70–92% → AI analysis (simulated smooth increment)
- 100% → complete

---

## Adding authentication

The codebase is auth-ready. To add auth:

1. Create `src/store/authStore.ts` (same Zustand pattern as analyzeStore)
2. Add token injection in `src/lib/api/client.ts` — the comment is already there
3. Add 401 redirect in the response interceptor — also commented in
4. Create `src/app/auth/login/page.tsx` and `src/app/auth/register/page.tsx`
5. Add a middleware.ts at the root to protect `/analyze` and `/results/*`

---

## Deployment

### Vercel (recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set env vars in Vercel dashboard:
# NEXT_PUBLIC_API_BASE_URL = https://your-api.com
# NEXT_PUBLIC_APP_URL = https://your-frontend.com
```

### Docker
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

---

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI backend URL | `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_APP_URL` | Frontend URL (for OG tags) | `http://localhost:3000` |

---

## Scripts

```bash
npm run dev         # Development server
npm run build       # Production build
npm run start       # Serve production build
npm run lint        # ESLint
npm run type-check  # TypeScript validation only
```

---

## Extending the product

**Add history page** — Create `src/app/history/page.tsx`. Add a `historyStore` with Zustand `persist` middleware to save past analyses to localStorage.

**Add PDF export** — Add a `Download report` button on the results page. Use `@react-pdf/renderer` to generate a branded PDF from the match data.

**Add comparison mode** — Allow uploading multiple JDs and comparing scores side by side. The API layer is already typed for multiple analyses.

**Add streaming analysis** — If your backend supports SSE/streaming, replace the `matchApi.analyze` call with an `EventSource` and update progress in real time.

**Add onboarding tour** — Use `driver.js` or `react-joyride` to walk new users through the analyze page on first visit.

---

## Tech stack

| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS + CSS variables |
| Components | shadcn/ui primitives + custom |
| Animation | Framer Motion |
| Forms | React Hook Form + Zod |
| State | Zustand |
| API | Axios with typed services |
| Data fetching | TanStack Query (React Query) |
| Icons | Lucide React |
| Dark mode | next-themes |
| Deployment | Vercel-ready |

---

*Built to YC startup standard — clean architecture, premium UI, production-ready.*
