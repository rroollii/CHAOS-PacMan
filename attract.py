"""Attract demo for the featured game only."""

from __future__ import annotations

from game_mode import GameMode


class AttractController:
    def tick(self, mode: GameMode, dt: float) -> None:
        mode.attract_tick(dt)
