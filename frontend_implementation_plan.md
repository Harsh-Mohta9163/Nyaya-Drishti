# NyayaDrishti — Frontend Implementation Plan

> **Court Judgment Intelligence System for CCMS**
> AI for Bharat Hackathon 2 | Theme 11 | 3-Day Sprint
> **Repo:** `nyaya-drishti-frontend/` → Deploys to **Vercel**

---

## Table of Contents

1. [Tech Stack](#1-tech-stack)
2. [Project Setup & Scaffold](#2-project-setup--scaffold)
3. [Design System & Tokens](#3-design-system--tokens)
4. [Project Structure](#4-project-structure)
5. [API Contract (Frozen — Both Teams Must Agree)](#5-api-contract-frozen--both-teams-must-agree)
6. [Mock Data Layer](#6-mock-data-layer)
7. [Phase 1 — Foundation](#7-phase-1--foundation)
8. [Phase 2 — Core Pages](#8-phase-2--core-pages)
9. [Phase 3 — Integration & Polish](#9-phase-3--integration--polish)
10. [Component Catalogue](#10-component-catalogue)
11. [State & Data Fetching Strategy](#11-state--data-fetching-strategy)
12. [i18n — Bilingual (EN / ಕನ್ನಡ)](#12-i18n--bilingual-en--ಕನ್ನಡ)
13. [Auth & Role-Based Access](#13-auth--role-based-access)
14. [Routing Map](#14-routing-map)
15. [Integration Checkpoints with Backend](#15-integration-checkpoints-with-backend)
16. [Deployment — Vercel](#16-deployment--vercel)
17. [Checklist](#17-master-checklist)

---

## 1. Tech Stack

| Layer | Technology | Version | Why |
|---|---|---|---|
| Framework | React + Vite | React 18, Vite 6 | Fast HMR, fast builds |
| Language | TypeScript | 5.x | Type safety across API contracts |
| UI Library | shadcn/ui + Radix UI | Latest | Premium components, full ownership, no runtime |
| Styling | Tailwind CSS | v4 | Glassmorphism, dark mode, utility-first |
| Animations | Framer Motion | 11.x | Page transitions, micro-animations |
| Charts | Recharts | 2.x | Dashboard visualizations (SVG-based) |
| Routing | React Router | v7 | SPA navigation, nested routes, loaders |
| Server State | TanStack Query | v5 | Caching, auto-refetch, optimistic updates |
| Tables | TanStack Table | v8 | Sorting, filtering, pagination |
| Forms | React Hook Form + Zod | Latest | Review workflow validation, type-safe schemas |
| PDF Viewer | react-pdf | 9.x | Side-by-side PDF viewer with page navigation |
| HTTP Client | Axios | 1.x | JWT interceptors, base URL config |
| i18n | react-i18next | 14.x | EN/ಕನ್ನಡ bilingual support |
| Icons | Lucide React | 0.383.0 | Consistent icon set |
| Font | Inter (Google Fonts) | — | Modern, legible for legal content |
| Linting | ESLint + Prettier | — | Consistent code style |

---

## 2. Project Setup & Scaffold

### Step-by-step setup commands

```bash
# 1. Create project
npm create vite@latest nyaya-drishti-frontend -- --template react-ts
cd nyaya-drishti-frontend

# 2. Install core dependencies
npm install react-router-dom@7 framer-motion recharts
npm install @tanstack/react-query @tanstack/react-table
npm install react-hook-form @hookform/resolvers zod
npm install react-pdf axios react-i18next i18next
npm install lucide-react

# 3. Install dev dependencies
npm install -D tailwindcss@4 postcss autoprefixer
npm install -D @types/react @types/react-dom

# 4. Initialize shadcn/ui (dark theme, "New York" style)
npx shadcn@latest init
# Choose: TypeScript → yes, style → New York, base color → slate, dark mode → yes

# 5. Add shadcn components used in this project
npx shadcn@latest add button card badge table dialog tabs
npx shadcn@latest add input label select textarea toast
npx shadcn@latest add dropdown-menu separator progress skeleton
npx shadcn@latest add alert avatar command popover
```

### Environment variables (`.env.local`)

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=NyayaDrishti
```

### Environment variables (production on Vercel)

```env
VITE_API_URL=https://nyaya-drishti-backend.onrender.com
```

> **Important:** Add a "Waking up server…" loading state for the Render cold-start delay (~30–60s). This is mandatory for demo.

---

## 3. Design System & Tokens

### Color Palette (defined in `index.css` + Tailwind config)

| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#0f172a` | Page background (deep navy) |
| `--bg-card` | `rgba(15,23,42,0.7)` | Glass card background |
| `--accent-blue` | `#3b82f6` | Primary actions, links, highlights |
| `--accent-amber` | `#f59e0b` | Warnings, medium risk |
| `--accent-red` | `#ef4444` | High risk, danger, rejection |
| `--accent-green` | `#22c55e` | Verified, success, approval |
| `--text-primary` | `#f8fafc` | Main text |
| `--text-muted` | `#94a3b8` | Secondary / muted text |
| `--border-glow` | `rgba(59,130,246,0.3)` | Card border glow |

### GlassCard Pattern

```css
/* src/index.css */
.glass-card {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
}

.glass-card-hover:hover {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
  transition: all 0.2s ease;
}
```

### Typography

```css
/* src/index.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body { font-family: 'Inter', sans-serif; }
```

### Risk Color Mapping (utility used across components)

```typescript
// src/lib/utils.ts
export const riskColor = {
  High: 'text-red-400 bg-red-500/10 border-red-500/30',
  Medium: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  Low: 'text-green-400 bg-green-500/10 border-green-500/30',
};

export const statusColor = {
  uploaded: 'text-slate-400 bg-slate-500/10',
  processing: 'text-blue-400 bg-blue-500/10',
  extracted: 'text-purple-400 bg-purple-500/10',
  review_pending: 'text-amber-400 bg-amber-500/10',
  verified: 'text-green-400 bg-green-500/10',
  action_created: 'text-emerald-400 bg-emerald-500/10',
};
```

---

## 4. Project Structure

```
nyaya-drishti-frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── components/
│   │   ├── ui/                    # shadcn/ui auto-generated components
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx        # Role-based nav items
│   │   │   ├── Header.tsx         # Language toggle, user avatar, notifications bell
│   │   │   └── PageShell.tsx      # Sidebar + Header wrapper
│   │   ├── dashboard/
│   │   │   ├── StatCard.tsx       # Animated stat card with icon + value
│   │   │   ├── DeadlineHeatmap.tsx # Calendar heatmap (7/30/90 day views)
│   │   │   ├── RiskBoard.tsx      # High-risk cases pinned list
│   │   │   └── AppealCountdown.tsx # Live timer for limitation period
│   │   ├── cases/
│   │   │   ├── CaseTable.tsx      # TanStack Table with filters
│   │   │   ├── CaseCard.tsx       # Card view for mobile
│   │   │   ├── StatusBadge.tsx    # Animated status pill
│   │   │   ├── PDFUpload.tsx      # Drag-drop upload with progress
│   │   │   └── ProcessingStatus.tsx # Polling status during extraction
│   │   ├── pdf/
│   │   │   ├── PDFViewer.tsx      # react-pdf with page nav
│   │   │   └── SplitView.tsx      # Left PDF + Right extracted data
│   │   ├── review/
│   │   │   ├── ReviewPanel.tsx    # 3-level review tabs
│   │   │   ├── FieldReview.tsx    # Field-level approve/edit/reject
│   │   │   ├── DirectiveReview.tsx # Directive-level review
│   │   │   ├── CaseReview.tsx     # Case-level final sign-off
│   │   │   ├── ApprovalActions.tsx # Action buttons with confirmation
│   │   │   └── ConflictAlert.tsx  # Logical inconsistency warning
│   │   ├── action-plan/
│   │   │   ├── ActionTimeline.tsx  # Step-by-step compliance timeline
│   │   │   ├── DeadlineCard.tsx   # Legal + internal deadline display
│   │   │   ├── CCMSStageMap.tsx   # CCMS workflow stage visualization
│   │   │   └── SimilarCases.tsx   # RAG evidence panel
│   │   └── common/
│   │       ├── GlassCard.tsx      # Reusable glass card wrapper
│   │       ├── LoadingSpinner.tsx  # Animated spinner
│   │       ├── EmptyState.tsx     # Empty list / no data state
│   │       ├── ErrorState.tsx     # Error boundary UI
│   │       ├── ServerWakeup.tsx   # Render cold-start warning banner
│   │       └── ConfidenceBadge.tsx # OCR/extraction confidence indicator
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── CasesListPage.tsx
│   │   ├── CaseDetailPage.tsx
│   │   ├── ActionPlanPage.tsx
│   │   ├── ReviewPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   └── NotificationsPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts             # Login, logout, token refresh
│   │   ├── useCases.ts            # List, upload, get case detail
│   │   ├── useExtraction.ts       # Trigger + poll extraction status
│   │   ├── useActionPlan.ts       # Get + generate action plan
│   │   ├── useReviews.ts          # Pending reviews, submit review
│   │   ├── useDashboard.ts        # Stats, deadlines, high-risk
│   │   ├── useNotifications.ts    # Fetch + mark-read notifications
│   │   └── useTranslate.ts        # Call /api/translate/ for dynamic content
│   ├── lib/
│   │   ├── api.ts                 # Axios instance + JWT interceptor
│   │   ├── mockData.ts            # All mock data for Phase 1 & 2
│   │   ├── utils.ts               # riskColor, statusColor, formatDate etc.
│   │   └── queryClient.ts         # TanStack Query client config
│   ├── context/
│   │   ├── AuthContext.tsx        # User + role + token state
│   │   └── ThemeContext.tsx       # Dark/light mode (dark-only for hackathon)
│   ├── locales/
│   │   ├── en.json                # English UI strings
│   │   └── kn.json                # Kannada UI strings
│   ├── types/
│   │   └── index.ts               # All TypeScript interfaces (shared contract)
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── .env.local
├── .env.production
├── vercel.json
├── vite.config.ts
└── package.json
```

---

## 5. API Contract (Frozen — Both Teams Must Agree)

> **Do not change these shapes without syncing with the backend developer.** Frontend mocks these exactly during Phase 1 & 2.

### 5.1 TypeScript Interfaces (`src/types/index.ts`)

```typescript
// ─── Auth ─────────────────────────────────────────────────────────────
export type Role = 'reviewer' | 'dept_officer' | 'dept_head' | 'legal_advisor';

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
  department: string;
  language_preference: 'en' | 'kn';
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role: Role;
  department?: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

// ─── Cases ────────────────────────────────────────────────────────────
export type CaseStatus =
  | 'uploaded'
  | 'processing'
  | 'extracted'
  | 'review_pending'
  | 'verified'
  | 'action_created';

export type CaseType = 'WP' | 'Appeal' | 'SLP' | 'CCP' | 'LPA';

export type ContemptRisk = 'High' | 'Medium' | 'Low';

export interface Case {
  id: number;
  case_number: string;
  court: string;
  bench: string;
  petitioner: string;
  respondent: string;
  case_type: CaseType;
  judgment_date: string;           // ISO date string
  status: CaseStatus;
  ocr_confidence: number | null;   // 0.0 – 1.0
  created_at: string;              // ISO datetime string
}

export interface CaseListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Case[];
}

export interface CaseListParams {
  page?: number;
  page_size?: number;
  status?: CaseStatus;
  case_type?: CaseType;
  contempt_risk?: ContemptRisk;
  search?: string;
  ordering?: string;               // e.g. '-judgment_date'
}

// ─── Extracted Data ────────────────────────────────────────────────────
export interface SourceReference {
  page: number;
  paragraph: number;
  char_offset: number;
  text_snippet: string;
}

export interface CourtDirection {
  id: string;
  verbatim_text: string;
  direction_type: string;           // e.g. 'compliance', 'payment', 'inquiry'
  responsible_entity: string;
  confidence: number;
  source_reference: SourceReference;
}

export interface ExtractedData {
  id: number;
  case: number;
  header_data: {
    case_number: string;
    court: string;
    bench: string;
    petitioner: string;
    respondent: string;
    judgment_date: string;
  };
  operative_order: string;
  court_directions: CourtDirection[];
  order_type: string;
  entities: string[];
  extraction_confidence: number;    // 0.0 – 1.0
  source_references: SourceReference[];
}

// ─── Action Plan ───────────────────────────────────────────────────────
export type Recommendation = 'Comply' | 'Appeal';

export interface ComplianceAction {
  id: string;
  step_number: number;
  action: string;
  responsible_department: string;
  depends_on: string[];             // step ids that must complete first
  is_complete: boolean;
}

export interface SimilarCase {
  case_number: string;
  outcome: string;
  similarity_score: number;
  summary: string;
}

export interface ActionPlan {
  id: number;
  case: number;
  recommendation: Recommendation;
  recommendation_confidence: number;   // 0.0 – 1.0
  compliance_actions: ComplianceAction[];
  legal_deadline: string;              // ISO date string
  internal_deadline: string;           // ISO date string
  statutory_basis: string;             // e.g. 'Art. 136 Constitution - 90 days'
  responsible_departments: string[];
  ccms_stage: string;
  contempt_risk: ContemptRisk;
  similar_cases: SimilarCase[];
  verification_status: 'pending' | 'field_approved' | 'directive_approved' | 'case_approved';
}

// ─── Review ────────────────────────────────────────────────────────────
export type ReviewLevel = 'field' | 'directive' | 'case';
export type ReviewAction = 'approve' | 'edit' | 'reject';

export interface ReviewRequest {
  review_level: ReviewLevel;
  action: ReviewAction;
  changes?: Record<string, unknown>;  // null for approve/reject
  reason?: string;                    // required for reject
}

export interface ReviewLog {
  id: number;
  action_plan: number;
  reviewer: User;
  review_level: ReviewLevel;
  action: ReviewAction;
  changes: Record<string, unknown> | null;
  reason: string | null;
  created_at: string;
}

export interface PendingReview {
  case_id: number;
  case_number: string;
  court: string;
  contempt_risk: ContemptRisk;
  review_level: ReviewLevel;
  created_at: string;
}

// ─── Dashboard ─────────────────────────────────────────────────────────
export interface DashboardStats {
  total_cases: number;
  pending_review: number;
  high_risk: number;
  upcoming_deadlines_7d: number;
  verified_this_month: number;
  avg_extraction_confidence: number;
}

export interface DeadlineItem {
  case_id: number;
  case_number: string;
  case_type: CaseType;
  legal_deadline: string;
  internal_deadline: string;
  contempt_risk: ContemptRisk;
  ccms_stage: string;
  days_remaining: number;
}

export interface HighRiskCase {
  case_id: number;
  case_number: string;
  court: string;
  petitioner: string;
  contempt_risk: ContemptRisk;
  legal_deadline: string;
  days_remaining: number;
  ccms_stage: string;
}

// ─── Notifications ─────────────────────────────────────────────────────
export type NotificationType =
  | 'deadline_warning'
  | 'high_risk_alert'
  | 'review_assigned'
  | 'case_verified'
  | 'escalation';

export interface Notification {
  id: number;
  case: number;
  case_number: string;
  notification_type: NotificationType;
  message: string;
  is_read: boolean;
  created_at: string;
}

// ─── Translation ───────────────────────────────────────────────────────
export interface TranslateRequest {
  text: string;
  source_lang: 'en' | 'kn';
  target_lang: 'en' | 'kn';
}

export interface TranslateResponse {
  translated_text: string;
}
```

---

### 5.2 API Endpoints Reference

All requests include `Authorization: Bearer <access_token>` header (except `/api/auth/login/` and `/api/auth/register/`).

Base URL: `VITE_API_URL` env var.

#### Auth Endpoints

| Method | Endpoint | Request Body | Response |
|---|---|---|---|
| POST | `/api/auth/register/` | `RegisterRequest` | `{ user: User, tokens: AuthTokens }` |
| POST | `/api/auth/login/` | `LoginRequest` | `LoginResponse` |
| POST | `/api/auth/refresh/` | `{ refresh: string }` | `{ access: string }` |
| GET | `/api/auth/me/` | — | `User` |

#### Cases Endpoints

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/cases/` | Query params: `CaseListParams`. Returns `CaseListResponse`. |
| POST | `/api/cases/` | Multipart form: `pdf_file` (File) + `case_number` (string). Returns `Case`. |
| GET | `/api/cases/{id}/` | Returns `Case` |
| GET | `/api/cases/{id}/pdf/` | Returns PDF binary (Content-Type: application/pdf) |
| PATCH | `/api/cases/{id}/status/` | Body: `{ status: CaseStatus }`. Returns `Case`. |

#### Extraction & Action Plans Endpoints

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/api/cases/{id}/extract/` | Triggers async extraction. Returns `{ task_id: string, status: 'processing' }`. |
| GET | `/api/cases/{id}/extraction/` | Returns `ExtractedData` |
| GET | `/api/cases/{id}/action-plan/` | Returns `ActionPlan` |
| POST | `/api/cases/{id}/action-plan/generate/` | Triggers action plan generation. Returns `{ task_id: string }`. |

#### Review Endpoints

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/reviews/pending/` | Returns `PendingReview[]` for current user's role |
| POST | `/api/cases/{id}/review/` | Body: `ReviewRequest`. Returns `ReviewLog`. |
| GET | `/api/cases/{id}/review-history/` | Returns `ReviewLog[]` |

#### Dashboard Endpoints

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/dashboard/stats/` | Returns `DashboardStats` |
| GET | `/api/dashboard/deadlines/` | Query: `?days=7|30|90`. Returns `DeadlineItem[]`. |
| GET | `/api/dashboard/high-risk/` | Returns `HighRiskCase[]` |
| GET | `/api/notifications/` | Returns `Notification[]`. Query: `?unread=true`. |
| PATCH | `/api/notifications/{id}/read/` | Marks notification as read. Returns `Notification`. |

#### Translation Endpoint

| Method | Endpoint | Request Body | Response |
|---|---|---|---|
| POST | `/api/translate/` | `TranslateRequest` | `TranslateResponse` |

---

## 6. Mock Data Layer

During Phase 1 & 2, all API calls are replaced with mock data. This means the entire UI is buildable without a running backend.

### `src/lib/mockData.ts`

```typescript
import type {
  Case, ExtractedData, ActionPlan, DashboardStats,
  DeadlineItem, HighRiskCase, Notification, PendingReview, ReviewLog
} from '../types';

export const mockUser = {
  id: 1, username: 'priya_reviewer', email: 'priya@karnataka.gov.in',
  role: 'reviewer' as const, department: 'Revenue Department',
  language_preference: 'en' as const,
};

export const mockCases: Case[] = [
  {
    id: 1, case_number: 'WP/12345/2024', court: 'Karnataka High Court',
    bench: 'Hon. Justice R. Nataraj', petitioner: 'ABC Industries Ltd.',
    respondent: 'State of Karnataka & Ors.', case_type: 'WP',
    judgment_date: '2024-11-15', status: 'review_pending',
    ocr_confidence: 0.94, created_at: '2024-11-15T10:30:00Z',
  },
  {
    id: 2, case_number: 'SLP/4567/2024', court: 'Karnataka High Court',
    bench: 'Division Bench', petitioner: 'Ramaiah & Sons',
    respondent: 'Revenue Department', case_type: 'SLP',
    judgment_date: '2024-11-10', status: 'action_created',
    ocr_confidence: 0.88, created_at: '2024-11-10T09:00:00Z',
  },
  // ... add 5+ more mock cases covering all statuses and risk levels
];

export const mockExtractedData: ExtractedData = {
  id: 1, case: 1,
  header_data: {
    case_number: 'WP/12345/2024',
    court: 'Karnataka High Court',
    bench: 'Hon. Justice R. Nataraj',
    petitioner: 'ABC Industries Ltd.',
    respondent: 'State of Karnataka & Ors.',
    judgment_date: '2024-11-15',
  },
  operative_order: `1. The Writ Petition is allowed. 2. The State Government is directed to...`,
  court_directions: [
    {
      id: 'd1', verbatim_text: 'The State Government is directed to pay compensation within 60 days.',
      direction_type: 'payment', responsible_entity: 'Revenue Department',
      confidence: 0.96,
      source_reference: { page: 38, paragraph: 4, char_offset: 1204, text_snippet: 'directed to pay compensation' },
    },
  ],
  order_type: 'Compliance',
  entities: ['Revenue Department', 'Finance Department'],
  extraction_confidence: 0.93,
  source_references: [],
};

export const mockActionPlan: ActionPlan = {
  id: 1, case: 1, recommendation: 'Comply', recommendation_confidence: 0.87,
  compliance_actions: [
    { id: 'a1', step_number: 1, action: 'Prepare LCO Proposal for compensation payment',
      responsible_department: 'Revenue Department', depends_on: [], is_complete: false },
    { id: 'a2', step_number: 2, action: 'Obtain GA/LCO Authorization',
      responsible_department: 'Law Department', depends_on: ['a1'], is_complete: false },
    { id: 'a3', step_number: 3, action: 'Release funds via Finance Department',
      responsible_department: 'Finance Department', depends_on: ['a2'], is_complete: false },
  ],
  legal_deadline: '2025-01-15',
  internal_deadline: '2024-12-31',
  statutory_basis: 'Writ compliance — 60 days from judgment date (court order)',
  responsible_departments: ['Revenue Department', 'Finance Department', 'Law Department'],
  ccms_stage: 'Order Compliance Stage',
  contempt_risk: 'High',
  similar_cases: [
    { case_number: 'WP/9876/2023', outcome: 'Compliance ordered', similarity_score: 0.91,
      summary: 'Similar compensation dispute; department complied within 45 days.' },
  ],
  verification_status: 'pending',
};

export const mockDashboardStats: DashboardStats = {
  total_cases: 142, pending_review: 23, high_risk: 8,
  upcoming_deadlines_7d: 5, verified_this_month: 31, avg_extraction_confidence: 0.91,
};

export const mockDeadlines: DeadlineItem[] = [
  { case_id: 1, case_number: 'WP/12345/2024', case_type: 'WP',
    legal_deadline: '2025-01-15', internal_deadline: '2024-12-31',
    contempt_risk: 'High', ccms_stage: 'Order Compliance Stage', days_remaining: 3 },
  // ...
];

export const mockHighRisk: HighRiskCase[] = [
  { case_id: 1, case_number: 'WP/12345/2024', court: 'Karnataka High Court',
    petitioner: 'ABC Industries Ltd.', contempt_risk: 'High',
    legal_deadline: '2025-01-15', days_remaining: 3, ccms_stage: 'Order Compliance Stage' },
];

export const mockNotifications: Notification[] = [
  { id: 1, case: 1, case_number: 'WP/12345/2024', notification_type: 'deadline_warning',
    message: 'Legal deadline in 3 days. Immediate action required.', is_read: false,
    created_at: new Date().toISOString() },
];

export const mockPendingReviews: PendingReview[] = [
  { case_id: 1, case_number: 'WP/12345/2024', court: 'Karnataka High Court',
    contempt_risk: 'High', review_level: 'field', created_at: new Date().toISOString() },
];
```

### Mock API wrapper (`src/lib/api.ts`)

```typescript
// During development, wrap mock data in promise delays to simulate network
export const mockDelay = (ms = 600) => new Promise(res => setTimeout(res, ms));

// Toggle this flag to switch between mock and real API
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
```

---

## 7. Phase 1 — Foundation

**Goal:** Scaffolded project, design system live, auth pages working with mocks, navigation working.

### Checklist

- [ ] Run scaffold commands from Section 2
- [ ] Configure Tailwind v4 with custom tokens from Section 3
- [ ] Configure `vite.config.ts` with path aliases (`@/` → `src/`)
- [ ] Create `src/types/index.ts` with all interfaces from Section 5.1
- [ ] Create `src/lib/api.ts` — axios instance, `USE_MOCK` flag, `mockDelay` helper
- [ ] Create `src/lib/mockData.ts` with all mock data from Section 6
- [ ] Create `src/lib/utils.ts` — `riskColor`, `statusColor`, `formatDate`, `daysUntil`, `cn` (clsx + twMerge)
- [ ] Create `src/lib/queryClient.ts` — TanStack Query client with 5-min stale time
- [ ] Build `GlassCard.tsx` — reusable glassmorphism wrapper
- [ ] Build `PageShell.tsx` — Sidebar + Header wrapper with Framer Motion layout
- [ ] Build `Sidebar.tsx` — role-based nav links (items filtered by user role)
- [ ] Build `Header.tsx` — language toggle (EN/ಕನ್ನಡ), user avatar, notifications bell with badge
- [ ] Set up `AuthContext.tsx` — stores `user`, `access`, `refresh` tokens in localStorage
- [ ] Set up `ThemeContext.tsx` — dark mode provider (dark-only for now)
- [ ] Set up i18n — `react-i18next` with `en.json` and `kn.json` locale files (see Section 12)
- [ ] Build `LoginPage.tsx` — email/password form, role info hint, mock login
- [ ] Build `RegisterPage.tsx` — username, email, password, role select, department input
- [ ] Build `ProtectedRoute.tsx` — redirect to login if no token
- [ ] Build `RoleRoute.tsx` — redirect if user role does not have access
- [ ] Set up `App.tsx` with full routing (see Section 14)
- [ ] Build `LoadingSpinner.tsx`, `EmptyState.tsx`, `ErrorState.tsx`, `ConfidenceBadge.tsx`
- [ ] Build `ServerWakeup.tsx` — banner that appears on first load, disappears after first successful API call

### Key implementation notes

**`src/lib/api.ts`** — Axios instance with interceptors:
```typescript
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor — handle 401, attempt refresh
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/refresh/`, { refresh });
          localStorage.setItem('access_token', data.access);
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return api(error.config);
        } catch {
          // Refresh failed — force logout
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

---

## 8. Phase 2 — Core Pages

**Goal:** All 8 pages built with mock data. Full UI/UX complete. No real API calls yet.

### 8.1 Dashboard Page (`DashboardPage.tsx`)

**Role-based rendering:**
- **Reviewer:** Verification queue stats + pending review list + confidence meter
- **Dept. Officer:** Their department's verified plans + deadline countdown
- **Dept. Head:** Aggregate summary + contempt risk board + interdependence alerts
- **Legal Advisor:** Appeal-recommended cases + RAG evidence panel + limitation tracker

**Components:**
- `StatCard` × 4 — Total Cases, Pending Review, High Risk, Upcoming Deadlines (7d). Animated count-up on mount.
- `DeadlineHeatmap` — Calendar grid (7/30/90 day toggle). Cells colored by urgency (green → amber → red). Click a cell → navigate to filtered cases list.
- `RiskBoard` — Sorted list of High contempt-risk cases, pinned at top. Shows `days_remaining` with pulse animation if ≤ 7 days.
- `AppealCountdown` — For legal_advisor role: live countdown timer for each active limitation period.

**Staggered entrance animation** with Framer Motion (`staggerChildren: 0.08`).

---

### 8.2 Cases List Page (`CasesListPage.tsx`)

**Components:**
- `PDFUpload` — Drag-and-drop zone + file input. Validates PDF type + size (<50MB). Shows upload progress bar. On success, shows new case in list.
- `CaseTable` — TanStack Table v8 columns:
  - Case Number (sortable, searchable)
  - Court
  - Case Type badge
  - Judgment Date (sortable)
  - Status badge (animated pill)
  - Contempt Risk badge (color-coded)
  - Days to Deadline (red if ≤ 7)
  - Actions (View Detail button)
- Filter bar: Status dropdown, Case Type dropdown, Risk dropdown, Search input (debounced 300ms)
- Pagination: page size 20, show total count

**PDF Upload flow:**
1. User drops PDF → validate format
2. Show `ProcessingStatus` component with polling every 3s
3. Status bar: `uploaded → processing → extracted → review_pending`
4. On completion, navigate to Case Detail page

---

### 8.3 Case Detail Page (`CaseDetailPage.tsx`)

**Split view layout:**
- **Left 50%:** `PDFViewer` — react-pdf component. Page navigation (prev/next, jump-to-page). Page count display. Zoom controls.
- **Right 50%:** Tabbed panel
  - **Extracted Data tab:** Shows `ExtractedData` fields. Each field shows its `confidence` score via `ConfidenceBadge`. Fields are grouped: Header Data, Court Directions (each direction as an expandable card), Entities.
  - **Action Plan tab:** Links to `ActionPlanPage` or inline preview.
  - **Review History tab:** Shows `ReviewLog[]` as timeline.

**PDF highlighting:** When a user clicks a `CourtDirection`, highlight the source span in the PDF viewer by jumping to `source_reference.page`. (Use PDF.js text layer or scroll to page as a simpler MVP approach.)

**Processing state:** If `case.status === 'processing'`, show `ProcessingStatus` overlay instead of split view. Poll `GET /api/cases/{id}/` every 3s until status changes.

---

### 8.4 Action Plan Page (`ActionPlanPage.tsx`)

**Components:**
- **Recommendation banner** — Large "COMPLY" (green) or "APPEAL" (amber/red) banner with confidence score and RAG evidence summary.
- `ActionTimeline` — Vertical stepper. Each step shows:
  - Step number + action text
  - Responsible department badge
  - Dependency indicator (grayed out until previous step complete)
  - Check/complete toggle (for dept_officer role)
- `DeadlineCard` × 2 — Legal Deadline (with statutory basis) + Internal Deadline. Shows days remaining with color-coded urgency.
- `CCMSStageMap` — Visual flowchart of the CCMS stages: highlight the current `ccms_stage`. The 8 stages are: LCO Proposal → GA/LCO Authorization → Draft PWR → Approved PWR → Draft SO from Advocate → Affidavit Filing → Order Compliance Stage → {Proposed for Appeal / Closed with Appeal Number / Not to Appeal}.
- `SimilarCases` — RAG evidence panel. Table of similar past cases with similarity score, outcome, and summary. Shows "(4 of 5 similar cases → compliance recommended)" summary line.
- Language toggle: button to translate all action plan content to Kannada via `/api/translate/`.

---

### 8.5 Review Workflow Page (`ReviewPage.tsx`)

**3-Level Tabs:** `Field Review` → `Directive Review` → `Case Review`

Tabs are sequential — Directive tab is locked until Field level is approved. Case tab locked until Directive approved.

#### Field Review (`FieldReview.tsx`)

Shows each extracted field as a card:
- Field name + AI-extracted value + Confidence badge
- Highlighted PDF source snippet
- Three buttons: **Approve** (green) / **Edit** (pencil opens inline input) / **Reject** (red)
- On edit: show inline editable field (React Hook Form). On save, call `POST /api/cases/{id}/review/` with `{ review_level: 'field', action: 'edit', changes: { field_name: new_value } }`.
- `ConflictAlert` — if an edit creates a logical inconsistency (e.g., order date after deadline), show warning banner before allowing save.

#### Directive Review (`DirectiveReview.tsx`)

Each court direction side-by-side with its generated compliance action. Same Approve/Edit/Reject flow at the directive level.

#### Case Review (`CaseReview.tsx`)

Full case summary: all verified fields + complete action plan. One final "Sign Off" button (role: `dept_head` or `legal_advisor` only). On approve → case moves to `verified` status.

**Reject with reason:** When rejecting at any level, show a dialog with required reason textarea. Reason is stored in `ReviewRequest.reason`.

---

### 8.6 Analytics Page (`AnalyticsPage.tsx`)

Recharts components:

| Chart | Type | Data |
|---|---|---|
| Cases Over Time | LineChart | Monthly case count (last 12 months) |
| Risk Distribution | PieChart | High/Medium/Low case counts |
| Department Workload | BarChart | Active cases per department |
| Extraction Confidence | AreaChart | Average confidence over time |
| Status Funnel | BarChart (horizontal) | Count at each status stage |
| Appeal vs Comply | PieChart | Recommendation distribution |

All charts use the design system colors. Show tooltips with full details on hover. Date range filter: last 30d / 90d / 12m.

---

### 8.7 Notifications Page (`NotificationsPage.tsx`)

- List of `Notification[]` grouped by date
- Each notification shows: type icon, case number (clickable → case detail), message, timestamp
- Notification types → icons:
  - `deadline_warning` → Clock (amber)
  - `high_risk_alert` → AlertTriangle (red)
  - `review_assigned` → ClipboardCheck (blue)
  - `case_verified` → CheckCircle (green)
  - `escalation` → ArrowUp (red)
- Mark all as read button
- Click individual → mark read + navigate to case
- Unread count badge in `Header.tsx` sidebar nav

---

### 8.8 Language Toggle — Kannada (ಕನ್ನಡ)

All static UI text is bilingual via `react-i18next`. Dynamic content (extracted data, action plan text) is translated on demand via `POST /api/translate/`.

The `Header.tsx` toggle switches between EN and KN. When KN is selected:
1. All i18n strings switch immediately (client-side).
2. Dynamic content (court directions, compliance actions) is fetched from `/api/translate/` and cached by TanStack Query.

---

## 9. Phase 3 — Integration & Polish

**Goal:** Replace all mock data with real API. Polish animations, loading states, error handling. Deploy to Vercel.

### Integration Checklist (in dependency order)

- [ ] **Checkpoint 2 — Auth:** Swap mock auth → `POST /api/auth/login/`, `POST /api/auth/register/`, `GET /api/auth/me/`. Test JWT storage + refresh flow.
- [ ] **Checkpoint 3 — Cases + Upload:** Wire `PDFUpload` → `POST /api/cases/` multipart. Wire `CaseTable` → `GET /api/cases/` with real pagination + filters.
- [ ] **Checkpoint 4 — Extraction Display:** Wire split view → `GET /api/cases/{id}/extraction/`. Trigger extraction with `POST /api/cases/{id}/extract/`. Poll case status every 3s.
- [ ] **Checkpoint 5 — Action Plan:** Wire `ActionPlanPage` → `GET /api/cases/{id}/action-plan/`. Trigger generation with `POST /api/cases/{id}/action-plan/generate/`.
- [ ] **Checkpoint 6 — Review Workflow:** Wire all review actions → `POST /api/cases/{id}/review/`. Wire pending reviews → `GET /api/reviews/pending/`. Wire review history → `GET /api/cases/{id}/review-history/`.
- [ ] **Checkpoint 7 — Dashboard:** Wire all dashboard components → `GET /api/dashboard/stats/`, `/deadlines/`, `/high-risk/`, `/api/notifications/`.
- [ ] **Translation:** Wire language toggle → `POST /api/translate/` for dynamic content. Cache results in TanStack Query (stale: Infinity for same text).
- [ ] **Loading states everywhere:** Every TanStack Query fetch shows skeleton loader (shadcn `Skeleton` component) while loading.
- [ ] **Error states everywhere:** Every page has `ErrorState` fallback with retry button.
- [ ] **Framer Motion polish:**
  - Page transitions: `AnimatePresence` + `motion.div` on each page (fade + slide up)
  - StatCard count-up animation on dashboard mount
  - Staggered card entrance: `staggerChildren: 0.06`
  - Pulse animation on high-risk items with `days_remaining ≤ 7`
  - Skeleton → content fade-in
- [ ] **Render cold-start handling:**
  - `ServerWakeup` banner appears on first page load
  - First API call: 60s timeout with "Server is waking up, please wait…" UI
  - Disappears after first successful response
- [ ] **Responsive design pass:** All pages tested at 375px (mobile), 768px (tablet), 1280px (desktop). Sidebar collapses to bottom nav on mobile.
- [ ] **Vercel deploy:** See Section 16.
- [ ] **End-to-end test:** Full demo script (Section 9 of main plan) tested with real backend.

---

## 10. Component Catalogue

### `GlassCard.tsx`
```typescript
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: 'blue' | 'red' | 'amber' | 'green' | 'none';
}
```

### `StatCard.tsx`
```typescript
interface StatCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  color?: 'blue' | 'red' | 'amber' | 'green';
  animateCount?: boolean;
}
```

### `StatusBadge.tsx`
```typescript
interface StatusBadgeProps {
  status: CaseStatus;
  animated?: boolean;   // pulse dot for 'processing'
}
```

### `ConfidenceBadge.tsx`
```typescript
interface ConfidenceBadgeProps {
  value: number;         // 0.0 – 1.0
  label?: string;        // e.g. 'OCR', 'Extraction', 'Recommendation'
  showPercent?: boolean;
}
// Color: ≥0.9 → green, 0.7-0.9 → amber, <0.7 → red
```

### `PDFUpload.tsx`
```typescript
interface PDFUploadProps {
  onUpload: (file: File) => Promise<Case>;
  maxSizeMB?: number;   // default: 50
}
```

### `DeadlineHeatmap.tsx`
```typescript
interface DeadlineHeatmapProps {
  deadlines: DeadlineItem[];
  view: '7d' | '30d' | '90d';
  onViewChange: (v: '7d' | '30d' | '90d') => void;
  onCellClick: (date: string) => void;
}
```

### `ConflictAlert.tsx`
```typescript
interface ConflictAlertProps {
  conflicts: string[];   // list of conflict descriptions
  onDismiss: () => void;
  onRevert: () => void;
}
```

### `CCMSStageMap.tsx`
```typescript
interface CCMSStageMapProps {
  currentStage: string;
  recommendation: Recommendation;
}
// Renders all CCMS stages as a flowchart, highlighting current stage
```

### `ServerWakeup.tsx`
```typescript
// No props — reads from a global flag set after first successful API call
// Shows amber banner: "Waking up server... This may take up to 60 seconds on first load."
// Auto-hides after successful response
```

---

## 11. State & Data Fetching Strategy

### TanStack Query keys (canonical, both devs must use same keys)

```typescript
// src/lib/queryKeys.ts
export const queryKeys = {
  auth: { me: ['auth', 'me'] },
  cases: {
    all: (params: CaseListParams) => ['cases', 'list', params],
    detail: (id: number) => ['cases', id],
    pdf: (id: number) => ['cases', id, 'pdf'],
    extraction: (id: number) => ['cases', id, 'extraction'],
    actionPlan: (id: number) => ['cases', id, 'action-plan'],
    reviewHistory: (id: number) => ['cases', id, 'review-history'],
  },
  reviews: { pending: ['reviews', 'pending'] },
  dashboard: {
    stats: ['dashboard', 'stats'],
    deadlines: (days: number) => ['dashboard', 'deadlines', days],
    highRisk: ['dashboard', 'high-risk'],
  },
  notifications: { all: ['notifications'] },
};
```

### Hook pattern

All hooks follow this structure:
```typescript
// src/hooks/useCases.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../lib/queryKeys';
import { api } from '../lib/api';
import type { Case, CaseListParams, CaseListResponse } from '../types';

export function useCasesList(params: CaseListParams) {
  return useQuery({
    queryKey: queryKeys.cases.all(params),
    queryFn: () => api.get<CaseListResponse>('/api/cases/', { params }).then(r => r.data),
    staleTime: 1000 * 60 * 2,  // 2 min
  });
}

export function useCaseDetail(id: number) {
  return useQuery({
    queryKey: queryKeys.cases.detail(id),
    queryFn: () => api.get<Case>(`/api/cases/${id}/`).then(r => r.data),
    staleTime: 1000 * 30,
  });
}

export function useUploadCase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append('pdf_file', file);
      form.append('case_number', `AUTO_${Date.now()}`);
      return api.post<Case>('/api/cases/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cases', 'list'] }),
  });
}
```

### Polling for extraction status

```typescript
// src/hooks/useExtraction.ts
export function useExtractionStatus(caseId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.cases.detail(caseId),
    queryFn: () => api.get<Case>(`/api/cases/${caseId}/`).then(r => r.data),
    refetchInterval: (data) => {
      // Stop polling once status is no longer 'processing'
      if (data?.status !== 'processing') return false;
      return 3000;  // Poll every 3s while processing
    },
    enabled,
  });
}
```

---

## 12. i18n — Bilingual (EN / ಕನ್ನಡ)

### Setup

```typescript
// src/lib/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '../locales/en.json';
import kn from '../locales/kn.json';

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, kn: { translation: kn } },
  lng: localStorage.getItem('language') || 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
```

### Key structure (`en.json` sample)

```json
{
  "nav": {
    "dashboard": "Dashboard",
    "cases": "Cases",
    "reviews": "Reviews",
    "analytics": "Analytics",
    "notifications": "Notifications"
  },
  "dashboard": {
    "totalCases": "Total Cases",
    "pendingReview": "Pending Review",
    "highRisk": "High Risk",
    "upcomingDeadlines": "Upcoming Deadlines (7d)"
  },
  "status": {
    "uploaded": "Uploaded",
    "processing": "Processing",
    "extracted": "Extracted",
    "review_pending": "Review Pending",
    "verified": "Verified",
    "action_created": "Action Plan Created"
  },
  "risk": {
    "High": "High Risk",
    "Medium": "Medium Risk",
    "Low": "Low Risk"
  },
  "review": {
    "approve": "Approve",
    "edit": "Edit",
    "reject": "Reject",
    "fieldLevel": "Field Review",
    "directiveLevel": "Directive Review",
    "caseLevel": "Case Sign-Off"
  },
  "upload": {
    "dragDrop": "Drag and drop a PDF judgment here",
    "orBrowse": "or click to browse",
    "uploading": "Uploading...",
    "processing": "Processing judgment..."
  },
  "wakeup": {
    "banner": "Server is waking up — this may take up to 60 seconds on first load."
  }
}
```

(`kn.json` has the same keys, with Kannada translations for all values.)

### Language toggle in Header

```typescript
// In Header.tsx
const { i18n } = useTranslation();
const toggleLanguage = () => {
  const next = i18n.language === 'en' ? 'kn' : 'en';
  i18n.changeLanguage(next);
  localStorage.setItem('language', next);
};
```

### Dynamic content translation

For extracted data and action plan text (which comes from backend), call the translate endpoint:

```typescript
// src/hooks/useTranslate.ts
export function useTranslate(text: string, enabled: boolean) {
  const { i18n } = useTranslation();
  return useQuery({
    queryKey: ['translate', text, i18n.language],
    queryFn: () =>
      api.post<TranslateResponse>('/api/translate/', {
        text, source_lang: 'en', target_lang: i18n.language,
      }).then(r => r.data.translated_text),
    enabled: enabled && i18n.language === 'kn',
    staleTime: Infinity,  // translated text never goes stale
  });
}
```

---

## 13. Auth & Role-Based Access

### Role → Page Access Matrix

| Page | reviewer | dept_officer | dept_head | legal_advisor |
|---|---|---|---|---|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Cases List | ✅ | ✅ | ✅ | ✅ |
| Case Detail | ✅ | ✅ | ✅ | ✅ |
| Action Plan | ✅ | ✅ | ✅ | ✅ |
| Review Workflow | ✅ | ❌ | ✅ | ✅ |
| Case Sign-Off | ❌ | ❌ | ✅ | ✅ |
| Analytics | ❌ | ✅ | ✅ | ✅ |
| Notifications | ✅ | ✅ | ✅ | ✅ |

### Role → Dashboard widget visibility

| Widget | reviewer | dept_officer | dept_head | legal_advisor |
|---|---|---|---|---|
| Verification Queue | ✅ | ❌ | ❌ | ❌ |
| Deadline Heatmap | ✅ | ✅ | ✅ | ✅ |
| Contempt Risk Board | ❌ | ❌ | ✅ | ✅ |
| Dept. Action Plans | ❌ | ✅ | ❌ | ❌ |
| Appeal Countdown | ❌ | ❌ | ❌ | ✅ |
| Aggregate Summary | ❌ | ❌ | ✅ | ❌ |
| RAG Evidence Panel | ❌ | ❌ | ❌ | ✅ |

### `ProtectedRoute.tsx`

```typescript
// Redirects to /login if no token
// Redirects to /unauthorized if role not in allowedRoles
interface ProtectedRouteProps {
  allowedRoles?: Role[];
  children: React.ReactNode;
}
```

---

## 14. Routing Map

```typescript
// src/App.tsx
<BrowserRouter>
  <Routes>
    {/* Public */}
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />

    {/* Protected — all roles */}
    <Route element={<ProtectedRoute><PageShell /></ProtectedRoute>}>
      <Route path="/" element={<Navigate to="/dashboard" />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/cases" element={<CasesListPage />} />
      <Route path="/cases/:id" element={<CaseDetailPage />} />
      <Route path="/cases/:id/action-plan" element={<ActionPlanPage />} />
      <Route path="/notifications" element={<NotificationsPage />} />

      {/* Reviewer + Dept Head + Legal Advisor only */}
      <Route element={<RoleRoute allowedRoles={['reviewer','dept_head','legal_advisor']} />}>
        <Route path="/cases/:id/review" element={<ReviewPage />} />
      </Route>

      {/* Dept Officer + Dept Head + Legal Advisor only */}
      <Route element={<RoleRoute allowedRoles={['dept_officer','dept_head','legal_advisor']} />}>
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>
    </Route>

    {/* 404 */}
    <Route path="*" element={<Navigate to="/dashboard" />} />
  </Routes>
</BrowserRouter>
```

---

## 15. Integration Checkpoints with Backend

| # | Checkpoint | What Frontend Does | What to Verify |
|---|---|---|---|
| 1 | **API Contract Lock** | Agree on all shapes in Section 5. Frontend uses mocks. | Both agree — no changes without sync. |
| 2 | **Auth Integration** | Replace mock auth with real JWT. Store tokens. Test refresh. | Login/register/logout work. Role stored correctly. |
| 3 | **Cases + PDF Upload** | Wire upload + cases list. Check multipart works. | PDF uploads, case appears in list, status updates. |
| 4 | **Extraction Display** | Wire split view. Poll status. Show `ExtractedData`. | Processing → extracted flow visible. Fields match types. |
| 5 | **Action Plan Flow** | Wire `ActionPlanPage`. Trigger generation endpoint. | Plan renders with deadlines, CCMS stage, risk, RAG cases. |
| 6 | **Review Workflow** | Wire all 3 review levels. Submit approve/edit/reject. | Audit log populates. Status updates. Conflict detection fires. |
| 7 | **Dashboard Data** | Wire all dashboard endpoints. Check charts render correctly. | Stats accurate. Deadlines sorted by urgency. |
| 8 | **Production Deploy** | Vercel frontend → Render backend. CORS verified. | Full demo script works end-to-end. |

---

## 16. Deployment — Vercel

### `vercel.json`
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [{ "key": "X-Content-Type-Options", "value": "nosniff" }]
    }
  ]
}
```

### `vite.config.ts`
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['framer-motion', '@radix-ui/react-dialog', 'lucide-react'],
          data: ['@tanstack/react-query', '@tanstack/react-table'],
          pdf: ['react-pdf'],
          charts: ['recharts'],
        },
      },
    },
  },
});
```

### Deploy steps
1. Push `nyaya-drishti-frontend/` to GitHub
2. Connect repo to Vercel
3. Set environment variable: `VITE_API_URL=https://nyaya-drishti-backend.onrender.com`
4. Deploy

### CORS requirement for backend
Backend must include Vercel frontend URL in `CORS_ALLOWED_ORIGINS`. Communicate the exact Vercel URL to Person B after first deploy.

---

## 17. Master Checklist

### Phase 1 — Foundation
- [ ] Vite + React + TypeScript scaffold
- [ ] Tailwind v4 + color tokens configured
- [ ] shadcn/ui initialized (dark, New York)
- [ ] All shadcn components installed
- [ ] `src/types/index.ts` — all interfaces from Section 5.1
- [ ] `src/lib/api.ts` — axios + JWT interceptors + mock flag
- [ ] `src/lib/mockData.ts` — all mock data
- [ ] `src/lib/utils.ts` — `riskColor`, `statusColor`, `formatDate`, `daysUntil`, `cn`
- [ ] `src/lib/queryClient.ts` — TanStack Query client
- [ ] `src/lib/queryKeys.ts` — canonical query key factory
- [ ] `src/lib/i18n.ts` — react-i18next setup
- [ ] `src/locales/en.json` + `kn.json`
- [ ] `GlassCard.tsx`, `LoadingSpinner.tsx`, `EmptyState.tsx`, `ErrorState.tsx`
- [ ] `ConfidenceBadge.tsx`, `StatusBadge.tsx`, `ServerWakeup.tsx`
- [ ] `AuthContext.tsx`, `ThemeContext.tsx`
- [ ] `PageShell.tsx`, `Sidebar.tsx`, `Header.tsx` (with language toggle)
- [ ] `ProtectedRoute.tsx`, `RoleRoute.tsx`
- [ ] `LoginPage.tsx`, `RegisterPage.tsx` (mock auth)
- [ ] Full routing in `App.tsx`

### Phase 2 — Core Pages
- [ ] `DashboardPage.tsx` + `StatCard`, `DeadlineHeatmap`, `RiskBoard`, `AppealCountdown`
- [ ] `CasesListPage.tsx` + `CaseTable` (TanStack Table), `PDFUpload`, `ProcessingStatus`
- [ ] `CaseDetailPage.tsx` + `SplitView`, `PDFViewer`
- [ ] `ActionPlanPage.tsx` + `ActionTimeline`, `DeadlineCard`, `CCMSStageMap`, `SimilarCases`
- [ ] `ReviewPage.tsx` + `FieldReview`, `DirectiveReview`, `CaseReview`, `ConflictAlert`
- [ ] `AnalyticsPage.tsx` + 6 Recharts components
- [ ] `NotificationsPage.tsx`
- [ ] All pages bilingual via i18n keys
- [ ] Dynamic content translation hook (`useTranslate`)
- [ ] Framer Motion staggered animations on all pages

### Phase 3 — Integration
- [ ] Auth checkpoint (Checkpoint 2)
- [ ] Cases + upload checkpoint (Checkpoint 3)
- [ ] Extraction display checkpoint (Checkpoint 4)
- [ ] Action plan checkpoint (Checkpoint 5)
- [ ] Review workflow checkpoint (Checkpoint 6)
- [ ] Dashboard data checkpoint (Checkpoint 7)
- [ ] Translation endpoint wired
- [ ] Skeleton loaders on all async data
- [ ] Error states + retry on all pages
- [ ] `ServerWakeup` banner wired to first API call
- [ ] Framer Motion page transitions with `AnimatePresence`
- [ ] Mobile responsive pass (375px, 768px, 1280px)
- [ ] `vercel.json` + `vite.config.ts` optimized
- [ ] Deployed to Vercel (Checkpoint 8)
- [ ] Full demo script tested end-to-end

---

> **Key reminder:** Communicate VITE_API_URL (Vercel URL) to Person B after first deploy so they can set `CORS_ALLOWED_ORIGINS` on Render. Use [cron-job.org](https://cron-job.org) to ping the Render backend every 14 min during the demo to prevent cold starts.
