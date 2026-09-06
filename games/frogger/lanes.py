"""Frogger hazards."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from assets_loader import draw_ms_mark
from config import MS_COLORS

FROG_TILE = 40
COLS = 15
ROWS = 13


@dataclass
class Hazard:
    x: float
    w: float
    kind: str
    color: tuple[int, int, int]
    submerged: bool = False


@dataclass
class Lane:
    row: int
    speed: float
    hazards: list[Hazard] = field(default_factory=list)
    kind: str = "car"
    dive: bool = False
    dive_t: float = 0.0

    def update(self, dt: float, width: float) -> None:
        self.dive_t += dt
        for h in self.hazards:
            h.x += self.speed * dt
            if self.speed > 0 and h.x > width:
                h.x = -h.w
            if self.speed < 0 and h.x + h.w < 0:
                h.x = width
            if self.dive and self.kind == "log":
                h.submerged = int(self.dive_t / 3.0) % 2 == 1 and (self.dive_t % 3.0) > 2.0

    def draw(self, surf: pygame.Surface, ox: int, oy: int) -> None:
        y = oy + self.row * FROG_TILE + 6
        for h in self.hazards:
            if h.submerged:
                continue
            rect = pygame.Rect(int(ox + h.x), y, int(h.w), FROG_TILE - 12)
            pygame.draw.rect(surf, h.color, rect, border_radius=4)
            if h.kind == "car":
                draw_ms_mark(surf, pygame.Rect(rect.x + 6, rect.y + 6, 10, 10))


def build_lanes(level: int) -> list[Lane]:
    speed = 70 * (1.12 ** (level - 1))
    lanes: list[Lane] = []
    # rows 1-4 road
    for i, row in enumerate((4, 3, 2, 1)):
        direction = 1 if i % 2 == 0 else -1
        extra = 1 if level > 1 and i == 0 else 0
        lane = Lane(row=row, speed=speed * direction * (0.7 + i * 0.1), kind="car")
        count = 2 + extra
        gap = 180
        for n in range(count):
            lane.hazards.append(
                Hazard(x=n * gap, w=FROG_TILE * 2, kind="car", color=MS_COLORS[n % 4])
            )
        lanes.append(lane)
    # rows 6-9 water
    for i, row in enumerate((9, 8, 7, 6)):
        direction = -1 if i % 2 == 0 else 1
        lane = Lane(
            row=row,
            speed=speed * 0.6 * direction,
            kind="log",
            dive=level >= 2 and i == 1,
        )
        for n in range(3):
            lane.hazards.append(
                Hazard(x=n * 220, w=FROG_TILE * (2 + n % 3), kind="log", color=(20, 70, 80))
            )
        lanes.append(lane)
    return lanes
