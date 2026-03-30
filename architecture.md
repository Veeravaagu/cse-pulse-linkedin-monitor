# Architecture — LinkedIn Monitoring via Gmail Notifications

## 1) System boundaries

### In scope
- Gmail notification ingestion (no profile scraping)
- Content parsing + extraction
- AI-based summarization + classification
- Structured persistence
- API for dashboard consumption

### Out of scope
- Direct LinkedIn profile crawling/scraping
- Production-grade distributed job orchestration (for now)

## 2) High-level flow

```text
Gmail notifications (LinkedIn)
    ↓
Ingestion adapter (mock JSON now, Gmail API later)
    ↓
Parser (extract name, URL, preview, timestamp)
    ↓
AI processor (summary, category, priority)
    ↓
Storage service (JSON now; DB later)
    ↓
Google Sheets sync (optional)
    ↓
FastAPI endpoints for dashboard
```

## 3) Ingestion adapter slice (Milestone 2)

- Interface: `GmailIngestionAdapter.fetch_emails() -> list[RawEmail]`
- Implementations:
  - `MockGmailIngestionAdapter`: reads local sample payload JSON
  - `GmailAPIIngestionAdapter`: scaffold only, safe placeholder with TODOs
- Factory: `build_ingestion_adapter(mode)` chooses implementation from config

This keeps parser/AI/storage independent from where emails come from.

## 4) Module responsibilities

- `app/config.py`
  - Centralized environment settings
- `app/services/gmail_parser.py`
  - Transform raw Gmail-like payload to structured parsed object
- `app/services/ai_processor.py`
  - Enrich parsed object with category/summary/priority/review status
- `app/services/storage.py`
  - Save/retrieve activities through a storage abstraction
- `app/services/sheets_client.py`
  - Push selected rows to Google Sheets (scaffold)
- `app/api/routes.py`
  - HTTP endpoints for ingestion + dashboard reads
- `app/models/schemas.py`
  - Request/response and domain schema definitions

## 5) Data model (activity row)

- `id`
- `faculty_name`
- `source_type`
- `source_url`
- `raw_text`
- `ai_summary`
- `category`
- `priority`
- `detected_at`
- `review_status`

## 6) Reliability choices for project

- Mock mode enabled by default for fast local development
- Defensive parsing for missing/dirty email data
- Local JSON persistence to avoid setup friction
- Clear interfaces to migrate to SQLite/PostgreSQL later

## 7) Extensibility path

1. Replace mock ingestion with Gmail API poller/webhook
2. Replace heuristic AI with LLM-backed summarizer/classifier
3. Add SQLite repository; then PostgreSQL repository
4. Move from file-based writes to background queue/job processing
