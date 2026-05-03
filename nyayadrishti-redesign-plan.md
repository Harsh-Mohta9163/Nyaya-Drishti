# NyayaDrishti — Full UI Redesign Plan

> React + Tailwind CSS v4 · shadcn/ui · Framer Motion
> Target: modern, professional, clean — no glassmorphism, no clutter

---

## Table of Contents

1. [Design System Foundation](#1-design-system-foundation)
2. [Global Shell — Sidebar & Topbar](#2-global-shell--sidebar--topbar)
3. [Shared Component Overhaul](#3-shared-component-overhaul)
4. [Page-by-Page Redesign](#4-page-by-page-redesign)
   - [Dashboard](#41-dashboard--dashboardpagetsx)
   - [Cases List](#42-cases-list--caseslistpagetsx)
   - [Case Detail](#43-case-detail--casedetailpagetsx)
   - [Action Plan](#44-action-plan--actionplanpagetsx)
   - [Review Workflow](#45-review-workflow--reviewpagetsx)
   - [Analytics](#46-analytics--analyticspagetsx)
   - [Notifications](#47-notifications--notificationspagetsx)
   - [Login & Register](#48-login--register)
5. [Animation System](#5-animation-system)
6. [CSS Token Changes](#6-css-token-changes)
7. [Do's and Don'ts](#7-dos-and-donts)

---

## 1. Design System Foundation

### Surface Hierarchy

Three distinct surface levels create depth without shadows or blur:

| Level | Tailwind token | Usage |
|---|---|---|
| Page background | `bg-background` / `bg-[#f8f8f6]` | The canvas everything sits on |
| Panels & sidebar | `bg-muted` / `bg-secondary` | Secondary surfaces, sidebar, filter bars |
| Cards & topbar | `bg-card` / `bg-white` (dark: `bg-[#1e1e20]`) | Raised elements, stat cards, content panels |

**Rule:** Never use explicit `bg-slate-800` or `bg-[#0f172a]` on cards or panels. The current dark card-on-dark-bg pattern is the primary cause of the cluttered feeling. Cards should always feel one step lighter than their container.

### Color Semantics

Stop using raw Tailwind color classes directly on text and backgrounds. Map everything through semantic intent:

| Intent | Light mode | Dark mode | Use for |
|---|---|---|---|
| Info / primary action | `#185fa5` bg, `#e6f1fb` fill | `#85b7eb` bg, `#042c53` fill | Buttons, links, blue stat |
| Success / verified | `#3b6d11` bg, `#eaf3de` fill | `#97c459` bg, `#173404` fill | Verified status, green stat |
| Warning / medium risk | `#854f0b` bg, `#faeeda` fill | `#ef9f27` bg, `#412402` fill | Pending, medium risk badge |
| Danger / high risk | `#a32d2d` bg, `#fcebeb` fill | `#f09595` bg, `#501313` fill | High risk, deadline alerts |
| Processing | `#534ab7` bg, `#eeedfe` fill | `#afa9ec` bg, `#26215c` fill | Extraction in progress |

### Typography

**Two weights only: 400 and 500.** Remove all `font-semibold` (600) and `font-bold` (700) — they look heavy and dated at this scale.

| Role | Size | Weight | Usage |
|---|---|---|---|
| Page title | `text-[17px]` | 500 | Topbar title |
| Section heading | `text-sm` (14px) | 500 | Panel titles, card headers |
| Body | `text-sm` (14px) | 400 | Row content, descriptions |
| Label / secondary | `text-xs` (12px) | 400 | Muted labels, timestamps |
| Micro | `text-[10px]` | 500 | Badges, uppercase tags |

```css
/* Remove these — replace with font-medium (500) */
font-semibold → font-medium
font-bold → font-medium

/* Micro labels */
.badge-label {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
```

### Borders & Radius

```css
/* Default — almost invisible, just enough to define the edge */
border: 0.5px solid var(--border);          /* use everywhere */
border: 0.5px solid var(--border)/50;       /* between rows, dividers */

/* Emphasis — hover states, active panels */
border: 0.5px solid var(--border)/80;

/* Accent — featured card only (2px is the ONE exception) */
border: 2px solid blue-500/30;

/* Never use border-left accent bars */
/* Never use box-shadow for depth */
```

```css
/* Radius scale */
--radius-sm: 6px;   /* badges, pills */
--radius-md: 8px;   /* buttons, inputs, small cards */
--radius-lg: 12px;  /* panels, main cards */
--radius-xl: 16px;  /* modals, full-page cards (login) */
```

---

## 2. Global Shell — Sidebar & Topbar

### Sidebar (`Sidebar.tsx`)

**Current problems:** Active item uses a harsh blue `bg-blue-600` that dominates. Icon-only display on some states. User profile at bottom feels disconnected.

**Redesign:**

```
Width: 220px fixed
Background: bg-secondary (one level above page bg)
Right edge: 0.5px border

Brand area (top):
  - 28×28 blue icon tile (rounded-md, blue fill)
  - "NyayaDrishti" 15px/500
  - "CCMS Intelligence" 10px/400, uppercase, letter-spacing, muted
  - Bottom margin: 20px

Nav groups (labelled):
  - "Overview" label: 10px uppercase muted, 8px top padding
  - "Workflow" label: same
  - Items: 36px tall, 8px vertical padding, 16px horizontal
    - Icon 14px (opacity 0.5, active: 1.0)
    - Label 13px/400 (active: 500)
    - Active state: bg-card (white) on bg-secondary — NOT blue fill
    - Hover: bg-card/50
    - Margin: 1px 8px (so active card has breathing room)
  - Badges: small pill, bg-danger/10 text-danger for urgent counts
             bg-amber/10 text-amber for pending
             bg-muted text-muted-foreground for neutral

User footer (bottom):
  - 28px avatar circle with initials (bg-info/20, text-info)
  - Username 12px/500
  - Role + Department 10px muted
  - Border-top 0.5px
```

**Tailwind class changes in `Sidebar.tsx`:**

```tsx
// Active nav item — REMOVE:
className="bg-blue-600 text-white"

// REPLACE WITH:
className="bg-card text-foreground font-medium border border-border/30"

// Nav item base — REMOVE:
className="text-slate-400 hover:text-white hover:bg-slate-800"

// REPLACE WITH:
className="text-muted-foreground hover:bg-card/50 hover:text-foreground"
```

### Topbar (`Header.tsx`)

```
Height: 52px
Background: bg-card
Bottom border: 0.5px border-border

Left side:
  - Page title: 17px/500, text-foreground
  - Subtitle: 12px/400, text-muted-foreground
    e.g. "Welcome back, Priya · May 2026"

Right side (flex row, gap-8px):
  - Language toggle: "EN | ಕನ್ನಡ" — plain text buttons,
    active underline, no dropdown, no border
  - Date pill: "May 2026" — 12px, bg-secondary, rounded-md, px-3 py-1.5
  - Notification bell: 20px icon, relative badge dot
  - New Case button: bg-info/10 text-info border-info/20
    hover: bg-info/20 — NOT a full blue filled button
```

---

## 3. Shared Component Overhaul

### `StatCard.tsx`

**Current:** Huge numbers floating on a semi-dark card. Icon is oversized. Trend text is cramped.

**Redesign:**

```
Card: bg-card, border, rounded-lg, p-4
Layout: vertical stack

Row 1 (space-between):
  Left: 11px muted label
  Right: 28×28 icon tile (colored bg matching stat intent, icon in matching dark color)

Row 2: Stat number — 26px/500, text-foreground (colored only for warning/danger)

Row 3: Trend — 11px
  Up: text-green-600 (dark: text-green-400) "↑ 12 this month"
  Down: text-red-600 "↓ 3 since last week"
  Neutral: text-muted-foreground

Landscape variant (for 2-wide row):
  Left: label + number
  Right: trend badge (pill) + comparison sub-label
```

```tsx
// Icon tile — replace large size-8 icons with:
<div className="size-7 rounded-md bg-blue-500/10 flex items-center justify-center">
  <FileText size={14} className="text-blue-600 dark:text-blue-400" />
</div>

// Number — remove bold, reduce size:
<span className="text-[26px] font-medium tabular-nums">{value}</span>
```

### `StatusBadge.tsx`

```tsx
// Current uses bg colors that are too dark. New mapping:
const statusConfig = {
  uploaded:       { bg: 'bg-muted',          text: 'text-muted-foreground' },
  processing:     { bg: 'bg-purple-500/10',  text: 'text-purple-500',  dot: true },
  extracted:      { bg: 'bg-blue-500/10',    text: 'text-blue-500' },
  review_pending: { bg: 'bg-amber-500/10',   text: 'text-amber-500' },
  verified:       { bg: 'bg-green-500/10',   text: 'text-green-500' },
  action_created: { bg: 'bg-emerald-500/10', text: 'text-emerald-500' },
}

// Pill style:
className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wide"

// Animated dot for 'processing' only:
<span className="size-1.5 rounded-full bg-purple-500 animate-pulse" />
```

### `ConfidenceBadge.tsx`

```tsx
// Three-tier color — tighter thresholds:
// ≥ 0.90 → green (high confidence, trust it)
// 0.75–0.89 → amber (review recommended)
// < 0.75 → red (manual verification needed)

// Visual: thin horizontal bar + percentage text
<div className="flex items-center gap-2">
  <div className="h-1 w-16 rounded-full bg-muted overflow-hidden">
    <div className="h-full rounded-full bg-green-500" style={{ width: `${value * 100}%` }} />
  </div>
  <span className="text-[11px] font-medium text-green-600">{Math.round(value * 100)}%</span>
</div>
```

### `GlassCard.tsx`

**Drop the glassmorphism entirely.** Replace with clean flat card:

```tsx
// REMOVE: backdrop-filter, bg-slate-800/70, border-blue-500/20
// REPLACE WITH:
export default function GlassCard({ children, className, hover = false }) {
  return (
    <div className={cn(
      "bg-card border border-border rounded-lg",
      hover && "transition-all duration-200 hover:border-border/80 hover:shadow-sm",
      className
    )}>
      {children}
    </div>
  )
}
```

---

## 4. Page-by-Page Redesign

### 4.1 Dashboard — `DashboardPage.tsx`

**Layout:** vertical stack of rows, `space-y-4`

#### Row 1 — Four stat cards

```
grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4
```

| Card | Icon | Number color | Trend |
|---|---|---|---|
| Total Cases | FileText, blue | foreground | "↑ 12 this month" green |
| Pending Review | Clock, amber | amber-600 | "Requires attention" muted |
| High Risk | AlertTriangle, red | red-600 | "↑ 3 since last week" red |
| Deadlines (7d) | Calendar, green | green-600 | "Nearest: 2 days" muted |

#### Row 2 — Two wide stat cards

```
grid grid-cols-1 gap-4 sm:grid-cols-2
```

Landscape layout — number left, badge+comparison right.

#### Row 3 — Heatmap + Risk Board

```
grid grid-cols-1 gap-4 lg:grid-cols-2
```

**Heatmap panel:**
- Panel header: title left, toggle pills right (`7d / 30d / 90d`)
  - Pill: `px-2 py-0.5 rounded-md text-[11px]`
  - Active: `bg-card border border-border text-foreground font-medium`
  - Inactive: `text-muted-foreground hover:text-foreground`
- Day labels: `text-[9px] text-muted-foreground/60 text-center`
- Cells: `aspect-square rounded-[4px]` — small, ~32px
  - None: `bg-muted/50 text-muted-foreground/50`
  - Low: `bg-green-500/10 text-green-700`
  - Medium: `bg-amber-500/10 text-amber-700`
  - High: `bg-red-500/10 text-red-700`
  - Today: `bg-blue-600 text-white` (only solid fill in the grid)
- Legend: bottom row, 10px, colored dots

**Risk board panel:**
- Panel header: title + urgent badge (`bg-red-500/10 text-red-600 text-[10px]`)
- Each row (`flex items-center gap-3 px-4 py-3 border-b border-border/50`):
  - Left: countdown tile (36×36, rounded-md, colored bg)
    - Number: 15px/500
    - "days" label: 9px/400
    - 2d = red fill, 3d = amber fill, 5d+ = green fill
  - Middle: case number (12px/500) + party name (11px muted)
  - Right: CCMS stage (10px muted) + risk badge

#### Row 4 — Role-gated widgets

**Reviewer:** Verification queue (full-width white card)
- Each row: case number + court left, risk badge + review level right
- Hover = `bg-muted/30`

**Legal Advisor:** Appeal countdown (full-width card)
- Each deadline as a horizontal row with live countdown in large tabular numerals

#### Framer Motion for Dashboard

```tsx
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } }
}
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: [0.25, 0.8, 0.25, 1] } }
}

// Count-up on stat numbers
// Pulse animation class only for days_remaining <= 7:
className={cn("rounded-md", daysRemaining <= 7 && "animate-pulse")}
```

---

### 4.2 Cases List — `CasesListPage.tsx`

**Layout:** topbar → filter bar → upload zone → table

#### Upload zone

```
Compact strip, not a full-page dropszone:
- Height: 64px
- Border: 1.5px dashed border-border
- Rounded-lg
- Content: icon + label left, file size hint right
- Drag-over: border-blue-500 bg-blue-500/5
- Uploading: thin blue progress bar at the bottom edge of the zone
- DO NOT use a modal or overlay for progress — show it inline
```

#### Filter bar

```
Horizontal flex row, gap-2, mb-4:
  <input placeholder="Search cases..." className="flex-1 h-9 ..." />
  <Select placeholder="Status" className="w-[140px]" />
  <Select placeholder="Type" className="w-[120px]" />
  <Select placeholder="Risk" className="w-[120px]" />

Styling:
  - All inputs/selects: bg-card border-border h-9 rounded-md text-sm
  - No separate filter card wrapping them — just the row directly on bg-tertiary
```

#### Case table

```
Table container: bg-card border border-border rounded-lg overflow-hidden

Column headers: bg-muted/30 text-[11px] font-medium uppercase tracking-wide text-muted-foreground
  height: 36px, px-4

Column widths:
  Case Number  → 160px  sortable
  Court        → flex-1
  Type         → 80px   badge
  Date         → 110px  sortable
  Status       → 130px  badge
  Risk         → 100px  badge
  Days left    → 90px   colored number
  Actions      → 64px

Row styling:
  - height: 48px (NOT 56px — current is too tall)
  - px-4 border-b border-border/50
  - hover: bg-muted/20
  - Last row: no bottom border

Days left cell:
  - > 30:  text-muted-foreground (not urgent)
  - 8–30:  text-amber-600
  - ≤ 7:   text-red-600 font-medium animate-pulse
  - Overdue: "Overdue" badge bg-red-500/10 text-red-600

Pagination:
  - Below table, right-aligned
  - "Showing 1–20 of 142 cases" muted text left
  - Prev / Next buttons right: bg-card border rounded-md
  - Current page highlighted: bg-blue-500/10 text-blue-600
```

---

### 4.3 Case Detail — `CaseDetailPage.tsx`

**Layout:** Full-height split view

```
Main container: flex h-[calc(100vh-52px)] overflow-hidden

Left (50%):
  PDF viewer panel — bg-card border-r border-border
  - Toolbar strip (40px): page nav buttons, page X/Y label, zoom controls
    All in muted style — no colored toolbar
  - PDF canvas: takes remaining height, overflow-y-auto

Right (50%):
  Tabbed panel — bg-card
  - Tabs: "Extracted data" | "Action plan" | "Review history"
    - Tab bar: bg-muted/30 rounded-lg p-1 mx-4 mt-4
    - Active tab: bg-card rounded-md text-foreground font-medium
    - Inactive: text-muted-foreground
  - Content area: overflow-y-auto px-4 py-3
```

#### Extracted data tab

```
Header info section:
  - Two-column grid of key-value pairs (text-sm)
  - Labels: text-muted-foreground text-xs
  - Values: text-foreground text-sm
  - Separated by thin horizontal rule

Court directions section:
  Each direction = expandable card:
    Collapsed: direction type badge + first 80 chars of verbatim text + confidence badge
    Expanded: full verbatim text in mono font, source reference (page/para), responsible entity
    Border-left: 2px solid matching risk/type color, border-radius: 0 (no rounding on accent border)

Confidence badge:
  - Thin bar (h-1, w-14) + percentage
  - ≥90% green, 75–89% amber, <75% red
```

#### Review history tab

```
Timeline layout (vertical):
  Each log entry:
    - Connector line (1px, bg-muted)
    - Circle node (8px): green=approve, amber=edit, red=reject
    - Right: reviewer name (12px/500) + action badge + timestamp
    - If edit: show changed fields as key: old → new
    - If reject: show reason in italic muted text
```

#### Processing overlay

```
When status === 'processing', cover the right panel with:
  - Centered column: spinning icon + "Extracting judgment..." text
  - Status bar: uploaded → processing → extracted (3 steps, current highlighted blue)
  - "This usually takes 15–30 seconds" muted sub-text
  - DO NOT use a full-screen overlay — keep the PDF visible on the left
```

---

### 4.4 Action Plan — `ActionPlanPage.tsx`

**Layout:** single scrollable column, max-w-4xl mx-auto

#### Recommendation banner

```
Not a full-width harsh block — instead a clean card:

bg-card border-l-4 rounded-lg p-5
  border-l color: green-500 (Comply) or amber-500 (Appeal)

Left: "COMPLY" or "APPEAL" in 22px/500 colored text
      "Recommendation" in 11px muted uppercase
Right: Confidence bar + percentage + "Based on 4 similar cases" link

Remove: large colored block bg — replace with left accent border only
```

#### Action timeline

```
Vertical stepper in a white card:

Each step:
  - Left: step number circle (24px) — bg-muted for pending, bg-blue-500 for current, bg-green-500 for complete
  - Connector: 1px dashed line between circles (not solid — shows incompleteness)
  - Right of circle:
    - Action text (14px/500)
    - Department badge (muted bg, muted text)
    - Depends-on hint: "After step 1" in 11px muted, if depends_on not empty
    - Complete toggle: checkmark button (dept_officer role only)
  - Locked step: opacity-50

Line connecting circles: dashed 1px border-border
```

#### Deadline cards

```
Side-by-side (grid-cols-2):

Legal deadline card:
  bg-card border border-red-500/20 rounded-lg p-4
  - "Legal deadline" label (muted)
  - Date: 16px/500
  - Days remaining: large number (color-coded) + "days remaining" label
  - Statutory basis: 11px muted italic

Internal deadline card:
  Same but with amber border if < 7 days remaining
```

#### CCMS stage map

```
Horizontal stepper (not a flowchart — too complex):
  8 stages as pills in a horizontal scroll container
  Current stage: bg-blue-500/10 border-blue-500/30 text-blue-700 font-medium
  Past stages: bg-muted text-muted-foreground line-through
  Future stages: bg-card border-border text-muted-foreground
  
  Final branch (Comply / Appeal / Not to Appeal):
    Shown below the linear stepper as a small fork diagram
    Active branch: colored, others: muted
```

#### Similar cases panel

```
White card with table:
  Columns: Case, Outcome badge, Similarity bar, Summary
  Similarity: thin bar (h-1.5) in blue, percentage alongside

Summary sentence at top:
  "4 of 5 similar cases recommend compliance (avg. similarity 89%)"
  Style: text-sm text-muted-foreground, italic
```

---

### 4.5 Review Workflow — `ReviewPage.tsx`

**Layout:** 3-level tabs + content area

#### Tab bar

```
Horizontal tabs at top of page (NOT inside the topbar):
  Tab strip: bg-card border-b border-border px-6
  Tab items: 44px tall, 14px text
  Active: border-b-2 border-blue-500 text-foreground font-medium (no background fill)
  Locked (future levels): opacity-50 cursor-not-allowed
  
  Lock indicator: small lock icon (12px) next to locked tab label
  Progress: "2 of 3 levels complete" muted text right-aligned in tab bar
```

#### Field review (`FieldReview.tsx`)

```
Two-column layout (lg):
  Left (45%): field list
  Right (55%): PDF snippet + source reference

Field card:
  bg-card border rounded-lg p-4 mb-3
  - Field name: text-xs uppercase muted
  - AI value: text-sm/500 text-foreground
  - Confidence badge (inline bar + %)
  - Source snippet: text-xs font-mono bg-muted px-2 py-1 rounded text-muted-foreground
  - Action row: Approve | Edit | Reject
    - Approve: bg-green-500/10 text-green-700 hover:bg-green-500/20
    - Edit: bg-blue-500/10 text-blue-700 (opens inline input below)
    - Reject: bg-red-500/10 text-red-700

Edit mode (inline, no modal):
  Input replaces the value display
  Save / Cancel buttons below
  Conflict alert (if triggered): amber banner above the save button

Conflict alert:
  bg-amber-500/10 border border-amber-500/30 rounded-md p-3
  - Warning icon + description text
  - "Revert" and "Proceed anyway" buttons
```

#### Case sign-off (`CaseReview.tsx`)

```
Full summary view:
  - All verified fields in a read-only list (approved = green dot, edited = blue dot, rejected = red dot)
  - Complete action plan preview
  - Sign-off button: only visible to dept_head / legal_advisor
    Styling: w-full h-11 bg-blue-600 text-white rounded-lg
    NOT a ghost/outline button — this is the most important action on the page

Reject with reason dialog:
  Use shadcn Dialog
  - Textarea: "Reason for rejection" (required)
  - Cancel (ghost) + Reject (red solid) buttons
```

---

### 4.6 Analytics — `AnalyticsPage.tsx`

**Layout:** grid of chart cards

```
Date range selector (top-right):
  Segmented control: "30d | 90d | 12m"
  Style: bg-muted rounded-lg p-0.5
  Active: bg-card rounded-md font-medium

Chart grid:
  Row 1: grid-cols-2 gap-4
    - Cases over time (LineChart) — full width of left card
    - Risk distribution (PieChart or DonutChart)
  Row 2: grid-cols-2 gap-4
    - Department workload (BarChart horizontal)
    - Status funnel (BarChart horizontal)
  Row 3: grid-cols-2 gap-4
    - Extraction confidence over time (AreaChart)
    - Appeal vs Comply split (DonutChart)
```

#### Recharts styling

```tsx
// Consistent chart token usage:
const CHART_COLORS = {
  blue:   '#378add',
  green:  '#639922',
  amber:  '#ba7517',
  red:    '#e24b4a',
  purple: '#7f77dd',
  teal:   '#1d9e75',
}

// All charts:
<CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.4} />
<XAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
<YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
<Tooltip
  contentStyle={{
    background: 'var(--card)',
    border: '0.5px solid var(--border)',
    borderRadius: '8px',
    fontSize: '12px',
  }}
/>

// Chart card container:
<div className="bg-card border border-border rounded-lg p-4">
  <div className="text-sm font-medium text-foreground mb-1">Chart title</div>
  <div className="text-xs text-muted-foreground mb-4">Subtitle / context</div>
  <ResponsiveContainer width="100%" height={200}>
    ...
  </ResponsiveContainer>
</div>
```

---

### 4.7 Notifications — `NotificationsPage.tsx`

**Layout:** single column, max-w-2xl mx-auto

```
Top bar:
  "Notifications" title left
  "Mark all read" ghost button right (only shown if unread > 0)

Date group header:
  text-xs uppercase tracking-wide text-muted-foreground mt-6 mb-2
  e.g. "Today", "Yesterday", "May 1, 2026"

Notification row:
  bg-card border border-border rounded-lg p-4 mb-2
  Unread: border-l-2 border-l-blue-500 (2px left accent — rounds to 0 on this edge)
  Read: border-border/50, opacity slightly reduced

  Layout: icon-left, content-middle, timestamp-right

  Icons (20px, in colored circle 32px):
    deadline_warning → Clock in amber circle
    high_risk_alert  → AlertTriangle in red circle
    review_assigned  → ClipboardCheck in blue circle
    case_verified    → CheckCircle in green circle
    escalation       → ArrowUp in red circle

  Content:
    - Case number link (12px/500, text-blue-600, hover:underline)
    - Message text (13px text-foreground for unread, text-muted-foreground for read)

  Timestamp: text-xs text-muted-foreground, right-aligned

  Click: mark read + navigate to case (the entire row is clickable)
```

---

### 4.8 Login & Register

**Layout:** centered card on full-page bg

```
Page: min-h-screen bg-muted flex items-center justify-content-center

Card:
  bg-card border border-border rounded-xl p-8
  width: 400px (max-w-md w-full)

Brand row at top:
  Icon tile (32×32) + "NyayaDrishti" (18px/500) + "CCMS Intelligence" (11px muted)
  Center-aligned, mb-8

Form fields:
  Each field: label above (12px/500, mb-1.5) + input (h-10, full-width)
  Input focus: border-blue-500 ring-1 ring-blue-500/20
  Error: border-red-500 + error text below (11px red-600)

Role select (Register only):
  shadcn Select with role descriptions as subtitles:
  Each option shows role name + one-line description

Submit button:
  w-full h-11 bg-blue-600 text-white rounded-lg
  Loading: spinner inside button, disabled state

Bottom link:
  "Already have an account? Sign in" — text-sm text-muted-foreground, link in text-blue-600

Hint box (Login page only):
  bg-muted border border-border rounded-md p-3 text-xs text-muted-foreground
  "Demo: use any email / password from the mock data"
```

---

## 5. Animation System

All Framer Motion variants follow a single consistent pattern. Define once in `src/lib/animations.ts` and import everywhere.

```typescript
// src/lib/animations.ts

export const pageVariants = {
  hidden: { opacity: 0, y: 8 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.2, ease: [0.25, 0.8, 0.25, 1] }
  },
  exit: { opacity: 0, y: -4, transition: { duration: 0.15 } }
}

export const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.05 }
  }
}

export const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.25, ease: [0.25, 0.8, 0.25, 1] }
  }
}

export const slideInLeft = {
  hidden: { opacity: 0, x: -8 },
  show: { opacity: 1, x: 0, transition: { duration: 0.2 } }
}

// Count-up hook for stat numbers
export function useCountUp(target: number, duration = 800) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    const start = performance.now()
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out-cubic
      setCount(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target, duration])
  return count
}
```

### Animation assignment by component

| Component | Animation | Notes |
|---|---|---|
| Page mount | `pageVariants` fade+slide | Wrap each page's root div |
| Stat cards | `containerVariants` + `itemVariants` | stagger = 0.06 |
| Stat numbers | `useCountUp` hook | duration 800ms |
| Table rows | `slideInLeft` with `delay: index * 0.03` | Cap at 10 rows (no delay after) |
| Risk board rows | `slideInLeft` | Same |
| High-risk badge | `animate-pulse` | Only when `days_remaining <= 7` |
| Modal open | `AnimatePresence` scale 0.96→1 + fade | Use shadcn Dialog's built-in |
| Processing status | Step indicator progress animation | 500ms between steps |
| Page transitions | `AnimatePresence` in `App.tsx` | `mode="wait"` |

---

## 6. CSS Token Changes

Changes to make in `index.css` and your Tailwind config:

### Remove from `index.css`

```css
/* REMOVE — glassmorphism is gone */
.glass-card {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(16px);
  ...
}
.glass-card-hover:hover {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
  ...
}
```

### Replace with

```css
/* Clean flat card — the new default */
.panel-card {
  background: var(--card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
}

.panel-card-hover:hover {
  border-color: hsl(var(--border) / 0.8);
  transition: border-color 0.15s ease;
}
```

### Update CSS variables (`:root`)

```css
:root {
  /* Remove dark overrides at root level — let dark class handle it */
  --bg-primary: transparent;   /* no longer needed */
  --bg-card: transparent;      /* no longer needed */

  /* Keep these — they're used correctly */
  --radius: 0.75rem;
  --background: hsl(0 0% 98%);    /* slightly off-white, not pure white */
  --foreground: hsl(240 10% 3.9%);
  --card: hsl(0 0% 100%);
  --muted: hsl(240 4.8% 95.9%);
  --border: hsl(240 5.9% 90%);
}

.dark {
  --background: hsl(240 10% 5%);   /* slightly lighter than current #0f172a */
  --card: hsl(240 8% 8%);          /* cards clearly distinct from bg */
  --muted: hsl(240 6% 13%);
  --border: hsl(240 5% 18%);       /* more visible in dark mode */
}
```

### `riskColor` utility — update in `utils.ts`

```typescript
// Replace the current riskColor map with lighter, less harsh fills:
export const riskColor: Record<ContemptRisk, string> = {
  High:   'text-red-600 bg-red-500/10 border border-red-500/20 dark:text-red-400',
  Medium: 'text-amber-600 bg-amber-500/10 border border-amber-500/20 dark:text-amber-400',
  Low:    'text-green-600 bg-green-500/10 border border-green-500/20 dark:text-green-400',
}

export const statusColor: Record<CaseStatus, string> = {
  uploaded:       'text-slate-500 bg-muted',
  processing:     'text-purple-600 bg-purple-500/10 dark:text-purple-400',
  extracted:      'text-blue-600 bg-blue-500/10 dark:text-blue-400',
  review_pending: 'text-amber-600 bg-amber-500/10 dark:text-amber-400',
  verified:       'text-green-600 bg-green-500/10 dark:text-green-400',
  action_created: 'text-emerald-600 bg-emerald-500/10 dark:text-emerald-400',
}
```

---

## 7. Do's and Don'ts

### Spacing

| Do | Don't |
|---|---|
| `p-4` (16px) for card content | `p-8` for card content — too loose |
| `gap-4` between rows | `gap-6` between stat cards |
| `space-y-4` in page content | `space-y-8` — creates visual disconnection |
| 48px table rows | 56–64px table rows |

### Color

| Do | Don't |
|---|---|
| `bg-red-500/10 text-red-600` for danger badges | `bg-red-500 text-white` — too loud |
| `font-medium` (500) for headings | `font-bold` (700) anywhere |
| Muted labels + colored numbers | Colored backgrounds on stat cards |
| `border-l-2` accent (no radius) for unread items | `border-l-4` with `rounded-lg` — can't have both |

### Layout

| Do | Don't |
|---|---|
| Sticky topbar, scrollable content | Fixed sidebar + fixed topbar + scrollable middle |
| Table inside a card with overflow-hidden | Table floating directly on page bg |
| Inline filter bar on same line | Filter bar in its own card |
| Compact upload strip | Full-screen drop zone overlay |

### Animations

| Do | Don't |
|---|---|
| `y: 12→0` entrance | `y: 20→0` — too dramatic |
| `duration: 0.2–0.25s` | `duration: 0.5s+` — feels slow |
| `staggerChildren: 0.06` | `staggerChildren: 0.1+` — cards pop in too slowly |
| `animate-pulse` only on urgent items | `animate-pulse` on all badges |
| Count-up on initial mount only | Count-up on every re-render |

---

*Last updated: May 2026 · NyayaDrishti Frontend Redesign v1.0*
