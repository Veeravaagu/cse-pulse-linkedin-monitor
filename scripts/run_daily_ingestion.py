from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_INGEST_URL = "http://127.0.0.1:8000/ingest"


def _ingest_url() -> str:
    base_url = os.environ.get("INGESTION_BASE_URL") or os.environ.get("INGESTION_URL") or DEFAULT_INGEST_URL
    return base_url.rstrip("/") + "/ingest" if not base_url.rstrip("/").endswith("/ingest") else base_url.rstrip("/")


def run_once(ingest_url: str | None = None) -> dict[str, object]:
    url = ingest_url or _ingest_url()
    request = Request(url, method="POST", headers={"Content-Type": "application/json"})

    try:
        with urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        message = f"ingestion request failed with HTTP {exc.code}"
        if detail:
            message += f": {detail}"
        raise RuntimeError(message) from exc
    except URLError as exc:
        raise RuntimeError(f"could not reach ingestion endpoint at {url}: {exc.reason}") from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ingestion endpoint returned invalid JSON") from exc

    if not isinstance(data, dict):
        raise RuntimeError("ingestion endpoint returned an unexpected response shape")

    return data


def main() -> None:
    try:
        result = run_once()
    except Exception as exc:
        print(f"daily ingestion failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    ingested_count = result.get("ingested_count")
    print(f"ingested_count={ingested_count}")
    for activity in result.get("activities", []):
        if isinstance(activity, dict):
            print(f"{activity.get('id')}\t{activity.get('review_status')}\t{activity.get('source_type')}")


if __name__ == "__main__":
    main()
