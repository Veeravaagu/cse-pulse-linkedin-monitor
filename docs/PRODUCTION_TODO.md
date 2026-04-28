# Production TODO

Completed items were moved into `README.md` (runtime env vars, deployment steps, cron usage, and main-dashboard integration contract).

## Remaining Future TODOs
- Add optional query filters for `GET /activities/public`:
  - `limit`
  - `category`
  - `since`
  - `source_type`
- Define and implement backup strategy for runtime `data/*.json` files.
- Decide long-term storage backend (move from local JSON to managed DB when ready).
- Add optional multi-user accounts and roles when needed.
- Add optional audit logs for admin actions (mode changes, review status updates, deletes, ingestion triggers).
