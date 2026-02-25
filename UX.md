# UX.md — Weaverbit Cite Design System

## Design Philosophy

**One sentence:** Weaverbit Cite should feel like a $100M-funded product that a world-class design team spent 6 months refining — not something an AI generated over a weekend.

**Core Principles:**
- **Polished trust** — Every pixel communicates "your data is safe here." Inspired by Stripe's obsessive attention to typography, spacing, and color harmony.
- **Quiet confidence** — No flashy gimmicks. The product speaks through craftsmanship: perfect alignment, consistent rhythm, intentional motion.
- **Functional beauty** — Every visual choice serves usability. Nothing is decorative-only.

**Anti-patterns (NEVER do these):**
- Generic AI aesthetics: purple gradients, Inter font, card grids with drop shadows
- Cookie-cutter SaaS templates: Bootstrap-looking sidebars, default shadcn/ui out-of-the-box
- Busy dashboards: cramming stats/charts where they don't belong
- Gratuitous animations: bouncing elements, spinning loaders, confetti

---

## Brand Identity

### Logo & Wordmark

- **Wordmark:** "Cite" in the display font (Instrument Serif), with "by Weaverbit" in the body font beneath it in a smaller, lighter weight
- **Icon mark:** A minimal quotation mark « » abstracted into two overlapping angular brackets — representing both citations and code
- **Usage:** Wordmark in sidebar header. Icon mark as favicon and mobile icon.

### Brand Voice (Microcopy)

- Professional but warm. Never robotic, never overly casual.
- Examples:
  - Empty state: "No documents yet. Upload your first file to get started." (NOT: "Looks like it's empty in here! 🎉")
  - Error: "We couldn't process this file. Try uploading a PDF or text file under 50MB." (NOT: "Oops! Something went wrong.")
  - Loading: "Preparing your knowledge base..." (NOT: "Hang tight!")
  - Success: "Document processed. 847 sections indexed." (NOT: "Awesome! You're all set! 🚀")

---

## Color System

### Philosophy

Inspired by Stripe's perceptually uniform color system. Colors are chosen for accessibility (WCAG 2.1 AA minimum), vibrancy without harshness, and consistent visual weight across hues.

### Light Theme (Default)

```css
:root[data-theme="light"] {
  /* ─── Backgrounds ─── */
  --bg-primary:          #FFFFFF;          /* Main content area */
  --bg-secondary:        #F7F8FA;          /* Sidebar, cards, offset sections */
  --bg-tertiary:         #EEF0F4;          /* Hover states, active selections */
  --bg-elevated:         #FFFFFF;          /* Modals, dialogs, dropdowns */
  --bg-overlay:          rgba(15, 23, 42, 0.6);  /* Backdrop behind modals */

  /* ─── Borders ─── */
  --border-primary:      #E2E5EB;          /* Card borders, dividers */
  --border-secondary:    #D0D4DB;          /* Input borders */
  --border-focus:        #4F6BF5;          /* Focus rings */

  /* ─── Text ─── */
  --text-primary:        #0F1729;          /* Headings, primary content — near-black, NOT pure #000 */
  --text-secondary:      #4A5568;          /* Descriptions, metadata */
  --text-tertiary:       #8892A4;          /* Placeholders, timestamps */
  --text-inverse:        #FFFFFF;          /* Text on colored backgrounds */

  /* ─── Brand / Accent ─── */
  --accent-primary:      #4F6BF5;          /* Primary buttons, links, active states */
  --accent-primary-hover:#3B54D4;          /* Darker on hover */
  --accent-primary-light:#EEF1FE;          /* Light tint for badges, tags, subtle highlights */
  --accent-primary-ghost:rgba(79, 107, 245, 0.08); /* Ghost button backgrounds */

  /* ─── Semantic Colors ─── */
  --color-success:       #16A34A;          /* Document ready, success toasts */
  --color-success-light: #ECFDF5;
  --color-warning:       #D97706;          /* Processing, caution */
  --color-warning-light: #FFFBEB;
  --color-error:         #DC2626;          /* Failed, destructive actions */
  --color-error-light:   #FEF2F2;
  --color-info:          #4F6BF5;          /* Informational, same as accent */
  --color-info-light:    #EEF1FE;

  /* ─── Chat-specific ─── */
  --chat-user-bg:        #4F6BF5;          /* User message bubble */
  --chat-user-text:      #FFFFFF;
  --chat-assistant-bg:   #F7F8FA;          /* Assistant message bubble */
  --chat-assistant-text:  #0F1729;
  --chat-citation-bg:    #EEF1FE;          /* Citation chip background */
  --chat-citation-text:  #3B54D4;

  /* ─── Shadows ─── */
  --shadow-sm:           0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md:           0 2px 8px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-lg:           0 8px 24px rgba(15, 23, 42, 0.08), 0 2px 8px rgba(15, 23, 42, 0.04);
  --shadow-xl:           0 16px 48px rgba(15, 23, 42, 0.10), 0 4px 12px rgba(15, 23, 42, 0.06);
  --shadow-focus:        0 0 0 3px rgba(79, 107, 245, 0.25);   /* Focus ring shadow */
  --shadow-input:        0 1px 2px rgba(15, 23, 42, 0.05);     /* Resting input shadow */
}
```

### Dark Theme

```css
:root[data-theme="dark"] {
  /* ─── Backgrounds ─── */
  --bg-primary:          #0B0F1A;          /* Main content — deep navy-black, NOT pure #000 */
  --bg-secondary:        #111827;          /* Sidebar, cards */
  --bg-tertiary:         #1A2235;          /* Hover, active selections */
  --bg-elevated:         #1E293B;          /* Modals, dialogs, dropdowns */
  --bg-overlay:          rgba(0, 0, 0, 0.7);

  /* ─── Borders ─── */
  --border-primary:      #1E293B;
  --border-secondary:    #2D3A4F;
  --border-focus:        #6B83F7;

  /* ─── Text ─── */
  --text-primary:        #F1F5F9;          /* NOT pure #FFF — slightly warm */
  --text-secondary:      #94A3B8;
  --text-tertiary:       #64748B;
  --text-inverse:        #0F1729;

  /* ─── Brand / Accent ─── */
  --accent-primary:      #6B83F7;          /* Slightly lighter indigo for dark backgrounds */
  --accent-primary-hover:#8599FA;
  --accent-primary-light:#1A2247;
  --accent-primary-ghost:rgba(107, 131, 247, 0.12);

  /* ─── Semantic Colors ─── */
  --color-success:       #22C55E;
  --color-success-light: #0D2818;
  --color-warning:       #FBBF24;
  --color-warning-light: #2D2308;
  --color-error:         #EF4444;
  --color-error-light:   #2D1010;
  --color-info:          #6B83F7;
  --color-info-light:    #1A2247;

  /* ─── Chat-specific ─── */
  --chat-user-bg:        #4F6BF5;
  --chat-user-text:      #FFFFFF;
  --chat-assistant-bg:   #1A2235;
  --chat-assistant-text:  #F1F5F9;
  --chat-citation-bg:    #1A2247;
  --chat-citation-text:  #8599FA;

  /* ─── Shadows (dark mode uses lighter, more diffused glows) ─── */
  --shadow-sm:           0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md:           0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-lg:           0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-xl:           0 16px 48px rgba(0, 0, 0, 0.6);
  --shadow-focus:        0 0 0 3px rgba(107, 131, 247, 0.3);
  --shadow-input:        0 1px 2px rgba(0, 0, 0, 0.2);
}
```

### Theme Toggle Implementation

```
- Store preference in localStorage: "cite-theme" = "light" | "dark" | "system"
- Default: "system" (follow OS preference via prefers-color-scheme)
- Apply theme via data-theme attribute on <html> element
- Toggle component: A pill switch in the sidebar footer — sun/moon icons, smooth slide animation
- Transition: All color changes use transition: background-color 200ms ease, color 200ms ease, border-color 200ms ease
- CRITICAL: No flash of wrong theme on page load — read localStorage before first paint (inline <script> in index.html)
```

---

## Typography

### Font Stack

```css
/* ─── Display / Headlines ─── */
--font-display: 'Instrument Serif', Georgia, 'Times New Roman', serif;

/* ─── Body / UI ─── */
--font-body: 'General Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* ─── Code / Monospace (for source citations, technical content) ─── */
--font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
```

**Font loading strategy:**
- Load via Google Fonts or Fontsource (self-hosted preferred for performance)
- `font-display: swap` on all web fonts
- Preload the body font (General Sans) in `<head>` for zero layout shift

### Type Scale

Using a **1.250 (Major Third)** scale for harmonious, non-generic sizing:

```
--text-xs:      0.75rem    / 12px    — Timestamps, badges, fine print
--text-sm:      0.875rem   / 14px    — Secondary text, metadata, table cells
--text-base:    1rem       / 16px    — Body text, chat messages, inputs
--text-lg:      1.125rem   / 18px    — Subheadings, emphasized content
--text-xl:      1.25rem    / 20px    — Card titles, section headers
--text-2xl:     1.5rem     / 24px    — Page titles within the app
--text-3xl:     1.875rem   / 30px    — Landing page subheadlines
--text-4xl:     2.25rem    / 36px    — Landing page headlines (mobile)
--text-5xl:     3rem       / 48px    — Landing page hero text (desktop)
--text-6xl:     3.75rem    / 60px    — Landing page hero text (large screens)
```

### Font Weights

```
--font-light:      300    — Rarely used; only for oversized display text
--font-regular:    400    — Body text, descriptions
--font-medium:     500    — UI labels, nav items, emphasis within body text
--font-semibold:   600    — Card titles, subheadings, button text
--font-bold:       700    — Page titles, hero headlines only
```

### Line Heights

```
--leading-tight:   1.2    — Headlines, display text
--leading-snug:    1.35   — Card titles, subheadings
--leading-normal:  1.6    — Body text, chat messages
--leading-relaxed: 1.75   — Long-form reading (landing page paragraphs)
```

### Letter Spacing

```
--tracking-tight:  -0.02em  — Display text (Instrument Serif, large sizes)
--tracking-normal: 0        — Body text
--tracking-wide:   0.02em   — Uppercase labels, badges, smallest text
--tracking-wider:  0.05em   — Overline labels (e.g., "KNOWLEDGE BASE")
```

### Typography Rules

- **NEVER** use uppercase for anything longer than 2-3 words
- Use uppercase ONLY for: overline labels, status badges, tiny category tags
- Headlines use `Instrument Serif` — everything else uses `General Sans`
- Chat messages ALWAYS at `--text-base` (16px) — readability is non-negotiable
- Source citations use `--font-mono` at `--text-sm`
- **Maximum line length:** 72ch for body text, 48ch for headings

---

## Spacing System

Using an **8px base grid** (Stripe's approach):

```
--space-0:    0
--space-1:    4px       — Inline padding, tight gaps
--space-2:    8px       — Between icon and label, between badge items
--space-3:    12px      — Internal card padding (compact), input padding
--space-4:    16px      — Standard internal padding, between form fields
--space-5:    20px      — Between cards in a list
--space-6:    24px      — Section padding inside pages
--space-8:    32px      — Between sections
--space-10:   40px      — Page-level top/bottom padding
--space-12:   48px      — Between major page sections
--space-16:   64px      — Landing page section spacing
--space-20:   80px      — Landing page hero padding
--space-24:   96px      — Landing page section spacing (large)
```

### Key Spacing Rules

- **Sidebar width:** 260px (collapsed: 64px)
- **Max content width:** 1200px (centered with auto margins)
- **Chat message max-width:** 680px (like Stripe's docs — readable, not stretched)
- **Card padding:** 24px on desktop, 16px on mobile
- **Button padding:** 10px 20px (default), 8px 16px (small), 14px 28px (large)
- **Input padding:** 10px 14px with 12px border-radius
- **Gap between sidebar items:** 2px (tight, like Linear)
- **Gap between chat messages:** 16px (user-to-assistant), 4px (same sender)

---

## Border Radius

```
--radius-sm:     6px      — Badges, tags, small chips
--radius-md:     8px      — Inputs, buttons, cards (THIS IS THE DEFAULT)
--radius-lg:     12px     — Dialogs, modals, larger cards
--radius-xl:     16px     — Chat bubbles, landing page feature cards
--radius-full:   9999px   — Avatar circles, pill buttons, toggle switches
```

**Rules:**
- Every interactive element has SOME border radius — no sharp 0px corners anywhere
- Nested elements have smaller radius than their parent (visual hierarchy)
- Chat bubbles: 16px on three corners, 4px on the corner closest to the sender (like iMessage but subtler)

---

## Component Specifications

### Sidebar (Left Navigation)

```
LAYOUT:
├── Logo area (Cite wordmark + icon) — 60px height
├── Navigation items
│   ├── Dashboard (icon + label)
│   ├── Knowledge Bases section
│   │   ├── KB 1 (name, doc count badge)
│   │   ├── KB 2
│   │   └── "+ New" button
│   └── Settings
├── Spacer (flex-grow)
├── Theme toggle (sun/moon pill)
└── User area (avatar circle + name + logout)
```

**Styling:**
- Background: `--bg-secondary`
- Border-right: 1px `--border-primary`
- Nav items: 36px height, 8px border-radius, 8px horizontal padding
- Active item: `--accent-primary-ghost` background, `--accent-primary` text, 2px left accent bar
- Hover: `--bg-tertiary` background
- Icons: 18px, stroke-width 1.75, using Lucide icons
- Transition on hover/active: `background-color 150ms ease`
- Collapse behavior: On screens < 1024px, sidebar collapses to 64px (icons only) with a hamburger toggle

### Top Header Bar (within main content area)

```
LAYOUT:
├── Page title (left-aligned) — "Documents" or "Chat" or KB name
├── Breadcrumb trail (on deeper pages)
├── Spacer
└── Action buttons (right-aligned) — "Upload Document", etc.
```

**Styling:**
- Height: 64px
- Background: `--bg-primary` with 1px bottom border `--border-primary`
- Sticky (position: sticky, top: 0, z-index: 10)
- Slight backdrop blur on scroll: `backdrop-filter: blur(8px)` with semi-transparent bg
- Page title: `--text-xl`, `--font-semibold`

### Cards (Knowledge Base Cards, Document Cards)

```
ANATOMY:
┌─────────────────────────────────────┐
│  Icon/Emoji     Title        Status │
│                                     │
│  Description text (2 lines max)     │
│                                     │
│  Metadata: 12 docs · Created Jan 5  │
└─────────────────────────────────────┘
```

**Styling:**
- Background: `--bg-primary` (light) or `--bg-secondary` (dark)
- Border: 1px `--border-primary`
- Shadow: `--shadow-sm` resting → `--shadow-md` on hover
- Border-radius: `--radius-md` (8px)
- Padding: 24px
- Hover: border transitions to `--border-secondary`, shadow lifts, subtle translateY(-1px)
- Transition: `all 200ms cubic-bezier(0.4, 0, 0.2, 1)` — Stripe's easing curve
- Status badge in top-right: small pill with semantic color
- CRITICAL: Cards are NOT clickable divs — they contain a stretch-link `<a>` for accessibility

### Buttons

**Variants:**

```
1. Primary (filled):
   bg: --accent-primary
   text: white
   hover: --accent-primary-hover
   shadow: --shadow-sm → --shadow-md on hover
   active: scale(0.98) — tiny press-down effect

2. Secondary (outlined):
   bg: transparent
   border: 1px --border-secondary
   text: --text-primary
   hover: bg --bg-tertiary

3. Ghost (text-only):
   bg: transparent
   text: --accent-primary
   hover: bg --accent-primary-ghost

4. Destructive:
   bg: --color-error
   text: white
   hover: darker red

5. Icon-only:
   44px × 44px touch target (accessibility minimum)
   8px border-radius
   Hover: --bg-tertiary
```

**All buttons:**
- Font: `--font-semibold`, `--text-sm` (14px)
- Height: 40px (default), 36px (small), 48px (large)
- Border-radius: `--radius-md`
- Transition: `all 150ms ease`
- Disabled: opacity 0.5, cursor not-allowed
- Loading state: text replaced by a subtle spinner (not the whole button — just the text swaps)
- NEVER use raw `<button>` without these styles applied

### Inputs

**Styling:**
- Height: 44px
- Background: `--bg-primary`
- Border: 1px `--border-secondary`
- Shadow: `--shadow-input`
- Border-radius: `--radius-md`
- Padding: 10px 14px
- Font: `--text-base`, `--font-regular`
- Placeholder: `--text-tertiary`
- Focus: border `--border-focus`, shadow `--shadow-focus`
- Error: border `--color-error`, shadow `0 0 0 3px rgba(220, 38, 38, 0.15)`
- Transition: `border-color 200ms ease, box-shadow 200ms ease`
- Label: above input, `--text-sm`, `--font-medium`, `--text-secondary`, 6px margin-bottom
- Help text: below input, `--text-xs`, `--text-tertiary`, 4px margin-top

### Dialogs / Modals

- Centered on screen with `--bg-overlay` backdrop
- Background: `--bg-elevated`
- Border-radius: `--radius-lg` (12px)
- Shadow: `--shadow-xl`
- Max-width: 480px (small), 640px (medium), 800px (large)
- Padding: 32px
- Enter animation: fade in backdrop (200ms) + dialog scales from 0.95 to 1.0 with opacity (200ms, cubic-bezier(0.4, 0, 0.2, 1))
- Exit: reverse, 150ms
- Close on backdrop click + Escape key
- Focus trap inside dialog (accessibility)

### Toast Notifications

- Position: bottom-right, 24px from edges
- Background: `--bg-elevated` with `--shadow-lg`
- Border-radius: `--radius-md`
- Left accent bar: 3px wide, colored by type (success/error/warning/info)
- Enter: slide up 16px + fade in (300ms, ease-out)
- Exit: slide right 32px + fade out (200ms)
- Auto-dismiss: 5 seconds (success/info), persistent (error/warning)
- Stack: newest on bottom, max 3 visible, older ones slide up

---

## Chat Interface (THE MOST IMPORTANT SCREEN)

This is what Upwork clients will judge you on. It must feel as premium as ChatGPT or Intercom, but with a distinct Cite identity.

### Layout

```
┌─────────────────────────────────────────────────────┐
│  HEADER: KB Name · "4 documents indexed"    [⋮ menu]│
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Welcome message / empty state               │   │
│  │  "Ask anything about your documents"         │   │
│  │                                              │   │
│  │  Suggestion chips:                           │   │
│  │  [Summarize key points] [What are the...]    │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──── USER MESSAGE ────────────────────────────┐   │
│  │ What are the key terms in the agreement?     │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──── ASSISTANT MESSAGE ───────────────────────┐   │
│  │ Based on the uploaded documents, the key     │   │
│  │ terms include:                               │   │
│  │                                              │   │
│  │ The agreement specifies a 24-month term...   │   │
│  │                                              │   │
│  │ ┌─ Sources ──────────────────────────────┐   │   │
│  │ │ 📄 Agreement.pdf · Section 3          │   │   │
│  │ │ 📄 Agreement.pdf · Section 7          │   │   │
│  │ └────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────── ⮐ ┐  │
│  │  Ask a question about your documents...       │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Chat Message Bubbles

**User message:**
- Align: right
- Background: `--chat-user-bg` (brand indigo)
- Text: `--chat-user-text` (white)
- Border-radius: 16px 16px 4px 16px (flat bottom-right — indicates sender)
- Max-width: 75% of chat container
- Padding: 12px 16px
- Font: `--text-base`, `--font-regular`
- Slight shadow: `--shadow-sm`

**Assistant message:**
- Align: left
- Background: `--chat-assistant-bg`
- Text: `--chat-assistant-text`
- Border-radius: 16px 16px 16px 4px (flat bottom-left)
- Max-width: 85% of chat container (wider — AI responses are longer)
- Padding: 16px 20px
- Border: 1px `--border-primary`
- NO shadow (flatter = feels like content, not a floating card)

**Streaming animation:**
- Tokens appear with a subtle fade-in (opacity 0→1, 100ms)
- Cursor: blinking block cursor after last token (like a terminal) — `|` in `--accent-primary` color, blinking at 1s interval
- When streaming completes: cursor disappears, sources slide in from below (200ms, ease-out)

### Source Citations (Within Chat)

```
┌───────────────────────────────────────────┐
│  📄 Agreement.pdf · Section 3, Page 2     │
│  "...the term shall commence on the..."   │
└───────────────────────────────────────────┘
```

- Background: `--chat-citation-bg`
- Text: `--chat-citation-text`
- Border-radius: `--radius-sm` (6px)
- Border-left: 3px solid `--accent-primary`
- Padding: 10px 14px
- Font for quote: `--font-mono`, `--text-sm`, italic
- Hover: border-left-color darkens, background slightly darker, cursor pointer
- Click: opens a slide-over panel showing the full source chunk with surrounding context highlighted
- Icon: Lucide `FileText` icon, 14px
- Enter animation: staggered slide-up (each citation 50ms after the previous)

### Chat Input Area

- Background: `--bg-primary`
- Border-top: 1px `--border-primary`
- Padding: 16px 24px
- Input itself:
  - Textarea (auto-expanding, min 1 row, max 6 rows)
  - Background: `--bg-secondary`
  - Border: 1px `--border-secondary`
  - Border-radius: `--radius-lg` (12px) — pill-like, modern
  - Padding: 12px 48px 12px 16px (right padding for send button)
  - Shadow: `--shadow-input`
  - Focus: `--border-focus` + `--shadow-focus`
  - Placeholder: "Ask a question about your documents..."
- Send button:
  - Positioned inside the input, bottom-right
  - 36px circle, `--accent-primary` background
  - White arrow-up icon (Lucide `ArrowUp`)
  - Disabled when input is empty (opacity 0.4)
  - Hover: `--accent-primary-hover`
  - Active: scale(0.92)
  - Transition: `all 150ms ease`
- Keyboard: Enter sends, Shift+Enter new line

### Suggestion Chips (Empty State)

- Displayed when conversation is empty
- 3-4 contextual suggestions based on uploaded document names
- Pill-shaped: `--radius-full`, border 1px `--border-secondary`
- Background: transparent → `--bg-tertiary` on hover
- Font: `--text-sm`, `--font-medium`
- Click: auto-fills the input and sends
- Staggered fade-in animation on appear (each chip 100ms delay)

### Thinking / Processing State

- When waiting for first token after sending:
- Show three pulsing dots in a minimal assistant bubble
- Dots: 6px circles, `--text-tertiary`, pulsing opacity 0.3 → 1.0 in sequence
- Animation: each dot 200ms offset, total cycle 1.2s
- DO NOT use a spinner. DO NOT use "thinking..." text. Just dots.

---

## Document Upload Interface

### Drag-and-Drop Zone

```
┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐
│                                                 │
│         ↑  Upload icon (Lucide Upload)          │
│                                                 │
│    Drop files here, or click to browse          │
│    Supports PDF, TXT, MD · Max 50MB             │
│                                                 │
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘
```

- Border: 2px dashed `--border-secondary`
- Border-radius: `--radius-lg`
- Background: `--bg-secondary`
- Padding: 48px (generous whitespace)
- Text: centered, `--text-secondary`
- **Drag active state:** border-color `--accent-primary`, background `--accent-primary-ghost`, scale(1.01)
- Transition: `all 200ms ease`
- Icon: 32px, `--text-tertiary`, transitions to `--accent-primary` on drag

### Document Processing Status

Each document in the list shows a progress indicator:

```
┌───────────────────────────────────────────────┐
│  📄 Agreement.pdf               Processing ⟳  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  68% · 847 sections   │
└───────────────────────────────────────────────┘
```

- **Uploading:** Blue indeterminate progress bar, pulsing
- **Processing:** Blue determinate bar with percentage + section count
- **Ready:** Green dot + "Ready · 847 sections"
- **Failed:** Red dot + error message + "Retry" button
- Progress bar: 3px height, `--radius-full`, smooth width transition (300ms)
- Status dots: 8px circles with subtle pulse animation on Processing
- Row hover: show delete icon (trash) on far right, `--text-tertiary` → `--color-error` on hover

---

## Landing Page (cite.weaverbit.com)

This is the first thing a potential Upwork client sees. It must feel like a VC-backed product, not a side project.

### Hero Section

```
LAYOUT:
┌─────────────────────────────────────────────────────┐
│  Nav: Logo (left) · Login | Get Started (right)     │
│                                                     │
│                                                     │
│        Your documents,                              │
│        instantly searchable.                        │
│                                                     │
│        AI-powered answers with source               │
│        citations from your uploaded files.           │
│                                                     │
│        [Get Started Free]  [See How It Works ↓]     │
│                                                     │
│        ┌─────────────────────────────────────┐      │
│        │  (Product screenshot / demo mock)   │      │
│        │  Showing the chat interface in       │      │
│        │  action with a real-looking convo    │      │
│        └─────────────────────────────────────┘      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Styling:**
- Headline: `Instrument Serif`, `--text-5xl` (desktop), `--font-bold`, `--tracking-tight`
- Subheadline: `General Sans`, `--text-lg`, `--text-secondary`, `--leading-relaxed`, max-width 540px
- CTA button: Primary, large size (48px height, 28px horizontal padding)
- Secondary link: Ghost button with downward arrow
- Background: `--bg-primary` with a **very subtle gradient mesh** — barely visible radial gradient of `--accent-primary` at 3-5% opacity in the top-right region
- Product screenshot: wrapped in a `--bg-secondary` container with `--shadow-xl`, `--radius-lg`, and a 1px `--border-primary` — looks like a macOS window
- The screenshot should show the DARK theme version of the chat (more visually striking)

### Navigation Bar (Landing Page)

- Transparent background, turns solid `--bg-primary` with `--shadow-sm` on scroll past 80px
- Height: 72px
- Logo left, nav links center (Features, How It Works, Pricing if applicable), CTA right
- Sticky: position fixed, top 0
- Blur on scroll: `backdrop-filter: blur(12px)`
- Transition: `background-color 300ms ease, box-shadow 300ms ease`

### "How It Works" Section

Three columns, numbered 01 / 02 / 03:

```
  01                    02                    03
  Upload               Ask                  Get Answers
  your documents       anything             with citations

  Drag and drop PDFs   Type a natural       Every answer links
  and text files.      language question.    back to the source.
  We handle the rest.                       Verify in one click.
```

- Number: `--accent-primary`, `--font-mono`, `--text-4xl`, `--font-bold`, low opacity (0.15) — big, faded background number
- Title: `--text-xl`, `--font-semibold`
- Description: `--text-base`, `--text-secondary`, max-width 320px
- Below each: a small, tasteful icon or illustration
- Column gap: `--space-12`
- Section padding: `--space-24` top and bottom

### Features Section

Two-column layout alternating image + text:

```
┌───────────────────────────────────────────────────┐
│                                                   │
│  ┌─────────────┐   Source Citations               │
│  │             │   Every answer cites the exact    │
│  │  Feature    │   document and section it came    │
│  │  Screenshot │   from. No hallucinations.        │
│  │             │                                   │
│  └─────────────┘   No guessing. No blind trust.   │
│                                                   │
├───────────────────────────────────────────────────┤
│                                                   │
│  Embeddable Widget   ┌─────────────┐              │
│  Add an AI assistant │             │              │
│  to your website     │  Widget     │              │
│  with one line of    │  Preview    │              │
│  code.               │             │              │
│                      └─────────────┘              │
│                                                   │
└───────────────────────────────────────────────────┘
```

- Feature screenshots in `--bg-secondary` containers with `--shadow-lg`
- Alternate left/right layout
- Scroll-triggered entrance: each section fades in + slides up 24px as it enters viewport (IntersectionObserver + CSS transition, 500ms, ease-out)
- Section padding: `--space-20`

### Footer

- Simple, minimal
- Logo + "Built by Weaverbit" text
- Links: Privacy, Terms, Contact
- Background: `--bg-secondary`
- Border-top: 1px `--border-primary`
- Padding: `--space-12` vertical

---

## Animation & Motion Specification

### Core Easing Functions

```css
--ease-default:    cubic-bezier(0.4, 0, 0.2, 1);    /* Stripe's standard — smooth deceleration */
--ease-in:         cubic-bezier(0.4, 0, 1, 1);       /* Elements entering */
--ease-out:        cubic-bezier(0, 0, 0.2, 1);       /* Elements exiting */
--ease-bounce:     cubic-bezier(0.34, 1.56, 0.64, 1);/* Subtle overshoot for delightful moments */
```

### Duration Standards

```
--duration-instant:  100ms   — Button active states, toggles
--duration-fast:     150ms   — Hover states, focus rings
--duration-normal:   200ms   — Most transitions (background, color, border)
--duration-smooth:   300ms   — Content reveals, slide-ins
--duration-slow:     500ms   — Page-level transitions, landing page scroll reveals
```

### Specific Animations

| Element | Trigger | Animation | Duration | Easing |
|---------|---------|-----------|----------|--------|
| Button | Hover | Background color change | 150ms | ease-default |
| Button | Active/click | scale(0.98) | 100ms | ease-default |
| Card | Hover | translateY(-1px) + shadow lift | 200ms | ease-default |
| Sidebar item | Active | Background + left accent bar | 150ms | ease-default |
| Modal | Open | opacity 0→1 + scale 0.95→1 | 200ms | ease-out |
| Modal | Close | opacity 1→0 + scale 1→0.95 | 150ms | ease-in |
| Toast | Enter | translateY(16px→0) + opacity | 300ms | ease-out |
| Toast | Exit | translateX(0→32px) + opacity | 200ms | ease-in |
| Chat message | Appear | opacity 0→1 + translateY(8px→0) | 200ms | ease-out |
| Citation chips | Appear | staggered opacity + translateY(4px→0) | 200ms ea. | ease-out |
| Streaming cursor | Blink | opacity 0↔1 | 1000ms | step-end |
| Page transition | Navigate | opacity fade | 200ms | ease-default |
| Drag zone | Drag enter | border-color + scale(1.01) | 200ms | ease-default |
| Suggestion chips | Load | staggered opacity + translateY(8px→0) | 200ms ea. | ease-bounce |
| Processing dots | Continuous | sequential opacity pulse | 1200ms | ease-in-out |
| Progress bar | Update | width transition | 300ms | ease-default |
| Theme toggle | Switch | translate slider + rotate icon | 300ms | ease-bounce |
| Scroll reveal | Viewport enter | translateY(24px→0) + opacity | 500ms | ease-out |

### Animation Rules

1. **Respect prefers-reduced-motion.** If user's OS requests reduced motion, ALL animations collapse to instant state changes (no transitions). This is non-negotiable for accessibility.
2. **No animation on data-heavy operations.** Don't animate 50 cards loading — just show them. Animate 1-3 items max per viewport.
3. **Landing page only:** Scroll-triggered reveals. Never in the dashboard — users are WORKING, not watching.
4. **Chat streaming is the hero moment.** This is where animation matters most. The token-by-token appearance with the blinking cursor should feel alive but calm.

---

## Embeddable Widget Design

The widget must look premium even when embedded on ugly third-party sites.

### Floating Button

```
┌───┐
│ 💬│  ← 56px circle, --accent-primary bg, white chat icon
└───┘
```

- Position: fixed, bottom 24px, right 24px
- Size: 56px × 56px circle
- Background: `--accent-primary`
- Icon: White message bubble (Lucide `MessageSquare`), 24px
- Shadow: `--shadow-lg` + `0 0 0 0 rgba(79, 107, 245, 0)` → subtle pulse glow on idle
- Hover: scale(1.05) + `--shadow-xl`
- Active: scale(0.95)
- Entrance animation: Scale up from 0 with ease-bounce, 400ms delay after page load

### Chat Window (Expanded)

```
┌──────────────────────────────────────┐
│  🔵 Cite · Powered by your docs   ✕ │
├──────────────────────────────────────┤
│                                      │
│  Chat messages here                  │
│  (Same styling as main chat UI)      │
│                                      │
├──────────────────────────────────────┤
│  ┌──────────────────────────── ⮐ ┐  │
│  │  Ask a question...            │  │
│  └───────────────────────────────┘  │
├──────────────────────────────────────┤
│  Powered by Cite · cite.weaverbit.com│
└──────────────────────────────────────┘
```

- Position: fixed, bottom 96px, right 24px
- Size: 400px wide × 560px tall (max 80vh)
- Background: `--bg-primary`
- Border-radius: `--radius-lg` (12px)
- Shadow: `--shadow-xl`
- Border: 1px `--border-primary`
- Header: 52px, `--bg-secondary`, brand icon + title + close button
- Footer: 40px, `--bg-secondary`, "Powered by Cite" link — drives traffic back
- Open animation: Scale from 0.8 + opacity, origin bottom-right, 250ms ease-out
- Close animation: reverse, 200ms
- The widget respects the site's light/dark preference OR allows the KB owner to set a fixed theme

---

## Responsive Breakpoints

```
--screen-sm:     640px    — Mobile landscape
--screen-md:     768px    — Tablet portrait
--screen-lg:     1024px   — Tablet landscape / small desktop
--screen-xl:     1280px   — Desktop
--screen-2xl:    1536px   — Large desktop
```

### Responsive Behaviors

| Component | Mobile (<768px) | Tablet (768-1024px) | Desktop (>1024px) |
|-----------|----------------|--------------------|--------------------|
| Sidebar | Hidden, hamburger toggle | Collapsed (64px) | Full (260px) |
| Chat + Docs | Stacked (tabs) | Stacked (tabs) | Side by side |
| Cards | 1 column | 2 columns | 3 columns |
| Landing hero | Stacked, smaller type | Stacked, medium type | Side by side |
| Chat max-width | 100% | 100% | 680px centered |
| Modal | Full-screen bottom sheet | Centered, 90% width | Centered, fixed width |
| Widget | Full-screen on open | 400px window | 400px window |

---

## Iconography

- **Library:** Lucide React (consistent, clean, 24px grid, customizable stroke)
- **Stroke width:** 1.75px (slightly lighter than default 2px — feels more refined)
- **Default size:** 18px in UI, 20px in navigation, 24px in feature sections
- **Color:** Inherits from parent text color via `currentColor`
- **Key icons:**
  - Dashboard: `LayoutDashboard`
  - Knowledge Base: `BookOpen`
  - Documents: `FileText`
  - Upload: `Upload`
  - Chat: `MessageSquare`
  - Send: `ArrowUp`
  - Settings: `Settings`
  - Theme toggle: `Sun` / `Moon`
  - Delete: `Trash2`
  - Processing: `Loader2` (with spin animation)
  - Success: `CheckCircle2`
  - Error: `XCircle`
  - Citation: `Quote`
  - External link: `ExternalLink`
  - Copy: `Copy`
  - Close: `X`

---

## Accessibility Requirements (Non-Negotiable)

1. **Color contrast:** All text meets WCAG 2.1 AA minimum (4.5:1 small text, 3:1 large text)
2. **Focus indicators:** Visible focus ring (`--shadow-focus`) on ALL interactive elements
3. **Keyboard navigation:** Full app usable with keyboard only — Tab, Enter, Escape, Arrow keys
4. **Focus trap:** In modals and dialogs
5. **Screen reader:** All images have alt text, all icons have aria-labels, status changes announced via aria-live regions
6. **Reduced motion:** Respect `prefers-reduced-motion: reduce` — disable all animations
7. **Touch targets:** Minimum 44px × 44px for all interactive elements on mobile
8. **Semantic HTML:** Proper heading hierarchy (h1 → h2 → h3), landmarks (nav, main, aside), button vs. link usage
9. **Chat accessibility:** Messages use role="log" with aria-live="polite" for new messages

---

## Implementation Notes for Claude Code

### Tailwind CSS v4 Configuration

**IMPORTANT:** This project uses **Tailwind CSS v4**, which configures design tokens via CSS `@theme inline` in `globals.css` — NOT via `tailwind.config.ts`.

Dark mode uses a custom variant:
```css
@custom-variant dark (&:is([data-theme="dark"] *));
```

Design tokens are defined as CSS variables in `globals.css` under `@theme inline`:
```css
@theme inline {
  --radius-sm: 0.375rem;    /* 6px */
  --radius-md: 0.5rem;      /* 8px — default */
  --radius-lg: 0.75rem;     /* 12px */
  --radius-xl: 1rem;        /* 16px */
  --radius-full: 9999px;

  --font-sans: 'General Sans', -apple-system, sans-serif;
  --font-display: 'Instrument Serif', Georgia, serif;
  --font-body: 'General Sans', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Colors mapped as Tailwind color tokens */
  --color-brand: var(--accent-primary);
  --color-success: /* mapped from theme variables */;
  --color-warning: /* mapped from theme variables */;
  --color-error: /* mapped from theme variables */;
  /* ... etc */
}
```

Light/dark theme values are applied via `:root` and `:root[data-theme="dark"]` CSS variable overrides.

### shadcn/ui Customization

Do NOT use shadcn/ui components with default styling. Every shadcn component must be customized to match this design system:

- Override the CSS variables in `globals.css` to use our color system
- Modify component source files after installing (shadcn adds them to your project — they're yours to modify)
- The shadcn components are a STARTING POINT, not the finish line

### CSS Architecture

```
frontend/src/
├── styles/
│   ├── globals.css         (CSS variable definitions, theme tokens, base resets)
│   ├── fonts.css           (web font @font-face declarations)
│   └── animations.css      (keyframe definitions for cursor-blink, dot-pulse, etc.)
```

- Use Tailwind utilities for 90% of styling
- Use CSS variables for theme-dependent values
- Use CSS modules or inline styles ONLY for complex animations that can't be expressed in Tailwind
- NEVER use styled-components, Emotion, or CSS-in-JS — Tailwind only

---

## Quality Checklist (Before Calling Any Page "Done")

- [ ] Does it look premium at first glance? Would a Stripe designer approve?
- [ ] Does the dark/light toggle work without flash on page load?
- [ ] Are ALL interactive elements keyboard-accessible with visible focus states?
- [ ] Is the typography crisp? No default system fonts leaking through?
- [ ] Do animations respect `prefers-reduced-motion`?
- [ ] Are empty states designed (not just blank white space)?
- [ ] Are error states designed (not browser default errors)?
- [ ] Are loading states designed (skeleton screens, not blank)?
- [ ] Does it work on mobile? Thumb-friendly?
- [ ] Would you put this in your Upwork portfolio and feel proud?

The last question is the only one that really matters.
