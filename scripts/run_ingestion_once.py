from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.routes import _run_ingestion
from app.models.schemas import IngestResponse


def run_once(run_ingestion: Callable[[], IngestResponse] = _run_ingestion) -> IngestResponse:
    return run_ingestion()


def main() -> None:
    result = run_once()
    print(f"ingested_count={result.ingested_count}")
    for activity in result.activities:
        print(f"{activity.id}\t{activity.review_status.value}\t{activity.source_type}")


if __name__ == "__main__":
    main()
