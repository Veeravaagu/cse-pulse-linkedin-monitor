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
  - `gmail` ingestion mode reads Gmail API messages with the read-only scope when configured
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
- scheduled or automated ingestion
- persistent database backend
- persistent review workflow state
- real LLM integration
- deployment, auth, and operational hardening

## Known Limitations

- Gmail ingestion requires either a service account credentials file or a pre-generated local OAuth user token
- service accounts can only read a real mailbox if your Google Workspace setup grants appropriate Gmail API access to that service account
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

Required local env vars (set placeholder values in `.env`):

```env
ENV=development
ADMIN_USERNAME=<local-admin-username>
ADMIN_PASSWORD=<local-admin-password>
ADMIN_SESSION_SECRET=<long-random-local-secret>
MAIN_DASHBOARD_API_KEY=<optional-in-development>
INGESTION_MODE=mock
DATA_FILE=data/activities.json
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
- Public preview: `http://127.0.0.1:8000/?public=1`

Suggested demo actions:
- run Gmail ingestion from the UI
- filter the activity inbox
- inspect the high-priority spotlight
- switch among digest preview, JSON, and Markdown views
- use frontend-only review actions to drive the mock sync status card

## Enabling Gmail Read-Only Ingestion

Gmail ingestion is disabled by default. The implementation only uses the Gmail API read-only scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

Set the shared Gmail settings in `.env`:

```env
INGESTION_MODE=gmail
AI_PROVIDER=mock
GMAIL_QUERY=from:linkedin.com
GMAIL_MAX_RESULTS=25
GOOGLE_SHEETS_ENABLED=false
```

Then choose one auth mode.

### Service Account / Workspace Delegation

```env
GMAIL_CREDENTIALS_PATH=/absolute/path/to/gmail-service-account.json
GMAIL_OAUTH_CLIENT_SECRET_PATH=
GMAIL_TOKEN_PATH=
```

`GMAIL_CREDENTIALS_PATH` must point to a Google service account JSON credentials file. Service-account auth is checked first when this value is set.

Notes:
- enable the Gmail API in the Google Cloud project that owns the service account
- for a real user mailbox, the service account must be authorized by your Google Workspace administrator for Gmail API read-only access

### Local OAuth User Token

```env
GMAIL_CREDENTIALS_PATH=
GMAIL_OAUTH_CLIENT_SECRET_PATH=/absolute/path/to/oauth-client-secret.json
GMAIL_TOKEN_PATH=/absolute/path/to/gmail-token.json
```

Use this mode for ordinary local Gmail accounts. `GMAIL_OAUTH_CLIENT_SECRET_PATH` is the installed-app OAuth client secret used to generate the user token outside the app. `GMAIL_TOKEN_PATH` must point to an existing authorized-user token JSON file.

The app does not launch a browser or run OAuth consent during ingestion. If `GMAIL_TOKEN_PATH` is missing, ingestion returns an empty batch safely. If the token is expired and has a refresh token, the app refreshes it and writes the updated token JSON back to `GMAIL_TOKEN_PATH`.

Generate the token once from your shell:

```bash
source .venv/bin/activate
python scripts/gmail_oauth_setup.py
```

The setup script reads `GMAIL_OAUTH_CLIENT_SECRET_PATH` and `GMAIL_TOKEN_PATH`, opens the browser for Google consent, and saves the authorized token JSON to `GMAIL_TOKEN_PATH`.

Notes:
- the token must be generated separately with the Gmail read-only scope
- the app does not delete, archive, label, or mark messages as read
- it lists matching messages and fetches each full message payload through the Gmail API

Local smoke test:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
curl -X POST http://127.0.0.1:8000/ingest
```

If credentials are missing, unavailable, or unauthorized, the ingestion path safely returns an empty batch and leaves mock mode unaffected.

## Ingestion Triggers

Manual ingestion remains available for administrators from either:
- the dashboard **Run Ingestion** button
- the API endpoint `POST /ingest`

Automatic daily ingestion should be run outside the app with cron. The FastAPI app does not include an internal scheduler. Cron should call the same one-shot ingestion script:

```bash
cd /path/to/cse-pulse-linkedin-monitor
.venv/bin/python scripts/run_daily_ingestion.py
```

Sample daily cron entry for local/dev use:

```cron
0 8 * * * cd /path/to/cse-pulse-linkedin-monitor && .venv/bin/python scripts/run_daily_ingestion.py >> logs/ingestion.log 2>&1
```

Create the `logs/` directory first if you use the sample redirect. The script does not schedule work itself; cron or another local scheduler calls it once per run.

By default the script posts to `http://127.0.0.1:8000/ingest`. To target another backend, set `INGESTION_BASE_URL` or `INGESTION_URL` before cron runs. For example:

```bash
INGESTION_BASE_URL=http://127.0.0.1:8000 .venv/bin/python scripts/run_daily_ingestion.py
```

Sample daily cron entry:

```cron
0 8 * * * cd <project> && .venv/bin/python scripts/run_daily_ingestion.py
```

For Gmail ingestion, successful runs store `last_successful_ingestion_at` in `data/ingestion_state.json` by default. Later runs use that cursor to query only newer Gmail messages where possible, while existing duplicate protection still prevents duplicate stored activities. Failed ingestion runs should not advance the cursor. Delete or reset the state file to force a wider local re-run.

Do not use `echo "[]" > data/activities.json` or `printf '[]\n' > data/activities.json` as a normal reset workflow. That deletes approved and rejected history as well as pending test clutter. For local cleanup that preserves reviewed history, clear only pending activities:

```bash
.venv/bin/python scripts/clear_pending_activities.py
```

Activities and the Gmail ingestion cursor must stay consistent. If `data/activities.json` is wiped but `data/ingestion_state.json` still contains an advanced `last_successful_ingestion_at`, the next `POST /ingest` may return `ingested_count=0` because Gmail is queried only for messages newer than the cursor. For development-only reset work that also resets the cursor, use:

```bash
# Clears pending activities and resets the Gmail ingestion cursor.
.venv/bin/python scripts/reset_local_ingestion_state.py

# Explicitly clear all local activities and reset the cursor.
.venv/bin/python scripts/reset_local_ingestion_state.py --all
```

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

## Production Configuration

Required production env vars:

```env
ENV=production
ADMIN_USERNAME=<admin-username>
ADMIN_PASSWORD=<admin-password>
ADMIN_SESSION_SECRET=<long-random-secret>
MAIN_DASHBOARD_API_KEY=<long-random-api-key>
DATA_FILE=<persistent-path>/activities.json
INGESTION_MODE=<mock-or-gmail>
GMAIL_CREDENTIALS_PATH=<optional-service-account-json-path>
GMAIL_OAUTH_CLIENT_SECRET_PATH=<optional-oauth-client-secret-path>
GMAIL_TOKEN_PATH=<optional-oauth-token-path>
```

Security notes:
- Never commit `.env` or real secrets.
- Use a long random value for `ADMIN_SESSION_SECRET`.
- Use a long random value for `MAIN_DASHBOARD_API_KEY`.
- `/?public=1` is a read-only preview page.
- Real downstream integration is `GET /activities/public` with `X-API-Key` in production.

## Main Dashboard Integration Contract

- Endpoint: `GET /activities/public`
- Production header: `X-API-Key: <MAIN_DASHBOARD_API_KEY>`
- Returns full activity objects (including `review_status`)
- `manual` mode returns approved only
- `auto` mode returns approved + pending
- Rejected items are never returned

## Deployment Checklist

1. Set production env vars (`ENV`, admin credentials, session secret, API key, storage path, ingestion mode).
2. Configure Gmail OAuth/service-account secrets if `INGESTION_MODE=gmail`.
3. Ensure persistent storage for `data/*.json` (or configured equivalent paths).
4. Configure daily scheduler/cron for `scripts/run_daily_ingestion.py`.
5. Verify admin login/logout on `/`.
6. Verify `GET /activities/public` with valid and invalid `X-API-Key`.
7. Verify public preview page at `/?public=1`.

## Operational API Reference

### `GET /health`

Purpose: report whether the app can read activity storage.

```bash
curl "http://127.0.0.1:8000/health"
```

Response shape: JSON object with `status`, `service`, `storage`, and `activity_count`.

### `POST /ingest`

Purpose: run the Gmail-backed ingestion flow once. New activities are stored with `review_status="pending"`.

```bash
curl -s -X POST "http://127.0.0.1:8000/ingest"
```

Response shape: JSON object with `ingested_count` and `activities`.

### `GET /activities?review_status=pending`

Purpose: list activities waiting for admin review.

```bash
curl -s "http://127.0.0.1:8000/activities?review_status=pending"
```

Response shape: JSON array of activity records.

### `POST /activities/{activity_id}/approve`

Purpose: approve one pending activity by id.

```bash
curl -s -X POST "http://127.0.0.1:8000/activities/activity-123/approve"
```

Response shape: one activity record with `review_status="approved"`.

### `POST /activities/{activity_id}/reject`

Purpose: reject one pending activity by id.

```bash
curl -s -X POST "http://127.0.0.1:8000/activities/activity-123/reject"
```

Response shape: one activity record with `review_status="rejected"`.

### `GET /activities/approved`

Purpose: downstream-safe feed containing only approved activities.

```bash
curl -s "http://127.0.0.1:8000/activities/approved"
```

Response shape: JSON array of activity records where every item has `review_status="approved"`.

### CLI ingestion command

Purpose: cron-friendly one-shot ingestion using the configured ingestion flow.

```bash
cd /path/to/cse-pulse-linkedin-monitor
.venv/bin/python scripts/run_ingestion_once.py
```

Response shape: plain text summary with `ingested_count`, followed by created activity ids/statuses/source types.

Other useful endpoints:
- `GET /activities`
- `GET /activities/high-priority`
- `GET /activities/{activity_id}`
- `GET /digest/preview`
- `GET /digest`
- `GET /digest/export/markdown`
- `GET /`

### Manual smoke test: ingestion -> review -> approved API

With the FastAPI app running locally:

```bash
# 1. Optional local cleanup: remove pending test clutter while preserving approved/rejected history.
.venv/bin/python scripts/clear_pending_activities.py

# 2. Run ingestion.
curl -s -X POST http://127.0.0.1:8000/ingest

# 3. Confirm pending activity appears.
curl -s "http://127.0.0.1:8000/activities?review_status=pending"

# 4. Approve one pending activity.
APPROVE_ID=$(curl -s "http://127.0.0.1:8000/activities?review_status=pending" | python3 -c 'import json,sys; items=json.load(sys.stdin); print(items[0]["id"] if items else "")')
curl -s -X POST "http://127.0.0.1:8000/activities/${APPROVE_ID}/approve"

# Optional: reject one remaining pending activity so exclusion is easy to verify.
REJECT_ID=$(curl -s "http://127.0.0.1:8000/activities?review_status=pending" | python3 -c 'import json,sys; items=json.load(sys.stdin); print(items[0]["id"] if items else "")')
if [ -n "$REJECT_ID" ]; then curl -s -X POST "http://127.0.0.1:8000/activities/${REJECT_ID}/reject"; fi

# 5. Confirm the approved-only endpoint returns the approved item.
curl -s "http://127.0.0.1:8000/activities/approved"

# 6. Confirm approved-only excludes pending/rejected records.
curl -s "http://127.0.0.1:8000/activities/approved" | python3 -c 'import json,sys; items=json.load(sys.stdin); assert items and all(item["review_status"] == "approved" for item in items); print("approved-only endpoint OK")'
```

## Configuration

See `.env.example` for the complete set of supported environment variables.

High-impact settings:
- `INGESTION_MODE`
- `MOCK_EMAIL_PAYLOAD_PATH`
- `AI_PROVIDER`
- `DATA_FILE`
- `INGESTION_STATE_FILE`
- `GOOGLE_SHEETS_ENABLED`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_PATH`
- `GMAIL_QUERY`
- `GMAIL_MAX_RESULTS`
- `GMAIL_CREDENTIALS_PATH`
- `GMAIL_OAUTH_CLIENT_SECRET_PATH`
- `GMAIL_TOKEN_PATH`

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
