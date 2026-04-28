import json
from pathlib import Path
from typing import Literal

PublicFetchMode = Literal["manual", "auto"]


class PublicFetchModeStore:
    """Small JSON-backed store for the public activity fetch mode."""

    DEFAULT_MODE: PublicFetchMode = "manual"

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def get_mode(self) -> PublicFetchMode:
        if not self.file_path.exists():
            return self.DEFAULT_MODE

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return self.DEFAULT_MODE

        mode = data.get("mode")
        return mode if mode in ("manual", "auto") else self.DEFAULT_MODE

    def set_mode(self, mode: PublicFetchMode) -> PublicFetchMode:
        self.file_path.write_text(json.dumps({"mode": mode}, indent=2), encoding="utf-8")
        return mode
