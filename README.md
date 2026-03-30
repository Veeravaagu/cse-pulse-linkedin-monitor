# CSE Pulse — LinkedIn Monitoring Module (P3)

> This project **does not scrape LinkedIn profiles directly**.  
> It ingests **LinkedIn-related Gmail notification emails**, extracts signals, runs AI-assisted enrichment, stores structured records, and exposes them through a FastAPI backend.

## What this module does

Pipeline:

1. Read Gmail notifications through an ingestion adapter (mock JSON now, Gmail API scaffold available)
2. Parse useful fields:
   - faculty name (when detectable)
   - source link
   - email preview text
   - received timestamp
3. Classify and summarize using an AI processor (mock or pluggable real model)
4. Persist data in local storage (JSON now; replaceable later)
5. Optionally sync rows to Google Sheets
6. Serve API endpoints for dashboard consumption

## Quick start

### 1) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

```bash
cp .env.example .env
```

Start with mock mode enabled in `.env`:

```env
MOCK_MODE=true
INGESTION_MODE=mock
```

To test the Gmail scaffold path (no auth yet, returns 0 records safely):

```env
INGESTION_MODE=gmail
```

### 4) Run the API

```bash
uvicorn app.main:app --reload
```

### 5) Try endpoints

- Health: `http://127.0.0.1:8000/health`
- All activities: `http://127.0.0.1:8000/activities`
- High priority: `http://127.0.0.1:8000/activities/high-priority`
- Single item: `http://127.0.0.1:8000/activities/{id}`
- Ingest via configured adapter: `POST http://127.0.0.1:8000/ingest`
- Force mock ingestion: `POST http://127.0.0.1:8000/ingest/mock`

## Test

```bash
pytest -q
```

## Folder structure

```text
app/
  api/routes.py            # API endpoints
  models/schemas.py        # Pydantic schemas
  services/
    ingestion/             # Ingestion adapter layer (mock + Gmail scaffold)
    gmail_parser.py        # Parse Gmail-like notification content
    ai_processor.py        # Summary + classification logic (mock/pluggable)
    sheets_client.py       # Google Sheets sync scaffold
    storage.py             # Local storage abstraction
  config.py                # Environment settings
  main.py                  # FastAPI app entrypoint
data/
  mock_emails/             # Sample email payloads for local runs
tests/                     # Pytest tests
```

## Why this design

- **Compliant by design**: no direct LinkedIn scraping
- **Extensible**: storage and AI backends can be swapped later
- **Operationally safe**: environment variables for secrets and clear boundaries

## Next roadmap

See:
- `plans.md` for milestones + acceptance criteria
- `architecture.md` for technical design
