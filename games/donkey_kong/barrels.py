"""True-up rolls and fall-notices."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from assets_loader import draw_ms_mark
from config import COLOR_DANGER, MS_RED
from games.donkey_kong.stage import GIRDERS, girder_y


@dataclass
class Barrel:
    x: float
    y: float
    vx: float
    vy: float
    falling: bool
    girder: int


def spawn(falling: bool) -> Barrel:
    g = GIRDERS[-1]
    return Barrel(x=g.x + 80, y=g.y - 18, vx=120 if not falling else 0, vy=220 if falling else 0, falling=falling, girder=len(GIRDERS) - 1)


def update_barrel(b: Barrel, dt: float) -> bool:
    if b.falling:
        b.y += 280 * dt
        return b.y < 680
    g = GIRDERS[b.girder]
    b.x += (1 if g.slope >= 0 else -1) * (140 * dt) * (1 if g.slope != 0 else (1 if b.vx >= 0 else -1))
    if g.slope == 0:
        b.x += b.vx * dt * 0.01
        b.x += 90 * dt
    b.y = girder_y(g, b.x) - 14
    if b.x < g.x + 8 or b.x > g.x + g.w - 8:
        if b.girder > 0:
            b.girder -= 1
            b.falling = False
            ng = GIRDERS[b.girder]
            b.x = max(ng.x + 10, min(ng.x + ng.w - 10, b.x))
            b.y = girder_y(ng, b.x) - 14
        else:
            return False
    return b.y < 700


def draw_barrel(surf: pygame.Surface, b: Barrel) -> None:
    rect = pygame.Rect(int(b.x) - 12, int(b.y) - 10, 24 if not b.falling else 16, 20)
    pygame.draw.ellipse(surf, MS_RED if not b.falling else COLOR_DANGER, rect)
    pygame.draw.ellipse(surf, (244, 241, 234), rect, 2)
    draw_ms_mark(surf, pygame.Rect(rect.centerx - 4, rect.centery - 4, 8, 8))
