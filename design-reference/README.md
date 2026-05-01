# UB CSE Admin Design System

## Overview

**Product:** University at Buffalo — Department of Computer Science & Engineering  
**Surface:** Internal admin dashboard for CSE activity monitoring  
**Audience:** Department administrators, faculty coordinators, and moderators  
**Use Case:** High-density moderation interface for reviewing student/faculty activity, approving/rejecting submissions, flagging priority items, and tracking events across the department.

## Sources

No external codebase or Figma link was provided. This design system was synthesized from the written brief:

> "High-density internal moderation dashboard. Fast scanning over visual beauty. Compact layout. Strong hierarchy. Minimal color palette (institutional, not playful). Clear approve/reject actions on every item. Activity items should be list rows, not large cards. Reduce text to 1–2 lines max per item. Highlight high-priority items visually."

University at Buffalo's official brand colors (UB Blue `#005BBB`, UB Gold `#FFB81C`) were used as the institutional anchors.

---

## CONTENT FUNDAMENTALS

**Tone:** Institutional, neutral, factual. This is a tool for administrators — copy is terse and action-oriented, not conversational.

**Casing:**
- Section labels: ALL CAPS (e.g. `PENDING REVIEW`, `ACTIVITY FEED`)
- Action buttons: Title Case (e.g. `Approve`, `Reject`, `Flag`)
- Status badges: ALL CAPS (e.g. `HIGH PRIORITY`, `PENDING`, `RESOLVED`)
- Body/metadata: Sentence case

**Voice:** Third-person, passive-free. Prefer `"3 items pending review"` over `"You have 3 items to review"`. No first-person.

**Density:** Labels are abbreviated where context is clear. E.g. `Subm.` → `Submission`, `Dept.` → `Department`. Timestamps use compact format: `Apr 30 · 2:14 PM` or `3h ago`.

**Emoji:** Never used. No decorative characters. Unicode arrows (→, ↑, ↓) allowed sparingly for directional cues in tables.

**Numbers:** Always display counts with zero-padding in badges (e.g. `07`). Use comma separators for large numbers (`1,204`).

**Vibe:** A government/university records system. Cold, clear, trustworthy. No marketing language.

---

## VISUAL FOUNDATIONS

### Colors
- **Primary:** UB Blue `#005BBB` — used for primary actions, active states, selected rows, links
- **Accent:** UB Gold `#FFB81C` — used sparingly for high-priority flags and warnings only
- **Background:** `#F4F5F7` — light institutional gray, page background
- **Surface:** `#FFFFFF` — panel/table surface
- **Border:** `#DDE1E7` — dividers, table row lines
- **Foreground Primary:** `#0D1117` — primary text
- **Foreground Secondary:** `#4A5568` — metadata, secondary labels
- **Foreground Tertiary:** `#8A95A3` — timestamps, disabled states
- **Success / Approve:** `#1A7F4B` — green for approved/resolved actions
- **Danger / Reject:** `#C0392B` — red for reject/flag actions
- **Warning / High Priority:** `#B8860B` (dark gold) — derived from UB Gold for text on light bg
- **Priority Highlight BG:** `#FFFBEB` — subtle yellow tint for high-priority rows

### Typography
- **Display/Heading:** `'IBM Plex Sans'` (Google Fonts) — institutional, modern, technical. Fallback: `'Arial', sans-serif`
- **Body/UI:** `'IBM Plex Sans'` — same family, weight 400/500
- **Monospace (IDs, codes):** `'IBM Plex Mono'` — for item IDs, hash codes, timestamps
- **Scale:** 11px (micro), 12px (caption), 13px (body-sm), 14px (body), 16px (label-lg), 18px (h3), 22px (h2), 28px (h1)
- **Line height:** Tight — 1.3 for headings, 1.5 for body, 1.2 for table rows
- **Letter spacing:** 0.04em on ALL CAPS labels

### Spacing
- Base unit: 4px
- Common values: 4, 8, 12, 16, 20, 24, 32, 48px
- Table row height: 36px (compact), 44px (comfortable)
- Section padding: 16px horizontal, 12px vertical
- Card/panel padding: 16px

### Backgrounds
- No images or illustrations
- No gradients
- No textures
- Flat, neutral surfaces only
- Subtle horizontal row striping for long lists (`#F9FAFB` alternating)

### Borders & Radius
- Border radius: 2px (inputs, badges), 4px (panels, dropdowns), 0px (table rows)
- Border width: 1px throughout
- No box shadows on rows; subtle shadow on floating panels: `0 2px 8px rgba(0,0,0,0.08)`
- Focus ring: `0 0 0 3px rgba(0,91,187,0.25)` (UB Blue at 25% opacity)

### Animation
- Minimal: opacity transitions only (0.1s ease-out) for hover states
- No bounces, springs, or decorative transitions
- Modals fade in (0.15s)
- No loading skeletons — spinner or "Loading…" text

### Hover / Press States
- Row hover: background `#EEF2F8` (light blue tint)
- Button hover: background darkened ~8% 
- Button press: background darkened ~15%, slight scale(0.98)
- Link hover: underline

### Cards & Panels
- No rounded card-heavy layout
- Panels use 1px border `#DDE1E7`, radius 4px, white background
- No card shadows on list items — borders only
- Floating panels (dropdowns, modals) get `box-shadow: 0 4px 16px rgba(0,0,0,0.12)`

### Color Imagery
- No photography used
- No illustrations
- Data visualization uses UB Blue scale + neutral grays

### Layout
- Fixed left sidebar (220px), fixed top header (48px)
- Content area scrolls vertically
- Max content width: none (fills available space)
- Responsive: not a primary concern (internal tool, desktop-only)

---

## ICONOGRAPHY

**Approach:** Lucide Icons (CDN: `https://unpkg.com/lucide@latest`) — stroke-based, 16px or 20px, `stroke-width: 1.5`. Consistent with institutional, clean aesthetic.

No custom SVG icon set. No emoji. No PNG icons.

**Usage rules:**
- Icons always accompany a text label (never icon-only in primary actions)
- Size 16px in table rows and tight UI, 20px in sidebar nav and section headers
- Color inherits from text (`currentColor`) — never independently colored except for status icons:
  - Approve: green `#1A7F4B`
  - Reject/Flag: red `#C0392B`
  - Warning: gold `#B8860B`

**Common icons used:**
- `check` / `check-circle` — approve
- `x` / `x-circle` — reject
- `flag` — priority flag
- `clock` — timestamps
- `user` — student/faculty
- `file-text` — submission
- `alert-triangle` — warnings
- `filter` — filter controls
- `search` — search input
- `chevron-down` — dropdowns
- `bar-chart-2` — analytics

---

## FILE INDEX

```
README.md                        ← This file
SKILL.md                         ← Agent skill definition
colors_and_type.css              ← CSS custom properties (colors, type scale)
assets/                          ← Logos and visual assets
  ub-logo.svg                    ← UB wordmark (constructed)
  ub-shield.svg                  ← UB shield mark
preview/                         ← Design System tab cards
  colors-primary.html
  colors-neutral.html
  colors-semantic.html
  type-scale.html
  type-specimens.html
  spacing-tokens.html
  spacing-in-use.html
  components-buttons.html
  components-badges.html
  components-inputs.html
  components-table-rows.html
  components-sidebar.html
  components-priority.html
ui_kits/
  admin_dashboard/
    README.md
    index.html                   ← Full interactive dashboard prototype
    Sidebar.jsx
    Header.jsx
    ActivityFeed.jsx
    ItemRow.jsx
    StatusBadge.jsx
    FilterBar.jsx
    StatsPanel.jsx
```
