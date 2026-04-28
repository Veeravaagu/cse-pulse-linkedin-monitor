from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


def clear_pending_activities(file_path: str | Path = settings.data_file) -> dict[str, int]:
    path = Path(file_path)
    if not path.exists():
        return {"removed": 0, "preserved": 0}

    records = json.loads(path.read_text(encoding="utf-8") or "[]")
    preserved = [record for record in records if record.get("review_status") != "pending"]
    removed_count = len(records) - len(preserved)

    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(preserved, handle, indent=2)
        handle.flush()
        Path(handle.name).replace(path)

    return {"removed": removed_count, "preserved": len(preserved)}


def main() -> None:
    result = clear_pending_activities()
    print(f"removed_pending={result['removed']}")
    print(f"preserved_non_pending={result['preserved']}")


if __name__ == "__main__":
    main()
