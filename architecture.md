# Architecture

## Overview

CSE Pulse is a layered service that transforms LinkedIn-like Gmail notifications into structured faculty activity records, supports query and digest workflows, and exposes those capabilities through a FastAPI backend and a lightweight browser dashboard.

The implementation today is intentionally optimized for local development and demos, while preserving clean service boundaries for future production work.

## High-Level Flow

```text
Notification source
  └─ Mock JSON payloads today
  └─ Gmail API ingestion scaffold for future use
        ↓
Ingestion adapter
        ↓
Parser
        ↓
Enrichment processor
        ↓
Storage layer
        ↓
Optional external sync (Google Sheets)
        ↓
Digest generation
        ↓
API layer
        ↓
FastAPI-served dashboard
```

## Layered Service Architecture

### 1. Ingestion Layer

Purpose:
- isolate how raw Gmail-style notifications are fetched
- keep downstream parsing and enrichment independent from source mechanics

Current implementation:
- `MockGmailIngestionAdapter` reads local JSON fixtures
- `GmailAPIIngestionAdapter` is present as a safe scaffold
- `build_ingestion_adapter(...)` selects the adapter from configuration

Current status:
- mock ingestion is implemented and used by demos/tests
- Gmail API ingestion is not yet implemented end-to-end

### 2. Parsing Layer

Purpose:
- normalize raw notification content into a parsed activity candidate

Current implementation:
- `GmailParser` extracts:
  - raw text
  - faculty name when detectable
  - source URL
  - detection timestamp

Characteristics:
- defensive handling for incomplete or noisy input
- intentionally heuristic and lightweight

### 3. Enrichment Layer

Purpose:
- convert parsed activity candidates into digest- and review-ready structured data

Current implementation:
- `MockProcessor`
  - rule-based classification
  - summary generation
  - bounded priority scoring
  - default `review_status=pending`
- `LLMProcessor`
  - scaffold only
  - exists to preserve the pluggable contract and config surface
- `build_enrichment_processor(...)`
  - selects implementation from configuration

Characteristics:
- stable output schema via `EnrichedActivity`
- pluggable interface already in place

### 4. Storage Layer

Purpose:
- persist and retrieve structured activity records
- support dashboard/API query patterns without coupling routes to a concrete backend

Current implementation:
- `ActivityStorage` protocol defines the storage contract
- `JSONStorageService` is the default backend

Capabilities:
- create activity records
- list all records
- get by ID
- filter by category and review status
- sort by `detected_at` or `priority`
- offset/limit pagination
- high-priority selection
- resilient reads for empty/corrupted JSON files
- atomic file replacement for writes

Current status:
- suitable for local and demo usage
- not appropriate for hosted multi-user operation

### 5. External Sync Layer

Purpose:
- mirror stored activity records to an external operational surface

Current implementation:
- `GoogleSheetsClient`
  - maps activity records to structured rows
  - appends rows when enabled and configured
  - no-ops safely when disabled or incomplete

Current status:
- append path exists
- no deduplication, reconciliation, or operational retry behavior yet

### 6. Digest Generation Layer

Purpose:
- transform stored activities into review- and export-ready summaries

Current implementation:
- `DigestService`
  - filters by date window
  - optionally filters by review status
  - groups by category
  - orders items deterministically within groups
  - emits:
    - plain-text preview
    - structured JSON digest
    - Markdown export

Current status:
- sufficient for dashboard and export demos
- not yet integrated with scheduled delivery channels

### 7. API Layer

Purpose:
- expose ingestion, query, digest, and dashboard functionality over HTTP

Current implementation:
- FastAPI routes in `app/api/routes.py`

Exposed capabilities:
- health check
- ingestion endpoints
- activity query endpoints
- digest endpoints
- dashboard entry page

Characteristics:
- backend response formats are intentionally simple
- current dashboard consumes these endpoints directly

### 8. Dashboard Layer

Purpose:
- provide a browser-based operations experience without adding a separate frontend deployment stack

Current implementation:
- static HTML/CSS/JS served directly by FastAPI
- operations-style UI built from existing endpoints only

Features:
- KPI summary cards
- searchable/filterable inbox
- high-priority spotlight
- digest workspace
- frontend-only review actions
- derived sync status card
- lightweight charts
- detail modal

Current status:
- suitable for demos and internal walkthroughs
- not a production-grade authenticated frontend

## Request and Data Flow

### Ingestion Request Flow

```text
POST /ingest or POST /ingest/mock
  → choose ingestion adapter
  → fetch raw emails
  → parse notifications
  → enrich parsed activities
  → persist records
  → optionally append to Google Sheets
  → return typed ingest response
```

### Query/Digest Flow

```text
GET /activities or GET /digest*
  → read from storage interface
  → apply filtering/sorting/grouping rules
  → serialize response
  → return API payload or text export
```

### Dashboard Flow

```text
GET /
  → serve static dashboard shell
  → browser fetches /activities, /activities/high-priority, /digest, /digest/preview, /digest/export/markdown
  → browser renders product-style operations view
```

## Module Responsibilities

- `app/config.py`
  - environment-backed settings
- `app/models/schemas.py`
  - shared typed schemas for parsing, enrichment, storage, and API responses
- `app/services/ingestion/`
  - source-specific ingestion adapters and factory
- `app/services/gmail_parser.py`
  - notification parsing
- `app/services/enrichment/`
  - enrichment interface, mock implementation, LLM scaffold, and factory
- `app/services/storage_base.py`
  - storage contract
- `app/services/storage.py`
  - JSON storage implementation and query helpers
- `app/services/sheets_client.py`
  - optional Google Sheets sync
- `app/services/digest_service.py`
  - digest assembly and export formatting
- `app/api/routes.py`
  - FastAPI routes and route-level orchestration
- `app/static/`
  - dashboard assets
- `app/main.py`
  - app bootstrap and static asset mounting

## Production-Readiness Gaps

The repository is functionally beyond a scaffold, but it is not yet a production MVP.

Major gaps:
- live Gmail API ingestion is not implemented
- there is no scheduler or background automation for periodic ingestion
- storage is file-based JSON rather than a persistent relational database
- deduplication/idempotency is not implemented across ingestion or Sheets sync
- review actions in the dashboard are frontend-only and not persisted
- observability is limited:
  - no structured request tracing
  - no ingestion/error metrics
  - no failure reporting integration
- configuration validation is minimal
- there is no authentication or authorization model
- deployment guidance, runtime tuning, and operational safeguards are not yet documented to production standards

## Architectural Direction Toward MVP

Recommended next production-oriented steps:
1. replace mock-only ingestion with a real Gmail integration
2. move storage from JSON to SQLite or PostgreSQL behind the existing interface
3. persist review actions and add deduplication semantics
4. add structured logging and operational error visibility
5. define deployment, security, and runtime guidance

The current architecture already supports this direction because ingestion, enrichment, storage, digest generation, and sync are separated behind explicit service boundaries.
