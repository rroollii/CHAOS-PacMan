"""Persisted featured GameId."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR, GameId

CABINET_PATH = DATA_DIR / "cabinet.json"


class CabinetStore:
    def __init__(self, path: Path = CABINET_PATH) -> None:
        self.path = path

    def load(self) -> GameId:
        if not self.path.exists():
            return GameId.PACMAN
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return GameId(data.get("featured_game", "PACMAN"))
        except (OSError, json.JSONDecodeError, ValueError):
            return GameId.PACMAN

    def save(self, game_id: GameId) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "featured_game": game_id.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)
