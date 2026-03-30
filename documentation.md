# Documentation — Ingestion Adapter Layer (Milestone 2)

## Goal
Introduce a small, clean ingestion architecture so the pipeline can switch between:
- local mock payload ingestion (`mock`)
- a future Gmail API path (`gmail`, scaffold for now)

## How the ingestion flow works

1. API route calls `_run_ingestion(mode=...)`.
2. `_run_ingestion` asks `build_ingestion_adapter(...)` for an adapter.
3. Adapter returns `list[RawEmail]`.
4. Each raw email is parsed by `GmailParser`.
5. Parsed activity is enriched by `AIProcessor`.
6. Final activity records are saved by storage.
7. If records exist, they are synced to Google Sheets.

Because all adapters return the same `RawEmail` schema, downstream services remain unchanged.

## Adapter types

### MockGmailIngestionAdapter
- Reads JSON payloads from `mock_email_payload_path`.
- Useful for local development and tests.

### GmailAPIIngestionAdapter (scaffold)
- Safe placeholder for future Gmail API integration.
- Currently logs intent and returns an empty list.
- Includes TODO comments for auth and payload conversion.

## Configuration

Use environment settings in `.env`:

```env
INGESTION_MODE=mock
MOCK_EMAIL_PAYLOAD_PATH=data/mock_emails/linkedin_notifications.json
```

Set `INGESTION_MODE=gmail` to exercise the Gmail scaffold path.

## Current limitations

- Gmail authentication is not implemented yet.
- Gmail API message retrieval and decoding is not implemented yet.
- This milestone intentionally focuses only on ingestion architecture.
