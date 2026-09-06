"""Girders, ladders, goal."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from assets_loader import draw_ms_mark
from config import COLOR_AMBER, COLOR_CYAN, COLOR_ORANGE


@dataclass
class Girder:
    x: int
    y: int
    w: int
    slope: float


@dataclass
class Ladder:
    x: int
    y: int
    h: int


GIRDERS = [
    Girder(160, 600, 880, 0.04),
    Girder(200, 520, 820, -0.04),
    Girder(160, 440, 860, 0.04),
    Girder(200, 360, 820, -0.04),
    Girder(160, 280, 860, 0.04),
    Girder(220, 200, 780, 0.0),
]

LADDERS = [
    Ladder(320, 520, 80),
    Ladder(780, 520, 80),
    Ladder(500, 440, 80),
    Ladder(300, 360, 80),
    Ladder(760, 360, 80),
    Ladder(480, 280, 80),
    Ladder(700, 200, 80),
]

GOAL = pygame.Rect(860, 150, 48, 40)
GORILLA = pygame.Rect(260, 108, 88, 96)


def girder_y(g: Girder, x: float) -> float:
    t = (x - g.x) / max(1, g.w)
    return g.y + (t - 0.5) * g.slope * g.w * 2


def draw_stage(surf: pygame.Surface) -> None:
    for g in GIRDERS:
        points = []
        for i in range(0, g.w, 16):
            x = g.x + i
            points.append((x, girder_y(g, x)))
        points.append((g.x + g.w, girder_y(g, g.x + g.w)))
        if len(points) > 1:
            pygame.draw.lines(surf, COLOR_ORANGE, False, points, 8)
            for p in points[::3]:
                pygame.draw.circle(surf, (200, 160, 80), (int(p[0]), int(p[1])), 3)
    for lad in LADDERS:
        pygame.draw.line(surf, COLOR_CYAN, (lad.x, lad.y), (lad.x, lad.y + lad.h), 3)
        pygame.draw.line(surf, COLOR_CYAN, (lad.x + 16, lad.y), (lad.x + 16, lad.y + lad.h), 3)
        for yy in range(lad.y, lad.y + lad.h, 10):
            pygame.draw.line(surf, COLOR_CYAN, (lad.x, yy), (lad.x + 16, yy), 2)
    pygame.draw.rect(surf, COLOR_AMBER, GOAL, border_radius=6)
    draw_ms_mark(surf, GOAL.inflate(-8, -8))
