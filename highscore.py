"""Named highscore persistence, one top-10 per GameId."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pygame

from config import DATA_DIR, GAME_ORDER, GameId, NAME_BLOCKLIST, NAME_MAX_LEN, NAME_MIN_LEN

HIGHSCORE_PATH = DATA_DIR / "highscores.json"
_NAME_RE = re.compile(r"^[A-Z0-9-]{3,8}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_name(raw: str) -> str:
    name = "".join(ch for ch in raw.upper() if ch.isalnum() or ch == "-")
    name = name.strip("-")[:NAME_MAX_LEN]
    return name


def name_blocked(name: str) -> bool:
    folded = name.casefold()
    return any(bad.casefold() in folded for bad in NAME_BLOCKLIST)


class HighscoreStore:
    def __init__(self, path: Path = HIGHSCORE_PATH) -> None:
        self.path = path
        self.games: dict[str, list[dict[str, Any]]] = {g.value: [] for g in GAME_ORDER}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.games = {g.value: [] for g in GAME_ORDER}
            return
        if "games" not in data and "entries" in data:
            migrated = []
            for entry in data.get("entries", []):
                entry = dict(entry)
                entry.setdefault("name", "---")
                migrated.append(entry)
            self.games = {g.value: [] for g in GAME_ORDER}
            self.games[GameId.PACMAN.value] = migrated[:10]
            return
        games = data.get("games", {})
        for gid in GAME_ORDER:
            rows = []
            for entry in games.get(gid.value, []):
                item = dict(entry)
                item.setdefault("name", "---")
                rows.append(item)
            self.games[gid.value] = rows[:10]

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _now(), "games": self.games}
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def table(self, game_id: GameId) -> list[dict[str, Any]]:
        return list(self.games[game_id.value])

    def qualifies(self, game_id: GameId, score: int) -> bool:
        return self.prospective_rank(game_id, score) > 0

    def prospective_rank(self, game_id: GameId, score: int) -> int:
        if score <= 0:
            return 0
        rows = self.table(game_id)
        for i, row in enumerate(rows, start=1):
            if score >= int(row["score"]):
                return i
        if len(rows) < 10:
            return len(rows) + 1
        return 0

    def add(self, game_id: GameId, name: str, score: int, level: int) -> int:
        clean = sanitize_name(name)
        if len(clean) < NAME_MIN_LEN or not _NAME_RE.match(clean) or name_blocked(clean):
            return 0
        if score <= 0:
            return 0
        rows = self.games[game_id.value]
        entry = {"name": clean, "score": int(score), "level": int(level), "ts": _now()}
        rows.append(entry)
        rows.sort(key=lambda r: (int(r["score"]), r.get("ts", "")), reverse=True)
        self.games[game_id.value] = rows[:10]
        self.save()
        for i, row in enumerate(self.games[game_id.value], start=1):
            if row is entry or (row["name"] == clean and row["score"] == score and row["ts"] == entry["ts"]):
                return i
        return 0

    def clear_all(self) -> None:
        self.games = {g.value: [] for g in GAME_ORDER}
        self.save()


def draw_highscore_table(
    surf: pygame.Surface,
    game_id: GameId,
    store: HighscoreStore,
    rect: pygame.Rect,
    font: pygame.font.Font,
    highlight_rank: int | None = None,
    blink: bool = False,
    pending_score: int | None = None,
) -> None:
    from config import COLOR_AMBER, COLOR_BG, COLOR_CYAN, COLOR_HUD, GAME_TITLES

    pygame.draw.rect(surf, COLOR_BG, rect.inflate(16, 16))
    pygame.draw.rect(surf, COLOR_CYAN, rect.inflate(16, 16), 2)
    title = font.render(f"HI-SCORE  {GAME_TITLES[game_id]}", True, COLOR_AMBER)
    surf.blit(title, (rect.x, rect.y))
    rows = store.table(game_id)
    line_h = max(28, font.get_height() + 4)
    for i in range(10):
        if highlight_rank == i + 1 and pending_score is not None:
            name = "........"
            score = f"{int(pending_score):06d}"
        elif i < len(rows):
            name = str(rows[i].get("name", "---"))[:8].ljust(8)
            score = f"{int(rows[i]['score']):06d}"
        else:
            name = "---     "
            score = "000000"
        text = f"{i + 1:02d}  {name}  {score}"
        color = COLOR_AMBER if i == 0 else COLOR_HUD
        if highlight_rank == i + 1:
            color = COLOR_CYAN
            if blink:
                continue
        img = font.render(text, True, color)
        surf.blit(img, (rect.x, rect.y + 36 + i * line_h))
