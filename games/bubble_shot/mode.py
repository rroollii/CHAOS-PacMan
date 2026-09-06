"""BubbleShotMode — sort the SKUs."""

from __future__ import annotations

import math
import random

import pygame

from assets_loader import LOGOS, draw_ms_mark
from config import COLOR_BG, COLOR_CYAN, COLOR_DANGER, GameId, INTERNAL_W
from game_mode import GameMode, Result
from games.bubble_shot.grid import (
    BUBBLE_D,
    cell_pos,
    colors_for,
    flood,
    generate,
    hanging,
    nearest_slot,
)
from input_map import Command

CEILING = {1: 6, 3: 5, 5: 4}


class BubbleShotMode(GameMode):
    id = GameId.BUBBLE_SHOT

    def __init__(self) -> None:
        self.ox = (INTERNAL_W - 10 * BUBBLE_D) // 2
        self.oy = 100
        self.grid: dict[tuple[int, int], tuple[int, int, int]] = {}
        self.angle = 0.0
        self.current = (243, 83, 37)
        self.next = (129, 188, 6)
        self.flying: dict[str, float | tuple[int, int, int]] | None = None
        self.shots = 0
        self._score = 0
        self._level = 1
        self._last_cmd: Command | None = None
        self.reset()

    def reset(self) -> None:
        self.grid = generate(1)
        self.angle = 0.0
        pal = colors_for(1)
        self.current = random.choice(pal)
        self.next = random.choice(pal)
        self.flying = None
        self.shots = 0
        self._score = 0
        self._level = 1
        self._last_cmd = None

    def score(self) -> int:
        return self._score

    def level(self) -> int:
        return self._level

    def lives(self) -> int:
        return 1

    def _ceiling_every(self) -> int:
        if self._level >= 5:
            return 4
        if self._level >= 3:
            return 5
        return 6

    def on_command(self, cmd: Command) -> None:
        self._last_cmd = cmd
        if cmd.dy < 0:
            self.angle -= 8
        elif cmd.dy > 0:
            self.angle += 8
        self.angle = max(-75, min(75, self.angle))
        if cmd.action and self.flying is None:
            rad = math.radians(self.angle)
            self.flying = {
                "x": INTERNAL_W / 2,
                "y": 640,
                "vx": math.sin(rad) * 720,
                "vy": -math.cos(rad) * 720,
                "color": self.current,
            }
            self.current = self.next
            self.next = random.choice(colors_for(self._level))

    def _shift_down(self) -> None:
        shifted: dict[tuple[int, int], tuple[int, int, int]] = {}
        for (r, c), color in self.grid.items():
            shifted[(r + 1, c)] = color
        pal = colors_for(self._level)
        for c in range(10):
            shifted[(0, c)] = random.choice(pal)
        self.grid = shifted

    def update(self, dt: float) -> Result:
        if self._last_cmd is not None:
            self.angle = max(-75, min(75, self.angle + self._last_cmd.dx * 90 * dt))
        if self.flying:
            self.flying["x"] += self.flying["vx"] * dt  # type: ignore[operator]
            self.flying["y"] += self.flying["vy"] * dt  # type: ignore[operator]
            left = self.ox
            right = self.ox + 10 * BUBBLE_D
            if self.flying["x"] < left + 18:  # type: ignore[operator]
                self.flying["x"] = left + 18
                self.flying["vx"] *= -1  # type: ignore[operator]
            if self.flying["x"] > right - 18:  # type: ignore[operator]
                self.flying["x"] = right - 18
                self.flying["vx"] *= -1  # type: ignore[operator]
            hit = self.flying["y"] <= self.oy + 18  # type: ignore[operator]
            for (r, c), _ in self.grid.items():
                px, py = cell_pos(r, c, self.ox, self.oy)
                if math.hypot(px - self.flying["x"], py - self.flying["y"]) < BUBBLE_D * 0.85:  # type: ignore[arg-type]
                    hit = True
                    break
            if hit:
                slot = nearest_slot(self.grid, float(self.flying["x"]), float(self.flying["y"]), self.ox, self.oy)
                color = self.flying["color"]
                self.grid[slot] = color  # type: ignore[index]
                group = flood(self.grid, slot)
                chain = 0
                if len(group) >= 3:
                    self._score += 50 * len(group)
                    for key in group:
                        del self.grid[key]
                    fallen = hanging(self.grid)
                    chain = 1
                    while fallen:
                        self._score += 20 * len(fallen) * chain
                        for key in fallen:
                            del self.grid[key]
                        chain += 1
                        fallen = hanging(self.grid)
                self.flying = None
                self.shots += 1
                if self.shots % self._ceiling_every() == 0:
                    self._shift_down()
                if any(cell_pos(r, c, self.ox, self.oy)[1] > 560 for (r, c) in self.grid):
                    return Result.GAME_OVER
                if not self.grid:
                    self._score += 1000
                    self._level += 1
                    self.grid = generate(self._level)
                    self.shots = 0
        return Result.CONTINUE

    def attract_tick(self, dt: float) -> None:
        self.angle = 25 * math.sin(pygame.time.get_ticks() / 400)
        if self.flying is None and random.random() < 0.02:
            self.on_command(Command(0, 0, False, True, False, False, 0, True, True, False))
        if self.update(dt) is Result.GAME_OVER:
            self.reset()

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(COLOR_BG)
        pygame.draw.rect(surf, COLOR_CYAN, (self.ox, self.oy - 16, 10 * BUBBLE_D, 14))
        for i in range(6):
            draw_ms_mark(surf, pygame.Rect(self.ox + 8 + i * 56, self.oy - 14, 12, 12))
        font = pygame.font.Font(None, 18)
        label = font.render("MICROSOFT", True, COLOR_BG)
        surf.blit(label, (INTERNAL_W // 2 - label.get_width() // 2, self.oy - 14))
        for (r, c), color in self.grid.items():
            px, py = cell_pos(r, c, self.ox, self.oy)
            pygame.draw.circle(surf, color, (px, py), BUBBLE_D // 2 - 1)
            pygame.draw.circle(surf, (244, 241, 234), (px, py), BUBBLE_D // 2 - 1, 2)
            mini = LOGOS.get("logo_nest")
            mini = mini.copy()
            mini.set_alpha(40)
            surf.blit(mini, mini.get_rect(center=(px, py)))
        pygame.draw.line(surf, COLOR_DANGER, (self.ox, 560), (self.ox + 10 * BUBBLE_D, 560), 2)
        cannon = LOGOS.cannon_at(int(self.angle))
        cx, cy = INTERNAL_W // 2, 640
        rad = math.radians(self.angle)
        pygame.draw.rect(surf, COLOR_CYAN, pygame.Rect(0, 0, 8, 36).move(0, 0))
        barrel = pygame.Surface((8, 36), pygame.SRCALPHA)
        barrel.fill(COLOR_CYAN)
        rot = pygame.transform.rotate(barrel, -self.angle)
        surf.blit(rot, rot.get_rect(center=(cx + math.sin(rad) * 20, cy - math.cos(rad) * 20)))
        surf.blit(cannon, cannon.get_rect(center=(cx, cy)))
        preview = LOGOS.tint(LOGOS.get("logo_bubble"), self.next)
        surf.blit(preview, preview.get_rect(center=(cx + 48, cy + 8)))
        # aim line
        x, y = float(cx), float(cy)
        vx, vy = math.sin(rad) * 18, -math.cos(rad) * 18
        bounced = False
        for _ in range(40):
            x += vx
            y += vy
            if x < self.ox + 8 or x > self.ox + 10 * BUBBLE_D - 8:
                if not bounced:
                    vx *= -1
                    bounced = True
            pygame.draw.circle(surf, (*COLOR_CYAN, ), (int(x), int(y)), 2)
        if self.flying:
            bubble = LOGOS.tint(LOGOS.get("logo_bubble"), self.flying["color"])  # type: ignore[arg-type]
            surf.blit(bubble, bubble.get_rect(center=(int(self.flying["x"]), int(self.flying["y"]))))  # type: ignore[arg-type]
