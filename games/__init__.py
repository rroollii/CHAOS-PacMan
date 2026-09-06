"""Game registry — one failed import must not block the other six."""

from __future__ import annotations

import importlib

from config import GameId
from game_mode import GameMode

_SPECS: tuple[tuple[GameId, str, str], ...] = (
    (GameId.PACMAN, "games.pacman.mode", "PacmanMode"),
    (GameId.DONKEY_KONG, "games.donkey_kong.mode", "DonkeyKongMode"),
    (GameId.SNAKE, "games.snake.mode", "SnakeMode"),
    (GameId.BUBBLE_SHOT, "games.bubble_shot.mode", "BubbleShotMode"),
    (GameId.FROGGER, "games.frogger.mode", "FroggerMode"),
    (GameId.INVADERS, "games.invaders.mode", "InvadersMode"),
    (GameId.BREAKOUT, "games.breakout.mode", "BreakoutMode"),
)

MODE_CLASSES: dict[GameId, type[GameMode]] = {}
for _gid, _mod, _name in _SPECS:
    try:
        MODE_CLASSES[_gid] = getattr(importlib.import_module(_mod), _name)
    except Exception as exc:
        print(f"[shell] import {_gid.value} failed: {exc!r}")
