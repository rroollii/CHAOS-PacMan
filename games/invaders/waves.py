"""Invader formation."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from assets_loader import draw_ms_mark
from config import COLOR_PINK, MS_COLORS


@dataclass
class Invader:
    col: int
    row: int
    alive: bool = True


@dataclass
class Bomb:
    x: float
    y: float


def row_color(row: int, rows: int) -> tuple[int, int, int]:
    if row == 0:
        return COLOR_PINK
    return MS_COLORS[(rows - 1 - row) % 4]


def draw_invader(surf: pygame.Surface, x: int, y: int, color: tuple[int, int, int]) -> None:
    pygame.draw.rect(surf, color, (x - 14, y - 10, 28, 20), border_radius=2)
    pygame.draw.rect(surf, (244, 241, 234), (x - 14, y - 10, 28, 20), 2, border_radius=2)
    draw_ms_mark(surf, pygame.Rect(x - 4, y - 4, 8, 8))
