"""FroggerMode — cross the renewal."""

from __future__ import annotations

import pygame

from assets_loader import LOGOS, draw_ms_mark, draw_stick_hero
from config import COLOR_AMBER, COLOR_BG, COLOR_CYAN, COLOR_DANGER, GameId, INTERNAL_W
from game_mode import GameMode, Result
from games.frogger.lanes import COLS, FROG_TILE, ROWS, Lane, build_lanes
from input_map import Command

HOP_COOLDOWN = 0.12
TIMER0 = 20.0


class FroggerMode(GameMode):
    id = GameId.FROGGER

    def __init__(self) -> None:
        self.col = 7
        self.row = 0
        self.fx = 0.0
        self.facing = "UP"
        self.homes = [False] * 5
        self.lanes: list[Lane] = []
        self.cool = 0.0
        self.timer = TIMER0
        self.hop_t = 0.0
        self._score = 0
        self._level = 1
        self._lives = 3
        self.ox = 0
        self.oy = 90
        self._prev_hop = (0, 0, False)
        self.reset()

    def reset(self) -> None:
        self.ox = (INTERNAL_W - COLS * FROG_TILE) // 2
        self.oy = 90
        self.col = 7
        self.row = 0
        self.fx = 0.0
        self.facing = "UP"
        self.homes = [False] * 5
        self.lanes = build_lanes(1)
        self.cool = 0.0
        self.timer = TIMER0
        self.hop_t = 0.0
        self._score = 0
        self._level = 1
        self._lives = 3
        self._prev_hop = (0, 0, False)

    def score(self) -> int:
        return self._score

    def level(self) -> int:
        return self._level

    def lives(self) -> int:
        return self._lives

    def _spawn(self) -> None:
        self.col = 7
        self.row = 0
        self.fx = 0.0
        self.facing = "UP"
        self.timer = max(12.0, TIMER0 - (self._level - 1) * 1.5)

    def on_command(self, cmd: Command) -> None:
        hop = (cmd.dx, cmd.dy, cmd.action)
        if hop == self._prev_hop:
            return
        self._prev_hop = hop
        if self.cool > 0:
            return
        dc = dr = 0
        if cmd.dx < 0:
            dc, self.facing = -1, "LEFT"
        elif cmd.dx > 0:
            dc, self.facing = 1, "RIGHT"
        elif cmd.dy < 0 or cmd.action:
            dr, self.facing = 1, "UP"
        elif cmd.dy > 0:
            dr, self.facing = -1, "DOWN"
        else:
            return
        nc, nr = self.col + dc, self.row + dr
        if nc < 0 or nc >= COLS or nr < 0 or nr >= ROWS:
            return
        if nr == 11 and nc % 3 != 1:
            return
        if nr == 11 and self.homes[nc // 3]:
            return
        self.col, self.row = nc, nr
        self.fx = 0.0
        self.cool = HOP_COOLDOWN
        self.hop_t = 0.08
        if dr == 1 and nr < 11:
            self._score += 10

    def _player_rect(self) -> pygame.Rect:
        x = self.ox + self.col * FROG_TILE + int(self.fx)
        y = self.oy + (ROWS - 1 - self.row) * FROG_TILE
        return pygame.Rect(x + 6, y + 6, FROG_TILE - 12, FROG_TILE - 12)

    def _die(self) -> Result:
        self._lives -= 1
        if self._lives <= 0:
            return Result.GAME_OVER
        self._spawn()
        return Result.CONTINUE

    def update(self, dt: float) -> Result:
        self.cool = max(0.0, self.cool - dt)
        self.hop_t = max(0.0, self.hop_t - dt)
        self.timer -= dt
        if self.timer <= 0:
            return self._die()
        width = COLS * FROG_TILE
        on_log = None
        for lane in self.lanes:
            lane.update(dt, width)
            screen_row = ROWS - 1 - lane.row
            # lane.row is from bottom in our build (1-4 road, 6-9 water)
        # remap: our row 0 is start (bottom). lane.row is also from bottom.
        prect = self._player_rect()
        for lane in self.lanes:
            if self.row != lane.row:
                continue
            for h in lane.hazards:
                hx = self.ox + h.x
                hy = self.oy + (ROWS - 1 - lane.row) * FROG_TILE
                hrect = pygame.Rect(int(hx), hy + 4, int(h.w), FROG_TILE - 8)
                if prect.colliderect(hrect) and not h.submerged:
                    if lane.kind == "car":
                        return self._die()
                    on_log = lane
        if 6 <= self.row <= 9:
            if on_log is None:
                return self._die()
            self.fx += on_log.speed * dt
            abs_x = self.ox + self.col * FROG_TILE + self.fx
            if abs_x < self.ox or abs_x > self.ox + width - FROG_TILE:
                return self._die()
        if self.row == 11:
            slot = self.col // 3
            if 0 <= slot < 5 and not self.homes[slot] and self.col % 3 == 1:
                self.homes[slot] = True
                self._score += 200 + int(self.timer) * 10
                if all(self.homes):
                    self._score += 500
                    self._level += 1
                    self.homes = [False] * 5
                    self.lanes = build_lanes(self._level)
                self._spawn()
        return Result.CONTINUE

    def attract_tick(self, dt: float) -> None:
        if self.cool <= 0:
            self._prev_hop = (0, 0, False)
            self.on_command(Command(0, -1, False, False, False, False, 0, False, True, False))
        if self.update(dt) is Result.GAME_OVER:
            self.reset()

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(COLOR_BG)
        for r in range(ROWS):
            y = self.oy + (ROWS - 1 - r) * FROG_TILE
            rect = pygame.Rect(self.ox, y, COLS * FROG_TILE, FROG_TILE)
            if r == 0 or r == 5 or r == 10:
                pygame.draw.rect(surf, (28, 36, 32), rect)
            elif 1 <= r <= 4:
                pygame.draw.rect(surf, (28, 20, 22), rect)
            elif 6 <= r <= 9:
                pygame.draw.rect(surf, (10, 40, 48), rect)
            elif r == 11:
                pygame.draw.rect(surf, (20, 20, 16), rect)
        for i in range(5):
            nest = pygame.Rect(self.ox + (i * 3 + 1) * FROG_TILE + 4, self.oy, FROG_TILE - 8, FROG_TILE - 8)
            pygame.draw.rect(surf, COLOR_AMBER, nest, border_radius=8)
            draw_ms_mark(surf, nest.inflate(-16, -16))
            if self.homes[i]:
                face = LOGOS.get("logo_nest")
                surf.blit(face, face.get_rect(center=nest.center))
        for lane in self.lanes:
            y_off = 0
            _ = y_off
            lane_y_base = self.oy + (ROWS - 1 - lane.row) * FROG_TILE
            for h in lane.hazards:
                if h.submerged:
                    continue
                rect = pygame.Rect(int(self.ox + h.x), lane_y_base + 6, int(h.w), FROG_TILE - 12)
                pygame.draw.rect(surf, h.color, rect, border_radius=4)
                if h.kind == "car":
                    draw_ms_mark(surf, pygame.Rect(rect.x + 6, rect.y + 6, 10, 10))
        prect = self._player_rect()
        logo = LOGOS.get_facing("logo_tile", self.facing)
        pose = "HOP" if self.hop_t > 0 else "IDLE"
        draw_stick_hero(surf, logo, prect.center, self.facing, pose)
        bar_w = int((self.timer / TIMER0) * 200)
        pygame.draw.rect(surf, COLOR_DANGER if self.timer < 5 else COLOR_CYAN, (self.ox, self.oy + ROWS * FROG_TILE + 8, bar_w, 8))
