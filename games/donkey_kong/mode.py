"""DonkeyKongMode — climb to the contract gorilla."""

from __future__ import annotations

import random

import pygame

from assets_loader import LOGOS, draw_ms_mark, draw_stick_hero
from config import COLOR_BG, COLOR_HUD, GameId
from game_mode import GameMode, Result
from games.donkey_kong.barrels import Barrel, draw_barrel, spawn, update_barrel
from games.donkey_kong.stage import GOAL, GORILLA, GIRDERS, LADDERS, draw_stage, girder_y
from input_map import Command

GRAVITY = 2200
TERMINAL = 720
RUN = 180
JUMP_V = -620
CLIMB = 140
AIR_CTRL = 0.35
TIMER = 45.0


class DonkeyKongMode(GameMode):
    id = GameId.DONKEY_KONG

    def __init__(self) -> None:
        self.x = 220.0
        self.y = 560.0
        self.vx = 0.0
        self.vy = 0.0
        self.grounded = False
        self.climbing = False
        self.facing = "RIGHT"
        self.pose = "IDLE"
        self.walk_t = 0.0
        self.barrels: list[Barrel] = []
        self.throw_t = 0.0
        self.timer = TIMER
        self.bonus_rows: set[int] = set()
        self._score = 0
        self._level = 1
        self._lives = 3
        self.freeze = 0.0
        self._cmd = Command(0, 0, False, False, False, False, 0, False, False, False)
        self.reset()

    def reset(self) -> None:
        self._spawn()
        self.barrels = []
        self.throw_t = 0.0
        self.timer = TIMER
        self.bonus_rows = set()
        self._score = 0
        self._level = 1
        self._lives = 3
        self.freeze = 0.0

    def _spawn(self) -> None:
        self.x, self.y = 220.0, 560.0
        self.vx = self.vy = 0.0
        self.grounded = True
        self.climbing = False
        self.facing = "RIGHT"
        self.pose = "IDLE"

    def score(self) -> int:
        return self._score

    def level(self) -> int:
        return self._level

    def lives(self) -> int:
        return self._lives

    def on_command(self, cmd: Command) -> None:
        self._cmd = cmd

    def _on_ladder(self) -> object | None:
        body = pygame.Rect(int(self.x) - 12, int(self.y) - 20, 24, 40)
        for lad in LADDERS:
            lrect = pygame.Rect(lad.x - 4, lad.y, 24, lad.h)
            if body.colliderect(lrect):
                overlap = body.clip(lrect).width / max(1, body.width)
                if overlap >= 0.4:
                    return lad
        return None

    def update(self, dt: float) -> Result:
        cmd = getattr(self, "_cmd", Command(0, 0, False, False, False, False, 0, False, False, False))
        if self.freeze > 0:
            self.freeze -= dt
            return Result.CONTINUE
        self.timer -= dt
        if self.timer <= 0:
            return self._die()
        lad = self._on_ladder()
        if lad and cmd.dy != 0:
            self.climbing = True
            self.vy = 0
            self.vx = 0
            if cmd.dy < 0:
                self.y -= CLIMB * dt
            else:
                self.y += CLIMB * dt
            self.pose = "CLIMB"
        else:
            self.climbing = False
            if self.grounded and cmd.action:
                self.vy = JUMP_V
                self.grounded = False
                self.pose = "JUMP"
            accel = RUN if self.grounded else RUN * AIR_CTRL
            self.vx = cmd.dx * accel
            if cmd.dx:
                self.facing = "RIGHT" if cmd.dx > 0 else "LEFT"
            self.vy = min(TERMINAL, self.vy + GRAVITY * dt)
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.grounded = False
            feet = self.y + 22
            for idx, g in enumerate(GIRDERS):
                if g.x - 8 <= self.x <= g.x + g.w + 8:
                    gy = girder_y(g, self.x)
                    if gy - 10 <= feet <= gy + 12 and self.vy >= 0:
                        self.y = gy - 22
                        self.vy = 0
                        self.grounded = True
                        if idx not in self.bonus_rows:
                            self.bonus_rows.add(idx)
                            self._score += 50
            if self.grounded:
                self.walk_t += dt
                self.pose = "IDLE" if cmd.dx == 0 else ("WALK_A" if int(self.walk_t * 8) % 2 == 0 else "WALK_B")
            else:
                self.pose = "JUMP"
        self.x = max(170, min(1040, self.x))
        interval = max(0.7, 1.6 - 0.12 * (self._level - 1))
        self.throw_t += dt
        if self.throw_t >= interval:
            self.throw_t = 0
            self.barrels.append(spawn(random.random() < 0.15))
        body = pygame.Rect(int(self.x) - 10, int(self.y) - 16, 20, 36)
        for b in list(self.barrels):
            if not update_barrel(b, dt):
                self.barrels.remove(b)
                continue
            brect = pygame.Rect(int(b.x) - 10, int(b.y) - 8, 20, 16)
            if body.colliderect(brect):
                if self.vy < 0 or (self.y + 22) < (b.y - 4):
                    self._score += 100
                    self.barrels.remove(b)
                else:
                    return self._die()
        if body.colliderect(GOAL):
            self._score += 500 + int(self.timer) * 10
            self._level += 1
            self.timer = TIMER
            self.bonus_rows.clear()
            self.barrels.clear()
            self._spawn()
        return Result.CONTINUE

    def _die(self) -> Result:
        self._lives -= 1
        if self._lives <= 0:
            return Result.GAME_OVER
        self.freeze = 1.2
        self._spawn()
        self.timer = TIMER
        return Result.CONTINUE

    def attract_tick(self, dt: float) -> None:
        self._cmd = Command(1, -1, False, False, False, False, 0, False, True, False)
        if self.update(dt) is Result.GAME_OVER:
            self.reset()

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(COLOR_BG)
        draw_stage(surf)
        # gorilla
        pygame.draw.ellipse(surf, (90, 58, 34), GORILLA)
        pygame.draw.circle(surf, (90, 58, 34), (GORILLA.centerx, GORILLA.top + 22), 22)
        pygame.draw.circle(surf, (90, 58, 34), (GORILLA.left + 16, GORILLA.top + 14), 8)
        pygame.draw.circle(surf, (90, 58, 34), (GORILLA.right - 16, GORILLA.top + 14), 8)
        shirt = pygame.Rect(GORILLA.x + 22, GORILLA.y + 40, 44, 28)
        pygame.draw.rect(surf, (244, 241, 234), shirt)
        draw_ms_mark(surf, shirt, label=True)
        for b in self.barrels:
            draw_barrel(surf, b)
        logo = LOGOS.get_facing("logo_dk", self.facing)
        draw_stick_hero(surf, logo, (int(self.x), int(self.y)), self.facing, self.pose)
        font = pygame.font.Font(None, 28)
        surf.blit(font.render(f"TIME {int(self.timer):02d}", True, COLOR_HUD), (40, 88))
