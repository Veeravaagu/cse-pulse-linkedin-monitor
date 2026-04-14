# Engineering Guide

## Purpose

This document is the developer guide for working on CSE Pulse safely and consistently. It is intended for engineers picking up the repository after the initial prototype phase.

The repository already contains a functioning local prototype. The goal of this guide is to explain how to work on it without assuming historical context from earlier milestone-based development.

## Working Model

The system is organized around a simple service pipeline:

1. ingestion retrieves Gmail-style notifications
2. parsing normalizes notification content
3. enrichment adds category, summary, priority, and review metadata
4. storage persists typed activity records
5. digest generation creates preview/export outputs
6. API routes expose the workflow
7. the dashboard consumes the existing API surface

Each stage is intentionally isolated behind a small abstraction so the implementation can evolve without rewriting the whole service.

## Development Principles

- keep backend contracts stable unless a change is necessary
- prefer extending existing abstractions over bypassing them
- preserve mock-safe local development wherever possible
- be explicit about what is implemented vs scaffolded
- treat production-oriented features separately from demo-only behavior

## Local Development Workflow

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Start the service

```bash
uvicorn app.main:app --reload
```

### Run tests

```bash
pytest -q
```

### Recommended default local mode

Use these settings for normal development:

```env
MOCK_MODE=true
INGESTION_MODE=mock
AI_PROVIDER=mock
GOOGLE_SHEETS_ENABLED=false
```

This keeps all external integrations optional and avoids requiring Gmail or Google Sheets credentials for most work.

## Mock Mode vs Live Integration Mode

### Mock Mode

Use mock mode when:
- developing UI behavior
- iterating on parsing or enrichment logic
- running tests
- validating the end-to-end flow locally

Characteristics:
- reads local fixture payloads
- uses heuristic enrichment
- stores records in local JSON
- can safely skip external sync

### Live Integration Mode

The repo has interfaces for live integrations, but not all live paths are implemented yet.

Current status:
- Gmail API ingestion
  - scaffolded, not production-ready
- LLM enrichment
  - scaffolded, not implemented
- Google Sheets sync
  - optional and partially operational

Use live integration mode only when intentionally working on one of those integration paths.

## Safe Ways to Extend the System

### Add or change ingestion behavior

Relevant files:
- `app/services/ingestion/base.py`
- `app/services/ingestion/factory.py`
- adapter implementations under `app/services/ingestion/`

Guidance:
- keep adapters returning `list[RawEmail]`
- avoid embedding parsing logic into ingestion adapters
- preserve mock ingestion as the default local path

### Add or change parsing behavior

Relevant file:
- `app/services/gmail_parser.py`

Guidance:
- keep output aligned with `ParsedEmailActivity`
- prefer defensive parsing over brittle assumptions
- add tests for noisy or partial notification content

### Add or change enrichment behavior

Relevant files:
- `app/services/enrichment/base.py`
- `app/services/enrichment/factory.py`
- `app/services/enrichment/mock_processor.py`
- `app/services/enrichment/llm_processor.py`

Guidance:
- preserve the `EnrichedActivity` contract
- keep category and priority bounded by schema
- if implementing LLM behavior, normalize and validate model output before returning it

### Add or change storage behavior

Relevant files:
- `app/services/storage_base.py`
- `app/services/storage.py`

Guidance:
- routes should depend on the storage interface, not a specific backend
- preserve filtering/sorting/pagination semantics where possible
- if adding a database backend, implement it behind `ActivityStorage`

### Add or change digest behavior

Relevant file:
- `app/services/digest_service.py`

Guidance:
- keep ordering deterministic
- preserve the existing preview and export endpoints unless there is a strong reason to version or replace them
- prefer deriving export formats from structured digest output rather than duplicating grouping logic

### Add or change dashboard behavior

Relevant location:
- `app/static/`

Guidance:
- prefer consuming existing endpoints over adding UI-only backend routes
- treat frontend-only workflow actions as demo affordances unless you are explicitly adding persistent backend state
- keep the dashboard lightweight enough to serve directly from FastAPI

## What Is Demo-Only Today

The following behaviors are intentionally demo-oriented and should not be described as production-ready:

- mock ingestion as the primary active ingestion mode
- mock heuristic enrichment as the primary active enrichment mode
- frontend-only review actions in the dashboard
- JSON file storage as the default persistence layer
- dashboard-derived sync status rather than true operational sync reconciliation

## Recommended Engineering Priorities

If you are continuing work toward production MVP, prioritize:

1. Gmail API ingestion
2. persistent database backend
3. deduplication/idempotency
4. persistent review workflow state
5. structured logging and failure visibility
6. deployment/security guidance

## Code Review Expectations

When making changes:
- keep new behavior modular
- update docs when the service surface changes
- add tests for changed business logic
- do not claim production support for scaffolded features
- preserve local mock-safe workflows unless the task explicitly changes them

## Repository Notes

- the dashboard is served from the same FastAPI app
- Google Sheets sync is optional and should fail open for local development
- the repo may contain prototype-era naming in a few places; when improving it, prefer incremental cleanup over broad renames that obscure reviewability
