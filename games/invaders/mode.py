"""InvadersMode — shoot the audit wave."""

from __future__ import annotations

import random

import pygame

from assets_loader import LOGOS, draw_ms_mark
from config import COLOR_AMBER, COLOR_BG, COLOR_CYAN, GameId, INTERNAL_W
from game_mode import GameMode, Result
from games.invaders.waves import Bomb, Invader, draw_invader, row_color
from input_map import Command

PLAY_W, PLAY_H = 720, 560


class InvadersMode(GameMode):
    id = GameId.INVADERS

    def __init__(self) -> None:
        self.ox = (INTERNAL_W - PLAY_W) // 2
        self.oy = 88
        self.px = PLAY_W / 2
        self.shot: tuple[float, float] | None = None
        self.cool = 0.0
        self.invaders: list[Invader] = []
        self.bombs: list[Bomb] = []
        self.ufo: tuple[float, float] | None = None
        self.ufo_t = 0.0
        self.bomb_t = 0.0
        self.dir = 1
        self.origin_x = 40.0
        self.origin_y = 40.0
        self.rows = 5
        self._score = 0
        self._level = 1
        self._lives = 3
        self.invuln = 0.0
        self._held_dx = 0
        self.stars = [(random.randrange(PLAY_W), random.randrange(PLAY_H)) for _ in range(40)]
        self.reset()

    def reset(self) -> None:
        self.px = PLAY_W / 2
        self.shot = None
        self.cool = 0.0
        self.rows = 5
        self._spawn_wave()
        self.bombs = []
        self.ufo = None
        self.ufo_t = 0.0
        self.bomb_t = 0.0
        self.dir = 1
        self._score = 0
        self._level = 1
        self._lives = 3
        self.invuln = 0.0
        self._held_dx = 0

    def _spawn_wave(self) -> None:
        self.invaders = [Invader(c, r) for r in range(self.rows) for c in range(8)]
        self.origin_x, self.origin_y = 40.0, 40.0
        self.dir = 1

    def score(self) -> int:
        return self._score

    def level(self) -> int:
        return self._level

    def lives(self) -> int:
        return self._lives

    def on_command(self, cmd: Command) -> None:
        self._held_dx = cmd.dx
        if cmd.action and self.shot is None and self.cool <= 0:
            self.shot = (self.px, PLAY_H - 70)
            self.cool = 0.28

    def _cell_pos(self, inv: Invader) -> tuple[float, float]:
        return self.origin_x + inv.col * 44, self.origin_y + inv.row * 40

    def update(self, dt: float) -> Result:
        self.px = max(30, min(PLAY_W - 30, self.px + self._held_dx * 320 * dt))
        self.cool = max(0.0, self.cool - dt)
        self.invuln = max(0.0, self.invuln - dt)
        if self.shot:
            sx, sy = self.shot
            sy -= 520 * dt
            self.shot = (sx, sy) if sy > 0 else None
        alive = [i for i in self.invaders if i.alive]
        speed = 40 * (1.10 ** (self._level - 1)) * (1.04 ** (40 - len(alive)))
        self.origin_x += self.dir * speed * dt
        xs = [self._cell_pos(i)[0] for i in alive] or [self.origin_x]
        if min(xs) < 20 or max(xs) > PLAY_W - 20:
            self.dir *= -1
            self.origin_y += 12
        if self.shot:
            sx, sy = self.shot
            for inv in alive:
                ix, iy = self._cell_pos(inv)
                if abs(sx - ix) < 16 and abs(sy - iy) < 14:
                    inv.alive = False
                    self.shot = None
                    self._score += (10, 20, 30, 40, 50)[min(4, self.rows - 1 - inv.row)]
                    break
        self.bomb_t += dt
        interval = max(0.45, 1.2 - 0.08 * (self._level - 1))
        if self.bomb_t >= interval and alive:
            self.bomb_t = 0
            shooter = random.choice(alive)
            ix, iy = self._cell_pos(shooter)
            self.bombs.append(Bomb(ix, iy + 12))
        for bomb in list(self.bombs):
            bomb.y += 220 * dt
            if bomb.y > PLAY_H:
                self.bombs.remove(bomb)
                continue
            if abs(bomb.x - self.px) < 18 and bomb.y > PLAY_H - 56 and self.invuln <= 0:
                self._lives -= 1
                self.invuln = 2.0
                self.bombs.clear()
                if self._lives <= 0:
                    return Result.GAME_OVER
        if any(self._cell_pos(i)[1] > PLAY_H - 70 for i in alive):
            return Result.GAME_OVER
        if not alive:
            self._score += 500
            self._level += 1
            self.rows = min(6, 5 + self._level // 3)
            self._spawn_wave()
        self.ufo_t += dt
        if self.ufo is None and self.ufo_t > 12:
            self.ufo = (-20.0, 24.0)
            self.ufo_t = 0
        if self.ufo:
            ux, uy = self.ufo
            ux += 180 * dt
            self.ufo = (ux, uy)
            if self.shot and abs(self.shot[0] - ux) < 22 and abs(self.shot[1] - uy) < 12:
                self._score += 150
                self.shot = None
                self.ufo = None
            elif ux > PLAY_W + 30:
                self.ufo = None
        return Result.CONTINUE

    def attract_tick(self, dt: float) -> None:
        self._held_dx = 1 if self.px < PLAY_W / 2 else -1
        if self.shot is None:
            self.shot = (self.px, PLAY_H - 70)
        if self.update(dt) is Result.GAME_OVER:
            self.reset()

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(COLOR_BG)
        for i, (sx, sy) in enumerate(self.stars):
            pygame.draw.circle(surf, COLOR_CYAN, (self.ox + (sx + i) % PLAY_W, self.oy + sy), 1)
        for inv in self.invaders:
            if not inv.alive:
                continue
            ix, iy = self._cell_pos(inv)
            draw_invader(surf, int(self.ox + ix), int(self.oy + iy), row_color(inv.row, self.rows))
        if self.shot:
            pygame.draw.rect(surf, COLOR_AMBER, (self.ox + int(self.shot[0]) - 2, self.oy + int(self.shot[1]) - 8, 4, 12))
        for bomb in self.bombs:
            pygame.draw.polygon(
                surf,
                (244, 241, 234),
                [
                    (self.ox + bomb.x, self.oy + bomb.y),
                    (self.ox + bomb.x - 5, self.oy + bomb.y + 10),
                    (self.ox + bomb.x + 5, self.oy + bomb.y + 10),
                ],
            )
        if self.ufo:
            ux, uy = self.ufo
            rect = pygame.Rect(self.ox + int(ux) - 28, self.oy + int(uy) - 12, 56, 28)
            pygame.draw.rect(surf, (80, 70, 50), rect, border_radius=4)
            draw_ms_mark(surf, pygame.Rect(rect.x + 8, rect.y + 2, 40, 24), label=True)
        ship = LOGOS.get("logo_ship")
        if self.invuln <= 0 or int(self.invuln * 8) % 2 == 0:
            surf.blit(ship, ship.get_rect(center=(self.ox + int(self.px), self.oy + PLAY_H - 40)))
