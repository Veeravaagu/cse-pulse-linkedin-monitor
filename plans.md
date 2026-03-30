# Implementation Plan (LinkedIn Monitoring Module - P3)

## Milestone 1 — Project Foundation

### Goals
- Initialize Python/FastAPI project layout
- Add environment configuration and dependency management
- Provide beginner-friendly setup docs

### Acceptance criteria
- Required files exist (`README.md`, `plans.md`, `architecture.md`, `.env.example`, `requirements.txt`, `documentation.md`)
- FastAPI app boots locally
- `/health` endpoint responds successfully

## Milestone 2 — Gmail Notification Ingestion (Mock First)

### Goals
- Build parser for LinkedIn-like Gmail notifications
- Support local mock ingestion without credentials
- Extract core fields (name/link/preview/timestamp)

### Acceptance criteria
- Mock email payloads ingested via API
- Parsed objects include required extracted fields
- Parser handles missing fields safely

## Milestone 3 — AI Enrichment Layer

### Goals
- Add category classification
- Add summary generation
- Add priority score + default review status

### Acceptance criteria
- Each parsed record gets enrichment fields
- Output category in allowed enum:
  - publication, grant, talk, award, event, student achievement, other
- Priority score always bounded (1-5)

## Milestone 4 — Storage + Query API

### Goals
- Persist activity records locally
- Implement dashboard-friendly read endpoints

### Acceptance criteria
- Endpoints available:
  - `GET /activities`
  - `GET /activities/high-priority`
  - `GET /activities/{id}`
- API returns typed schema-compliant responses

## Milestone 5 — Google Sheets Sync Scaffold

### Goals
- Add integration surface for writing rows to Google Sheets
- Keep credentials out of code

### Acceptance criteria
- Sheets client scaffold exists and is configurable by env vars
- Clear TODO docs for service account setup
- Mock-safe behavior when credentials unavailable

## Milestone 6 — Testing + Hardening

### Goals
- Add unit tests for parser, AI processor, and key endpoints
- Improve logging + error handling

### Acceptance criteria
- `pytest` runs successfully in mock mode
- Errors are returned with clear messages
- Structured logs indicate ingestion/enrichment/storage flow

## Milestone 7 — Evolution Path

### Goals
- Document migration path from JSON storage / Sheets to PostgreSQL
- Define future automation options (Gmail API scheduler)

### Acceptance criteria
- Roadmap documented with technical tradeoffs and sequencing
