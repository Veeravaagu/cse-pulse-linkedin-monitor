# Developer Notes + Codex Learning Guide

## Why we start with mock mode

As a student project, mock mode lets you validate parsing, AI enrichment, storage, and API behavior without waiting on OAuth credentials.

## Implementation strategy (small reviewable steps)

1. Plan architecture + milestones
2. Scaffold app modules + schemas
3. Add parser + AI processor with deterministic behavior
4. Add storage abstraction and API routes
5. Add tests and sample data
6. Add integrations (Gmail API + Sheets) behind interfaces

## Recommended Codex prompt flow

Use these prompts in sequence:

1. **Plan prompt**
   - “Inspect the repo and propose a step-by-step plan for Milestone 2 only. Do not code yet.”
2. **Implement prompt**
   - “Implement Milestone 2 from the approved plan. Keep changes small and add tests.”
3. **Review prompt**
   - “Summarize what changed, list risks, and suggest manual verification steps.”
4. **Refine prompt**
   - “Refactor the parser for readability and add comments for beginners.”

## When to ask for PLAN vs IMPLEMENT

- Ask for **PLAN** when:
  - requirements are changing
  - there are multiple possible designs
  - you need acceptance criteria first
- Ask for **IMPLEMENT** when:
  - scope is already approved
  - you want concrete code/tests

## Branch / commit / PR cadence (recommended)

- Branch per milestone or sub-milestone:
  - `feature/p3-m1-foundation`
  - `feature/p3-m2-gmail-parser`
- Commit every coherent checkpoint:
  - scaffolding
  - parser
  - tests
- Open PR after green tests and docs update
- Pause and review before merging each milestone

## Migration notes (future)

- JSONStorage -> SQLiteStorage -> PostgresStorage
- Keep `StorageService` interface stable to minimize API layer changes
- Keep AI processor behind an interface to swap local heuristics with real LLM
