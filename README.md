# CSE Pulse

Internal service for monitoring faculty activity signals from LinkedIn-related Gmail notifications, enriching them into structured records, and presenting them through an API and lightweight operations dashboard.

This repository is currently a mock-safe prototype with several production-oriented interfaces already in place:
- FastAPI backend
- pluggable ingestion architecture
- parsing of LinkedIn-like Gmail notifications
- pluggable enrichment layer
- resilient local JSON storage behind a storage interface
- query API with filtering, sorting, and pagination
- optional Google Sheets sync
- digest generation in preview, JSON, and Markdown forms
- FastAPI-served dashboard for demos and internal review

The system is intentionally designed to avoid direct LinkedIn scraping. The current ingestion path works from Gmail-style notification payloads.

## Product Overview

The service turns notification-style activity signals into structured records that can be reviewed, queried, summarized, and exported. It is suitable today for local development, demos, and architecture validation. It is not yet a production-ready monitoring service.

Primary use cases:
- ingest notification payloads from a mock source or future Gmail source
- normalize unstructured email content into activity records
- enrich each record with category, summary, priority, and review status
- browse and filter activity records through API endpoints
- generate digest-ready summaries for editorial or operations workflows
- optionally mirror records to Google Sheets
- demonstrate an end-to-end workflow in a browser dashboard

## Main Capabilities

- Ingestion
  - `mock` ingestion mode reads local sample payloads
  - `gmail` mode exists as an architectural scaffold, not a live integration
- Parsing
  - extracts source URL, faculty name when detectable, raw text, and detection timestamp
- Enrichment
  - mock heuristic processor is implemented
  - LLM-backed processor exists as a scaffold only
- Storage
  - JSON-backed storage is implemented behind a storage interface
  - supports resilient reads, atomic writes, filtering, sorting, and pagination
- Digest generation
  - plain-text preview
  - structured JSON digest
  - Markdown export
- Dashboard
  - static operations-style UI served by FastAPI
  - uses only existing backend endpoints
- External sync
  - optional Google Sheets append flow
  - safe no-op when not configured

## Current Status

Implemented today:
- FastAPI API and local dashboard
- mock ingestion flow
- Gmail-ready ingestion interface and factory
- parsing and enrichment pipeline
- resilient JSON storage abstraction
- query endpoints for activities and high-priority records
- digest generation and export endpoints
- optional Google Sheets sync path

Not yet production-ready:
- real Gmail API ingestion
- scheduled or automated ingestion
- persistent database backend
- deduplication/idempotency
- persistent review workflow state
- real LLM integration
- deployment, auth, and operational hardening

## Known Limitations

- `gmail` ingestion mode is a scaffold and currently does not pull live messages
- the `llm` enrichment mode is a scaffold and raises until implemented
- JSON storage is suitable for local use, not multi-user or hosted operation
- dashboard review actions are frontend-only and do not persist to backend storage
- Google Sheets sync is append-oriented and does not yet support deduplication or reconciliation
- there is no authentication, authorization, or tenant separation
- observability is minimal compared with a production service

## Local Setup

### Requirements

- Python 3.11+ recommended
- local virtual environment

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create an environment file

```bash
cp .env.example .env
```

Recommended starting configuration:

```env
MOCK_MODE=true
INGESTION_MODE=mock
AI_PROVIDER=mock
GOOGLE_SHEETS_ENABLED=false
```

## Running the Backend

Start the FastAPI app:

```bash
uvicorn app.main:app --reload
```

Default local URLs:
- API root/dashboard: `http://127.0.0.1:8000/`
- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Running the Dashboard

The dashboard is served by the same FastAPI process. No separate frontend build step is required.

After starting the backend, open:

- `http://127.0.0.1:8000/`

Suggested demo actions:
- run mock ingestion from the UI
- filter the activity inbox
- inspect the high-priority spotlight
- switch among digest preview, JSON, and Markdown views
- use frontend-only review actions to drive the mock sync status card

## Enabling Google Sheets Sync

Google Sheets sync is optional and disabled by default.

Set the following in `.env`:

```env
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_PATH=/absolute/path/to/service-account.json
GOOGLE_SHEETS_WORKSHEET=Sheet1
```

Notes:
- if sync is disabled or incomplete, ingestion continues normally
- if Google client libraries or credentials are unavailable, the sync path safely no-ops
- the current implementation appends rows; it does not yet deduplicate or update existing rows

## Key Endpoints

### Core API

- `GET /health`
- `POST /ingest`
- `POST /ingest/mock`
- `GET /activities`
- `GET /activities/high-priority`
- `GET /activities/{activity_id}`

### Digest API

- `GET /digest/preview`
- `GET /digest`
- `GET /digest/export/markdown`

### Dashboard

- `GET /`

### Common query patterns

List filtered activities:

```bash
curl "http://127.0.0.1:8000/activities?category=award&review_status=pending"
```

List sorted activities:

```bash
curl "http://127.0.0.1:8000/activities?sort_by=priority&sort_order=desc"
```

List paginated activities:

```bash
curl "http://127.0.0.1:8000/activities?offset=0&limit=10"
```

Fetch a structured digest:

```bash
curl "http://127.0.0.1:8000/digest?review_status=pending&max_items_per_category=3"
```

Fetch a Markdown digest export:

```bash
curl "http://127.0.0.1:8000/digest/export/markdown?include_section_totals=true"
```

## Configuration

See `.env.example` for the complete set of supported environment variables.

High-impact settings:
- `INGESTION_MODE`
- `MOCK_EMAIL_PAYLOAD_PATH`
- `AI_PROVIDER`
- `DATA_FILE`
- `GOOGLE_SHEETS_ENABLED`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_PATH`
- `GMAIL_QUERY`
- `GMAIL_MAX_RESULTS`

## Testing

Run the test suite locally:

```bash
pytest -q
```

If your shell environment does not already have dependencies installed, activate the virtual environment first.

## Repository Structure

```text
app/
  api/routes.py              FastAPI routes and dashboard entrypoint
  config.py                  Environment-backed application settings
  models/schemas.py          Pydantic domain and API schemas
  services/
    ingestion/               Ingestion adapter layer
    enrichment/              Enrichment processor layer
    digest_service.py        Digest generation and export logic
    gmail_parser.py          Notification parsing
    sheets_client.py         Optional Google Sheets sync
    storage.py               JSON storage implementation
    storage_base.py          Storage interface
  static/                    Dashboard UI assets
  main.py                    FastAPI app bootstrap
data/
  mock_emails/               Sample ingestion payloads
tests/                       Unit and API tests
```

## Additional Documentation

- [architecture.md](./architecture.md) — service architecture and production-readiness gaps
- [plans.md](./plans.md) — roadmap from current prototype to production MVP
- [documentation.md](./documentation.md) — engineering and development guide
