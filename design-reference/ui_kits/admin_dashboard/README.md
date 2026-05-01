/* UB CSE Admin Dashboard — UI Kit README
   ========================================

## Overview
High-density internal moderation dashboard for CSE department administrators.
Desktop-only internal tool. Fixed sidebar + fixed header layout.

## Screens
1. Dashboard (index.html) — Stats overview + priority queue + recent activity
2. Submissions Queue — Full filterable table of pending submissions
3. Activity Feed — Chronological feed of all events
4. Item Detail — Single item review panel with approve/reject

## Components
- Sidebar.jsx        — Dark left nav with sections, counts, active state
- Header.jsx         — Fixed top bar with breadcrumb, search, user
- StatsPanel.jsx     — 4-up KPI stat cards
- ActivityFeed.jsx   — List of recent activity rows
- ItemRow.jsx        — Single table/list row with actions
- StatusBadge.jsx    — Status + type badges
- FilterBar.jsx      — Search + filter controls row

## Design Notes
- Row height: 36px compact, 44px default
- Sidebar: 220px, dark (#0D1117)
- Header: 48px, white with border
- No card shadows on list rows — borders only
- Priority rows: gold left-border + #FFFBEB background
- Urgent rows: red left-border + #FFF5F5 background
*/
