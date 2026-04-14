# Roadmap

## Completed Milestones

### Foundation and Service Bootstrap

Completed:
- FastAPI application structure
- environment-backed configuration
- repository-level documentation and test scaffolding
- local development entrypoint

### Ingestion Architecture

Completed:
- ingestion adapter abstraction
- local mock ingestion path
- Gmail ingestion scaffold and factory wiring
- mock payload fixtures for local development

### Parsing and Enrichment

Completed:
- parser for LinkedIn-like Gmail notification content
- pluggable enrichment contract
- mock heuristic enrichment processor
- LLM processor scaffold with shared interface
- stable enrichment schema for category, summary, priority, and review status

### Storage and Query API

Completed:
- storage interface abstraction
- resilient JSON storage implementation
- activity query endpoints
- filtering, sorting, pagination, and high-priority queries
- atomic local writes and safe degraded reads for empty/corrupted files

### Sync, Digest, and Demo UI

Completed:
- optional Google Sheets sync client
- plain-text, JSON, and Markdown digest outputs
- FastAPI-served dashboard using existing backend endpoints
- operations-style dashboard interactions for local demos

## Current System State

The repository currently provides a working local prototype and demo environment with the following characteristics:

- backend
  - FastAPI service with ingestion, query, digest, and dashboard endpoints
- ingestion
  - mock ingestion is fully usable
  - Gmail integration is architected but not live
- enrichment
  - mock heuristic enrichment is active
  - LLM integration is not yet implemented
- storage
  - JSON-backed storage behind an interface
  - resilient enough for local use, not for production concurrency or scale
- sync
  - Google Sheets append path is present and optional
- dashboard
  - realistic demo UI exists
  - some workflow actions are frontend-only for demo value

In practical terms, the repo is beyond scaffold stage, but still below production MVP.

## Remaining Work for Production MVP

The items below are the recommended checklist to move from the current prototype to a production-capable MVP.

### Ingestion and Automation

- implement real Gmail API ingestion
  - authentication flow
  - message retrieval
  - payload decoding/normalization
- add periodic ingestion automation
  - scheduler or worker-based trigger
  - operational retry strategy
- define ingestion failure handling and replay approach

### Persistence and Data Integrity

- replace JSON-only storage with a persistent database backend
  - SQLite for a minimal hosted MVP, or PostgreSQL for a more standard service backend
- preserve the existing storage interface during migration
- implement idempotency and deduplication
  - repeated ingestion should not create duplicate activity records
  - repeated Sheets sync should not blindly duplicate rows
- define record identity strategy
  - source-derived keys or dedupe fingerprints

### Review Workflow and Operational State

- persist review workflow actions in backend storage
- define canonical review states and transitions
- ensure dashboard actions reflect stored backend state, not browser-only state

### Observability and Error Reporting

- add structured logging across:
  - ingestion
  - parsing
  - enrichment
  - storage
  - digest generation
  - Google Sheets sync
- add operational error visibility
  - surfaced sync failures
  - surfaced ingestion failures
  - actionable runtime diagnostics
- define health/readiness expectations for deployed environments

### Configuration and Runtime Hardening

- validate required configuration at startup for non-mock modes
- improve environment separation and config safety
- document safe defaults and production-required overrides
- remove ambiguity around legacy config fields where appropriate

### Security and Access Control

- define authentication requirements for hosted use
- add access control considerations for:
  - dashboard access
  - ingestion triggers
  - export endpoints
  - external sync configuration
- review handling of secrets and service account files

### Deployment and Operations

- document deployment/runtime guidance for a hosted environment
- define recommended process model
  - API process only vs API + scheduler/worker
- document persistent storage expectations
- document backup/recovery expectations for production data

## Post-MVP Enhancements

These are useful extensions, but they are not required to claim a production MVP.

### Intelligence and Content Quality

- real LLM integration for enrichment
- enrichment confidence scoring
- better summarization quality controls
- richer entity extraction from activity text

### Delivery and Export

- email delivery of digests
- HTML digest export
- scheduled digest generation
- recipient-specific digest variants

### Collaboration and Workflow

- role-based multi-user review
- assignment and ownership workflows
- audit history for review decisions

### Dashboard and Analytics

- richer dashboard analytics
- deeper charting and trend analysis
- saved filters/views
- export actions from the dashboard

### Integrations

- Slack or Teams notifications
- additional spreadsheet or document exports
- downstream BI/reporting integrations

## Recommended Near-Term Sequence

Recommended order for the next engineering phase:

1. implement real Gmail ingestion
2. migrate storage to a persistent database
3. add deduplication/idempotency
4. persist review workflow state
5. add structured logging and operational error visibility
6. document deployment and security expectations

This sequencing keeps the existing service boundaries intact while moving the highest-risk prototype constraints out of the critical path.
