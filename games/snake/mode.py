"""SnakeMode — eat unused Microsoft seats."""

from __future__ import annotations

import math
import random
import time

import pygame

from assets_loader import LOGOS, draw_ms_mark
from config import COLOR_BG, COLOR_CYAN, GameId, INTERNAL_W
from game_mode import GameMode, Result
from input_map import Command

SNAKE_COLS = 28
SNAKE_ROWS = 16
SNAKE_TILE = 32
STEP0 = 0.16
REVERSE = {(-1, 0): (1, 0), (1, 0): (-1, 0), (0, -1): (0, 1), (0, 1): (0, -1)}


class SnakeMode(GameMode):
    id = GameId.SNAKE

    def __init__(self) -> None:
        self.body: list[tuple[int, int]] = []
        self.direction = (1, 0)
        self.queued = (1, 0)
        self.food = (10, 8)
        self.acc = 0.0
        self.step = STEP0
        self.foods = 0
        self._score = 0
        self._level = 1
        self.ox = 0
        self.oy = 80
        self.reset()

    def reset(self) -> None:
        self.ox = (INTERNAL_W - SNAKE_COLS * SNAKE_TILE) // 2
        self.oy = 80 + 16
        mid = (SNAKE_COLS // 2, SNAKE_ROWS // 2)
        self.body = [(mid[0] - i, mid[1]) for i in range(4)]
        self.direction = (1, 0)
        self.queued = (1, 0)
        self.foods = 0
        self._score = 0
        self._level = 1
        self.step = STEP0
        self.acc = 0.0
        self._place_food()

    def _place_food(self) -> None:
        free = [(c, r) for c in range(SNAKE_COLS) for r in range(SNAKE_ROWS) if (c, r) not in self.body]
        self.food = random.choice(free) if free else (0, 0)

    def score(self) -> int:
        return self._score

    def level(self) -> int:
        return self._level

    def lives(self) -> int:
        return 1

    def on_command(self, cmd: Command) -> None:
        nxt = None
        if cmd.dx < 0:
            nxt = (-1, 0)
        elif cmd.dx > 0:
            nxt = (1, 0)
        elif cmd.dy < 0:
            nxt = (0, -1)
        elif cmd.dy > 0:
            nxt = (0, 1)
        if nxt and nxt != REVERSE.get(self.direction):
            self.queued = nxt

    def update(self, dt: float) -> Result:
        self.acc += dt
        if self.acc < self.step:
            return Result.CONTINUE
        self.acc -= self.step
        self.direction = self.queued
        hx, hy = self.body[0]
        nx, ny = hx + self.direction[0], hy + self.direction[1]
        if nx < 0 or ny < 0 or nx >= SNAKE_COLS or ny >= SNAKE_ROWS or (nx, ny) in self.body:
            return Result.GAME_OVER
        self.body.insert(0, (nx, ny))
        if (nx, ny) == self.food:
            self._score += 10 * len(self.body)
            self.foods += 1
            self._level = 1 + self.foods // 5
            self.step = max(0.07, STEP0 * (0.94 ** self.foods))
            self._place_food()
        else:
            self.body.pop()
        return Result.CONTINUE

    def attract_tick(self, dt: float) -> None:
        hx, hy = self.body[0]
        fx, fy = self.food
        if abs(fx - hx) > abs(fy - hy):
            self.queued = (1 if fx > hx else -1, 0)
        else:
            self.queued = (0, 1 if fy > hy else -1)
        if self.queued == REVERSE.get(self.direction):
            self.queued = self.direction
        if self.update(dt) is Result.GAME_OVER:
            self.reset()

    def _cell(self, c: int, r: int) -> pygame.Rect:
        return pygame.Rect(self.ox + c * SNAKE_TILE, self.oy + r * SNAKE_TILE, SNAKE_TILE, SNAKE_TILE)

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(COLOR_BG)
        border = pygame.Rect(self.ox - SNAKE_TILE, self.oy - SNAKE_TILE, (SNAKE_COLS + 2) * SNAKE_TILE, (SNAKE_ROWS + 2) * SNAKE_TILE)
        pygame.draw.rect(surf, COLOR_CYAN, border, 3)
        draw_ms_mark(surf, pygame.Rect(border.x + 4, border.y + 4, 14, 14))
        draw_ms_mark(surf, pygame.Rect(border.right - 18, border.y + 4, 14, 14))
        pulse = 1.0 + 0.08 * math.sin(time.perf_counter() * 4 * math.pi)
        fr = self._cell(*self.food).inflate(int(-6 * pulse), int(-6 * pulse))
        draw_ms_mark(surf, fr)
        facing = {(1, 0): "RIGHT", (-1, 0): "LEFT", (0, -1): "UP", (0, 1): "DOWN"}[self.direction]
        for i, (c, r) in enumerate(self.body):
            cell = self._cell(c, r)
            if i == 0:
                logo = LOGOS.get_facing("logo_tile", facing)
                surf.blit(logo, logo.get_rect(center=cell.center))
            else:
                body = LOGOS.get("logo_snake_body")
                tinted = LOGOS.tint(body, COLOR_CYAN)
                tinted.set_alpha(max(90, 220 - i * 8))
                surf.blit(tinted, tinted.get_rect(center=cell.center))
