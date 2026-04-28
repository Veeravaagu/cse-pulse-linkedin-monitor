from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


def _write_records(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(records, handle, indent=2)
        handle.flush()
        Path(handle.name).replace(path)


def reset_local_ingestion_state(
    *,
    activities_file: str | Path = settings.data_file,
    state_file: str | Path = settings.ingestion_state_file,
    clear_all: bool = False,
) -> dict[str, int | bool]:
    activities_path = Path(activities_file)
    state_path = Path(state_file)
    records = json.loads(activities_path.read_text(encoding="utf-8") or "[]") if activities_path.exists() else []

    if clear_all:
        preserved: list[dict[str, object]] = []
    else:
        preserved = [record for record in records if record.get("review_status") != "pending"]

    _write_records(activities_path, preserved)

    cursor_existed = state_path.exists()
    if cursor_existed:
        state_path.unlink()

    return {
        "removed_activities": len(records) - len(preserved),
        "preserved_activities": len(preserved),
        "cursor_reset": cursor_existed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Development-only reset for local activity data and Gmail ingestion cursor.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Remove all local activities. Without this flag, only pending activities are removed.",
    )
    args = parser.parse_args()

    result = reset_local_ingestion_state(clear_all=args.all)
    print(f"removed_activities={result['removed_activities']}")
    print(f"preserved_activities={result['preserved_activities']}")
    print(f"cursor_reset={str(result['cursor_reset']).lower()}")


if __name__ == "__main__":
    main()
